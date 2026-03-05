"""Tests for message composer service."""
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.models.interaction import Interaction
from app.services.message_composer import analyze_conversation_tone


def _make_interaction(content: str, direction: str = "inbound") -> Interaction:
    """Create a mock interaction for testing."""
    ix = MagicMock(spec=Interaction)
    ix.content_preview = content
    ix.direction = direction
    return ix


def test_tone_formal_empty():
    assert analyze_conversation_tone([]) == "formal"


def test_tone_formal():
    interactions = [
        _make_interaction("Dear Mr. Smith, please find attached the quarterly report."),
        _make_interaction("Thank you for the update on the project status."),
        _make_interaction("We would like to schedule a meeting next week."),
    ]
    assert analyze_conversation_tone(interactions) == "formal"


def test_tone_casual():
    interactions = [
        _make_interaction("Hey! How's it going?"),
        _make_interaction("lol that's hilarious"),
        _make_interaction("Awesome, see you there!"),
        _make_interaction("btw, check this out"),
        _make_interaction("thx for the intro!"),
    ]
    assert analyze_conversation_tone(interactions) == "casual"


def test_tone_mixed():
    interactions = [
        _make_interaction("Hey, quick question about the proposal"),
        _make_interaction("Sounds good, let me review the document"),
        _make_interaction("Please let me know your availability"),
    ]
    tone = analyze_conversation_tone(interactions)
    assert tone in ("formal", "casual")


def test_tone_no_content():
    ix = MagicMock(spec=Interaction)
    ix.content_preview = None
    assert analyze_conversation_tone([ix]) == "formal"
