"""The OpenAPI schema is the contract the frontend client is generated from."""

from typing import Any

from app.api import api
from app.core.config import settings
from tests.utils.utils import APIClient


def get_schema() -> dict[str, Any]:
    return api.get_openapi_schema()  # type: ignore[no-any-return]


def test_openapi_served(client: APIClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/openapi.json")
    assert r.status_code == 200
    assert r.json()["info"]["title"] == settings.PROJECT_NAME


def test_operation_ids_are_tag_and_function_name() -> None:
    schema = get_schema()
    op_ids = [
        op["operationId"] for path in schema["paths"].values() for op in path.values()
    ]
    assert len(op_ids) == len(set(op_ids))
    assert "users-read_user_me" in op_ids
    assert "login-login_access_token" in op_ids


def test_login_form_body_component() -> None:
    schema = get_schema()
    body = schema["paths"][f"{settings.API_V1_STR}/login/access-token"]["post"][
        "requestBody"
    ]["content"]["application/x-www-form-urlencoded"]["schema"]
    assert body == {"$ref": "#/components/schemas/Body_login-login_access_token"}
    assert "Body_login-login_access_token" in schema["components"]["schemas"]
    assert "OAuth2PasswordRequestForm" not in schema["components"]["schemas"]


def test_security_scheme_and_validation_errors() -> None:
    schema = get_schema()
    assert list(schema["components"]["securitySchemes"]) == ["OAuth2PasswordBearer"]
    users = schema["paths"][f"{settings.API_V1_STR}/users/"]["get"]
    assert users["security"] == [{"OAuth2PasswordBearer": []}]
    assert users["responses"][200]["description"] == "Successful Response"
    assert 422 in users["responses"]
    me = schema["paths"][f"{settings.API_V1_STR}/users/me"]["get"]
    assert 422 not in me["responses"]
