from typing import Annotated

from pydantic import (
    AliasChoices,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


def validate_password_strength(v: str) -> str:
    """Reject weak passwords. Required: 8+ chars, lowercase, uppercase, digit, special."""
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not any(c.islower() for c in v):
        raise ValueError("Password must contain at least one lowercase letter")
    if not any(c.isupper() for c in v):
        raise ValueError("Password must contain at least one uppercase letter")
    if not any(c.isdigit() for c in v):
        raise ValueError("Password must contain at least one digit")
    if not any(not c.isalnum() for c in v):
        raise ValueError("Password must contain at least one special character")
    return v


_NAME_FIELD = Field(
    min_length=2,
    max_length=30,
    examples=["User Userson"],
    validation_alias=AliasChoices("name", "full_name"),
    serialization_alias="full_name",
    default=None,
)
_USERNAME_FIELD = Field(min_length=2, max_length=20, pattern=r"^[a-z0-9]+$", examples=["userson"], default=None)
_EMAIL_FIELD = Field(examples=["user.userson@example.com"])
_PROFILE_IMAGE_FIELD = Field(
    pattern=r"^(https?|ftp)://[^\s/$.?#].[^\s]*$",
    examples=["https://www.profileimageurl.com"],
    default=None,
)


class UserBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Annotated[str | None, _NAME_FIELD]
    username: Annotated[str | None, _USERNAME_FIELD]
    email: Annotated[EmailStr, _EMAIL_FIELD]


class UserRead(BaseModel):
    """Public-facing user representation. Used for every read response."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: Annotated[str, BeforeValidator(lambda v: str(v)), Field(examples=["1"])]
    full_name: Annotated[str, Field(min_length=2, max_length=30, examples=["User Userson"], validation_alias="name")]
    username: Annotated[str, Field(min_length=2, max_length=20, pattern=r"^[a-z0-9]+$", examples=["userson"])]
    email: Annotated[EmailStr, _EMAIL_FIELD]
    profile_image_url: str
    is_active: bool
    is_superuser: bool


class UserCreate(UserBase):
    """Body for `POST /users` — superuser-only endpoint, so privilege flags live here."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    password: Annotated[str, Field(examples=["Str1ngst!"])]
    is_superuser: bool = False
    is_active: bool = True

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return validate_password_strength(v)


class UserUpdate(BaseModel):
    """Body for `PATCH /users/me` — self-update only. Privilege flags and password are intentionally absent.

    Privilege flags can only be changed via `UserAdminUpdate` on the admin endpoint.
    Password changes go through `PATCH /users/me/password` so the current password is verified.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: Annotated[str | None, _NAME_FIELD]
    username: Annotated[str | None, _USERNAME_FIELD]
    email: Annotated[EmailStr | None, Field(examples=["user.userberg@example.com"], default=None)]
    profile_image_url: Annotated[str | None, _PROFILE_IMAGE_FIELD]


class UserAdminUpdate(UserUpdate):
    """Body for `PATCH /users/{user_id}` — superuser-only endpoint."""

    password: str | None = Field(default=None)
    is_active: bool | None = None
    is_superuser: bool | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str | None) -> str | None:
        return validate_password_strength(v) if v is not None else v


class UpdatePassword(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def new_password_strength(cls, v: str) -> str:
        return validate_password_strength(v)
