"""Tests for the LinkedIn extension pairing API."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.extension_pairing import ExtensionPairing
from app.models.user import User

PAIR_URL = "/api/v1/extension/pair"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


async def _post_code(client: AsyncClient, code: str, headers: dict) -> dict:
    resp = await client.post(PAIR_URL, json={"code": code}, headers=headers)
    return resp


# ---------------------------------------------------------------------------
# Task 1: POST creates pairing successfully
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_pair_creates_pairing(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_user: User,
):
    """POST /pair creates an ExtensionPairing row and returns status ok."""
    code = "TESTCODE1234"
    resp = await client.post(PAIR_URL, json={"code": code}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "ok"

    result = await db.execute(
        select(ExtensionPairing).where(ExtensionPairing.code == code)
    )
    pairing = result.scalar_one_or_none()
    assert pairing is not None
    assert pairing.user_id == test_user.id
    assert pairing.token != ""
    assert pairing.claimed_at is None

    # User should have linkedin_extension_paired_at set
    await db.refresh(test_user)
    assert test_user.linkedin_extension_paired_at is not None


# ---------------------------------------------------------------------------
# Task 2: GET returns 404 for unknown code
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_pair_404_unknown_code(client: AsyncClient):
    """GET /pair with an unknown code returns 404."""
    resp = await client.get(PAIR_URL, params={"code": "NOSUCHCODE1"})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Task 3: GET returns token after POST
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_pair_returns_token_after_post(
    client: AsyncClient,
    auth_headers: dict,
):
    """After a POST, GET /pair returns the scoped token."""
    code = "VALIDCODE123"
    post_resp = await client.post(PAIR_URL, json={"code": code}, headers=auth_headers)
    assert post_resp.status_code == 200

    get_resp = await client.get(PAIR_URL, params={"code": code})
    assert get_resp.status_code == 200

    data = get_resp.json()["data"]
    assert "token" in data
    assert data["token"] != ""
    assert "api_url" in data


# ---------------------------------------------------------------------------
# Task 4: GET returns 410 for expired code
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_pair_410_expired_code(
    client: AsyncClient,
    db: AsyncSession,
    test_user: User,
):
    """GET /pair returns 410 when the pairing code has expired."""
    code = "EXPIREDCODE1"
    pairing = ExtensionPairing(
        code=code,
        user_id=test_user.id,
        token="some-token",
        expires_at=datetime.now(UTC) - timedelta(minutes=1),  # already expired
    )
    db.add(pairing)
    await db.commit()

    resp = await client.get(PAIR_URL, params={"code": code})
    assert resp.status_code == 410


# ---------------------------------------------------------------------------
# Task 5: GET returns 429 after 20 attempts
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_pair_429_after_max_attempts(
    client: AsyncClient,
    db: AsyncSession,
    test_user: User,
):
    """GET /pair returns 429 when attempts >= 20."""
    code = "MAXATTEMPTS1"
    pairing = ExtensionPairing(
        code=code,
        user_id=test_user.id,
        token="some-token",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        attempts=20,
    )
    db.add(pairing)
    await db.commit()

    resp = await client.get(PAIR_URL, params={"code": code})
    assert resp.status_code == 429


# ---------------------------------------------------------------------------
# Task 6: DELETE disconnects
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_pair_disconnects(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_user: User,
):
    """DELETE /pair removes all pairings and clears linkedin_extension_paired_at."""
    code = "DELETEME1234"
    post_resp = await client.post(PAIR_URL, json={"code": code}, headers=auth_headers)
    assert post_resp.status_code == 200

    delete_resp = await client.delete(PAIR_URL, headers=auth_headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["data"]["status"] == "ok"

    # Pairing should be gone
    result = await db.execute(
        select(ExtensionPairing).where(ExtensionPairing.user_id == test_user.id)
    )
    assert result.scalar_one_or_none() is None

    # linkedin_extension_paired_at should be cleared
    await db.refresh(test_user)
    assert test_user.linkedin_extension_paired_at is None


# ---------------------------------------------------------------------------
# Task 7: POST rejects duplicate code from a different user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_pair_rejects_duplicate_code_different_user(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
):
    """POST /pair with a code already claimed by another user returns 409."""
    code = "DUPCODE12345"

    # Create a second user who owns the pairing
    from app.core.auth import hash_password

    other_user = User(
        id=uuid.uuid4(),
        email="other@example.com",
        hashed_password=hash_password("otherpass"),
        full_name="Other User",
    )
    db.add(other_user)
    await db.commit()

    # Pre-create a pairing owned by other_user with this code
    pairing = ExtensionPairing(
        code=code,
        user_id=other_user.id,
        token="other-token",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    db.add(pairing)
    await db.commit()

    # test_user (via auth_headers) tries to pair with the same code
    resp = await client.post(PAIR_URL, json={"code": code}, headers=auth_headers)
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# POST requires authentication
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_pair_requires_auth(client: AsyncClient):
    """POST /pair without auth returns 401."""
    resp = await client.post(PAIR_URL, json={"code": "NOAUTHCODE12"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# DELETE requires authentication
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_pair_requires_auth(client: AsyncClient):
    """DELETE /pair without auth returns 401."""
    resp = await client.delete(PAIR_URL)
    assert resp.status_code == 401
