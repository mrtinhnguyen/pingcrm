"""Sync history recording helpers."""
import json
import time
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sync_event import SyncEvent


async def record_sync_start(
    user_id: uuid.UUID,
    platform: str,
    sync_type: str,
    db: AsyncSession,
) -> SyncEvent:
    """Create a sync event record at the start of a sync."""
    event = SyncEvent(
        user_id=user_id,
        platform=platform,
        sync_type=sync_type,
        status="started",
        started_at=datetime.now(UTC),
    )
    db.add(event)
    await db.flush()
    return event


async def record_sync_complete(
    event: SyncEvent,
    *,
    records_created: int = 0,
    records_updated: int = 0,
    records_failed: int = 0,
    details: dict | None = None,
    db: AsyncSession,
) -> None:
    """Mark a sync event as completed successfully."""
    now = datetime.now(UTC)
    event.status = "success"
    event.records_created = records_created
    event.records_updated = records_updated
    event.records_failed = records_failed
    event.completed_at = now
    if event.started_at:
        event.duration_ms = int((now - event.started_at).total_seconds() * 1000)
    if details:
        event.details = json.dumps(details)
    await db.flush()


async def record_sync_failure(
    event: SyncEvent,
    error: str,
    *,
    records_created: int = 0,
    db: AsyncSession,
) -> None:
    """Mark a sync event as failed."""
    now = datetime.now(UTC)
    event.status = "failed"
    event.records_created = records_created
    event.error_message = error[:2000]  # cap error length
    event.completed_at = now
    if event.started_at:
        event.duration_ms = int((now - event.started_at).total_seconds() * 1000)
    await db.flush()
