"""Tests for identity resolution service."""
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.user import User
from app.services.identity_resolution import (
    _levenshtein,
    _names_similar,
    _normalize_phone,
    find_deterministic_matches,
    merge_contacts,
)


def test_normalize_phone():
    assert _normalize_phone("+1 (234) 567-8900") == "12345678900"
    assert _normalize_phone("") == ""


def test_levenshtein():
    assert _levenshtein("kitten", "sitting") == 3
    assert _levenshtein("", "abc") == 3
    assert _levenshtein("same", "same") == 0


def test_names_similar():
    assert _names_similar("John Doe", "John Doe") is True
    assert _names_similar("John Doe", "Jon Doe") is True  # 1 edit
    assert _names_similar("Alice", "Bob") is False
    assert _names_similar("", "Bob") is False


@pytest.mark.asyncio
async def test_deterministic_match_by_email(db: AsyncSession, test_user: User):
    c1 = Contact(user_id=test_user.id, full_name="Alice A", emails=["shared@test.com"])
    c2 = Contact(user_id=test_user.id, full_name="Alice B", emails=["shared@test.com"])
    db.add_all([c1, c2])
    await db.flush()

    matches = await find_deterministic_matches(test_user.id, db)
    assert len(matches) == 1
    assert matches[0].status == "merged"


@pytest.mark.asyncio
async def test_deterministic_match_by_phone(db: AsyncSession, test_user: User):
    c1 = Contact(user_id=test_user.id, full_name="Bob A", phones=["+1-234-567-8900"])
    c2 = Contact(user_id=test_user.id, full_name="Bob B", phones=["12345678900"])
    db.add_all([c1, c2])
    await db.flush()

    matches = await find_deterministic_matches(test_user.id, db)
    assert len(matches) == 1


@pytest.mark.asyncio
async def test_no_false_deterministic_match(db: AsyncSession, test_user: User):
    c1 = Contact(user_id=test_user.id, full_name="Alice", emails=["alice@test.com"])
    c2 = Contact(user_id=test_user.id, full_name="Bob", emails=["bob@test.com"])
    db.add_all([c1, c2])
    await db.flush()

    matches = await find_deterministic_matches(test_user.id, db)
    assert len(matches) == 0


@pytest.mark.asyncio
async def test_merge_contacts(db: AsyncSession, test_user: User):
    c1 = Contact(
        user_id=test_user.id, full_name="Primary",
        emails=["primary@test.com"], company="PrimaryCo",
    )
    c2 = Contact(
        user_id=test_user.id, full_name="Secondary",
        emails=["secondary@test.com"], twitter_handle="@secondary",
    )
    db.add_all([c1, c2])
    await db.flush()

    match = await merge_contacts(c1.id, c2.id, db)
    assert match.status == "merged"

    # Primary should have merged emails
    result = await db.execute(select(Contact).where(Contact.id == c1.id))
    merged = result.scalar_one()
    assert "primary@test.com" in merged.emails
    assert "secondary@test.com" in merged.emails
    assert merged.twitter_handle == "@secondary"

    # Secondary should be deleted
    result = await db.execute(select(Contact).where(Contact.id == c2.id))
    assert result.scalar_one_or_none() is None


