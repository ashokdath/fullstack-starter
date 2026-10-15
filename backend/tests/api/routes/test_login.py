from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.hashers import make_password
from django.core.mail import EmailMessage

from app.core.config import settings
from app.core.security import create_access_token
from app.users import services
from app.users.models import User
from app.users.schemas import UserCreate
from app.users.tokens import generate_password_reset_token
from tests.utils.user import create_random_user
from tests.utils.utils import APIClient, random_email, random_lower_string


def test_get_access_token(client: APIClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    assert r.status_code == 200
    assert "access_token" in tokens
    assert tokens["access_token"]


def test_get_access_token_incorrect_password(client: APIClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": "incorrect",
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 400


def test_use_access_token(
    client: APIClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/login/test-token",
        headers=superuser_token_headers,
    )
    result = r.json()
    assert r.status_code == 200
    assert "email" in result


def test_recovery_password(
    client: APIClient, normal_user_token_headers: dict[str, str]
) -> None:
    with (
        patch("app.core.config.settings.SMTP_HOST", "smtp.example.com"),
        patch("app.core.config.settings.SMTP_USER", "admin@example.com"),
    ):
        email = "test@example.com"
        r = client.post(
            f"{settings.API_V1_STR}/password-recovery/{email}",
            headers=normal_user_token_headers,
        )
        assert r.status_code == 200
        assert r.json() == {
            "message": "If that email is registered, we sent a password recovery link"
        }


def test_recovery_password_user_not_exits(
    client: APIClient, normal_user_token_headers: dict[str, str]
) -> None:
    email = "jVgQr@example.com"
    r = client.post(
        f"{settings.API_V1_STR}/password-recovery/{email}",
        headers=normal_user_token_headers,
    )
    # Should return 200 with generic message to prevent email enumeration attacks
    assert r.status_code == 200
    assert r.json() == {
        "message": "If that email is registered, we sent a password recovery link"
    }


def test_reset_password(client: APIClient) -> None:
    email = random_email()
    password = random_lower_string()
    new_password = random_lower_string()

    user_create = UserCreate(
        email=email,
        full_name="Test User",
        password=password,
        is_active=True,
        is_superuser=False,
    )
    user = services.create_user(user_create=user_create)
    token = generate_password_reset_token(user)
    data = {"new_password": new_password, "token": token}

    r = client.post(f"{settings.API_V1_STR}/reset-password/", json_body=data)

    assert r.status_code == 200
    assert r.json() == {"message": "Password updated successfully"}

    user.refresh_from_db()
    assert user.check_password(new_password)


def test_reset_password_token_is_single_use(client: APIClient) -> None:
    user = create_random_user()
    token = generate_password_reset_token(user)
    url = f"{settings.API_V1_STR}/reset-password/"

    r = client.post(
        url, json_body={"new_password": random_lower_string(), "token": token}
    )
    assert r.status_code == 200

    r = client.post(
        url, json_body={"new_password": random_lower_string(), "token": token}
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "Invalid token"


def test_reset_password_inactive_user(client: APIClient) -> None:
    user = create_random_user()
    token = generate_password_reset_token(user)
    user.is_active = False
    user.save()

    r = client.post(
        f"{settings.API_V1_STR}/reset-password/",
        json_body={"new_password": random_lower_string(), "token": token},
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "Inactive user"


@pytest.mark.parametrize(
    "token", ["invalid", "invalid.token", "bm90LWEtdXVpZA.token", ".token", "uid."]
)
def test_reset_password_invalid_token(
    client: APIClient, superuser_token_headers: dict[str, str], token: str
) -> None:
    data = {"new_password": "changethis", "token": token}
    r = client.post(
        f"{settings.API_V1_STR}/reset-password/",
        headers=superuser_token_headers,
        json_body=data,
    )
    response = r.json()

    assert "detail" in response
    assert r.status_code == 400
    assert response["detail"] == "Invalid token"


def test_recovery_password_sends_email(
    client: APIClient, mailoutbox: list[EmailMessage]
) -> None:
    user = create_random_user()
    with patch("app.core.config.settings.SMTP_HOST", "smtp.example.com"):
        r = client.post(f"{settings.API_V1_STR}/password-recovery/{user.email}")
    assert r.status_code == 200
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == [user.email]
    assert "/reset-password?token=" in str(mailoutbox[0].alternatives[0].content)


def test_get_access_token_inactive_user(client: APIClient) -> None:
    email = random_email()
    password = random_lower_string()
    services.create_user(
        user_create=UserCreate(email=email, password=password, is_active=False)
    )
    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": email, "password": password},
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "Inactive user"


def test_use_access_token_invalid(client: APIClient) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/login/test-token",
        headers={"Authorization": "Bearer invalid"},
    )
    assert r.status_code == 401
    assert r.json() == {"detail": "Not authenticated"}


def test_use_access_token_missing(client: APIClient) -> None:
    r = client.post(f"{settings.API_V1_STR}/login/test-token")
    assert r.status_code == 401


def test_use_access_token_deleted_user(client: APIClient) -> None:
    user = create_random_user()
    token = create_access_token(user.id, expires_delta=timedelta(minutes=5))
    user.delete()
    r = client.post(
        f"{settings.API_V1_STR}/login/test-token",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "User not found"


def test_use_access_token_inactive_user(client: APIClient) -> None:
    user = create_random_user()
    token = create_access_token(user.id, expires_delta=timedelta(minutes=5))
    user.is_active = False
    user.save()
    r = client.post(
        f"{settings.API_V1_STR}/login/test-token",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "Inactive user"


def test_recover_password_html_content(
    client: APIClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/password-recovery-html-content/{settings.FIRST_SUPERUSER}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    assert r["content-type"].startswith("text/html")
    assert "/reset-password?token=" in r.content.decode()


def test_recover_password_html_content_user_not_found(
    client: APIClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/password-recovery-html-content/{random_email()}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 404


def test_recover_password_html_content_normal_user(
    client: APIClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/password-recovery-html-content/{settings.FIRST_SUPERUSER}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403


def test_login_with_pbkdf2_password_upgrades_to_argon2(client: APIClient) -> None:
    """Test that logging in with a legacy PBKDF2 hash upgrades it to argon2."""
    email = random_email()
    password = random_lower_string()

    user = User(email=email, password=make_password(password, hasher="pbkdf2_sha256"))
    user.save()
    assert user.password.startswith("pbkdf2_sha256$")

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 200
    assert "access_token" in r.json()

    user.refresh_from_db()
    assert user.password.startswith("argon2$")
    assert user.check_password(password)


def test_login_with_argon2_password_keeps_hash(client: APIClient) -> None:
    """Test that logging in with an argon2 password hash does not update it."""
    user = User.objects.create_user(email=random_email(), password="secret-password")
    original_hash = user.password
    assert original_hash.startswith("argon2$")

    login_data = {"username": user.email, "password": "secret-password"}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 200

    user.refresh_from_db()
    assert user.password == original_hash
