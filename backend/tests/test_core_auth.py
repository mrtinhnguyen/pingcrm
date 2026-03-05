"""Tests for core auth utilities."""
import uuid
from datetime import timedelta

import pytest

from app.core.auth import create_access_token, hash_password, verify_password


def test_hash_and_verify_password():
    hashed = hash_password("mypassword")
    assert hashed != "mypassword"
    assert verify_password("mypassword", hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_create_access_token():
    token = create_access_token(data={"sub": str(uuid.uuid4())})
    assert isinstance(token, str)
    assert len(token) > 20


def test_create_access_token_with_expiry():
    token = create_access_token(
        data={"sub": "user123"},
        expires_delta=timedelta(minutes=5),
    )
    assert isinstance(token, str)


def test_create_access_token_different_per_user():
    t1 = create_access_token(data={"sub": "user1"})
    t2 = create_access_token(data={"sub": "user2"})
    assert t1 != t2
