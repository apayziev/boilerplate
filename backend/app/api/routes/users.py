import re

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.api.deps import CurrentUser, SessionDep, SuperUserDep
from app.core.exceptions import DuplicateValueException, ForbiddenException, NotFoundException
from app.core.security import get_password_hash, verify_password
from app.crud import crud_users
from app.models.user import User
from app.schemas.users import UpdatePassword, UserAdminUpdate, UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


class PaginatedResponse(BaseModel):
    data: list[UserRead]
    count: int


async def _ensure_unique(db: SessionDep, *, email: str | None, username: str | None, current: User) -> None:
    """Reject the update when another user already owns the requested email or username."""
    if email is not None and email != current.email and await crud_users.exists(db=db, email=email):
        raise DuplicateValueException("Email is already registered")
    if username is not None and username != current.username and await crud_users.exists(db=db, username=username):
        raise DuplicateValueException("Username not available")


@router.post("/", response_model=UserRead, status_code=201, operation_id="create_user")
async def write_user(
    user: UserCreate,
    current_user: SuperUserDep,
    db: SessionDep,
) -> UserRead:
    """Create a new user (superuser only). If `username` is omitted, derive one from the email local-part."""
    if await crud_users.exists(db=db, email=user.email):
        raise DuplicateValueException("Email is already registered")

    if user.username:
        if await crud_users.exists(db=db, username=user.username):
            raise DuplicateValueException("Username not available")
    else:
        base_username = re.sub(r"[^a-z0-9]", "", user.email.split("@")[0].lower())
        username = base_username
        counter = 1
        while await crud_users.exists(db=db, username=username):
            username = f"{base_username}{counter}"
            counter += 1
        user.username = username

    created_user = await crud_users.create(db=db, user_create=user)
    return UserRead.model_validate(created_user)


@router.get("/", response_model=PaginatedResponse, operation_id="read_users")
async def read_users(
    db: SessionDep,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
) -> PaginatedResponse:
    """List users with pagination."""
    rows, total = await crud_users.get_multi(db=db, offset=skip, limit=limit)
    return PaginatedResponse(
        data=[UserRead.model_validate(user) for user in rows],
        count=total,
    )


@router.get("/me", response_model=UserRead, operation_id="read_user_me")
async def read_users_me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)


@router.patch("/me", response_model=UserRead, operation_id="update_user_me")
async def update_user_me(
    values: UserUpdate,
    current_user: CurrentUser,
    db: SessionDep,
) -> UserRead:
    """Update the caller's own profile. Privilege flags are not in the schema, so escalation is impossible here."""
    await _ensure_unique(db, email=values.email, username=values.username, current=current_user)
    update_data = values.model_dump(exclude_unset=True)
    updated_user = await crud_users.update(db=db, db_user=current_user, user_update=update_data)
    return UserRead.model_validate(updated_user)


@router.patch("/me/password", response_model=dict[str, str], operation_id="update_password_me")
async def update_password_me(
    body: UpdatePassword,
    current_user: CurrentUser,
    db: SessionDep,
) -> dict[str, str]:
    if not await verify_password(body.current_password, current_user.hashed_password):
        raise ForbiddenException("Incorrect password")
    if body.current_password == body.new_password:
        raise DuplicateValueException("New password cannot be the same as the current password")

    await crud_users.update(
        db=db, db_user=current_user, user_update={"hashed_password": get_password_hash(body.new_password)}
    )
    return {"message": "Password updated successfully"}


@router.delete("/me", response_model=dict[str, str], operation_id="delete_user_me")
async def delete_user_me(current_user: CurrentUser, db: SessionDep) -> dict[str, str]:
    if current_user.is_superuser:
        raise ForbiddenException(
            "Superusers cannot delete themselves. Please ask another admin to delete your account."
        )
    await crud_users.delete(db=db, id=current_user.id)
    return {"message": "User deleted successfully"}


@router.get("/{user_id}", response_model=UserRead, operation_id="read_user_by_id")
async def read_user_by_id(user_id: int, db: SessionDep) -> UserRead:
    db_user = await crud_users.get(db=db, id=user_id)
    if db_user is None:
        raise NotFoundException("User not found")
    return UserRead.model_validate(db_user)


@router.patch("/{user_id}", response_model=UserRead, operation_id="update_user")
async def patch_user(
    values: UserAdminUpdate,
    user_id: int,
    current_user: SuperUserDep,
    db: SessionDep,
) -> UserRead:
    """Update any user (superuser only). Self-updates should go through `PATCH /users/me`."""
    db_user = await crud_users.get(db=db, id=user_id)
    if db_user is None:
        raise NotFoundException("User not found")

    await _ensure_unique(db, email=values.email, username=values.username, current=db_user)
    updated_user = await crud_users.update(db=db, db_user=db_user, user_update=values.model_dump(exclude_unset=True))
    return UserRead.model_validate(updated_user)


@router.delete("/{user_id}", operation_id="delete_user")
async def erase_user(
    user_id: int,
    current_user: CurrentUser,
    db: SessionDep,
) -> dict[str, str]:
    """Soft-delete a user. Allowed for the user themselves or any superuser."""
    db_user = await crud_users.get(db=db, id=user_id)
    if not db_user:
        raise NotFoundException("User not found")
    if not current_user.is_superuser and user_id != current_user.id:
        raise ForbiddenException()

    await crud_users.delete(db=db, id=user_id)
    return {"message": "User deleted"}


@router.delete("/db_user/{username}", operation_id="delete_db_user")
async def erase_db_user(
    username: str,
    current_user: SuperUserDep,
    db: SessionDep,
) -> dict[str, str]:
    """Hard-delete a user (superuser only)."""
    if not await crud_users.exists(db=db, username=username):
        raise NotFoundException("User not found")
    await crud_users.db_delete(db=db, username=username)
    return {"message": "User deleted from the database"}
