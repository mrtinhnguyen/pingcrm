"""Unit tests for the Twitter OAuth 2.0 PKCE API endpoints.

Covers:
- GET  /api/v1/auth/twitter/url       (OAuth callback URL generation)
- POST /api/v1/auth/twitter/callback  (token exchange with mocked exchange_twitter_code)
"""
from __future__ import annotations

import time
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.models.user import User

# The in-memory PKCE store lives at module level in the twitter router.
# Import it so tests can inspect or seed it directly.
import app.api.twitter as twitter_router_module


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_pkce_store(state: str, verifier: str, user_id: str) -> None:
    """Directly insert a PKCE entry so callback tests can use it."""
    twitter_router_module._pkce_store[state] = (verifier, user_id, time.time())


def _clear_pkce_store() -> None:
    twitter_router_module._pkce_store.clear()


# ---------------------------------------------------------------------------
# GET /api/v1/auth/twitter/url
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_twitter_url_returns_url_and_state(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """URL endpoint returns a Twitter auth URL and a state token."""
    _clear_pkce_store()

    with (
        patch(
            "app.api.twitter.generate_pkce_pair",
            return_value=("test_verifier_abc123", "test_challenge_xyz"),
        ),
        patch(
            "app.api.twitter.build_twitter_oauth2_url",
            return_value="https://twitter.com/i/oauth2/authorize?mock=1",
        ) as mock_build_url,
    ):
        response = await client.get(
            "/api/v1/auth/twitter/url",
            headers=auth_headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    data = body["data"]
    assert "url" in data
    assert "state" in data
    assert data["url"] == "https://twitter.com/i/oauth2/authorize?mock=1"
    assert isinstance(data["state"], str)
    assert len(data["state"]) > 0

    # Verify build_twitter_oauth2_url was called with the generated challenge
    mock_build_url.assert_called_once_with(
        state=data["state"],
        code_challenge="test_challenge_xyz",
    )


@pytest.mark.asyncio
async def test_get_twitter_url_stores_pkce_entry(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_user: User,
):
    """URL endpoint stores PKCE verifier in the in-memory store keyed by state."""
    _clear_pkce_store()

    with (
        patch(
            "app.api.twitter.generate_pkce_pair",
            return_value=("my_verifier", "my_challenge"),
        ),
        patch(
            "app.api.twitter.build_twitter_oauth2_url",
            return_value="https://twitter.com/i/oauth2/authorize?mock=1",
        ),
    ):
        response = await client.get(
            "/api/v1/auth/twitter/url",
            headers=auth_headers,
        )

    assert response.status_code == 200
    state = response.json()["data"]["state"]

    # The PKCE store must have an entry for this state
    assert state in twitter_router_module._pkce_store
    stored_verifier, stored_user_id, _ = twitter_router_module._pkce_store[state]
    assert stored_verifier == "my_verifier"
    assert stored_user_id == str(test_user.id)


@pytest.mark.asyncio
async def test_get_twitter_url_requires_auth(client: AsyncClient):
    """URL endpoint returns 401 without auth headers."""
    response = await client.get("/api/v1/auth/twitter/url")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_twitter_url_prunes_expired_pkce_entries(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """URL endpoint prunes expired entries from the PKCE store on each call."""
    _clear_pkce_store()

    # Seed an artificially expired entry (created 700 seconds ago; TTL is 600)
    expired_state = "expired_state_token"
    twitter_router_module._pkce_store[expired_state] = (
        "old_verifier",
        "some-user-id",
        time.time() - 700,
    )

    with (
        patch("app.api.twitter.generate_pkce_pair", return_value=("v", "c")),
        patch(
            "app.api.twitter.build_twitter_oauth2_url",
            return_value="https://twitter.com/i/oauth2/authorize",
        ),
    ):
        await client.get("/api/v1/auth/twitter/url", headers=auth_headers)

    # The expired entry must have been pruned
    assert expired_state not in twitter_router_module._pkce_store


@pytest.mark.asyncio
async def test_get_twitter_url_each_call_generates_unique_state(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """URL endpoint generates a fresh unique state on every call."""
    _clear_pkce_store()

    with (
        patch("app.api.twitter.generate_pkce_pair", return_value=("v", "c")),
        patch(
            "app.api.twitter.build_twitter_oauth2_url",
            return_value="https://twitter.com/i/oauth2/authorize",
        ),
    ):
        r1 = await client.get("/api/v1/auth/twitter/url", headers=auth_headers)
        r2 = await client.get("/api/v1/auth/twitter/url", headers=auth_headers)

    state1 = r1.json()["data"]["state"]
    state2 = r2.json()["data"]["state"]
    assert state1 != state2


# ---------------------------------------------------------------------------
# POST /api/v1/auth/twitter/callback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_callback_exchanges_code_and_returns_connected(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_user: User,
):
    """callback endpoint returns connected:True on successful token exchange."""
    _clear_pkce_store()
    state = "valid_state_abc"
    _seed_pkce_store(state, "valid_verifier", str(test_user.id))

    mock_tokens = {
        "access_token": "tw_access_token_xyz",
        "refresh_token": "tw_refresh_token_xyz",
        "token_type": "bearer",
    }

    with patch(
        "app.api.twitter.exchange_twitter_code",
        new=AsyncMock(return_value=mock_tokens),
    ) as mock_exchange:
        response = await client.post(
            "/api/v1/auth/twitter/callback",
            json={"code": "auth_code_123", "state": state},
            headers=auth_headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["data"]["connected"] is True

    # Verify the correct code and verifier were passed to the exchange function
    mock_exchange.assert_awaited_once_with("auth_code_123", "valid_verifier")


@pytest.mark.asyncio
async def test_callback_without_refresh_token_succeeds(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_user: User,
):
    """callback endpoint succeeds even when exchange response omits refresh_token."""
    _clear_pkce_store()
    state = "state_no_refresh"
    _seed_pkce_store(state, "verifier_no_refresh", str(test_user.id))

    mock_tokens = {
        "access_token": "tw_access_only",
        "token_type": "bearer",
    }

    with patch(
        "app.api.twitter.exchange_twitter_code",
        new=AsyncMock(return_value=mock_tokens),
    ):
        response = await client.post(
            "/api/v1/auth/twitter/callback",
            json={"code": "some_code", "state": state},
            headers=auth_headers,
        )

    assert response.status_code == 200
    assert response.json()["data"]["connected"] is True


@pytest.mark.asyncio
async def test_callback_invalid_state_returns_400(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """callback endpoint returns 400 when state is unknown or not in store."""
    _clear_pkce_store()

    response = await client.post(
        "/api/v1/auth/twitter/callback",
        json={"code": "some_code", "state": "nonexistent_state"},
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert "Invalid or expired state" in response.json()["detail"]


@pytest.mark.asyncio
async def test_callback_state_belongs_to_different_user_returns_403(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """callback endpoint returns 403 when state was issued to a different user."""
    _clear_pkce_store()
    state = "state_other_user"
    # Seed with a user ID that does not match the authenticated test_user
    _seed_pkce_store(state, "some_verifier", "00000000-0000-0000-0000-000000000099")

    response = await client.post(
        "/api/v1/auth/twitter/callback",
        json={"code": "auth_code", "state": state},
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert "does not belong to the authenticated user" in response.json()["detail"]


@pytest.mark.asyncio
async def test_callback_exchange_failure_returns_400(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_user: User,
):
    """callback endpoint returns 400 when the token exchange raises an exception."""
    _clear_pkce_store()
    state = "state_exchange_fails"
    _seed_pkce_store(state, "verifier", str(test_user.id))

    with patch(
        "app.api.twitter.exchange_twitter_code",
        new=AsyncMock(side_effect=RuntimeError("Twitter API unreachable")),
    ):
        response = await client.post(
            "/api/v1/auth/twitter/callback",
            json={"code": "bad_code", "state": state},
            headers=auth_headers,
        )

    assert response.status_code == 400
    assert "Failed to exchange code" in response.json()["detail"]


@pytest.mark.asyncio
async def test_callback_requires_auth(client: AsyncClient):
    """callback endpoint returns 401 without auth headers."""
    response = await client.post(
        "/api/v1/auth/twitter/callback",
        json={"code": "code", "state": "state"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_callback_state_consumed_after_successful_use(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_user: User,
):
    """callback endpoint pops state from store; a replay attempt returns 400."""
    _clear_pkce_store()
    state = "state_one_time_use"
    _seed_pkce_store(state, "verifier_one_time", str(test_user.id))

    mock_tokens = {"access_token": "tok", "token_type": "bearer"}

    with patch(
        "app.api.twitter.exchange_twitter_code",
        new=AsyncMock(return_value=mock_tokens),
    ):
        first = await client.post(
            "/api/v1/auth/twitter/callback",
            json={"code": "code1", "state": state},
            headers=auth_headers,
        )
        second = await client.post(
            "/api/v1/auth/twitter/callback",
            json={"code": "code2", "state": state},
            headers=auth_headers,
        )

    assert first.status_code == 200
    # The state was popped on first use; replay must fail
    assert second.status_code == 400
