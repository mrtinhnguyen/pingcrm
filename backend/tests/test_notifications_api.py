"""Tests for notifications API endpoints."""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.models.user import User


@pytest.mark.asyncio
async def test_list_notifications(client: AsyncClient, auth_headers: dict, test_notification: Notification):
    resp = await client.get("/api/v1/notifications", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) >= 1
    assert data["data"][0]["notification_type"] == "suggestion"


@pytest.mark.asyncio
async def test_unread_count(client: AsyncClient, auth_headers: dict, test_notification: Notification):
    resp = await client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["count"] >= 1


@pytest.mark.asyncio
async def test_mark_read(client: AsyncClient, auth_headers: dict, test_notification: Notification):
    resp = await client.put(f"/api/v1/notifications/{test_notification.id}/read", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["read"] is True

    # Count should decrease
    resp = await client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert resp.json()["data"]["count"] == 0


@pytest.mark.asyncio
async def test_mark_read_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.put(f"/api/v1/notifications/{uuid.uuid4()}/read", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_mark_all_read(client: AsyncClient, auth_headers: dict, db: AsyncSession, test_user: User):
    # Create multiple unread notifications
    for i in range(3):
        n = Notification(
            user_id=test_user.id,
            notification_type="event",
            title=f"Event {i}",
            body=f"Body {i}",
            read=False,
        )
        db.add(n)
    await db.flush()

    resp = await client.put("/api/v1/notifications/read-all", headers=auth_headers)
    assert resp.status_code == 200

    resp = await client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert resp.json()["data"]["count"] == 0
