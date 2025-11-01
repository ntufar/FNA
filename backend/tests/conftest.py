import asyncio
import uuid
from typing import AsyncGenerator, Dict

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport

from src.main import app
from src.database.connection import init_database, get_engine, get_db_session
from sqlalchemy import text


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def _init_db():
    # Ensure the application initializes the database engine
    init_database()
    # Optionally verify connectivity
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))


@pytest_asyncio.fixture()
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture()
def db_session():
    session = get_db_session()
    try:
        yield session
        session.commit()
    finally:
        session.close()


async def _register_and_login(client: httpx.AsyncClient, *, email: str, password: str, full_name: str, subscription_tier: str = "Pro") -> Dict[str, str]:
    register_payload = {
        "email": email,
        "password": password,
        "full_name": full_name,
        "subscription_tier": subscription_tier,
    }
    r = await client.post("/v1/auth/register", json=register_payload)
    if r.status_code not in (200, 201, 400):
        r.raise_for_status()

    login_payload = {"email": email, "password": password}
    r = await client.post("/v1/auth/login", json=login_payload)
    r.raise_for_status()
    data = r.json()
    return {
        "access_token": data["access_token"],
        "refresh_token": data.get("refresh_token", ""),
        "token_type": data.get("token_type", "Bearer"),
    }


@pytest_asyncio.fixture()
async def auth_headers(client: httpx.AsyncClient) -> Dict[str, str]:
    tokens = await _register_and_login(
        client,
        email="us1_tester@example.com",
        password="StrongP@ssw0rd!",
        full_name="US1 Tester",
        subscription_tier="Pro",
    )
    return {"Authorization": f"Bearer {tokens['access_token']}"}


