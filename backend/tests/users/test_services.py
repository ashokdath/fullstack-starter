import io

from django.contrib.auth.hashers import make_password
from django.core.management import call_command

from app.core.config import settings
from app.users import services
from app.users.models import User
from app.users.schemas import UserCreate, UserUpdate
from tests.utils.utils import random_email, random_lower_string


def test_create_user() -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = services.create_user(user_create=user_in)
    assert user.email == email
    assert user.check_password(password)
    assert user.password != password


def test_authenticate_user() -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = services.create_user(user_create=user_in)
    authenticated_user = services.authenticate(email=email, password=password)
    assert authenticated_user
    assert user.email == authenticated_user.email


def test_not_authenticate_user() -> None:
    user = services.authenticate(email=random_email(), password=random_lower_string())
    assert user is None


def test_not_authenticate_user_wrong_password() -> None:
    email = random_email()
    services.create_user(user_create=UserCreate(email=email, password="password1"))
    assert services.authenticate(email=email, password="password2") is None


def test_check_if_user_is_active() -> None:
    user_in = UserCreate(email=random_email(), password=random_lower_string())
    user = services.create_user(user_create=user_in)
    assert user.is_active is True


def test_check_if_user_is_active_inactive() -> None:
    user_in = UserCreate(
        email=random_email(), password=random_lower_string(), is_active=False
    )
    user = services.create_user(user_create=user_in)
    assert user.is_active is False


def test_check_if_user_is_superuser() -> None:
    user_in = UserCreate(
        email=random_email(), password=random_lower_string(), is_superuser=True
    )
    user = services.create_user(user_create=user_in)
    assert user.is_superuser is True
    # Django admin access follows is_superuser
    assert user.is_staff is True


def test_check_if_user_is_superuser_normal_user() -> None:
    user_in = UserCreate(email=random_email(), password=random_lower_string())
    user = services.create_user(user_create=user_in)
    assert user.is_superuser is False
    assert user.is_staff is False


def test_get_user() -> None:
    user_in = UserCreate(
        email=random_email(), password=random_lower_string(), is_superuser=True
    )
    user = services.create_user(user_create=user_in)
    user_2 = User.objects.get(pk=user.id)
    assert user.email == user_2.email
    assert str(user_2) == user.email


def test_update_user() -> None:
    user_in = UserCreate(
        email=random_email(), password=random_lower_string(), is_superuser=True
    )
    user = services.create_user(user_create=user_in)
    new_password = random_lower_string()
    user_in_update = UserUpdate(password=new_password, is_superuser=True)
    services.update_user(db_user=user, user_in=user_in_update)
    user_2 = User.objects.get(pk=user.id)
    assert user.email == user_2.email
    assert user_2.check_password(new_password)


def test_authenticate_user_with_pbkdf2_upgrades_to_argon2() -> None:
    """A user with a legacy hash gets upgraded to argon2 on login."""
    email = random_email()
    password = random_lower_string()
    User(email=email, password=make_password(password, hasher="pbkdf2_sha256")).save()

    authenticated_user = services.authenticate(email=email, password=password)
    assert authenticated_user
    authenticated_user.refresh_from_db()
    assert authenticated_user.password.startswith("argon2$")


def test_create_user_requires_email() -> None:
    try:
        User.objects.create_user(email="", password="x")
    except ValueError as e:
        assert "email" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_create_initial_data_is_idempotent() -> None:
    call_command("create_initial_data", stdout=io.StringIO())
    call_command("create_initial_data", stdout=io.StringIO())
    assert User.objects.filter(email=settings.FIRST_SUPERUSER).count() == 1
    assert User.objects.get(email=settings.FIRST_SUPERUSER).is_superuser
