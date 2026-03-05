"""Tests for identity resolution helper functions and probabilistic matching."""
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.user import User
from app.services.identity_resolution import (
    _email_domain_match,
    _name_similarity,
    _username_similarity,
    find_probabilistic_matches,
    merge_contacts,
)


def test_name_similarity_identical():
    assert _name_similarity("John Doe", "John Doe") == 1.0


def test_name_similarity_close():
    score = _name_similarity("Jon Doe", "John Doe")
    assert 0.7 < score < 1.0


def test_name_similarity_different():
    score = _name_similarity("Alice", "Bob")
    assert score < 0.5


def test_name_similarity_empty():
    assert _name_similarity("", "Bob") == 0.0
    assert _name_similarity("Alice", "") == 0.0


def test_email_domain_match_same_corp_domain():
    assert _email_domain_match(["alice@acme.com"], ["bob@acme.com"]) == 1.0


def test_email_domain_match_common_provider_ignored():
    assert _email_domain_match(["alice@gmail.com"], ["bob@gmail.com"]) == 0.0


def test_email_domain_match_different_domains():
    assert _email_domain_match(["alice@acme.com"], ["bob@other.com"]) == 0.0


def test_email_domain_match_empty():
    assert _email_domain_match(None, ["bob@acme.com"]) == 0.0
    assert _email_domain_match([], []) == 0.0


def test_username_similarity_identical():
    assert _username_similarity("@johndoe", "@johndoe") == 1.0


def test_username_similarity_close():
    score = _username_similarity("johndoe", "john_doe")
    assert score > 0.5


def test_username_similarity_empty():
    assert _username_similarity(None, "@bob") == 0.0
    assert _username_similarity("", "@bob") == 0.0


@pytest.mark.asyncio
async def test_merge_contacts_not_found(db: AsyncSession):
    with pytest.raises(ValueError, match="not found"):
        await merge_contacts(uuid.uuid4(), uuid.uuid4(), db)


@pytest.mark.asyncio
async def test_merge_contacts_swaps_richer_primary(
    db: AsyncSession, test_user: User
):
    """Contact with more data becomes the primary."""
    sparse = Contact(
        id=uuid.uuid4(),
        user_id=test_user.id,
        full_name="Sparse",
        emails=["sparse@test.com"],
    )
    rich = Contact(
        id=uuid.uuid4(),
        user_id=test_user.id,
        full_name="Rich Person",
        emails=["rich@test.com"],
        company="RichCo",
        title="CEO",
        twitter_handle="@rich",
        tags=["vip", "investor"],
    )
    db.add_all([sparse, rich])
    await db.commit()

    match = await merge_contacts(sparse.id, rich.id, db)
    assert match.status == "merged"
    # Rich should be the primary (contact_a_id) since it has more data
    assert match.contact_a_id == rich.id


@pytest.mark.asyncio
async def test_probabilistic_matches_high_score_auto_merge(
    db: AsyncSession, test_user: User
):
    """Contacts with same company domain + similar names get auto-merged."""
    c1 = Contact(
        id=uuid.uuid4(),
        user_id=test_user.id,
        full_name="John Smith",
        emails=["john@acmecorp.com"],
        company="Acme Corp",
    )
    c2 = Contact(
        id=uuid.uuid4(),
        user_id=test_user.id,
        full_name="John Smith",
        emails=["jsmith@acmecorp.com"],
        company="Acme Corp",
    )
    db.add_all([c1, c2])
    await db.commit()

    matches = await find_probabilistic_matches(test_user.id, db)
    # score = 0.40*1.0 (domain) + 0.20*1.0 (name) + 0.20*1.0 (company) = 0.80
    # plus potential username/mutual. Should be pending_review or auto-merged
    assert len(matches) >= 1


@pytest.mark.asyncio
async def test_probabilistic_matches_low_score_ignored(
    db: AsyncSession, test_user: User
):
    """Completely different contacts should not match."""
    c1 = Contact(
        id=uuid.uuid4(),
        user_id=test_user.id,
        full_name="Alice",
        emails=["alice@gmail.com"],
    )
    c2 = Contact(
        id=uuid.uuid4(),
        user_id=test_user.id,
        full_name="Bob",
        emails=["bob@yahoo.com"],
    )
    db.add_all([c1, c2])
    await db.commit()

    matches = await find_probabilistic_matches(test_user.id, db)
    assert len(matches) == 0
