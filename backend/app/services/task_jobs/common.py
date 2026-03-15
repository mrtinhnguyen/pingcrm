"""Shared helpers and utility tasks for all Celery task modules."""
from __future__ import annotations

import asyncio
import logging
import uuid

import httpx  # noqa: F401 — re-exported for sub-modules that import from here

from celery import shared_task
from sqlalchemy import select  # noqa: F401 — re-exported for sub-modules

from app.core.celery_app import celery_app  # noqa: F401 — registers the app
from app.core.database import task_session
from app.models.contact import Contact  # noqa: F401 — re-exported
from app.models.user import User  # noqa: F401 — re-exported

logger = logging.getLogger(__name__)


def _run(coro):
    """Run an async coroutine synchronously inside a Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def dismiss_suggestions_for_contacts(contact_ids: list[uuid.UUID]) -> int:
    """Dismiss pending follow-up suggestions for contacts that just received new interactions."""
    if not contact_ids:
        return 0
    from sqlalchemy import update
    from app.models.follow_up import FollowUpSuggestion

    async with task_session() as db:
        result = await db.execute(
            update(FollowUpSuggestion)
            .where(
                FollowUpSuggestion.contact_id.in_(contact_ids),
                FollowUpSuggestion.status == "pending",
            )
            .values(status="dismissed")
        )
        await db.commit()
        return result.rowcount  # type: ignore[return-value]


@shared_task(name="app.services.tasks.notify_sync_failure")
def notify_sync_failure(user_id: str, platform: str, error: str) -> None:
    """Create a notification when a background sync exhausts retries."""
    from app.models.notification import Notification

    async def _create(uid: uuid.UUID) -> None:
        async with task_session() as db:
            db.add(Notification(
                user_id=uid,
                notification_type="sync",
                title=f"{platform} sync failed",
                body=f"Sync failed after multiple retries: {error[:200]}",
                link="/settings",
            ))
            await db.commit()

    _run(_create(uuid.UUID(user_id)))


@shared_task(name="app.services.tasks.notify_tagging_failure")
def notify_tagging_failure(user_id: str, error: str) -> None:
    """Create a notification when auto-tagging fails outside the main loop."""
    from app.models.notification import Notification

    async def _create(uid: uuid.UUID) -> None:
        async with task_session() as db:
            db.add(Notification(
                user_id=uid,
                notification_type="tagging",
                title="Auto-tagging failed",
                body=error[:500],
                link="/settings?tab=tags",
            ))
            await db.commit()

    _run(_create(uuid.UUID(user_id)))
