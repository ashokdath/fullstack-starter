from datetime import timedelta

from django.http import HttpRequest, HttpResponse
from ninja import Form, Router
from ninja.errors import HttpError

from app.core.config import settings
from app.core.email import generate_reset_password_email, send_email
from app.core.security import (
    create_access_token,
    current_user,
    jwt_auth,
    require_superuser,
)
from app.schemas import Message, NewPassword, Token
from app.users import services
from app.users.models import User
from app.users.schemas import OAuth2PasswordRequestForm, UserPublic
from app.users.tokens import (
    generate_password_reset_token,
    verify_password_reset_token,
)

router = Router(tags=["login"])


@router.post("/login/access-token", response=Token)
def login_access_token(
    request: HttpRequest, form_data: Form[OAuth2PasswordRequestForm]
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = services.authenticate(email=form_data.username, password=form_data.password)
    if not user:
        raise HttpError(400, "Incorrect email or password")
    elif not user.is_active:
        raise HttpError(400, "Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=create_access_token(user.id, expires_delta=access_token_expires)
    )


@router.post("/login/test-token", response=UserPublic, auth=jwt_auth)
def test_token(request: HttpRequest) -> User:
    """
    Test access token
    """
    return current_user(request)


@router.post("/password-recovery/{email}", response=Message)
def recover_password(request: HttpRequest, email: str) -> Message:
    """
    Password Recovery
    """
    user = services.get_user_by_email(email=email)

    # Always return the same response to prevent email enumeration attacks
    # Only send email if user actually exists
    if user:
        password_reset_token = generate_password_reset_token(user)
        email_data = generate_reset_password_email(
            email_to=user.email, email=email, token=password_reset_token
        )
        send_email(
            email_to=user.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return Message(
        message="If that email is registered, we sent a password recovery link"
    )


@router.post("/reset-password/", response=Message)
def reset_password(request: HttpRequest, body: NewPassword) -> Message:
    """
    Reset password
    """
    # Unknown user and bad/expired/used token share one error: no enumeration
    user = verify_password_reset_token(body.token)
    if not user:
        raise HttpError(400, "Invalid token")
    elif not user.is_active:
        raise HttpError(400, "Inactive user")
    user.set_password(body.new_password)
    user.save()
    return Message(message="Password updated successfully")


@router.post(
    "/password-recovery-html-content/{email}",
    response={200: str},
    auth=jwt_auth,
    openapi_extra={
        "responses": {
            200: {
                "description": "Successful Response",
                "content": {"text/html": {"schema": {"type": "string"}}},
            }
        }
    },
)
def recover_password_html_content(request: HttpRequest, email: str) -> HttpResponse:
    """
    HTML Content for Password Recovery
    """
    require_superuser(request)
    user = services.get_user_by_email(email=email)

    if not user:
        raise HttpError(
            404, "The user with this username does not exist in the system."
        )
    password_reset_token = generate_password_reset_token(user)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )

    return HttpResponse(
        email_data.html_content, headers={"subject:": email_data.subject}
    )
