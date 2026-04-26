import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.user import User


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient, superuser_token_headers):
    data = {
        "email": "testcreate@example.com",
        "password": "Password123!",
        "name": "Test Create",
        "username": "testcreate",
    }
    response = await client.post("/api/v1/users/", json=data, headers=superuser_token_headers)
    assert response.status_code == 201
    content = response.json()
    assert content["email"] == data["email"]
    assert "id" in content
    assert content["full_name"] == data["name"]


@pytest.mark.asyncio
async def test_create_user_as_normal_user_fails(client: AsyncClient, normal_user_token_headers):
    data = {
        "email": "testadminfail@example.com",
        "password": "Password123!",
        "name": "Test Admin Fail",
    }
    response = await client.post("/api/v1/users/", json=data, headers=normal_user_token_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "You do not have enough privileges."


@pytest.mark.asyncio
async def test_read_users_me(client: AsyncClient, normal_user_token_headers):
    response = await client.get("/api/v1/users/me", headers=normal_user_token_headers)
    assert response.status_code == 200
    assert "email" in response.json()


@pytest.mark.asyncio
async def test_read_user_by_id(client: AsyncClient, normal_user_token_headers, db):
    me_response = await client.get("/api/v1/users/me", headers=normal_user_token_headers)
    user_id = me_response.json()["id"]

    response = await client.get(f"/api/v1/users/{user_id}", headers=normal_user_token_headers)
    assert response.status_code == 200
    assert response.json()["id"] == user_id


@pytest.mark.asyncio
async def test_update_user_self(client: AsyncClient, normal_user_token_headers):
    update_data = {"name": "Updated Name"}
    response = await client.patch("/api/v1/users/me", json=update_data, headers=normal_user_token_headers)
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_normal_user_cannot_escalate_to_superuser_me(client: AsyncClient, normal_user_token_headers):
    # `is_superuser` is not a field on UserUpdate, so Pydantic drops it via extra="ignore".
    update_data = {"is_superuser": True, "name": "Hackerman"}
    response = await client.patch("/api/v1/users/me", json=update_data, headers=normal_user_token_headers)
    assert response.status_code == 200
    content = response.json()

    assert content["full_name"] == "Hackerman"
    assert content["is_superuser"] is False


@pytest.mark.asyncio
async def test_normal_user_cannot_use_admin_endpoint(client: AsyncClient, normal_user_token_headers):
    me = await client.get("/api/v1/users/me", headers=normal_user_token_headers)
    user_id = me.json()["id"]

    # PATCH /users/{id} is now superuser-only — non-superusers must go through /users/me.
    update_data = {"is_superuser": True, "is_active": False}
    response = await client.patch(f"/api/v1/users/{user_id}", json=update_data, headers=normal_user_token_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_superuser_can_use_admin_endpoint(client: AsyncClient, superuser_token_headers, db):
    from tests.helpers.generators import create_user

    target = await create_user(db, email="target@example.com")
    update_data = {"is_superuser": True, "name": "Promoted"}
    response = await client.patch(f"/api/v1/users/{target.id}", json=update_data, headers=superuser_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert content["is_superuser"] is True
    assert content["full_name"] == "Promoted"


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient, db):
    # Need a fresh user for deletion test
    from app.core.security import create_access_token
    from tests.helpers.generators import create_user

    user = await create_user(db, email="todelete@example.com")
    token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.delete(f"/api/v1/users/{user.id}", headers=headers)
    assert response.status_code == 200

    # Verify deleted
    stmt = select(User).where(User.id == user.id)
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()
    assert db_user.is_deleted is True
