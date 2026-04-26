import pytest
from httpx import AsyncClient

from tests.helpers.generators import create_user


@pytest.mark.asyncio
async def test_get_access_token(client: AsyncClient, db):
    password = "password123"
    phone = "+998900000300"
    await create_user(db, password=password, phone=phone)

    login_data = {"username": phone, "password": password}
    response = await client.post("/api/v1/login/access-token", data=login_data)
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"
    assert "refresh_token" not in tokens  # Refresh lives in an httpOnly cookie.
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_incorrect_login(client: AsyncClient):
    login_data = {"username": "+998900099999", "password": "wrongpassword"}
    response = await client.post("/api/v1/login/access-token", data=login_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Wrong username, phone, or password."


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, db):
    password = "password123"
    phone = "+998900000301"
    await create_user(db, password=password, phone=phone)

    login_data = {"username": phone, "password": password}
    response = await client.post("/api/v1/login/access-token", data=login_data)
    refresh_token = response.cookies["refresh_token"]

    client.cookies.set("refresh_token", refresh_token)
    response_refresh = await client.post("/api/v1/login/refresh")
    assert response_refresh.status_code == 200
    assert "access_token" in response_refresh.json()
