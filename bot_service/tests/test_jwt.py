from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from app.core.config import settings
from app.core.jwt import decode_and_validate


def _make_token(sub: str = "1", role: str = "user", exp_delta_minutes: int = 60) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=exp_delta_minutes),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def test_valid_token_sub_extracted():
    token = _make_token(sub="1")
    payload = decode_and_validate(token)
    assert payload["sub"] == "1"


def test_garbage_string_raises_value_error():
    with pytest.raises(ValueError):
        decode_and_validate("this.is.garbage")
