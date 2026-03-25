"""Tests for meeting-prep email sending via Gmail API."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Gmail send service tests
# ---------------------------------------------------------------------------


class _FakeGoogleAccount:
    """Minimal stand-in for a Google account object."""

    def __init__(self, refresh_token: str = "refresh_tok", email: str = "user@example.com"):
        self.refresh_token = refresh_token
        self.email = email


@patch("app.integrations.gmail_send.build")
@patch("app.integrations.gmail_send.Credentials")
def test_send_email_calls_gmail_api(mock_creds_cls, mock_build):
    """send_email builds credentials, sends message, and returns True."""
    from app.integrations.gmail_send import send_email

    mock_service = MagicMock()
    mock_build.return_value = mock_service

    account = _FakeGoogleAccount()
    result = send_email(account, "Subject", "<p>Hello</p>")

    assert result is True
    mock_creds_cls.assert_called_once()
    mock_build.assert_called_once()
    mock_service.users.return_value.messages.return_value.send.assert_called_once()


@patch("app.integrations.gmail_send.build")
@patch("app.integrations.gmail_send.Credentials")
def test_send_email_returns_false_on_network_failure(mock_creds_cls, mock_build):
    """send_email returns False when the API execute() raises a generic exception."""
    from app.integrations.gmail_send import send_email

    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.users.return_value.messages.return_value.send.return_value.execute.side_effect = (
        Exception("network timeout")
    )

    account = _FakeGoogleAccount()
    result = send_email(account, "Subject", "<p>Hello</p>")

    assert result is False


@patch("app.integrations.gmail_send.build")
@patch("app.integrations.gmail_send.Credentials")
def test_send_email_returns_auth_error_on_refresh_failure(mock_creds_cls, mock_build):
    """send_email returns 'auth_error' when credential refresh fails."""
    from google.auth.exceptions import RefreshError

    from app.integrations.gmail_send import send_email

    mock_build.side_effect = RefreshError("token revoked")

    account = _FakeGoogleAccount()
    result = send_email(account, "Subject", "<p>Hello</p>")

    assert result == "auth_error"
