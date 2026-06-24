import asyncio
import threading
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from app.core.config import settings


async def start_bot():
    from app.bot.dispatcher import create_bot, create_dispatcher
    bot = create_bot()
    dp = create_dispatcher()
    await dp.start_polling(bot)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    asyncio.create_task(start_bot())
    yield


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": settings.APP_NAME}
