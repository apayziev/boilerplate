import pytest
from httpx import AsyncClient

from app.core.security import verify_password
from app.crud.users import crud_users
from app.schemas.users import UserCreate


@pytest.mark.asyncio
async def test_update_password_me(client: AsyncClient, normal_user_token_headers: dict[str, str], db):
    # Placeholder — the detailed tests below cover the real flows.
    pass


@pytest.mark.asyncio
async def test_user_change_password_success(client: AsyncClient, db):
    phone = "+998900000100"
    password = "OldPassword123!"
    user_in = UserCreate(phone=phone, password=password, name="Test User", username="changepass")
    user = await crud_users.create(db, user_in)

    r_login = await client.post("/api/v1/login/access-token", data={"username": phone, "password": password})
    token = r_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    new_password = "NewPassword123!"
    r_update = await client.patch(
        "/api/v1/users/me/password",
        headers=headers,
        json={"current_password": password, "new_password": new_password},
    )
    assert r_update.status_code == 200

    await db.refresh(user)
    assert await verify_password(new_password, user.hashed_password)

    r_fail = await client.post("/api/v1/login/access-token", data={"username": phone, "password": password})
    assert r_fail.status_code == 401

    r_success = await client.post(
        "/api/v1/login/access-token", data={"username": phone, "password": new_password}
    )
    assert r_success.status_code == 200


@pytest.mark.asyncio
async def test_user_change_password_wrong_current(client: AsyncClient, db):
    phone = "+998900000101"
    password = "Password123!"
    user_in = UserCreate(phone=phone, password=password, name="Test User", username="wrongcurrent")
    await crud_users.create(db, user_in)

    r_login = await client.post("/api/v1/login/access-token", data={"username": phone, "password": password})
    token = r_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r_update = await client.patch(
        "/api/v1/users/me/password",
        headers=headers,
        json={"current_password": "WrongPassword!", "new_password": "NewPassword123!"},
    )
    assert r_update.status_code == 403
    assert r_update.json()["detail"] == "Incorrect password"


@pytest.mark.asyncio
async def test_user_change_password_same_password(client: AsyncClient, db):
    phone = "+998900000102"
    password = "Password123!"
    user_in = UserCreate(phone=phone, password=password, name="Test User", username="samepass")
    await crud_users.create(db, user_in)

    r_login = await client.post("/api/v1/login/access-token", data={"username": phone, "password": password})
    token = r_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r_update = await client.patch(
        "/api/v1/users/me/password",
        headers=headers,
        json={"current_password": password, "new_password": password},
    )
    assert r_update.status_code == 409
    assert r_update.json()["detail"] == "New password cannot be the same as the current password"


@pytest.mark.asyncio
async def test_delete_user_me(client: AsyncClient, db):
    phone = "+998900000103"
    password = "Password123!"
    user_in = UserCreate(phone=phone, password=password, name="Tmp User", username="deleteme")
    user = await crud_users.create(db, user_in)
    user_id = user.id

    r_login = await client.post("/api/v1/login/access-token", data={"username": phone, "password": password})
    token = r_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r_delete = await client.delete("/api/v1/users/me", headers=headers)
    assert r_delete.status_code == 200
    assert r_delete.json()["message"] == "User deleted successfully"

    user_in_db = await crud_users.get(db, id=user_id, is_deleted=True)
    assert user_in_db is not None
    assert user_in_db.is_deleted is True
    assert user_in_db.deleted_at is not None
