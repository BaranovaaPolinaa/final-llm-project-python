import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.db import models  # noqa: F401
from app.db.base import Base
from app.main import app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def async_client():
    test_engine = create_async_engine(TEST_DB_URL, echo=False)
    TestSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()
    await test_engine.dispose()


@pytest.mark.asyncio
async def test_register_creates_user(async_client: AsyncClient):
    response = await async_client.post(
        "/auth/register",
        json={"email": "example@email.com", "password": "password123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "example@email.com"
    assert data["role"] == "user"
    assert "id" in data
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_full_login_and_me_flow(async_client: AsyncClient):
    await async_client.post(
        "/auth/register",
        json={"email": "example@email.com", "password": "password123"},
    )

    login_response = await async_client.post(
        "/auth/login",
        data={"username": "example@email.com", "password": "password123"},
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    token = token_data["access_token"]

    me_response = await async_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "example@email.com"


@pytest.mark.asyncio
async def test_duplicate_registration_returns_409(async_client: AsyncClient):
    await async_client.post(
        "/auth/register",
        json={"email": "example@email.com", "password": "password123"},
    )
    response = await async_client.post(
        "/auth/register",
        json={"email": "example@email.com", "password": "password123"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_wrong_password_returns_401(async_client: AsyncClient):
    await async_client.post(
        "/auth/register",
        json={"email": "example@email.com", "password": "password123"},
    )
    response = await async_client.post(
        "/auth/login",
        data={"username": "example@email.com", "password": "wrong_password"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_without_token_returns_401(async_client: AsyncClient):
    response = await async_client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_invalid_token_returns_401(async_client: AsyncClient):
    response = await async_client.get(
        "/auth/me",
        headers={"Authorization": "Bearer this.is.not.a.valid.token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
