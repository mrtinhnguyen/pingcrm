"""Bio refresh service — fetch updated Twitter and Telegram bios for a contact."""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.notification import Notification
from app.models.user import User

logger = logging.getLogger(__name__)

_BIO_CHECK_TTL = 86400  # 24 hours


async def refresh_contact_bios(
    contact: Contact,
    current_user: User,
    db: AsyncSession,
) -> dict[str, Any]:
    """Fetch updated bios from Twitter and Telegram for *contact*.

    Persists changes to *contact* in place and creates Notification rows when
    a bio has changed from a previously-known value.

    Args:
        contact: The contact whose bios should be refreshed (already loaded).
        current_user: The authenticated user (owner of the contact).
        db: Database session.

    Returns:
        A dict with keys ``twitter_bio_changed`` (bool) and
        ``telegram_bio_changed`` (bool).
    """
    changes: dict[str, Any] = {
        "twitter_bio_changed": False,
        "telegram_bio_changed": False,
    }

    # ------------------------------------------------------------------
    # Twitter bio check
    # ------------------------------------------------------------------
    if contact.twitter_handle:
        try:
            from app.integrations.twitter import fetch_user_profile, download_twitter_avatar

            handle = (contact.twitter_handle or "").lstrip("@").strip()
            if handle:
                profile = await fetch_user_profile(handle)
                new_bio = profile.get("description", "")

                # Download Twitter avatar if the contact doesn't have one
                if not contact.avatar_url:
                    image_url = profile.get("profile_image_url")
                    if image_url:
                        avatar_path = await download_twitter_avatar(image_url, contact.id)
                        if avatar_path:
                            contact.avatar_url = avatar_path
                if new_bio and new_bio != (contact.twitter_bio or ""):
                    old_bio = contact.twitter_bio
                    contact.twitter_bio = new_bio
                    changes["twitter_bio_changed"] = True
                    if old_bio:
                        db.add(Notification(
                            user_id=current_user.id,
                            notification_type="bio_change",
                            title=f"@{handle} updated their Twitter bio",
                            body=(
                                f"{contact.full_name or handle} changed their bio to: "
                                f"{new_bio[:200]}"
                            ),
                            link=f"/contacts/{contact.id}",
                        ))
        except Exception:
            logger.warning(
                "bio_refresh: Twitter bio fetch failed for contact %s", contact.id
            )

    # ------------------------------------------------------------------
    # Telegram bio check
    # ------------------------------------------------------------------
    if contact.telegram_username and current_user.telegram_session:
        try:
            from app.integrations.telegram import make_client, ensure_connected
            from telethon.tl.functions.users import GetFullUserRequest

            username = (contact.telegram_username or "").lstrip("@").strip()
            if username:
                client = make_client(current_user.telegram_session)
                await ensure_connected(client)
                try:
                    input_user = await client.get_input_entity(username)
                    full = await client(GetFullUserRequest(input_user))
                    new_bio = getattr(full.full_user, "about", None) or ""
                    if new_bio and new_bio != (contact.telegram_bio or ""):
                        old_bio = contact.telegram_bio
                        contact.telegram_bio = new_bio
                        changes["telegram_bio_changed"] = True
                        if old_bio:
                            db.add(Notification(
                                user_id=current_user.id,
                                notification_type="bio_change",
                                title=f"@{username} updated their Telegram bio",
                                body=(
                                    f"{contact.full_name or username} changed their bio to: "
                                    f"{new_bio[:200]}"
                                ),
                                link=f"/contacts/{contact.id}",
                            ))
                finally:
                    await client.disconnect()
        except Exception:
            logger.warning(
                "bio_refresh: Telegram bio fetch failed for contact %s", contact.id
            )

    await db.flush()
    return changes
