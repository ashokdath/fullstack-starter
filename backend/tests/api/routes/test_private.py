from app.core.config import settings
from app.users.models import User
from tests.utils.utils import APIClient


def test_create_user(client: APIClient) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/private/users/",
        json_body={
            "email": "pollo@listo.com",
            "password": "password123",
            "full_name": "Pollo Listo",
        },
    )

    assert r.status_code == 200

    data = r.json()

    user = User.objects.filter(id=data["id"]).first()

    assert user
    assert user.email == "pollo@listo.com"
    assert user.full_name == "Pollo Listo"
