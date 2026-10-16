import pytest
from django.test import Client


def test_admin_login_page(client: Client) -> None:
    assert client.get("/django-admin/login/").status_code == 200


def test_admin_without_slash_redirects(client: Client) -> None:
    r = client.get("/django-admin")
    assert r.status_code == 301
    assert r["Location"] == "/django-admin/"


@pytest.mark.parametrize("path", ["/", "/login", "/admin/", "/items"])
def test_frontend_routes_not_served(client: Client, path: str) -> None:
    """The backend is API-only: the proxy sends these paths to the frontend."""
    assert client.get(path).status_code == 404


def test_admin_login_behind_https_proxy(client: Client) -> None:
    """CSRF origin check passes when the proxy terminates TLS."""
    client = Client(enforce_csrf_checks=True)
    # A proxy always forwards the Host header (without it Django adds :80)
    proxy = {"host": "testserver", "x-forwarded-proto": "https"}
    page = client.get("/django-admin/login/", headers=proxy)
    r = client.post(
        "/django-admin/login/",
        {
            "username": "nobody@example.com",
            "password": "wrong",
            "csrfmiddlewaretoken": page.cookies["csrftoken"].value,
        },
        headers={
            **proxy,
            "origin": "https://testserver",
            "referer": "https://testserver/django-admin/login/",
        },
    )
    assert r.status_code == 200  # form re-rendered with an error, not 403
