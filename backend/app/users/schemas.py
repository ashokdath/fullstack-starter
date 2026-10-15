import uuid
from datetime import datetime

from ninja import Schema
from pydantic import EmailStr, Field


# Shared properties
class UserBase(Schema):
    email: EmailStr = Field(max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(Schema):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(Schema):
    email: EmailStr | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    is_superuser: bool | None = None
    full_name: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(Schema):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(Schema):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(Schema):
    data: list[UserPublic]
    count: int


# Dev-only endpoint used by the Playwright tests to create users directly
class PrivateUserCreate(Schema):
    email: str
    password: str
    full_name: str
    is_verified: bool = False


# OAuth2 password flow form, same fields as FastAPI's OAuth2PasswordRequestForm.
# Published in OpenAPI as `Body_login-login_access_token` (see app.core.openapi).
class OAuth2PasswordRequestForm(Schema):
    grant_type: str | None = Field(default=None, pattern="^password$")
    username: str
    password: str = Field(json_schema_extra={"format": "password"})
    scope: str = ""
    client_id: str | None = None
    client_secret: str | None = Field(
        default=None, json_schema_extra={"format": "password"}
    )
