"""Tests for Google Contacts sync error handling and notification details."""
import pytest

from app.integrations.google_contacts import _extract_contact_fields, _name_from_email


class TestExtractContactFields:
    def test_empty_emails_returns_empty_list(self):
        """Contacts without emails should return [] not None."""
        person = {"names": [{"displayName": "John Doe", "givenName": "John"}]}
        fields = _extract_contact_fields(person)
        assert fields["emails"] == []
        assert fields["phones"] == []

    def test_with_emails(self):
        person = {
            "names": [{"displayName": "Jane", "givenName": "Jane"}],
            "emailAddresses": [{"value": "jane@example.com"}],
        }
        fields = _extract_contact_fields(person)
        assert fields["emails"] == ["jane@example.com"]

    def test_with_phones(self):
        person = {
            "names": [{"displayName": "Bob"}],
            "phoneNumbers": [{"value": "+1234567890"}],
        }
        fields = _extract_contact_fields(person)
        assert fields["phones"] == ["+1234567890"]

    def test_with_organization(self):
        person = {
            "names": [{"displayName": "Alice"}],
            "organizations": [{"name": "Acme", "title": "CEO"}],
        }
        fields = _extract_contact_fields(person)
        assert fields["company"] == "Acme"
        assert fields["title"] == "CEO"

    def test_no_names(self):
        person = {"emailAddresses": [{"value": "anon@test.com"}]}
        fields = _extract_contact_fields(person)
        assert fields["full_name"] is None
        assert fields["given_name"] is None
        assert fields["emails"] == ["anon@test.com"]

    def test_emails_with_empty_values_filtered(self):
        person = {
            "emailAddresses": [
                {"value": "good@test.com"},
                {"value": ""},
                {},
            ],
        }
        fields = _extract_contact_fields(person)
        assert fields["emails"] == ["good@test.com"]

    def test_name_inferred_from_email_when_no_names(self):
        """When Google provides no names, infer from email local part."""
        person = {
            "emailAddresses": [{"value": "david.rodriguez@blockworks.co"}],
        }
        fields = _extract_contact_fields(person)
        assert fields["given_name"] == "David"
        assert fields["family_name"] == "Rodriguez"
        assert fields["full_name"] == "David Rodriguez"

    def test_name_not_inferred_when_names_present(self):
        """When Google provides names, don't override with email inference."""
        person = {
            "names": [{"givenName": "Dave", "familyName": "R", "displayName": "Dave R"}],
            "emailAddresses": [{"value": "david.rodriguez@blockworks.co"}],
        }
        fields = _extract_contact_fields(person)
        assert fields["given_name"] == "Dave"
        assert fields["family_name"] == "R"


class TestNameFromEmail:
    def test_dot_separated(self):
        assert _name_from_email("david.rodriguez@company.co") == ("David", "Rodriguez")

    def test_underscore_separated(self):
        assert _name_from_email("john_smith@gmail.com") == ("John", "Smith")

    def test_hyphen_separated(self):
        assert _name_from_email("jane-doe@example.com") == ("Jane", "Doe")

    def test_trailing_digits_stripped(self):
        assert _name_from_email("john.smith01@gmail.com") == ("John", "Smith")

    def test_ambiguous_returns_none(self):
        assert _name_from_email("jdoe@example.com") is None

    def test_single_word_returns_none(self):
        assert _name_from_email("admin@company.com") is None

    def test_single_char_fragments_filtered(self):
        """Single-char fragments like 'j' in j.doe are filtered out."""
        assert _name_from_email("j.doe@example.com") is None

    def test_three_parts_uses_first_two(self):
        assert _name_from_email("john.middle.doe@example.com") == ("John", "Middle")
