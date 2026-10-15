from app.core.config import settings
from app.users import services
from app.users.models import User
from app.users.schemas import UserCreate, UserUpdate
from tests.utils.utils import APIClient, random_email, random_lower_string


def user_authentication_headers(
    *, client: APIClient, email: str, password: str
) -> dict[str, str]:
    data = {"username": email, "password": password}

    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=data)
    response = r.json()
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers


def create_random_user() -> User:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    return services.create_user(user_create=user_in)


def authentication_token_from_email(*, client: APIClient, email: str) -> dict[str, str]:
    """
    Return a valid token for the user with given email.

    If the user doesn't exist it is created first.
    """
    password = random_lower_string()
    user = services.get_user_by_email(email=email)
    if not user:
        user_in_create = UserCreate(email=email, password=password)
        user = services.create_user(user_create=user_in_create)
    else:
        user_in_update = UserUpdate(password=password)
        user = services.update_user(db_user=user, user_in=user_in_update)

    return user_authentication_headers(client=client, email=email, password=password)
