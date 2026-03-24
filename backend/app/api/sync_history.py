"""Sync history API — view past sync events."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.sync_event import SyncEvent
from app.models.user import User

router = APIRouter(prefix="/api/v1/sync-history", tags=["sync-history"])


@router.get("")
async def list_sync_events(
    platform: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List sync events for the current user, most recent first."""
    filters = [SyncEvent.user_id == current_user.id]
    if platform:
        filters.append(SyncEvent.platform == platform)
    if status:
        filters.append(SyncEvent.status == status)

    count_result = await db.execute(
        select(func.count()).select_from(SyncEvent).where(*filters)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(SyncEvent)
        .where(*filters)
        .order_by(SyncEvent.started_at.desc())
        .limit(limit)
        .offset(offset)
    )
    events = result.scalars().all()

    return {
        "data": [
            {
                "id": str(e.id),
                "platform": e.platform,
                "sync_type": e.sync_type,
                "status": e.status,
                "records_created": e.records_created,
                "records_updated": e.records_updated,
                "records_failed": e.records_failed,
                "duration_ms": e.duration_ms,
                "error_message": e.error_message,
                "details": e.details,
                "started_at": e.started_at.isoformat() if e.started_at else None,
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
            }
            for e in events
        ],
        "error": None,
        "meta": {"total": total, "limit": limit, "offset": offset},
    }


@router.get("/stats")
async def sync_stats(
    platform: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Quick stats: total syncs, success rate, last sync per platform."""
    filters = [SyncEvent.user_id == current_user.id]
    if platform:
        filters.append(SyncEvent.platform == platform)

    result = await db.execute(
        select(
            SyncEvent.platform,
            func.count().label("total"),
            func.count().filter(SyncEvent.status == "success").label("success"),
            func.count().filter(SyncEvent.status == "failed").label("failed"),
            func.max(SyncEvent.started_at).label("last_sync"),
        )
        .where(*filters)
        .group_by(SyncEvent.platform)
    )

    stats = {}
    for row in result.all():
        stats[row.platform] = {
            "total_syncs": row.total,
            "success_count": row.success,
            "failed_count": row.failed,
            "success_rate": round(row.success / row.total * 100, 1) if row.total > 0 else 0,
            "last_sync": row.last_sync.isoformat() if row.last_sync else None,
        }

    return {"data": stats, "error": None}
