from __future__ import annotations

from mt5_bridge import create_bridge_app


def test_mt5_bridge_requires_api_key_configuration(monkeypatch) -> None:
    monkeypatch.delenv("MT5_BRIDGE_API_KEY", raising=False)
    app = create_bridge_app()
    client = app.test_client()

    response = client.get("/api/mt5/status")

    assert response.status_code == 500
    assert b"MT5_BRIDGE_API_KEY is not configured" in response.data


def test_mt5_bridge_rejects_missing_client_key(monkeypatch) -> None:
    monkeypatch.setenv("MT5_BRIDGE_API_KEY", "secret")
    app = create_bridge_app()
    client = app.test_client()

    response = client.get("/api/mt5/status")

    assert response.status_code == 401
    assert b"Unauthorized" in response.data


def test_mt5_bridge_reports_missing_metatrader_package(monkeypatch) -> None:
    monkeypatch.setenv("MT5_BRIDGE_API_KEY", "secret")
    app = create_bridge_app()
    client = app.test_client()

    response = client.get("/api/mt5/status", headers={"X-API-Key": "secret"})

    assert response.status_code in {200, 503}
    if response.status_code == 503:
        assert b"MetaTrader5 Python package is not installed" in response.data or b"MT5 is not open" in response.data
