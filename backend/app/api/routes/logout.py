from typing import Annotated

from fastapi import APIRouter, Cookie, Response

from app.api.deps import CurrentUser, SessionDep
from app.core.exceptions import UnauthorizedException
from app.core.security import REFRESH_COOKIE_NAME, clear_auth_cookies
from app.crud import crud_users

router = APIRouter(tags=["login"])


@router.post("/logout", operation_id="logout")
async def logout(
    response: Response,
    db: SessionDep,
    current_user: CurrentUser,
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE_NAME)] = None,
) -> dict[str, str]:
    """Log the user out by bumping `token_version`, which invalidates every outstanding access/refresh token."""
    if not refresh_token:
        raise UnauthorizedException("Refresh token not found")

    await crud_users.increment_token_version(db=db, user=current_user)
    clear_auth_cookies(response)
    return {"message": "Logged out successfully"}
