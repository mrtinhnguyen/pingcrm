"""Telegram transport layer: client lifecycle and rate limiting helpers."""
from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import User as TelegramUser

from app.core.config import settings

logger = logging.getLogger(__name__)

RATE_GATE_KEY = "tg_flood:{user_id}"

AVATARS_DIR = Path(os.environ.get(
    "AVATARS_DIR",
    str(Path(__file__).resolve().parent.parent.parent / "static" / "avatars"),
))


async def _check_rate_gate(user_id: str) -> int | None:
    """Return seconds remaining if user is rate-gated, else None."""
    from app.core.redis import get_redis
    r = get_redis()
    ttl = await r.ttl(RATE_GATE_KEY.format(user_id=user_id))
    return ttl if ttl > 0 else None


async def _set_rate_gate(user_id: str, seconds: int) -> None:
    """Record a FloodWait so all operations respect the cooldown."""
    from app.core.redis import get_redis
    r = get_redis()
    await r.set(RATE_GATE_KEY.format(user_id=user_id), "1", ex=seconds)


def _make_client(session_string: str | None = None) -> TelegramClient:
    """Construct a TelegramClient backed by a StringSession."""
    if not settings.TELEGRAM_API_ID or not settings.TELEGRAM_API_HASH:
        raise RuntimeError(
            "Telegram credentials not configured: set TELEGRAM_API_ID and "
            "TELEGRAM_API_HASH environment variables."
        )
    session = StringSession(session_string or "")
    return TelegramClient(
        session,
        settings.TELEGRAM_API_ID,
        settings.TELEGRAM_API_HASH,
    )


async def _ensure_connected(client: TelegramClient) -> None:
    """Connect the client, retrying once if the first attempt silently fails."""
    await client.connect()
    if not client.is_connected():
        await client.connect()
    if not client.is_connected():
        raise RuntimeError("Failed to establish connection to Telegram servers")


# Public aliases — use these instead of the private _-prefixed functions
make_client = _make_client
ensure_connected = _ensure_connected


async def _download_avatar(
    client: TelegramClient, entity: TelegramUser, contact_id: uuid.UUID
) -> str | None:
    """Download a Telegram user's profile photo and return the relative URL path."""
    try:
        AVATARS_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"{contact_id}.jpg"
        filepath = AVATARS_DIR / filename
        result = await client.download_profile_photo(
            entity, file=str(filepath), download_big=False,
        )
        if result:
            return f"/static/avatars/{filename}"
    except Exception:
        logger.debug("Failed to download avatar for entity %s", entity.id)
    return None
