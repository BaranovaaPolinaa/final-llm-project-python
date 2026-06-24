from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from jose import jwt

from app.core.config import settings


def _make_token(sub: str = "42", role: str = "user", exp_minutes: int = 60) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=exp_minutes),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def _make_message(text: str, user_id: int = 123, chat_id: int = 456) -> MagicMock:
    message = MagicMock()
    message.text = text
    message.from_user = MagicMock()
    message.from_user.id = user_id
    message.chat = MagicMock()
    message.chat.id = chat_id
    message.answer = AsyncMock()
    return message


@pytest.mark.asyncio
async def test_token_command_saves_to_redis(fake_redis):
    token = _make_token(sub="10")
    message = _make_message(f"/token {token}", user_id=10)

    async def mock_get_redis():
        return fake_redis

    with patch("app.bot.handlers.get_redis", mock_get_redis):
        from app.bot.handlers import cmd_token
        await cmd_token(message)

    stored = await fake_redis.get("token:10")
    assert stored == token


@pytest.mark.asyncio
async def test_text_without_token_does_not_call_celery(fake_redis):
    message = _make_message("Привет! Что ты умеешь?", user_id=100)

    async def mock_get_redis():
        return fake_redis

    mock_task = MagicMock()

    with patch("app.bot.handlers.get_redis", mock_get_redis):
        with patch("app.bot.handlers.llm_request", mock_task):
            from app.bot.handlers import handle_text
            await handle_text(message)

    mock_task.delay.assert_not_called()


@pytest.mark.asyncio
async def test_text_with_valid_token_calls_celery_with_correct_args(fake_redis):
    token = _make_token(sub="200")
    await fake_redis.set("token:200", token)

    message = _make_message("Привет! Что такое FastAPI?", user_id=200, chat_id=200)

    async def mock_get_redis():
        return fake_redis

    mock_task = MagicMock()

    with patch("app.bot.handlers.get_redis", mock_get_redis):
        with patch("app.bot.handlers.llm_request", mock_task):
            from app.bot.handlers import handle_text
            await handle_text(message)

    mock_task.delay.assert_called_once_with(200, "Привет! Что такое FastAPI?")
