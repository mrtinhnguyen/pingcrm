"""Tests for interactions API endpoints."""
import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

from app.models.contact import Contact
from app.models.interaction import Interaction


@pytest.mark.asyncio
async def test_list_interactions(client: AsyncClient, auth_headers: dict, test_contact: Contact, test_interaction: Interaction):
    resp = await client.get(f"/api/v1/contacts/{test_contact.id}/interactions", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 1
    assert data[0]["platform"] == "email"


@pytest.mark.asyncio
async def test_create_interaction(client: AsyncClient, auth_headers: dict, test_contact: Contact):
    resp = await client.post(f"/api/v1/contacts/{test_contact.id}/interactions", json={
        "platform": "manual",
        "direction": "outbound",
        "content_preview": "Had a great coffee chat",
        "occurred_at": datetime.now(UTC).isoformat(),
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["content_preview"] == "Had a great coffee chat"
    assert data["platform"] == "manual"


@pytest.mark.asyncio
async def test_create_interaction_nonexistent_contact(client: AsyncClient, auth_headers: dict):
    resp = await client.post(f"/api/v1/contacts/{uuid.uuid4()}/interactions", json={
        "platform": "manual",
        "direction": "outbound",
        "content_preview": "Test",
        "occurred_at": datetime.now(UTC).isoformat(),
    }, headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_interactions_nonexistent_contact(client: AsyncClient, auth_headers: dict):
    resp = await client.get(f"/api/v1/contacts/{uuid.uuid4()}/interactions", headers=auth_headers)
    assert resp.status_code == 404
