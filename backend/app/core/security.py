from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from django.http import HttpRequest
from jwt.exceptions import InvalidTokenError
from ninja.errors import HttpError
from ninja.security import HttpBearer
from pydantic import ValidationError

from app.core.config import settings
from app.schemas import TokenPayload
from app.users.models import User

ALGORITHM = "HS256"


def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    expire = datetime.now(UTC) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


class JWTBearer(HttpBearer):
    """Bearer token auth. Published in OpenAPI as `OAuth2PasswordBearer`."""

    def authenticate(self, request: HttpRequest, token: str) -> User | None:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            token_data = TokenPayload(**payload)
        except InvalidTokenError, ValidationError:
            return None
        user = (
            User.objects.filter(pk=token_data.sub).first() if token_data.sub else None
        )
        if not user:
            raise HttpError(404, "User not found")
        if not user.is_active:
            raise HttpError(400, "Inactive user")
        return user


jwt_auth = JWTBearer()


def current_user(request: HttpRequest) -> User:
    """The authenticated user of a view protected by `jwt_auth`."""
    user = request.auth  # type: ignore[attr-defined]
    assert isinstance(user, User)
    return user


def require_superuser(request: HttpRequest) -> User:
    user = current_user(request)
    if not user.is_superuser:
        raise HttpError(403, "The user doesn't have enough privileges")
    return user
