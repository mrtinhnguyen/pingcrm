"""Tests for poll_twitter_all() task filtering.

Verifies that only users with twitter_refresh_token set are enqueued,
matching the pattern used by sync_gmail_all().

poll_twitter_all() is a synchronous Celery task that internally calls
asyncio.run() with a task_session query.  Because the task is
synchronous (not an async def), we test it by:

  1. Calling it directly (no event loop active — plain pytest, not pytest-asyncio).
  2. Mocking task_session so the DB query is fully controlled without
     real database access, avoiding cross-loop asyncpg issues.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.tasks import poll_twitter_all


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_session(user_ids: list[str]):
    """Return a mocked task_session context manager that yields user IDs."""
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = user_ids

    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_mock

    session_mock = AsyncMock()
    session_mock.execute.return_value = result_mock

    cm = AsyncMock()
    cm.__aenter__.return_value = session_mock
    cm.__aexit__.return_value = None

    return cm


# ---------------------------------------------------------------------------
# Tests (plain, not async — poll_twitter_all is synchronous)
# ---------------------------------------------------------------------------


def test_poll_twitter_all_only_queues_connected_users():
    """Only users with twitter_refresh_token get tasks enqueued."""
    uid_with = uuid.uuid4()
    # User without token is never returned by the filtered query — the mock
    # simulates the WHERE clause having already excluded them.
    mock_session = _make_mock_session([uid_with])

    with (
        patch("app.services.task_jobs.twitter.task_session", return_value=mock_session),
        patch("app.services.task_jobs.twitter.poll_twitter_activity") as mock_activity,
        patch("app.services.task_jobs.twitter.sync_twitter_dms_for_user") as mock_dms,
    ):
        mock_activity.delay = MagicMock(return_value=None)
        mock_dms.delay = MagicMock(return_value=None)

        result = poll_twitter_all()

    assert result["queued"] == 1
    mock_activity.delay.assert_called_once_with(str(uid_with))
    mock_dms.delay.assert_called_once_with(str(uid_with))


def test_poll_twitter_all_no_connected_users():
    """Returns queued=0 when no users have twitter_refresh_token."""
    mock_session = _make_mock_session([])

    with (
        patch("app.services.task_jobs.twitter.task_session", return_value=mock_session),
        patch("app.services.task_jobs.twitter.poll_twitter_activity") as mock_activity,
        patch("app.services.task_jobs.twitter.sync_twitter_dms_for_user") as mock_dms,
    ):
        mock_activity.delay = MagicMock(return_value=None)
        mock_dms.delay = MagicMock(return_value=None)

        result = poll_twitter_all()

    assert result["queued"] == 0
    mock_activity.delay.assert_not_called()
    mock_dms.delay.assert_not_called()


def test_poll_twitter_all_queues_all_connected_users():
    """All connected users are enqueued when multiple have tokens."""
    uids = [uuid.uuid4() for _ in range(3)]
    mock_session = _make_mock_session(uids)

    with (
        patch("app.services.task_jobs.twitter.task_session", return_value=mock_session),
        patch("app.services.task_jobs.twitter.poll_twitter_activity") as mock_activity,
        patch("app.services.task_jobs.twitter.sync_twitter_dms_for_user") as mock_dms,
    ):
        mock_activity.delay = MagicMock(return_value=None)
        mock_dms.delay = MagicMock(return_value=None)

        result = poll_twitter_all()

    assert result["queued"] == 3
    assert mock_activity.delay.call_count == 3
    assert mock_dms.delay.call_count == 3
    called_ids = {call.args[0] for call in mock_activity.delay.call_args_list}
    assert called_ids == {str(u) for u in uids}


def test_poll_twitter_all_query_filters_by_refresh_token():
    """The DB query includes a WHERE twitter_refresh_token IS NOT NULL filter."""
    from sqlalchemy import Select

    captured_queries: list = []

    mock_session = _make_mock_session([])

    original_execute = mock_session.__aenter__.return_value.execute

    async def capture_execute(stmt, *args, **kwargs):
        captured_queries.append(stmt)
        return await original_execute(stmt, *args, **kwargs)

    mock_session.__aenter__.return_value.execute = capture_execute

    with (
        patch("app.services.task_jobs.twitter.task_session", return_value=mock_session),
        patch("app.services.task_jobs.twitter.poll_twitter_activity"),
        patch("app.services.task_jobs.twitter.sync_twitter_dms_for_user"),
    ):
        poll_twitter_all()

    assert len(captured_queries) == 1
    compiled = str(captured_queries[0].compile(compile_kwargs={"literal_binds": True}))
    assert "twitter_refresh_token" in compiled
    assert "IS NOT NULL" in compiled
