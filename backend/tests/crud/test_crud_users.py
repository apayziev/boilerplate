import pytest

from app.crud.users import crud_users
from app.schemas.users import UserCreate, UserUpdate
from tests.helpers.generators import create_user


@pytest.mark.asyncio
async def test_create_user(db):
    user_in = UserCreate(name="New User", username="newuser", phone="+998900000010", password="Password123!")
    user = await crud_users.create(db, user_in)
    assert user.phone == user_in.phone
    assert user.id is not None
    assert user.hashed_password != user_in.password


@pytest.mark.asyncio
async def test_authenticate_user(db):
    phone = "+998900000020"
    password = "Password123!"
    user_in = UserCreate(name="Auth User", username="authuser", phone=phone, password=password)
    await crud_users.create(db, user_in)

    authenticated_user = await crud_users.authenticate(db, username_or_phone=phone, password=password)
    assert authenticated_user is not None
    assert authenticated_user.phone == phone

    wrong_password = await crud_users.authenticate(db, username_or_phone=phone, password="wrongpassword")
    assert wrong_password is None


@pytest.mark.asyncio
async def test_not_authenticate_user(db):
    user = await crud_users.authenticate(db, username_or_phone="+998900099999", password="password")
    assert user is None


@pytest.mark.asyncio
async def test_update_user(db):
    user = await create_user(db)
    new_name = "Updated Name"
    user_update = UserUpdate(name=new_name)
    updated_user = await crud_users.update(db, db_user=user, user_update=user_update)
    assert updated_user.name == new_name
    assert updated_user.phone == user.phone
