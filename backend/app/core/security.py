from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

import bcrypt
import jwt
from fastapi import Response
from fastapi.security import OAuth2PasswordBearer
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.schemas import TokenData

from .config import EnvironmentOption, settings

SECRET_KEY: SecretStr = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login/access-token")


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return await run_in_threadpool(bcrypt.checkpw, plain_password.encode(), hashed_password.encode())


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)).decode()


def _create_token(data: dict[str, Any], token_type: TokenType, expires_delta: timedelta) -> str:
    expire = datetime.now(UTC).replace(tzinfo=None) + expires_delta
    payload = {**data, "exp": expire, "token_type": token_type.value}
    return jwt.encode(payload, SECRET_KEY.get_secret_value(), algorithm=ALGORITHM)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    return _create_token(data, TokenType.ACCESS, expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    return _create_token(data, TokenType.REFRESH, expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))


async def verify_token(token: str, expected_token_type: TokenType, db: AsyncSession) -> TokenData | None:
    """Decode JWT and return TokenData if it matches expected type, else None."""
    try:
        payload = jwt.decode(token, SECRET_KEY.get_secret_value(), algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None

    username_or_email = payload.get("sub")
    if username_or_email is None or payload.get("token_type") != expected_token_type.value:
        return None

    return TokenData(username_or_email=username_or_email, token_version=payload.get("token_version", 0))


def _is_secure_environment() -> bool:
    return settings.ENVIRONMENT != EnvironmentOption.LOCAL


def set_auth_cookie(response: Response, key: str, value: str, max_age: int) -> None:
    """Set an httpOnly auth cookie.

    - ``secure`` is auto-disabled in local env so cookies work over plain HTTP.
    - ``samesite="strict"`` blocks the cookie from being sent on cross-site requests, which neutralises the
      classic CSRF vector for state-changing endpoints.
    """
    response.set_cookie(
        key=key,
        value=value,
        httponly=True,
        secure=_is_secure_environment(),
        samesite="strict",
        max_age=max_age,
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key=ACCESS_COOKIE_NAME)
    response.delete_cookie(key=REFRESH_COOKIE_NAME)
