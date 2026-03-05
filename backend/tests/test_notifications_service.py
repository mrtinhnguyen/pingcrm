"""Tests for notifications service."""
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.models.user import User
from app.services.notifications import (
    create_notification,
    notify_detected_event,
    notify_new_suggestions,
)


@pytest.mark.asyncio
async def test_create_notification(db: AsyncSession, test_user: User):
    notif = await create_notification(
        user_id=test_user.id,
        notification_type="test",
        title="Test Title",
        body="Test body",
        link="/test",
        db=db,
    )
    assert notif.id is not None
    assert notif.notification_type == "test"
    assert notif.title == "Test Title"
    assert notif.read is False


@pytest.mark.asyncio
async def test_notify_new_suggestions(db: AsyncSession, test_user: User):
    notif = await notify_new_suggestions(test_user.id, 5, db)
    assert "5 new follow-up suggestions" in notif.title
    assert notif.link == "/suggestions"
    assert notif.notification_type == "suggestion"


@pytest.mark.asyncio
async def test_notify_detected_event(db: AsyncSession, test_user: User):
    contact_id = uuid.uuid4()
    notif = await notify_detected_event(
        user_id=test_user.id,
        event_summary="Started a new company",
        contact_name="John Doe",
        contact_id=contact_id,
        db=db,
    )
    assert "John Doe" in notif.title
    assert notif.body == "Started a new company"
    assert notif.link == f"/contacts/{contact_id}"
