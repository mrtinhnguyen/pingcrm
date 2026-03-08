"""Contact search and filter query builder."""
from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

from sqlalchemy import String, cast, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.interaction import Interaction
from app.schemas.contact import ContactListResponse, ContactResponse, PaginationMeta


def build_contact_filter_query(
    user_id: object,
    *,
    search: str | None = None,
    tag: str | None = None,
    source: str | None = None,
    score: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> object:
    """Build a SQLAlchemy select query for contacts with optional filters.

    Args:
        user_id: The authenticated user's UUID.
        search: Full-text search string (matched against multiple fields).
        tag: Filter to contacts that have this tag.
        source: Filter to contacts from this source.
        score: Score tier filter: 'strong' (8-10), 'active' (4-7), 'dormant' (0-3).
        date_from: ISO date string (YYYY-MM-DD) — include contacts created on/after.
        date_to: ISO date string (YYYY-MM-DD) — include contacts created on/before.

    Returns:
        A SQLAlchemy select statement (not yet executed).
    """
    base_query = select(Contact).where(
        Contact.user_id == user_id,
        Contact.priority_level != "archived",
    )

    if search:
        # Escape SQL LIKE wildcards to prevent wildcard injection
        safe_search = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{safe_search}%"
        interaction_match = exists(
            select(Interaction.id).where(
                Interaction.contact_id == Contact.id,
                Interaction.content_preview.ilike(pattern),
            )
        )
        base_query = base_query.where(
            or_(
                Contact.full_name.ilike(pattern),
                Contact.given_name.ilike(pattern),
                Contact.family_name.ilike(pattern),
                Contact.company.ilike(pattern),
                Contact.title.ilike(pattern),
                Contact.twitter_handle.ilike(pattern),
                Contact.telegram_username.ilike(pattern),
                Contact.twitter_bio.ilike(pattern),
                Contact.telegram_bio.ilike(pattern),
                Contact.notes.ilike(pattern),
                Contact.source.ilike(pattern),
                cast(Contact.emails, String).ilike(pattern),
                cast(Contact.phones, String).ilike(pattern),
                interaction_match,
            )
        )

    if tag:
        base_query = base_query.where(Contact.tags.any(tag))

    if source:
        base_query = base_query.where(Contact.source == source)

    if date_from:
        try:
            dt_from = datetime.strptime(date_from, "%Y-%m-%d").replace(tzinfo=UTC)
            base_query = base_query.where(Contact.created_at >= dt_from)
        except ValueError:
            pass

    if date_to:
        try:
            dt_to = datetime.strptime(date_to, "%Y-%m-%d").replace(tzinfo=UTC) + timedelta(days=1)
            base_query = base_query.where(Contact.created_at < dt_to)
        except ValueError:
            pass

    if score == "strong":
        base_query = base_query.where(Contact.relationship_score >= 8)
    elif score == "active":
        base_query = base_query.where(
            Contact.relationship_score >= 4, Contact.relationship_score <= 7
        )
    elif score == "dormant":
        base_query = base_query.where(Contact.relationship_score <= 3)

    return base_query


async def list_contacts_paginated(
    db: AsyncSession,
    user_id: object,
    *,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    tag: str | None = None,
    source: str | None = None,
    score: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> ContactListResponse:
    """Execute a filtered, paginated contact query and return the response model."""
    base_query = build_contact_filter_query(
        user_id,
        search=search,
        tag=tag,
        source=source,
        score=score,
        date_from=date_from,
        date_to=date_to,
    )

    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        base_query.order_by(
            Contact.relationship_score.desc(), Contact.created_at.desc()
        ).offset(offset).limit(page_size)
    )
    contacts = result.scalars().all()

    return ContactListResponse(
        data=[ContactResponse.model_validate(c) for c in contacts],
        error=None,
        meta=PaginationMeta(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total > 0 else 1,
        ),
    )
