"""Tests for the send-message endpoint and related functionality."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_access_token
from app.models.contact import Contact
from app.models.interaction import Interaction
from app.models.user import User


@pytest.mark.asyncio
async def test_send_telegram_message_success(
    client: AsyncClient, db: AsyncSession, test_user: User, test_contact: Contact
):
    """POST /contacts/{id}/send-message sends via Telegram and creates interaction."""
    test_contact.telegram_username = "johndoe"
    test_user.telegram_session = "session_data"
    db.add(test_contact)
    db.add(test_user)
    await db.commit()

    token = create_access_token(data={"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    with patch(
        "app.integrations.telegram.send_telegram_message",
        new=AsyncMock(return_value={"sent": True, "message_id": 12345}),
    ):
        resp = await client.post(
            f"/api/v1/contacts/{test_contact.id}/send-message",
            json={"message": "Hey John!", "channel": "telegram"},
            headers=headers,
        )

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["sent"] is True
    assert data["channel"] == "telegram"
    assert data["interaction_id"] is not None


@pytest.mark.asyncio
async def test_send_message_empty_body(
    client: AsyncClient, auth_headers: dict, test_contact: Contact
):
    """POST /contacts/{id}/send-message rejects empty message."""
    resp = await client.post(
        f"/api/v1/contacts/{test_contact.id}/send-message",
        json={"message": "   ", "channel": "telegram"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_send_message_no_telegram_username(
    client: AsyncClient, auth_headers: dict, test_contact: Contact
):
    """POST /contacts/{id}/send-message rejects when contact has no Telegram username."""
    resp = await client.post(
        f"/api/v1/contacts/{test_contact.id}/send-message",
        json={"message": "Hello!", "channel": "telegram"},
        headers=auth_headers,
    )
    assert resp.status_code == 422
    assert "no Telegram username" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_send_message_unsupported_channel(
    client: AsyncClient, auth_headers: dict, test_contact: Contact
):
    """POST /contacts/{id}/send-message rejects unsupported channels."""
    resp = await client.post(
        f"/api/v1/contacts/{test_contact.id}/send-message",
        json={"message": "Hello!", "channel": "email"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "not yet supported" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_send_message_contact_not_found(
    client: AsyncClient, auth_headers: dict
):
    """POST /contacts/{id}/send-message returns 404 for non-existent contact."""
    fake_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/contacts/{fake_id}/send-message",
        json={"message": "Hello!", "channel": "telegram"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_send_message_creates_interaction(
    client: AsyncClient, db: AsyncSession, test_user: User, test_contact: Contact
):
    """Sending a message creates an outbound interaction record."""
    test_contact.telegram_username = "johndoe"
    test_user.telegram_session = "session_data"
    db.add(test_contact)
    db.add(test_user)
    await db.commit()

    token = create_access_token(data={"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    with patch(
        "app.integrations.telegram.send_telegram_message",
        new=AsyncMock(return_value={"sent": True, "message_id": 99}),
    ):
        resp = await client.post(
            f"/api/v1/contacts/{test_contact.id}/send-message",
            json={"message": "Test message content", "channel": "telegram"},
            headers=headers,
        )

    assert resp.status_code == 200
    interaction_id = resp.json()["data"]["interaction_id"]

    result = await db.execute(
        select(Interaction).where(Interaction.id == uuid.UUID(interaction_id))
    )
    interaction = result.scalar_one()
    assert interaction.direction == "outbound"
    assert interaction.platform == "telegram"
    assert "Test message content" in interaction.content_preview


@pytest.mark.asyncio
async def test_send_message_telegram_runtime_error(
    client: AsyncClient, db: AsyncSession, test_user: User, test_contact: Contact
):
    """RuntimeError from send_telegram_message returns 400."""
    test_contact.telegram_username = "johndoe"
    test_user.telegram_session = "session_data"
    db.add(test_contact)
    db.add(test_user)
    await db.commit()

    token = create_access_token(data={"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    with patch(
        "app.integrations.telegram.send_telegram_message",
        new=AsyncMock(side_effect=RuntimeError("No Telegram session")),
    ):
        resp = await client.post(
            f"/api/v1/contacts/{test_contact.id}/send-message",
            json={"message": "Hello!", "channel": "telegram"},
            headers=headers,
        )

    assert resp.status_code == 400
    assert "No Telegram session" in resp.json()["detail"]
