import json
import random
import string
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode

from django.test import Client

from app.core.config import settings

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse as Response


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))


def random_email() -> str:
    return f"{random_lower_string()}@{random_lower_string()}.com"


class APIClient:
    """Thin wrapper over Django's test client with FastAPI TestClient-like
    `json=` / `data=` (form) arguments, going through the real URL routing."""

    def __init__(self) -> None:
        self._client = Client()

    def request(
        self,
        method: str,
        url: str,
        *,
        json_body: Any = None,
        data: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Response:
        kwargs: dict[str, Any] = {"headers": headers or {}}
        if json_body is not None:
            kwargs["data"] = json.dumps(json_body)
            kwargs["content_type"] = "application/json"
        elif data is not None:
            kwargs["data"] = urlencode(data)
            kwargs["content_type"] = "application/x-www-form-urlencoded"
        return getattr(self._client, method)(url, **kwargs)  # type: ignore[no-any-return]

    def get(self, url: str, **kwargs: Any) -> Response:
        return self.request("get", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Response:
        return self.request("post", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> Response:
        return self.request("put", url, **kwargs)

    def patch(self, url: str, **kwargs: Any) -> Response:
        return self.request("patch", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> Response:
        return self.request("delete", url, **kwargs)


def get_superuser_token_headers(client: APIClient) -> dict[str, str]:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers
