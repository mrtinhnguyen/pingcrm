"""Tests for Google Contacts sync endpoint."""
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_access_token
from app.models.user import User


@pytest.mark.asyncio
async def test_google_sync_not_connected(client: AsyncClient, auth_headers: dict):
    """POST /contacts/sync/google returns 400 when Google not connected."""
    resp = await client.post("/api/v1/contacts/sync/google", headers=auth_headers)
    assert resp.status_code == 400
    assert "not connected" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_google_sync_refresh_failure(
    client: AsyncClient, db: AsyncSession, test_user: User
):
    """POST /contacts/sync/google returns 502 when token refresh fails."""
    test_user.google_refresh_token = "expired_token"
    db.add(test_user)
    await db.commit()

    token = create_access_token(data={"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    with patch("app.api.contacts.refresh_access_token", side_effect=RuntimeError("expired")):
        resp = await client.post("/api/v1/contacts/sync/google", headers=headers)
    assert resp.status_code == 502


@pytest.mark.asyncio
async def test_google_sync_fetch_failure(
    client: AsyncClient, db: AsyncSession, test_user: User
):
    """POST /contacts/sync/google returns 502 when fetch fails."""
    test_user.google_refresh_token = "valid_token"
    db.add(test_user)
    await db.commit()

    token = create_access_token(data={"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    with patch("app.api.contacts.refresh_access_token", return_value="access_tok"), \
         patch("app.api.contacts.fetch_google_contacts", side_effect=RuntimeError("API error")):
        resp = await client.post("/api/v1/contacts/sync/google", headers=headers)
    assert resp.status_code == 502


@pytest.mark.asyncio
async def test_google_sync_success(
    client: AsyncClient, db: AsyncSession, test_user: User
):
    """POST /contacts/sync/google creates contacts from Google data."""
    test_user.google_refresh_token = "valid_token"
    db.add(test_user)
    await db.commit()

    token = create_access_token(data={"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    google_contacts = [
        {"full_name": "Alice G", "emails": ["alice@google.com"], "given_name": "Alice"},
    ]

    with patch("app.api.contacts.refresh_access_token", return_value="access_tok"), \
         patch("app.api.contacts.fetch_google_contacts", return_value=google_contacts):
        resp = await client.post("/api/v1/contacts/sync/google", headers=headers)

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["created"] == 1
