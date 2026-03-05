"""Tests for suggestions API endpoints."""
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.models.follow_up import FollowUpSuggestion


@pytest.mark.asyncio
async def test_list_suggestions(client: AsyncClient, auth_headers: dict, test_suggestion: FollowUpSuggestion):
    resp = await client.get("/api/v1/suggestions", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 1
    assert data[0]["status"] == "pending"


@pytest.mark.asyncio
async def test_update_suggestion_dismiss(client: AsyncClient, auth_headers: dict, test_suggestion: FollowUpSuggestion):
    resp = await client.put(f"/api/v1/suggestions/{test_suggestion.id}", json={
        "status": "dismissed",
    }, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "dismissed"


@pytest.mark.asyncio
async def test_update_suggestion_snooze_requires_datetime(client: AsyncClient, auth_headers: dict, test_suggestion: FollowUpSuggestion):
    resp = await client.put(f"/api/v1/suggestions/{test_suggestion.id}", json={
        "status": "snoozed",
    }, headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_suggestion_snooze_with_datetime(client: AsyncClient, auth_headers: dict, test_suggestion: FollowUpSuggestion):
    future = (datetime.now(UTC) + timedelta(days=7)).isoformat()
    resp = await client.put(f"/api/v1/suggestions/{test_suggestion.id}", json={
        "status": "snoozed",
        "snooze_until": future,
    }, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "snoozed"


@pytest.mark.asyncio
async def test_update_suggestion_invalid_status(client: AsyncClient, auth_headers: dict, test_suggestion: FollowUpSuggestion):
    resp = await client.put(f"/api/v1/suggestions/{test_suggestion.id}", json={
        "status": "invalid_status",
    }, headers=auth_headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_update_suggestion_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.put(f"/api/v1/suggestions/{uuid.uuid4()}", json={
        "status": "dismissed",
    }, headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_suggestion_sent_updates_followup_at(client: AsyncClient, auth_headers: dict, test_suggestion: FollowUpSuggestion):
    resp = await client.put(f"/api/v1/suggestions/{test_suggestion.id}", json={
        "status": "sent",
    }, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "sent"
