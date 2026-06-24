from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.core.jwt import decode_and_validate
from app.infra.redis import get_redis
from typing import Any, cast

from app.tasks.llm_tasks import llm_request

router = Router()


def _token_key(user_id: int) -> str:
    return f"token:{user_id}"


def _get_user_id(message: Message) -> int:
    """Return a stable user id for storing tokens (fallback to chat id)."""
    if message.from_user and getattr(message.from_user, "id", None):
        return message.from_user.id
    return message.chat.id


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(
        "👋 Привет! Я LLM-консультант.\n\n"
        "Для работы необходима авторизация:\n"
        "Зарегистрируйтесь в Auth Service (Swagger: http://localhost:8000/docs)\n"
        "Получите JWT-токен через POST /auth/login\n"
        "Передайте токен боту командой:\n"
        "   /token <ваш_JWT_токен>\n\n"
        "После этого просто напишите ваш вопрос!"
    )


@router.message(Command("token"))
async def cmd_token(message: Message) -> None:
    parts = (message.text or "").strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /token <ваш_JWT_токен>")
        return

    token = parts[1].strip()

    try:
        decode_and_validate(token)
    except ValueError as exc:
        await message.answer(f"Токен невалиден: {exc}\nПолучите новый токен в Auth Service.")
        return

    redis = await get_redis()
    user_id = _get_user_id(message)
    await redis.set(_token_key(user_id), token)
    await message.answer("Токен принят и сохранён! Теперь вы можете задавать вопросы.")


@router.message(Command("whoami"))
async def cmd_whoami(message: Message) -> None:
    redis = await get_redis()
    user_id = _get_user_id(message)
    token = await redis.get(_token_key(user_id))

    if not token:
        await message.answer("Токен не найден. Авторизуйтесь через /token <jwt>")
        return

    assert isinstance(token, str)

    try:
        payload = decode_and_validate(token)
        await message.answer(
            f"👤 Ваш профиль:\n"
            f"  user_id (sub): {payload['sub']}\n"
            f"  role: {payload.get('role', 'n/a')}"
        )
    except ValueError as exc:
        await message.answer(f"Токен недействителен: {exc}")


@router.message()
async def handle_text(message: Message) -> None:
    """Handle any regular text message — validate JWT then dispatch to Celery."""
    user_id = _get_user_id(message)
    redis = await get_redis()
    token = await redis.get(_token_key(user_id))

    if not token:
        await message.answer(
            "Доступ запрещён — токен не найден.\n"
            "Авторизуйтесь через Auth Service и отправьте токен командой /token <jwt>"
        )
        return

    assert isinstance(token, str)
    assert message.chat is not None

    try:
        decode_and_validate(token)
    except ValueError as exc:
        await redis.delete(_token_key(user_id))
        await message.answer(
            f"Токен недействителен: {exc}\n"
            "Получите новый токен и авторизуйтесь снова через /token <jwt>"
        )
        return

    cast(Any, llm_request).delay(message.chat.id, (message.text or ""))
    await message.answer("Запрос принят! Обрабатываю, ответ придёт через несколько секунд…")
