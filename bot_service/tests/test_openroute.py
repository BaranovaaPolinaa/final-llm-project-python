import json

import httpx
import pytest
import respx

from app.core.config import settings
from app.services.openrouter_client import call_openrouter


@pytest.mark.asyncio
@respx.mock
async def test_call_openrouter_returns_content():
    mock_json = {
        "choices": [
            {"message": {"role": "assistant", "content": "Python — отличный язык!"}}
        ]
    }
    respx.post(f"{settings.OPENROUTER_BASE_URL}/chat/completions").mock(
        return_value=httpx.Response(200, json=mock_json)
    )

    result = await call_openrouter("Расскажи про Python")

    assert result == "Python — отличный язык!"


@pytest.mark.asyncio
@respx.mock
async def test_call_openrouter_sends_correct_payload():
    mock_json = {
        "choices": [{"message": {"role": "assistant", "content": "Ответ"}}]
    }
    route = respx.post(f"{settings.OPENROUTER_BASE_URL}/chat/completions").mock(
        return_value=httpx.Response(200, json=mock_json)
    )

    await call_openrouter("Вопрос пользователя")

    body = json.loads(route.calls.last.request.content)
    assert body["messages"][0]["role"] == "user"
    assert body["messages"][0]["content"] == "Вопрос пользователя"
