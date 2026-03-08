"""Tests for auto_tagger service."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.auto_tagger import (
    _build_contact_summary,
    _parse_json_response,
    assign_tags,
    discover_taxonomy,
    merge_tags,
)


# ---------------------------------------------------------------------------
# merge_tags
# ---------------------------------------------------------------------------

class TestMergeTags:
    def test_case_insensitive_dedup(self):
        result = merge_tags(["CEO", "Founder"], ["ceo", "Developer"])
        assert result == ["CEO", "Founder", "Developer"]

    def test_append_only_never_removes(self):
        existing = ["CEO", "Founder"]
        result = merge_tags(existing, [])
        assert "CEO" in result
        assert "Founder" in result
        assert len(result) == 2

    def test_none_existing(self):
        result = merge_tags(None, ["A"])
        assert result == ["A"]

    def test_empty_new_tags_returns_existing_unchanged(self):
        existing = ["Tag1", "Tag2"]
        result = merge_tags(existing, [])
        assert result == ["Tag1", "Tag2"]

    def test_preserves_order_existing_first(self):
        result = merge_tags(["B", "A"], ["C", "D"])
        assert result == ["B", "A", "C", "D"]

    def test_preserves_existing_case_on_duplicate(self):
        # "CEO" is existing; "ceo" is new — "CEO" canonical form is kept, not added again
        result = merge_tags(["CEO"], ["ceo", "Founder"])
        assert result.count("CEO") == 1
        assert "ceo" not in result
        assert "Founder" in result

    def test_empty_existing_list(self):
        result = merge_tags([], ["X", "Y"])
        assert result == ["X", "Y"]

    def test_all_new_already_present(self):
        result = merge_tags(["A", "B"], ["a", "B"])
        assert len(result) == 2

    def test_returns_new_list_not_mutation(self):
        existing = ["A"]
        result = merge_tags(existing, ["B"])
        assert result is not existing


# ---------------------------------------------------------------------------
# _build_contact_summary
# ---------------------------------------------------------------------------

class TestBuildContactSummary:
    def test_all_fields_populated(self):
        contact = {
            "full_name": "Jane Doe",
            "title": "CTO",
            "company": "Acme",
            "twitter_bio": "Building things",
            "telegram_bio": "Crypto builder",
            "notes": "Met at conference",
            "tags": ["Founder", "AI"],
            "location": "San Francisco",
            "interaction_topics": ["Web3", "AI Safety"],
        }
        summary = _build_contact_summary(contact)
        assert "Name:" in summary
        assert "Title:" in summary
        assert "Company:" in summary
        assert "Twitter bio:" in summary
        assert "Telegram bio:" in summary
        assert "Notes:" in summary
        assert "Existing tags:" in summary
        assert "Location:" in summary
        assert "Interaction topics:" in summary

    def test_empty_dict_returns_minimal_data(self):
        result = _build_contact_summary({})
        assert result == "(minimal data)"

    def test_values_wrapped_in_value_tags(self):
        contact = {"full_name": "Alice"}
        summary = _build_contact_summary(contact)
        assert "<value>Alice</value>" in summary

    def test_long_name_truncated_at_100_chars(self):
        long_name = "A" * 200
        contact = {"full_name": long_name}
        summary = _build_contact_summary(contact)
        # The truncated name inside <value> tags should be 100 chars
        assert "<value>" + "A" * 100 + "</value>" in summary
        assert "A" * 101 not in summary

    def test_long_twitter_bio_truncated_at_200_chars(self):
        long_bio = "B" * 300
        contact = {"twitter_bio": long_bio}
        summary = _build_contact_summary(contact)
        assert "<value>" + "B" * 200 + "</value>" in summary
        assert "B" * 201 not in summary

    def test_notes_filter_excludes_twitter_bio_sentinel(self):
        contact = {
            "notes": "Met at ETHdenver\n__twitter_bio__: Engineer at Acme\nFollowup needed",
        }
        summary = _build_contact_summary(contact)
        assert "__twitter_bio__:" not in summary
        assert "Met at ETHdenver" in summary
        assert "Followup needed" in summary

    def test_notes_only_sentinel_lines_gives_empty_notes(self):
        contact = {"notes": "__twitter_bio__: some bio"}
        summary = _build_contact_summary(contact)
        # After filtering, trimmed is empty → Notes line should not appear
        assert "Notes:" not in summary

    def test_tags_list_formatted_correctly(self):
        contact = {"tags": ["CEO", "Founder", "AI"]}
        summary = _build_contact_summary(contact)
        assert "Existing tags:" in summary
        assert "CEO" in summary
        assert "Founder" in summary
        assert "AI" in summary

    def test_missing_optional_fields_skipped(self):
        contact = {"full_name": "Bob"}
        summary = _build_contact_summary(contact)
        assert "Title:" not in summary
        assert "Company:" not in summary
        assert "Twitter bio:" not in summary


# ---------------------------------------------------------------------------
# _parse_json_response
# ---------------------------------------------------------------------------

class TestParseJsonResponse:
    def test_bare_json_object(self):
        result = _parse_json_response('{"a": 1}')
        assert result == {"a": 1}

    def test_code_fence_with_language(self):
        raw = '```json\n{"a": 1}\n```'
        result = _parse_json_response(raw)
        assert result == {"a": 1}

    def test_code_fence_without_language(self):
        raw = '```\n{"a": 1}\n```'
        result = _parse_json_response(raw)
        assert result == {"a": 1}

    def test_invalid_json_returns_none(self):
        result = _parse_json_response("this is not json at all")
        assert result is None

    def test_empty_string_returns_none(self):
        result = _parse_json_response("")
        assert result is None

    def test_bare_json_array(self):
        result = _parse_json_response('["x", "y"]')
        assert result == ["x", "y"]

    def test_whitespace_stripped(self):
        result = _parse_json_response('  {"b": 2}  ')
        assert result == {"b": 2}

    def test_nested_object(self):
        raw = '{"Role": ["CEO", "Founder"], "Industry": ["Tech"]}'
        result = _parse_json_response(raw)
        assert result["Role"] == ["CEO", "Founder"]
        assert result["Industry"] == ["Tech"]


# ---------------------------------------------------------------------------
# discover_taxonomy
# ---------------------------------------------------------------------------

def _make_mock_client(response_text: str):
    """Build a mock AsyncAnthropic client returning the given text."""
    mock_content = MagicMock()
    mock_content.text = response_text

    mock_message = MagicMock()
    mock_message.content = [mock_content]

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_message)
    return mock_client


@pytest.mark.asyncio
async def test_discover_taxonomy_no_api_key():
    with patch("app.services.auto_tagger.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = ""
        result = await discover_taxonomy([{"full_name": "Alice"}])
    assert result == {}


@pytest.mark.asyncio
async def test_discover_taxonomy_empty_contacts():
    with patch("app.services.auto_tagger.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        result = await discover_taxonomy([])
    assert result == {}


@pytest.mark.asyncio
async def test_discover_taxonomy_valid_response():
    taxonomy_json = '{"Role": ["CEO", "CTO"], "Industry": ["Tech"]}'
    mock_client = _make_mock_client(taxonomy_json)

    with patch("app.services.auto_tagger.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        with patch("app.services.auto_tagger._get_anthropic_client", return_value=mock_client):
            result = await discover_taxonomy([{"full_name": "Alice", "title": "CEO"}])

    assert "Role" in result
    assert "CEO" in result["Role"]
    assert "CTO" in result["Role"]
    assert "Industry" in result
    assert "Tech" in result["Industry"]


@pytest.mark.asyncio
async def test_discover_taxonomy_batching_60_contacts():
    """60 contacts with _BATCH_SIZE=50 should result in 2 API calls."""
    taxonomy_json = '{"Role": ["Engineer"]}'
    mock_client = _make_mock_client(taxonomy_json)

    contacts = [{"full_name": f"Contact {i}"} for i in range(60)]

    with patch("app.services.auto_tagger.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        with patch("app.services.auto_tagger._get_anthropic_client", return_value=mock_client):
            result = await discover_taxonomy(contacts)

    # Should have been called twice (batch 1: 50 contacts, batch 2: 10 contacts)
    assert mock_client.messages.create.call_count == 2
    assert "Role" in result
    assert "Engineer" in result["Role"]


@pytest.mark.asyncio
async def test_discover_taxonomy_first_batch_failure_raises():
    """If the first batch API call raises, discover_taxonomy must propagate the exception."""
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(side_effect=RuntimeError("API down"))

    contacts = [{"full_name": "Alice"}]

    with patch("app.services.auto_tagger.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        with patch("app.services.auto_tagger._get_anthropic_client", return_value=mock_client):
            with pytest.raises(RuntimeError, match="API down"):
                await discover_taxonomy(contacts)


@pytest.mark.asyncio
async def test_discover_taxonomy_second_batch_failure_continues():
    """If only the second batch fails, partial results from the first batch are returned."""
    good_json = '{"Role": ["Engineer"]}'
    mock_content = MagicMock()
    mock_content.text = good_json

    mock_message = MagicMock()
    mock_message.content = [mock_content]

    call_count = 0

    async def side_effect(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_message
        raise RuntimeError("second batch failed")

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(side_effect=side_effect)

    contacts = [{"full_name": f"Contact {i}"} for i in range(60)]

    with patch("app.services.auto_tagger.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        with patch("app.services.auto_tagger._get_anthropic_client", return_value=mock_client):
            result = await discover_taxonomy(contacts)

    # First batch succeeded, so we get partial results
    assert "Role" in result
    assert "Engineer" in result["Role"]


# ---------------------------------------------------------------------------
# assign_tags
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_assign_tags_no_api_key():
    with patch("app.services.auto_tagger.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = ""
        result = await assign_tags({"full_name": "Alice"}, {"Role": ["CEO"]})
    assert result == []


@pytest.mark.asyncio
async def test_assign_tags_returns_matching_tags():
    taxonomy = {"Role": ["CEO", "Founder"]}
    response_json = '{"tags": ["CEO", "Founder"], "new_tags": []}'
    mock_client = _make_mock_client(response_json)

    with patch("app.services.auto_tagger.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        result = await assign_tags(
            {"full_name": "Alice", "title": "CEO and Founder"},
            taxonomy,
            client=mock_client,
        )

    assert "CEO" in result
    assert "Founder" in result


@pytest.mark.asyncio
async def test_assign_tags_filters_out_tags_not_in_taxonomy():
    taxonomy = {"Role": ["CEO"]}
    # LLM returns a tag that's not in the taxonomy
    response_json = '{"tags": ["CEO", "Alien Overlord"], "new_tags": []}'
    mock_client = _make_mock_client(response_json)

    with patch("app.services.auto_tagger.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        result = await assign_tags(
            {"full_name": "Alice"},
            taxonomy,
            client=mock_client,
        )

    assert "CEO" in result
    assert "Alien Overlord" not in result


@pytest.mark.asyncio
async def test_assign_tags_case_insensitive_match_returns_canonical():
    """LLM returns 'ceo' (lowercase); taxonomy has 'CEO' — canonical form is returned."""
    taxonomy = {"Role": ["CEO", "Founder"]}
    response_json = '{"tags": ["ceo"], "new_tags": []}'
    mock_client = _make_mock_client(response_json)

    with patch("app.services.auto_tagger.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        result = await assign_tags(
            {"full_name": "Alice"},
            taxonomy,
            client=mock_client,
        )

    assert "CEO" in result
    assert "ceo" not in result


@pytest.mark.asyncio
async def test_assign_tags_api_failure_returns_empty_list():
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(side_effect=RuntimeError("API error"))

    with patch("app.services.auto_tagger.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        result = await assign_tags(
            {"full_name": "Alice"},
            {"Role": ["CEO"]},
            client=mock_client,
        )

    assert result == []


@pytest.mark.asyncio
async def test_assign_tags_invalid_json_response_returns_empty_list():
    mock_client = _make_mock_client("not json at all")

    with patch("app.services.auto_tagger.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        result = await assign_tags(
            {"full_name": "Alice"},
            {"Role": ["CEO"]},
            client=mock_client,
        )

    assert result == []


@pytest.mark.asyncio
async def test_assign_tags_uses_provided_client_not_new_one():
    """When a client is passed in, _get_anthropic_client should not be called."""
    taxonomy = {"Role": ["Engineer"]}
    response_json = '{"tags": ["Engineer"], "new_tags": []}'
    mock_client = _make_mock_client(response_json)

    with patch("app.services.auto_tagger.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        with patch("app.services.auto_tagger._get_anthropic_client") as mock_factory:
            result = await assign_tags(
                {"full_name": "Bob", "title": "Software Engineer"},
                taxonomy,
                client=mock_client,
            )
            mock_factory.assert_not_called()

    assert "Engineer" in result


@pytest.mark.asyncio
async def test_assign_tags_empty_tags_in_response():
    taxonomy = {"Role": ["CEO"]}
    response_json = '{"tags": [], "new_tags": []}'
    mock_client = _make_mock_client(response_json)

    with patch("app.services.auto_tagger.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        result = await assign_tags({"full_name": "Alice"}, taxonomy, client=mock_client)

    assert result == []
