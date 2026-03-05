"""Tests for digest email service."""
import uuid
from datetime import UTC, datetime

import pytest

from app.services.digest_email import _build_html, _format_date


def test_format_date_none():
    assert _format_date(None) == "Unknown"


def test_format_date():
    dt = datetime(2024, 6, 15, 12, 0, 0)
    assert _format_date(dt) == "Jun 15, 2024"


def test_build_html_empty():
    html = _build_html("user@test.com", [])
    assert "Ping" in html
    assert "weekly networking digest" in html


def test_build_html_with_items():
    items = [
        {
            "contact_name": "Alice",
            "reason": "It's been a while",
            "last_interaction": "Jan 01, 2024",
            "message_preview": "Hey Alice, how are things?",
            "suggestion_id": str(uuid.uuid4()),
        }
    ]
    html = _build_html("user@test.com", items)
    assert "Alice" in html
    assert "It's been a while" in html
    assert "Open in Ping" in html
