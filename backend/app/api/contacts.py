from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.contact import Contact
from app.models.user import User
from app.schemas.contact import (
    ContactCreate,
    ContactListResponse,
    ContactResponse,
    ContactUpdate,
)
from app.schemas.responses import (
    BioRefreshData,
    ContactStatsData,
    CsvImportResult,
    DeletedData,
    DuplicateContactData,
    Envelope,
    LinkedInImportResult,
    LinkedInMessagesImportResult,
    MergedContactData,
    ScoresRecalculatedData,
    SyncStartedData,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/contacts", tags=["contacts"])


def envelope(data: Any, error: str | None = None, meta: dict | None = None) -> dict:
    return {"data": data, "error": error, "meta": meta}


@router.get("", response_model=ContactListResponse)
async def list_contacts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    tag: str | None = Query(None),
    source: str | None = Query(None),
    score: str | None = Query(None, description="Filter by score tier: strong (8-10), active (4-7), dormant (0-3)"),
    date_from: str | None = Query(None, description="Filter contacts created on or after this date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="Filter contacts created on or before this date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContactListResponse:
    from app.services.contact_search import list_contacts_paginated

    return await list_contacts_paginated(
        db,
        current_user.id,
        page=page,
        page_size=page_size,
        search=search,
        tag=tag,
        source=source,
        score=score,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/tags", response_model=Envelope[list[str]])
async def list_tags(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Envelope[list[str]]:
    """Return all unique tags used across the user's contacts."""
    result = await db.execute(
        select(func.unnest(Contact.tags)).where(
            Contact.user_id == current_user.id,
            Contact.tags.isnot(None),
        ).distinct()
    )
    tags = sorted(row[0] for row in result.all())
    return {"data": tags, "error": None}


@router.get("/stats", response_model=Envelope[ContactStatsData])
async def contact_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Envelope[ContactStatsData]:
    """Return aggregate contact stats for the dashboard."""
    result = await db.execute(
        select(
            func.count().label("total"),
            func.count().filter(Contact.relationship_score >= 8).label("strong"),
            func.count().filter(
                Contact.relationship_score >= 4,
                Contact.relationship_score < 8,
            ).label("active"),
            func.count().filter(Contact.relationship_score < 4).label("dormant"),
        ).where(Contact.user_id == current_user.id)
    )
    row = result.one()
    return {
        "data": {
            "total": row.total,
            "strong": row.strong,
            "active": row.active,
            "dormant": row.dormant,
        },
        "error": None,
    }


@router.post("", response_model=Envelope[ContactResponse], status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_in: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Envelope[ContactResponse]:
    contact = Contact(**contact_in.model_dump(), user_id=current_user.id)
    db.add(contact)
    await db.flush()
    await db.refresh(contact)
    return envelope(ContactResponse.model_validate(contact).model_dump())


@router.get("/{contact_id}", response_model=Envelope[ContactResponse])
async def get_contact(
    contact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Envelope[ContactResponse]:
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.user_id == current_user.id)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return envelope(ContactResponse.model_validate(contact).model_dump())


@router.put("/{contact_id}", response_model=Envelope[ContactResponse])
async def update_contact(
    contact_id: uuid.UUID,
    contact_in: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Envelope[ContactResponse]:
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.user_id == current_user.id)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    for field, value in contact_in.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)

    await db.flush()
    await db.refresh(contact)
    return envelope(ContactResponse.model_validate(contact).model_dump())


@router.delete("/{contact_id}", response_model=Envelope[DeletedData])
async def delete_contact(
    contact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Envelope[DeletedData]:
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.user_id == current_user.id)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    await db.delete(contact)
    return envelope({"id": str(contact_id), "deleted": True})


@router.get("/{contact_id}/duplicates", response_model=Envelope[list[DuplicateContactData]])
async def find_contact_duplicates(
    contact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Envelope[list[DuplicateContactData]]:
    """Find possible duplicates for a specific contact."""
    from app.services.identity_resolution import compute_adaptive_score, build_blocking_keys

    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.user_id == current_user.id)
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    # Get all other contacts for this user
    all_result = await db.execute(
        select(Contact).where(Contact.user_id == current_user.id, Contact.id != contact_id)
    )
    others: list[Contact] = list(all_result.scalars().all())

    # Use blocking keys for efficiency
    target_keys = set(build_blocking_keys(target))

    duplicates = []
    for other in others:
        other_keys = set(build_blocking_keys(other))
        if not target_keys & other_keys:
            continue
        score = compute_adaptive_score(target, other)
        if score < 0.40:
            continue
        duplicates.append({
            "id": str(other.id),
            "full_name": other.full_name,
            "given_name": other.given_name,
            "family_name": other.family_name,
            "emails": other.emails or [],
            "phones": other.phones or [],
            "company": other.company,
            "title": other.title,
            "twitter_handle": other.twitter_handle,
            "telegram_username": other.telegram_username,
            "score": round(score, 2),
        })

    duplicates.sort(key=lambda d: d["score"], reverse=True)
    return envelope(duplicates[:20])


@router.post("/{contact_id}/merge/{other_id}", response_model=Envelope[MergedContactData])
async def merge_contact_pair(
    contact_id: uuid.UUID,
    other_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Envelope[MergedContactData]:
    """Merge other_id into contact_id. Returns the surviving contact."""
    from app.services.identity_resolution import merge_contacts

    # Verify both contacts belong to current user
    for cid in (contact_id, other_id):
        result = await db.execute(
            select(Contact).where(Contact.id == cid, Contact.user_id == current_user.id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Contact {cid} not found")

    match_record = await merge_contacts(contact_id, other_id, db)
    await db.flush()

    # Re-fetch the surviving contact
    result = await db.execute(select(Contact).where(Contact.id == match_record.contact_a_id))
    surviving = result.scalar_one()

    return envelope({
        "id": str(surviving.id),
        "full_name": surviving.full_name,
        "merged_contact_id": str(other_id),
    })


@router.post("/import/csv", response_model=Envelope[CsvImportResult])
async def import_contacts_csv(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Envelope[CsvImportResult]:
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a CSV")

    from app.services.contact_import import import_csv

    content = await file.read()
    result = await import_csv(content, current_user.id, db)
    return envelope(result)


@router.post("/import/linkedin", response_model=Envelope[LinkedInImportResult])
async def import_linkedin_csv(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Envelope[LinkedInImportResult]:
    """Import contacts from LinkedIn Connections.csv export."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a CSV")

    from app.services.contact_import import import_linkedin_connections

    content = await file.read()
    result = await import_linkedin_connections(content, current_user.id, db)
    return envelope(result)


@router.post("/import/linkedin-messages", response_model=Envelope[LinkedInMessagesImportResult])
async def import_linkedin_messages(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Envelope[LinkedInMessagesImportResult]:
    """Import LinkedIn messages.csv and create interactions matched to existing contacts."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a CSV")

    from app.services.contact_import import import_linkedin_messages as _import_messages

    content = await file.read()
    user_name = (current_user.full_name or current_user.email or "").lower()
    result = await _import_messages(content, current_user.id, user_name, db)
    return envelope(result)


@router.post("/sync/google", response_model=Envelope[SyncStartedData])
async def sync_google_contacts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Envelope[SyncStartedData]:
    """Dispatch a background Google Contacts sync.

    Returns immediately. A notification is created when sync completes.
    """
    from app.models.google_account import GoogleAccount

    ga_result = await db.execute(
        select(GoogleAccount).where(GoogleAccount.user_id == current_user.id)
    )
    has_accounts = ga_result.scalars().first() is not None
    if not has_accounts and not current_user.google_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Google account connected. Complete Google OAuth first.",
        )

    from app.services.tasks import sync_google_contacts_for_user
    sync_google_contacts_for_user.delay(str(current_user.id))

    return envelope({"status": "started"})


@router.post("/sync/google-calendar", response_model=Envelope[SyncStartedData])
async def sync_google_calendar(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Envelope[SyncStartedData]:
    """Dispatch a background Google Calendar sync.

    Returns immediately. A notification is created when sync completes.
    """
    from app.models.google_account import GoogleAccount

    ga_result = await db.execute(
        select(GoogleAccount).where(GoogleAccount.user_id == current_user.id)
    )
    has_accounts = ga_result.scalars().first() is not None
    if not has_accounts and not current_user.google_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Google account connected. Complete Google OAuth first.",
        )

    from app.services.tasks import sync_google_calendar_for_user
    sync_google_calendar_for_user.delay(str(current_user.id))

    return envelope({"status": "started"})


@router.post("/sync/twitter", response_model=Envelope[SyncStartedData])
async def sync_twitter(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Envelope[SyncStartedData]:
    """Dispatch a background Twitter sync (DMs + mentions + bios).

    Returns immediately. A notification is created when sync completes.
    """
    if not current_user.twitter_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Twitter account not connected. Complete Twitter OAuth first.",
        )

    from app.services.tasks import sync_twitter_dms_for_user
    sync_twitter_dms_for_user.delay(str(current_user.id))

    return envelope({"status": "started"})


@router.post("/scores/recalculate", response_model=Envelope[ScoresRecalculatedData])
async def recalculate_scores(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Envelope[ScoresRecalculatedData]:
    """Recalculate relationship scores for all contacts of the authenticated user."""
    from app.services.scoring import calculate_score

    contacts_result = await db.execute(
        select(Contact.id).where(Contact.user_id == current_user.id)
    )
    updated = 0
    for (contact_id,) in contacts_result.all():
        await calculate_score(contact_id, db)
        updated += 1

    await db.flush()
    return envelope({"updated": updated})


from app.core.redis import get_redis

@router.post("/{contact_id}/refresh-bios", response_model=Envelope[BioRefreshData])
async def refresh_contact_bios(
    contact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Envelope[BioRefreshData]:
    """Check for bio updates on Twitter and Telegram for a single contact.

    Rate-limited to once per 24 hours per contact.
    """
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.user_id == current_user.id)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    r = get_redis()
    cache_key = f"bio_check:{contact_id}"
    if await r.exists(cache_key):
        return envelope({"skipped": True, "reason": "checked_recently"})

    from app.services.bio_refresh import refresh_contact_bios as _refresh_bios, _BIO_CHECK_TTL

    changes = await _refresh_bios(contact, current_user, db)

    await r.setex(cache_key, _BIO_CHECK_TTL, "1")
    return envelope(changes)
