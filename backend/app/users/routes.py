import uuid

from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError

from app.core.config import settings
from app.core.email import generate_new_account_email, send_email
from app.core.security import current_user, jwt_auth, require_superuser
from app.schemas import Message
from app.users import services
from app.users.models import User
from app.users.schemas import (
    UpdatePassword,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)

router = Router(tags=["users"])


@router.get("/", response=UsersPublic, auth=jwt_auth)
def read_users(request: HttpRequest, skip: int = 0, limit: int = 100) -> UsersPublic:
    """
    Retrieve users.
    """
    require_superuser(request)
    users = User.objects.order_by("-created_at")
    return UsersPublic(
        data=[UserPublic.model_validate(u) for u in users[skip : skip + limit]],
        count=users.count(),
    )


@router.post("/", response=UserPublic, auth=jwt_auth)
def create_user(request: HttpRequest, user_in: UserCreate) -> User:
    """
    Create new user.
    """
    require_superuser(request)
    user = services.get_user_by_email(email=user_in.email)
    if user:
        raise HttpError(400, "The user with this email already exists in the system.")

    user = services.create_user(user_create=user_in)
    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user


@router.patch("/me", response=UserPublic, auth=jwt_auth)
def update_user_me(request: HttpRequest, user_in: UserUpdateMe) -> User:
    """
    Update own user.
    """
    user = current_user(request)
    if user_in.email:
        existing_user = services.get_user_by_email(email=user_in.email)
        if existing_user and existing_user.id != user.id:
            raise HttpError(409, "User with this email already exists")
    for field, value in user_in.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    user.save()
    return user


@router.patch("/me/password", response=Message, auth=jwt_auth)
def update_password_me(request: HttpRequest, body: UpdatePassword) -> Message:
    """
    Update own password.
    """
    user = current_user(request)
    if not user.check_password(body.current_password):
        raise HttpError(400, "Incorrect password")
    if body.current_password == body.new_password:
        raise HttpError(400, "New password cannot be the same as the current one")
    user.set_password(body.new_password)
    user.save()
    return Message(message="Password updated successfully")


@router.get("/me", response=UserPublic, auth=jwt_auth)
def read_user_me(request: HttpRequest) -> User:
    """
    Get current user.
    """
    return current_user(request)


@router.delete("/me", response=Message, auth=jwt_auth)
def delete_user_me(request: HttpRequest) -> Message:
    """
    Delete own user.
    """
    user = current_user(request)
    if user.is_superuser:
        raise HttpError(403, "Super users are not allowed to delete themselves")
    user.delete()
    return Message(message="User deleted successfully")


@router.post("/signup", response=UserPublic)
def register_user(request: HttpRequest, user_in: UserRegister) -> User:
    """
    Create new user without the need to be logged in.
    """
    user = services.get_user_by_email(email=user_in.email)
    if user:
        raise HttpError(400, "The user with this email already exists in the system")
    user_create = UserCreate.model_validate(user_in.model_dump())
    return services.create_user(user_create=user_create)


@router.get("/{uuid:user_id}", response=UserPublic, auth=jwt_auth)
def read_user_by_id(request: HttpRequest, user_id: uuid.UUID) -> User:
    """
    Get a specific user by id.
    """
    user = User.objects.filter(pk=user_id).first()
    me = current_user(request)
    if user == me:
        return me
    if not me.is_superuser:
        raise HttpError(403, "The user doesn't have enough privileges")
    if user is None:
        raise HttpError(404, "User not found")
    return user


@router.patch("/{uuid:user_id}", response=UserPublic, auth=jwt_auth)
def update_user(request: HttpRequest, user_id: uuid.UUID, user_in: UserUpdate) -> User:
    """
    Update a user.
    """
    require_superuser(request)
    db_user = User.objects.filter(pk=user_id).first()
    if not db_user:
        raise HttpError(404, "The user with this id does not exist in the system")
    if user_in.email:
        existing_user = services.get_user_by_email(email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HttpError(409, "User with this email already exists")

    return services.update_user(db_user=db_user, user_in=user_in)


@router.delete("/{uuid:user_id}", response=Message, auth=jwt_auth)
def delete_user(request: HttpRequest, user_id: uuid.UUID) -> Message:
    """
    Delete a user.
    """
    me = require_superuser(request)
    user = User.objects.filter(pk=user_id).first()
    if not user:
        raise HttpError(404, "User not found")
    if user == me:
        raise HttpError(403, "Super users are not allowed to delete themselves")
    # Items are removed by the ON DELETE CASCADE of `Item.owner`
    user.delete()
    return Message(message="User deleted successfully")
