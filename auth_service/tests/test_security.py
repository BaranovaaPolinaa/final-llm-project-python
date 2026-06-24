import pytest

from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_not_equal_to_password():
    hashed = hash_password("password123")
    assert hashed != "password123"


def test_verify_correct_password():
    hashed = hash_password("password123")
    assert verify_password("password123", hashed) is True


def test_verify_wrong_password():
    hashed = hash_password("password123")
    assert verify_password("wrong_password", hashed) is False


def test_different_hashes_for_same_password():
    hash_1 = hash_password("password123")
    hash_2 = hash_password("password123")
    assert hash_1 != hash_2


def test_create_and_decode_token_contains_required_fields():
    token = create_access_token(sub="1", role="user")
    payload = decode_token(token)
    assert payload["sub"] == "1"
    assert payload["role"] == "user"
    assert "iat" in payload
    assert "exp" in payload
