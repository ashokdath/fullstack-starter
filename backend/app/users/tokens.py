"""Single-use password reset tokens.

Wraps Django's `PasswordResetTokenGenerator`: a token is invalidated as soon as
the password changes (or the user logs in), and expires after
`PASSWORD_RESET_TIMEOUT`. The frontend treats the token as an opaque string
(`/reset-password?token=...`), so the user id and the token travel together as
`<uidb64>.<token>`.
"""

import uuid

from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from app.users.models import User


def generate_password_reset_token(user: User) -> str:
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    return f"{uidb64}.{default_token_generator.make_token(user)}"


def verify_password_reset_token(token: str) -> User | None:
    uidb64, _, user_token = token.partition(".")
    if not uidb64 or not user_token:
        return None
    try:
        user_id = uuid.UUID(force_str(urlsafe_base64_decode(uidb64)))
    except ValueError, TypeError, OverflowError:
        return None
    user = User.objects.filter(pk=user_id).first()
    if user is None or not default_token_generator.check_token(user, user_token):
        return None
    return user
