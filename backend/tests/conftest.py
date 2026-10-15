import io

import pytest
from django.core.management import call_command

from app.core.config import settings
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import APIClient, get_superuser_token_headers


@pytest.fixture(autouse=True)
def initial_data(db: None) -> None:
    """Every test runs in a rolled-back transaction with the first superuser."""
    call_command("create_initial_data", stdout=io.StringIO())


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def superuser_token_headers(client: APIClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture
def normal_user_token_headers(client: APIClient) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER
    )
