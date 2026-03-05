"""Tests for Pydantic schemas and validation."""
import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate
from app.schemas.contact import ContactCreate, ContactUpdate


def test_user_create_valid():
    user = UserCreate(email="test@example.com", password="securepass123")
    assert user.email == "test@example.com"


def test_user_create_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(email="not-an-email", password="securepass123")


def test_user_create_short_password():
    with pytest.raises(ValidationError):
        UserCreate(email="test@example.com", password="short")


def test_user_create_empty_password():
    with pytest.raises(ValidationError):
        UserCreate(email="test@example.com", password="")


def test_contact_create_defaults():
    contact = ContactCreate()
    assert contact.full_name is None
    assert contact.emails == []
    assert contact.priority_level == "medium"


def test_contact_create_with_fields():
    contact = ContactCreate(
        full_name="John Doe",
        emails=["john@test.com"],
        twitter_handle="@johndoe",
        tags=["vip", "investor"],
    )
    assert contact.full_name == "John Doe"
    assert contact.twitter_handle == "@johndoe"
    assert len(contact.tags) == 2


def test_contact_update_partial():
    update = ContactUpdate(company="NewCo")
    data = update.model_dump(exclude_unset=True)
    assert "company" in data
    assert "full_name" not in data
