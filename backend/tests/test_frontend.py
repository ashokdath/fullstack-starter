from pathlib import Path

import pytest
from django.test import Client
from pytest_django.fixtures import Settings as SettingsWrapper


def test_spa_routes_serve_index(
    tmp_path: Path, settings: SettingsWrapper, client: Client
) -> None:
    (tmp_path / "index.html").write_text("<div id='root'></div>")
    settings.FRONTEND_DIR = tmp_path
    for path in ["/", "/login", "/items", "/reset-password?token=x"]:
        r = client.get(path)
        assert r.status_code == 200
        assert b"<div id='root'>" in b"".join(r.streaming_content)  # type: ignore[attr-defined]


def test_spa_not_built(
    tmp_path: Path, settings: SettingsWrapper, client: Client
) -> None:
    settings.FRONTEND_DIR = tmp_path
    assert client.get("/").status_code == 404


@pytest.mark.parametrize("path", ["/api/v1/nope", "/static/nope.css"])
def test_spa_does_not_catch_api_or_static(client: Client, path: str) -> None:
    r = client.get(path)
    assert r.status_code == 404
    assert b"root" not in r.content


def test_admin_login_page(client: Client) -> None:
    assert client.get("/admin/login/").status_code == 200
