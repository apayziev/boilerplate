from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_get_db
from app.core.exceptions import UnauthorizedException
from app.core.security import (
    ACCESS_COOKIE_NAME,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_COOKIE_NAME,
    REFRESH_TOKEN_EXPIRE_DAYS,
    TokenType,
    create_access_token,
    create_refresh_token,
    set_auth_cookie,
    verify_token,
)
from app.crud import crud_users
from app.schemas.auth import Token

router = APIRouter(prefix="/login", tags=["login"])

ACCESS_MAX_AGE = ACCESS_TOKEN_EXPIRE_MINUTES * 60
REFRESH_MAX_AGE = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


def _issue_token_pair(response: Response, username: str, token_version: int) -> str:
    """Generate access+refresh tokens and set both as httpOnly cookies. Returns the access token."""
    payload = {"sub": username, "token_version": token_version}
    access_token = create_access_token(data=payload)
    refresh_token = create_refresh_token(data=payload)
    set_auth_cookie(response, ACCESS_COOKIE_NAME, access_token, ACCESS_MAX_AGE)
    set_auth_cookie(response, REFRESH_COOKIE_NAME, refresh_token, REFRESH_MAX_AGE)
    return access_token


@router.post("/access-token", response_model=Token, operation_id="login_access_token")
async def login_for_access_token(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict[str, str]:
    user = await crud_users.authenticate(db=db, username_or_email=form_data.username, password=form_data.password)
    if not user:
        raise UnauthorizedException("Wrong username, email or password.")
    if not user.is_active:
        raise UnauthorizedException("Inactive user")

    access_token = _issue_token_pair(response, user.username, user.token_version)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh", operation_id="refresh_access_token")
async def refresh_access_token(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict[str, str]:
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise UnauthorizedException("Refresh token missing.")

    token_data = await verify_token(refresh_token, TokenType.REFRESH, db)
    if not token_data:
        raise UnauthorizedException("Invalid refresh token.")

    user = await crud_users.get_by_login(db=db, identifier=token_data.username_or_email)
    if not user or user.token_version != token_data.token_version:
        raise UnauthorizedException("Token has been revoked.")

    # Rotate both tokens — limits the reuse window if a refresh token is compromised.
    access_token = _issue_token_pair(response, user.username, user.token_version)
    return {"access_token": access_token, "token_type": "bearer"}
