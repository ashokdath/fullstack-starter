"""Schemas shared across apps. Names are part of the API contract: they become
the type names in the generated frontend client (`frontend/src/client`)."""

from ninja import Schema
from pydantic import Field


# Generic message
class Message(Schema):
    message: str


# JSON payload containing access token
class Token(Schema):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(Schema):
    sub: str | None = None


class NewPassword(Schema):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
