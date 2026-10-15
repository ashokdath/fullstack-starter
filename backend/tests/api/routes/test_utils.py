from unittest.mock import patch

from django.core.mail import EmailMessage

from app.core.config import settings
from tests.utils.utils import APIClient


def test_health_check(client: APIClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/utils/health-check/")
    assert r.status_code == 200
    assert r.json() is True


def test_test_email(
    client: APIClient,
    superuser_token_headers: dict[str, str],
    mailoutbox: list[EmailMessage],
) -> None:
    with patch("app.core.config.settings.SMTP_HOST", "smtp.example.com"):
        r = client.post(
            f"{settings.API_V1_STR}/utils/test-email/?email_to=test@example.com",
            headers=superuser_token_headers,
        )
    assert r.status_code == 201
    assert r.json() == {"message": "Test email sent"}
    assert mailoutbox[0].to == ["test@example.com"]


def test_test_email_normal_user(
    client: APIClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/utils/test-email/?email_to=test@example.com",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403
