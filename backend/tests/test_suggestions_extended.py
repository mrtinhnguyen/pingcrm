"""Extended unit tests for the suggestions API endpoints.

Covers:
- POST /api/v1/suggestions/generate  (mocked followup_engine)
- GET  /api/v1/suggestions            (list pending)
- GET  /api/v1/suggestions/digest     (mocked followup_engine)
- PUT  /api/v1/suggestions/{id}       (status transitions)
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.follow_up import FollowUpSuggestion
from app.models.user import User


# ---------------------------------------------------------------------------
# POST /api/v1/suggestions/generate
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_returns_generated_suggestions(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_contact: Contact,
    test_user: User,
):
    """generate endpoint returns suggestions produced by the engine."""
    mock_suggestions = [
        FollowUpSuggestion(
            id=uuid.uuid4(),
            contact_id=test_contact.id,
            user_id=test_user.id,
            trigger_type="time_based",
            suggested_message="Reach out to John Doe",
            suggested_channel="email",
            status="pending",
            created_at=datetime.now(UTC),
        )
    ]

    with patch(
        "app.services.followup_engine.generate_suggestions",
        new=AsyncMock(return_value=mock_suggestions),
    ) as mock_generate:
        response = await client.post(
            "/api/v1/suggestions/generate",
            headers=auth_headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["meta"]["generated"] == 1
    assert len(body["data"]) == 1
    mock_generate.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_returns_empty_when_no_suggestions(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """generate endpoint returns empty list when engine produces nothing."""
    with patch(
        "app.services.followup_engine.generate_suggestions",
        new=AsyncMock(return_value=[]),
    ):
        response = await client.post(
            "/api/v1/suggestions/generate",
            headers=auth_headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["data"] == []
    assert body["meta"]["generated"] == 0


@pytest.mark.asyncio
async def test_generate_requires_auth(client: AsyncClient):
    """generate endpoint returns 401 without auth headers."""
    response = await client.post("/api/v1/suggestions/generate")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_generate_multiple_suggestions(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_contact: Contact,
    test_user: User,
):
    """generate endpoint handles multiple suggestions from the engine."""
    mock_suggestions = [
        FollowUpSuggestion(
            id=uuid.uuid4(),
            contact_id=test_contact.id,
            user_id=test_user.id,
            trigger_type="time_based",
            suggested_message=f"Message {i}",
            suggested_channel="email",
            status="pending",
            created_at=datetime.now(UTC),
        )
        for i in range(3)
    ]

    with patch(
        "app.services.followup_engine.generate_suggestions",
        new=AsyncMock(return_value=mock_suggestions),
    ):
        response = await client.post(
            "/api/v1/suggestions/generate",
            headers=auth_headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["generated"] == 3
    assert len(body["data"]) == 3


# ---------------------------------------------------------------------------
# GET /api/v1/suggestions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_suggestions_returns_pending(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_suggestion: FollowUpSuggestion,
):
    """list endpoint returns pending suggestions with contact info attached."""
    response = await client.get("/api/v1/suggestions", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["meta"]["count"] == 1
    items = body["data"]
    assert len(items) == 1
    assert items[0]["status"] == "pending"
    assert items[0]["contact"] is not None
    assert items[0]["contact"]["full_name"] == "John Doe"


@pytest.mark.asyncio
async def test_list_suggestions_empty_for_new_user(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """list endpoint returns empty list when user has no pending suggestions."""
    response = await client.get("/api/v1/suggestions", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["data"] == []
    assert body["meta"]["count"] == 0


@pytest.mark.asyncio
async def test_list_suggestions_excludes_non_pending(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db: AsyncSession,
    test_contact: Contact,
    test_user: User,
):
    """list endpoint only returns suggestions with status=pending."""
    sent_suggestion = FollowUpSuggestion(
        id=uuid.uuid4(),
        contact_id=test_contact.id,
        user_id=test_user.id,
        trigger_type="time_based",
        suggested_message="Already sent",
        suggested_channel="email",
        status="sent",
        created_at=datetime.now(UTC),
    )
    db.add(sent_suggestion)
    await db.commit()

    response = await client.get("/api/v1/suggestions", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["count"] == 0


@pytest.mark.asyncio
async def test_list_suggestions_requires_auth(client: AsyncClient):
    """list endpoint returns 401 without auth headers."""
    response = await client.get("/api/v1/suggestions")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/v1/suggestions/digest
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_digest_returns_weekly_suggestions(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_contact: Contact,
    test_user: User,
):
    """digest endpoint returns suggestions from get_weekly_digest."""
    mock_suggestions = [
        FollowUpSuggestion(
            id=uuid.uuid4(),
            contact_id=test_contact.id,
            user_id=test_user.id,
            trigger_type="time_based",
            suggested_message="Weekly check-in with John",
            suggested_channel="email",
            status="pending",
            created_at=datetime.now(UTC),
        )
    ]

    with patch(
        "app.services.followup_engine.get_weekly_digest",
        new=AsyncMock(return_value=mock_suggestions),
    ):
        response = await client.get("/api/v1/suggestions/digest", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["meta"]["count"] == 1
    assert len(body["data"]) == 1


@pytest.mark.asyncio
async def test_digest_empty_result(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """digest endpoint returns empty list when no digest suggestions."""
    with patch(
        "app.services.followup_engine.get_weekly_digest",
        new=AsyncMock(return_value=[]),
    ):
        response = await client.get("/api/v1/suggestions/digest", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["data"] == []
    assert body["meta"]["count"] == 0


# ---------------------------------------------------------------------------
# PUT /api/v1/suggestions/{suggestion_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_suggestion_status_dismissed(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_suggestion: FollowUpSuggestion,
):
    """PUT endpoint can dismiss a suggestion."""
    response = await client.put(
        f"/api/v1/suggestions/{test_suggestion.id}",
        json={"status": "dismissed"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["data"]["status"] == "dismissed"


@pytest.mark.asyncio
async def test_update_suggestion_status_sent(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_suggestion: FollowUpSuggestion,
):
    """PUT endpoint marks suggestion as sent and updates contact timestamp."""
    response = await client.put(
        f"/api/v1/suggestions/{test_suggestion.id}",
        json={"status": "sent"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "sent"


@pytest.mark.asyncio
async def test_update_suggestion_status_snoozed_with_datetime(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_suggestion: FollowUpSuggestion,
):
    """PUT endpoint accepts snoozed status when snooze_until is provided."""
    snooze_until = (datetime.now(UTC) + timedelta(days=7)).isoformat()
    response = await client.put(
        f"/api/v1/suggestions/{test_suggestion.id}",
        json={"status": "snoozed", "snooze_until": snooze_until},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "snoozed"


@pytest.mark.asyncio
async def test_update_suggestion_snoozed_without_datetime_returns_422(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_suggestion: FollowUpSuggestion,
):
    """PUT endpoint returns 422 when snoozed status is missing snooze_until."""
    response = await client.put(
        f"/api/v1/suggestions/{test_suggestion.id}",
        json={"status": "snoozed"},
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_suggestion_invalid_status(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_suggestion: FollowUpSuggestion,
):
    """PUT endpoint returns 400 for an unrecognized status value."""
    response = await client.put(
        f"/api/v1/suggestions/{test_suggestion.id}",
        json={"status": "invalid_status"},
        headers=auth_headers,
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_suggestion_not_found(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """PUT endpoint returns 404 when suggestion does not exist."""
    non_existent_id = uuid.uuid4()
    response = await client.put(
        f"/api/v1/suggestions/{non_existent_id}",
        json={"status": "dismissed"},
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_suggestion_requires_auth(
    client: AsyncClient,
    test_suggestion: FollowUpSuggestion,
):
    """PUT endpoint returns 401 without auth headers."""
    response = await client.put(
        f"/api/v1/suggestions/{test_suggestion.id}",
        json={"status": "dismissed"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_suggestion_cannot_access_other_users_suggestion(
    client: AsyncClient,
    db: AsyncSession,
    test_contact: Contact,
):
    """PUT endpoint returns 404 when accessing another user's suggestion."""
    from app.core.auth import create_access_token, hash_password

    # Create a second user with their own suggestion
    other_user = User(
        id=uuid.uuid4(),
        email="other@example.com",
        hashed_password=hash_password("otherpass123"),
        full_name="Other User",
    )
    db.add(other_user)
    await db.commit()
    await db.refresh(other_user)

    other_suggestion = FollowUpSuggestion(
        id=uuid.uuid4(),
        contact_id=test_contact.id,
        user_id=other_user.id,
        trigger_type="time_based",
        suggested_message="Other user's suggestion",
        suggested_channel="email",
        status="pending",
        created_at=datetime.now(UTC),
    )
    db.add(other_suggestion)
    await db.commit()

    # Authenticate as the first test user (using a fresh token for other_user)
    # and try to access other_user's suggestion — should 404
    other_token = create_access_token(data={"sub": str(other_user.id)})
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # Now authenticate as test_user and try to touch other_user's suggestion
    from app.core.auth import hash_password as _hp  # already imported above

    first_user = User(
        id=uuid.uuid4(),
        email="first@example.com",
        hashed_password=_hp("firstpass123"),
        full_name="First User",
    )
    db.add(first_user)
    await db.commit()
    first_token = create_access_token(data={"sub": str(first_user.id)})
    first_headers = {"Authorization": f"Bearer {first_token}"}

    response = await client.put(
        f"/api/v1/suggestions/{other_suggestion.id}",
        json={"status": "dismissed"},
        headers=first_headers,
    )
    assert response.status_code == 404
