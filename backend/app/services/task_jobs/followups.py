"""Follow-up suggestion and weekly digest Celery tasks."""
from __future__ import annotations

import uuid

from celery import shared_task
from sqlalchemy import select

from app.core.database import task_session
from app.models.user import User
from app.services.task_jobs.common import _run, logger


@shared_task(name="app.services.tasks.generate_weekly_suggestions", bind=True, max_retries=3)
def generate_weekly_suggestions(self, user_id: str) -> dict:
    """Generate follow-up suggestions for a single user.

    Args:
        user_id: String representation of the user's UUID.

    Returns:
        A dict with ``generated`` count and ``status``.
    """
    async def _generate(uid: uuid.UUID) -> dict:
        from app.services.followup_engine import generate_suggestions
        from app.services.notifications import notify_new_suggestions

        async with task_session() as db:
            result = await db.execute(select(User).where(User.id == uid))
            user = result.scalar_one_or_none()
            if user is None:
                logger.warning("generate_weekly_suggestions: user %s not found.", uid)
                return {"status": "user_not_found", "generated": 0}

            ps = user.priority_settings
            suggestions = await generate_suggestions(uid, db, priority_settings=ps)
            if suggestions:
                await notify_new_suggestions(uid, len(suggestions), db)
            await db.commit()

        return {"status": "ok", "generated": len(suggestions)}

    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        logger.error("generate_weekly_suggestions: invalid user_id %r", user_id)
        return {"status": "invalid_user_id", "generated": 0}

    try:
        return _run(_generate(uid))
    except Exception as exc:
        logger.exception("generate_weekly_suggestions failed for %s, retrying.", user_id)
        raise self.retry(exc=exc, countdown=60) from exc


@shared_task(name="app.services.tasks.send_weekly_digests")
def send_weekly_digests() -> dict:
    """Beat-scheduled task: send weekly digest emails to all users (Mondays 09:00 UTC).

    Returns:
        A dict with ``sent`` and ``errors`` counts.
    """
    async def _send_all() -> dict:
        from app.services.digest_email import send_weekly_digest

        sent = 0
        errors = 0

        async with task_session() as db:
            result = await db.execute(select(User.id))
            user_ids = result.scalars().all()

            for uid in user_ids:
                try:
                    await send_weekly_digest(uid, db)
                    sent += 1
                except Exception:
                    logger.exception("send_weekly_digests: failed for user %s.", uid)
                    errors += 1

        return {"sent": sent, "errors": errors}

    result = _run(_send_all())
    logger.info(
        "send_weekly_digests: sent=%d errors=%d", result["sent"], result["errors"]
    )
    return result


@shared_task(name="app.services.tasks.generate_suggestions_all")
def generate_suggestions_all() -> dict:
    """Daily task: generate follow-up suggestions (incl. birthday) for all users."""
    async def _generate_all() -> dict:
        from app.services.followup_engine import generate_suggestions
        from app.services.notifications import notify_new_suggestions

        generated = 0
        errors = 0

        async with task_session() as db:
            result = await db.execute(select(User))
            users = result.scalars().all()

            for user in users:
                try:
                    suggestions = await generate_suggestions(
                        user.id, db, priority_settings=user.priority_settings,
                    )
                    if suggestions:
                        await notify_new_suggestions(user.id, len(suggestions), db)
                    generated += len(suggestions)
                except Exception:
                    logger.exception("generate_suggestions_all: failed for user %s.", user.id)
                    errors += 1

            await db.commit()

        return {"generated": generated, "errors": errors}

    result = _run(_generate_all())
    logger.info(
        "generate_suggestions_all: generated=%d errors=%d",
        result["generated"], result["errors"],
    )
    return result


@shared_task(name="app.services.tasks.reactivate_snoozed_suggestions")
def reactivate_snoozed_suggestions() -> dict:
    """Hourly task: set snoozed suggestions back to pending when their scheduled_for has passed."""
    async def _reactivate() -> int:
        from datetime import UTC, datetime

        from app.models.follow_up import FollowUpSuggestion
        from sqlalchemy import update

        async with task_session() as db:
            now = datetime.now(UTC)
            result = await db.execute(
                update(FollowUpSuggestion)
                .where(
                    FollowUpSuggestion.status == "snoozed",
                    FollowUpSuggestion.scheduled_for <= now,
                )
                .values(status="pending")
                .returning(FollowUpSuggestion.id)
            )
            reactivated = len(result.all())
            await db.commit()
            return reactivated

    count = _run(_reactivate())
    logger.info("reactivate_snoozed_suggestions: reactivated %d suggestion(s).", count)
    return {"reactivated": count}
