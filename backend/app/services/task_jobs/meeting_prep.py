"""Celery beat task: scan upcoming meetings and send prep emails."""
from __future__ import annotations

import redis as _redis
from celery import shared_task
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from sqlalchemy import select

from app.core.config import settings
from app.core.database import task_session
from app.models.google_account import GoogleAccount
from app.models.notification import Notification
from app.models.user import User
from app.services.task_jobs.common import _run, logger


@shared_task(name="app.services.tasks.scan_meeting_preps")
def scan_meeting_preps() -> dict:
    """Scan for meetings starting in ~30 minutes and email prep briefs."""

    async def _scan() -> dict:
        from app.integrations.gmail_send import send_email
        from app.services.meeting_prep import (
            build_prep_brief,
            compose_prep_email,
            generate_talking_points,
            get_upcoming_meetings,
        )

        r = _redis.from_url(settings.REDIS_URL, decode_responses=True)

        now = datetime.now(UTC)
        window_start = now + timedelta(minutes=30)
        window_end = now + timedelta(minutes=40)

        sent = 0
        skipped = 0
        errors = 0

        async with task_session() as db:
            # Get distinct user_ids from GoogleAccount table
            ga_result = await db.execute(
                select(GoogleAccount.user_id).distinct()
            )
            ga_user_ids = {row for row in ga_result.scalars().all()}

            # Also get users with legacy google_refresh_token
            legacy_result = await db.execute(
                select(User.id).where(User.google_refresh_token.isnot(None))
            )
            legacy_user_ids = {row for row in legacy_result.scalars().all()}

            all_user_ids = ga_user_ids | legacy_user_ids

            for user_id in all_user_ids:
                # Fetch user
                user_result = await db.execute(
                    select(User).where(User.id == user_id)
                )
                user = user_result.scalar_one_or_none()
                if user is None:
                    continue

                # Check meeting_prep_enabled setting (default True)
                sync_settings = user.sync_settings or {}
                gmail_settings = sync_settings.get("gmail", {})
                if not gmail_settings.get("meeting_prep_enabled", True):
                    skipped += 1
                    continue

                # Get GoogleAccount entries for this user
                accounts_result = await db.execute(
                    select(GoogleAccount).where(GoogleAccount.user_id == user_id)
                )
                google_accounts = list(accounts_result.scalars().all())

                # Get upcoming meetings
                meetings = await get_upcoming_meetings(
                    user_id, window_start, window_end, db
                )

                for meeting in meetings:
                    event_id = meeting["event_id"]
                    dedup_key = f"meeting_prep:{user_id}:{event_id}"

                    # Redis dedup check
                    if r.exists(dedup_key):
                        skipped += 1
                        continue

                    contact_ids = meeting.get("contact_ids", [])
                    if not contact_ids:
                        skipped += 1
                        continue

                    briefs = await build_prep_brief(contact_ids, db)
                    if not briefs:
                        skipped += 1
                        continue

                    talking_points = await generate_talking_points(
                        briefs, meeting["title"]
                    )
                    subject, html = compose_prep_email(
                        meeting, briefs, talking_points
                    )

                    # Determine which Google account to use for sending
                    if google_accounts:
                        ga = google_accounts[0]
                    elif user.google_refresh_token:
                        ga = SimpleNamespace(
                            refresh_token=user.google_refresh_token,
                            email=user.email,
                        )
                    else:
                        skipped += 1
                        continue

                    result = send_email(ga, subject, html)

                    if result is True:
                        r.set(dedup_key, "1", ex=86400)  # 24h TTL
                        sent += 1
                    elif result == "auth_error":
                        db.add(Notification(
                            user_id=user_id,
                            notification_type="system",
                            title="Re-authorize Gmail for meeting prep emails",
                            body="Your Gmail credentials have expired. Please re-connect Gmail in Settings to continue receiving meeting prep emails.",
                            link="/settings",
                        ))
                        # Stop processing meetings for this user
                        break
                    else:
                        errors += 1

            await db.commit()

        return {"sent": sent, "skipped": skipped, "errors": errors}

    return _run(_scan())
