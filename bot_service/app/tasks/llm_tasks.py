import asyncio

import httpx

from app.core.config import settings
from app.infra.celery_app import celery_app


@celery_app.task(name="app.tasks.llm_tasks.llm_request", bind=True, max_retries=3)
def llm_request(self, tg_chat_id: int, prompt: str) -> None:

    try:
        answer = asyncio.run(_get_llm_answer(prompt))
    except Exception as exc:
        answer = f"Ошибка при обращении к LLM: {exc}"

    asyncio.run(_send_to_telegram(tg_chat_id, answer))


async def _get_llm_answer(prompt: str) -> str:
    from app.services.openrouter_client import call_openrouter
    return await call_openrouter(prompt)


async def _send_to_telegram(chat_id: int, text: str) -> None:
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    safe_text = text[:4096] if text else "Нет ответа от модели"
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(url, json={"chat_id": chat_id, "text": safe_text})
            if response.status_code != 200:
                print(f"[llm_request] Telegram error: {response.status_code} {response.text}")
        except Exception as exc:
            print(f"[llm_request] Failed to send message to {chat_id}: {exc}")
