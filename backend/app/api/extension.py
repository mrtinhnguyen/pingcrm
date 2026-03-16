"""LinkedIn Chrome Extension pairing endpoints."""
from __future__ import annotations

import logging
import secrets
import string
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.extension_pairing import ExtensionPairing
from app.models.user import User
from app.schemas.responses import Envelope

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/extension", tags=["extension"])

_PAIRING_CODE_ALPHABET = string.ascii_uppercase + string.digits
_PAIRING_CODE_LENGTH = 12
_PAIRING_TTL_MINUTES = 10
_EXTENSION_TOKEN_EXPIRE_DAYS = 30
_MAX_POLL_ATTEMPTS = 20


def _generate_pairing_code() -> str:
    return "".join(secrets.choice(_PAIRING_CODE_ALPHABET) for _ in range(_PAIRING_CODE_LENGTH))


def _create_extension_token(user_id: str) -> str:
    """Create a scoped JWT for the extension (aud: pingcrm-extension, 30-day expiry)."""
    from jose import jwt

    payload = {
        "sub": user_id,
        "aud": "pingcrm-extension",
        "exp": datetime.now(UTC) + timedelta(days=_EXTENSION_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


class PairRequest(BaseModel):
    code: str


class PairTokenResponse(BaseModel):
    token: str
    api_url: str


@router.post("/pair", response_model=Envelope[dict])
async def create_pairing(
    body: PairRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Authenticated user submits a pairing code from the extension popup.

    Creates an ExtensionPairing record with a scoped JWT, and marks
    the user's linkedin_extension_paired_at timestamp.
    """
    code = body.code.strip().upper()

    # Check for existing pairing with this code
    result = await db.execute(
        select(ExtensionPairing).where(ExtensionPairing.code == code)
    )
    existing = result.scalar_one_or_none()

    now = datetime.now(UTC)

    if existing is not None:
        # Reject if already claimed or expired
        if existing.claimed_at is not None:
            raise HTTPException(status_code=409, detail="Pairing code already claimed")
        if existing.expires_at <= now:
            raise HTTPException(status_code=410, detail="Pairing code expired")
        if existing.user_id != current_user.id:
            raise HTTPException(status_code=409, detail="Pairing code in use by another user")
        # Same user re-submitted the same code — idempotent, update token
        existing.token = _create_extension_token(str(current_user.id))
        existing.expires_at = now + timedelta(minutes=_PAIRING_TTL_MINUTES)
    else:
        token = _create_extension_token(str(current_user.id))
        pairing = ExtensionPairing(
            code=code,
            user_id=current_user.id,
            token=token,
            expires_at=now + timedelta(minutes=_PAIRING_TTL_MINUTES),
        )
        db.add(pairing)

    current_user.linkedin_extension_paired_at = now
    await db.flush()

    return {"data": {"status": "ok"}, "error": None, "meta": None}


@router.get("/pair", response_model=Envelope[PairTokenResponse])
async def poll_pairing(
    code: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Unauthenticated endpoint polled by the extension after the user enters their code.

    Returns the scoped JWT when the pairing is ready.
    Increments attempt counter to prevent brute-force enumeration.
    """
    code = code.strip().upper()

    result = await db.execute(
        select(ExtensionPairing).where(ExtensionPairing.code == code)
    )
    pairing = result.scalar_one_or_none()

    if pairing is None:
        raise HTTPException(status_code=404, detail="Pairing code not found")

    now = datetime.now(UTC)

    if pairing.expires_at <= now and pairing.claimed_at is None:
        raise HTTPException(status_code=410, detail="Pairing code expired")

    if pairing.attempts >= _MAX_POLL_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many attempts")

    # First successful poll: mark claimed
    if pairing.claimed_at is None:
        pairing.claimed_at = now
    else:
        # Subsequent polls after first claim increment attempts
        pairing.attempts += 1

    await db.flush()

    api_url = settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else "http://localhost:8000"

    return {
        "data": PairTokenResponse(token=pairing.token, api_url=api_url),
        "error": None,
        "meta": None,
    }


@router.delete("/pair", response_model=Envelope[dict])
async def disconnect_extension(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Authenticated endpoint to disconnect the extension.

    Deletes all pairing records for the user and clears linkedin_extension_paired_at.
    """
    await db.execute(
        delete(ExtensionPairing).where(ExtensionPairing.user_id == current_user.id)
    )
    current_user.linkedin_extension_paired_at = None
    await db.flush()

    return {"data": {"status": "ok"}, "error": None, "meta": None}
