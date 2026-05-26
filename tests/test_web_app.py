from __future__ import annotations

from web_app import app


def test_home_page_loads() -> None:
    client = app.test_client()
    response = client.get("/")

    assert response.status_code == 200
    assert b"Smart System A Agent" in response.data
    assert b"Analyze SSA Setup" in response.data
