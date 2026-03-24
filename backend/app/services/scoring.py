import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, func, case, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.interaction import Interaction


@dataclass
class ScoreBreakdown:
    total: int              # 0-10 composite
    reciprocity: int        # 0-4
    recency: int            # 0-3
    frequency: int          # 0-2
    breadth: int            # 0-1
    tenure: int = 0         # 0-2 (bonus for long-term contacts)
    inbound_365d: int = 0   # raw inbound count
    outbound_365d: int = 0  # raw outbound count
    count_30d: int = 0      # interactions in last 30d
    count_90d: int = 0      # interactions in 30-90d window
    platforms: list[str] = field(default_factory=list)  # distinct platform names
    interaction_count: int = 0  # lifetime total


async def calculate_score_breakdown(contact_id: uuid.UUID, db: AsyncSession) -> ScoreBreakdown:
    """Calculate full score breakdown for a contact.

    Includes tenure bonus and extended decay for long-term contacts:
    - Interactions 1-2 years old contribute at 0.05x weight
    - Interactions 2-5 years old contribute at 0.02x weight
    - Tenure bonus: +1 for 20+ lifetime interactions spanning 1+ year,
      +2 for 50+ interactions spanning 2+ years
    """
    now = datetime.now(UTC)
    d30 = now - timedelta(days=30)
    d90 = now - timedelta(days=90)
    d365 = now - timedelta(days=365)
    d2y = now - timedelta(days=730)
    d5y = now - timedelta(days=1825)

    # Query 1: inbound/outbound counts in last 365 days + extended windows
    counts_result = await db.execute(
        select(
            # Last 365 days
            func.count().filter(
                Interaction.direction == "inbound",
                Interaction.occurred_at >= d365,
            ).label("inbound"),
            func.count().filter(
                Interaction.direction == "outbound",
                Interaction.occurred_at >= d365,
            ).label("outbound"),
            # 1-2 year window
            func.count().filter(
                Interaction.direction == "inbound",
                Interaction.occurred_at >= d2y,
                Interaction.occurred_at < d365,
            ).label("inbound_1_2y"),
            func.count().filter(
                Interaction.direction == "outbound",
                Interaction.occurred_at >= d2y,
                Interaction.occurred_at < d365,
            ).label("outbound_1_2y"),
            # 2-5 year window
            func.count().filter(
                Interaction.direction == "inbound",
                Interaction.occurred_at >= d5y,
                Interaction.occurred_at < d2y,
            ).label("inbound_2_5y"),
            func.count().filter(
                Interaction.direction == "outbound",
                Interaction.occurred_at >= d5y,
                Interaction.occurred_at < d2y,
            ).label("outbound_2_5y"),
        )
        .select_from(Interaction)
        .where(Interaction.contact_id == contact_id)
    )
    row = counts_result.one()
    inbound_count = row.inbound
    outbound_count = row.outbound
    total = inbound_count + outbound_count

    # Extended decay: add old interactions at reduced weight for reciprocity
    effective_inbound = inbound_count + row.inbound_1_2y * 0.05 + row.inbound_2_5y * 0.02
    effective_outbound = outbound_count + row.outbound_1_2y * 0.05 + row.outbound_2_5y * 0.02
    effective_total = effective_inbound + effective_outbound

    # Reciprocity (0-4) — uses extended decay counts
    if effective_total == 0 or effective_inbound == 0:
        reciprocity = 0
    else:
        ratio = min(effective_inbound, effective_outbound) / max(effective_inbound, effective_outbound)
        reciprocity = round(ratio * 4)

    # Query 2: last inbound date + last any date
    dates_result = await db.execute(
        select(
            func.max(
                case(
                    (Interaction.direction == "inbound", Interaction.occurred_at),
                )
            ).label("last_inbound"),
            func.max(Interaction.occurred_at).label("last_any"),
        )
        .select_from(Interaction)
        .where(Interaction.contact_id == contact_id)
    )
    dates_row = dates_result.one()
    last_inbound = dates_row.last_inbound
    last_any = dates_row.last_any

    # Recency (0-3)
    if last_inbound is not None:
        base_date = last_inbound if last_inbound.tzinfo else last_inbound.replace(tzinfo=UTC)
        multiplier = 1.0
    elif last_any is not None:
        base_date = last_any if last_any.tzinfo else last_any.replace(tzinfo=UTC)
        multiplier = 0.5
    else:
        base_date = None
        multiplier = 0.0

    if base_date is not None:
        days_ago = (now - base_date).days
        if days_ago <= 7:
            raw = 3
        elif days_ago <= 30:
            raw = 2
        elif days_ago <= 90:
            raw = 1
        else:
            raw = 0
        recency = round(raw * multiplier)
    else:
        recency = 0

    # Query 3: interaction counts per time window (including extended decay)
    freq_result = await db.execute(
        select(
            func.count().filter(Interaction.occurred_at >= d30).label("c30"),
            func.count().filter(
                Interaction.occurred_at >= d90,
                Interaction.occurred_at < d30,
            ).label("c90"),
            func.count().filter(
                Interaction.occurred_at >= d365,
                Interaction.occurred_at < d90,
            ).label("c365"),
            func.count().filter(
                Interaction.occurred_at >= d2y,
                Interaction.occurred_at < d365,
            ).label("c1_2y"),
            func.count().filter(
                Interaction.occurred_at >= d5y,
                Interaction.occurred_at < d2y,
            ).label("c2_5y"),
        )
        .select_from(Interaction)
        .where(Interaction.contact_id == contact_id)
    )
    freq_row = freq_result.one()
    count_30d = freq_row.c30
    count_90d = freq_row.c90
    # Extended decay: old interactions contribute at reduced rates
    weighted = (
        count_30d * 1.0
        + count_90d * 0.3
        + freq_row.c365 * 0.1
        + freq_row.c1_2y * 0.05
        + freq_row.c2_5y * 0.02
    )
    if weighted >= 8:
        frequency = 2
    elif weighted >= 3:
        frequency = 1
    else:
        frequency = 0

    # Query 4: platforms + lifetime count + first interaction (merged from 3 queries)
    meta_result = await db.execute(
        select(
            func.count().label("lifetime_count"),
            func.min(Interaction.occurred_at).label("first_at"),
            func.array_agg(distinct(Interaction.platform)).label("platforms"),
        )
        .select_from(Interaction)
        .where(Interaction.contact_id == contact_id)
    )
    meta_row = meta_result.one()
    interaction_count = meta_row.lifetime_count
    first_at = meta_row.first_at
    platforms = [p for p in (meta_row.platforms or []) if p is not None]
    breadth = 1 if len(platforms) >= 2 else 0

    # Tenure bonus: acknowledges established relationships during quiet periods
    tenure = 0
    if first_at is not None:
        first_date = first_at if first_at.tzinfo else first_at.replace(tzinfo=UTC)
        tenure_years = (now - first_date).days / 365.25
        if interaction_count >= 50 and tenure_years >= 2:
            tenure = 2
        elif interaction_count >= 20 and tenure_years >= 1:
            tenure = 1

    score = min(10, reciprocity + recency + frequency + breadth + tenure)

    return ScoreBreakdown(
        total=score,
        reciprocity=reciprocity,
        recency=recency,
        frequency=frequency,
        breadth=breadth,
        tenure=tenure,
        inbound_365d=inbound_count,
        outbound_365d=outbound_count,
        count_30d=count_30d,
        count_90d=count_90d,
        platforms=platforms,
        interaction_count=interaction_count,
    )


async def calculate_score(contact_id: uuid.UUID, db: AsyncSession) -> int:
    """Calculate and persist relationship score (0-10) for a contact."""
    breakdown = await calculate_score_breakdown(contact_id, db)

    contact_result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = contact_result.scalar_one_or_none()
    if contact:
        contact.relationship_score = breakdown.total
        contact.interaction_count = breakdown.interaction_count
        await db.flush()

    return breakdown.total
