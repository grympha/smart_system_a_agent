from __future__ import annotations

import base64
from io import BytesIO

from PIL import Image

import web_app as web_module
from web_app import app, build_live_status
from tests.conftest import _bullish_h1, _bullish_h4
from tests.test_upas_agent import h1_confirmation, h4_last_kiss, trend_data


def test_home_page_loads() -> None:
    client = app.test_client()
    response = client.get("/")

    assert response.status_code == 200
    assert b"Gold Smart Agent" in response.data
    assert b"Developed by Grympha" in response.data
    assert b"2026 Grympha" in response.data
    assert b"Run Analysis" in response.data
    assert b"Risk Settings" not in response.data
    assert b"SSA CSV Template" in response.data
    assert b"UPAS CSV Template" in response.data
    assert b"Wave Structure Analyst" in response.data
    assert b"Wave CSV Template" in response.data
    assert b"Wave Result View" not in response.data


def test_api_ping() -> None:
    client = app.test_client()
    response = client.get("/api/ping")

    assert response.status_code == 200
    assert response.get_json()["status"] == "READY"


def test_image_upload_returns_image_intake_no_setup() -> None:
    buffer = BytesIO()
    Image.new("RGB", (320, 180), color="white").save(buffer, format="PNG")
    buffer.seek(0)

    client = app.test_client()
    response = client.post(
        "/",
        data={"chart_image": (buffer, "chart.png")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"Image Accepted - No Setup" in response.data
    assert b"Chart Screenshot Preview" in response.data
    assert b"data:image/png;base64" in response.data


def test_dashboard_sections_render_for_csv_upload() -> None:
    def csv_bytes() -> BytesIO:
        text = "timeframe,timestamp,open,high,low,close,volume\n"
        for timeframe, data in [("H4", _bullish_h4()), ("H1", _bullish_h1())]:
            for c in data.candles:
                text += f"{timeframe},{c.timestamp},{c.open},{c.high},{c.low},{c.close},{c.volume}\n"
        return BytesIO(text.encode("utf-8"))

    client = app.test_client()
    response = client.post(
        "/",
        data={
            "ohlc_data": (csv_bytes(), "ohlc.csv"),
            "symbol": "XAU/USD",
            "data_source": "csv",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"H4 Trend And Wave" in response.data
    assert b"H1 Structure And Entry" in response.data
    assert b"Six-Condition SSA Checklist" in response.data
    assert b"Decision Summary" in response.data
    assert b"View raw analysis output" in response.data


def test_upas_selector_renders_upas_dashboard() -> None:
    def csv_bytes() -> BytesIO:
        text = "timeframe,timestamp,open,high,low,close,volume\n"
        for timeframe, data in [
            ("MN1", trend_data("MN1")),
            ("W1", trend_data("W1")),
            ("D1", trend_data("D1")),
            ("H4", h4_last_kiss()),
            ("H1", h1_confirmation()),
        ]:
            for c in data.candles:
                text += f"{timeframe},{c.timestamp},{c.open},{c.high},{c.low},{c.close},{c.volume}\n"
        return BytesIO(text.encode("utf-8"))

    client = app.test_client()
    response = client.post(
        "/",
        data={
            "analysis_system": "upas",
            "data_source": "csv",
            "ohlc_data": (csv_bytes(), "ohlc.csv"),
            "symbol": "XAUUSD",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"UPAS Market Bias" in response.data
    assert b"UPAS Confluence Checklist" in response.data
    assert b"UPAS Trade Assistant" in response.data
    assert b"Trade Plan" in response.data
    assert b"Take Profit" in response.data
    assert b"Stop Loss" in response.data
    assert b"Decision Summary" in response.data
    assert b"View raw analysis output" in response.data


def test_template_downloads() -> None:
    client = app.test_client()

    ssa = client.get("/templates/ssa.csv")
    upas = client.get("/templates/upas.csv")

    assert ssa.status_code == 200
    assert b"timeframe,timestamp,open,high,low,close,volume" in ssa.data
    assert b"H4" in ssa.data
    assert b"H1" in ssa.data
    assert upas.status_code == 200
    assert b"MN1" in upas.data
    assert b"W1" in upas.data
    assert b"D1" in upas.data


def test_api_analyze_accepts_mt5_ohlc_csv() -> None:
    text = "timeframe,timestamp,open,high,low,close,volume\n"
    for timeframe, data in [("H4", _bullish_h4()), ("H1", _bullish_h1())]:
        for c in data.candles:
            text += f"{timeframe},{c.timestamp},{c.open},{c.high},{c.low},{c.close},{c.volume}\n"

    client = app.test_client()
    response = client.post(
        "/api/analyze",
        json={"analysis_system": "ssa", "symbol": "XAUUSD", "ohlc_csv": text},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["analysis_system"] == "Smart System A"
    assert payload["trade_plan"]["action"] in {"ENTER BUY LIMIT", "ENTER SELL LIMIT", "WAIT"}
    assert "output" in payload


def test_api_analyze_stores_market_snapshot_and_chart_image() -> None:
    text = "timeframe,timestamp,open,high,low,close,volume\n"
    for timeframe, data in [("H4", _bullish_h4()), ("H1", _bullish_h1())]:
        for c in data.candles:
            text += f"{timeframe},{c.timestamp},{c.open},{c.high},{c.low},{c.close},{c.volume}\n"
    buffer = BytesIO()
    Image.new("RGB", (32, 18), color="white").save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")

    client = app.test_client()
    response = client.post(
        "/api/analyze",
        json={
            "analysis_system": "ssa",
            "symbol": "XAUUSD",
            "current_price": 3368.45,
            "timestamp": "2026-06-01T15:30:00",
            "chart_timeframe": "H1",
            "chart_filename": "XAUUSD_H1_20260601_153000.png",
            "chart_image": encoded,
            "ohlc_csv": text,
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["market_snapshot"]["current_price"] == 3368.45
    assert payload["market_snapshot"]["chart_available"] == "Yes"
    assert payload["chart_snapshot"]["symbol"] == "XAUUSD"
    assert payload["chart_snapshot"]["metadata"]["timeframe"] == "H1"

    image_response = client.get(payload["chart_snapshot"]["image_url"])
    assert image_response.status_code == 200
    assert image_response.mimetype == "image/png"


def test_api_analyze_accepts_mt5_wave_ohlc_csv() -> None:
    text = "timeframe,timestamp,open,high,low,close,volume\n"
    rows = [
        (4000, 4014, 3995, 4010),
        (4010, 4026, 4008, 4022),
        (4022, 4040, 4020, 4036),
        (4036, 4056, 4034, 4052),
        (4052, 4074, 4050, 4070),
        (4070, 4082, 4064, 4078),
        (4078, 4080, 4058, 4062),
        (4062, 4070, 4048, 4052),
        (4052, 4062, 4046, 4058),
        (4058, 4090, 4056, 4088),
        (4088, 4118, 4077, 4110),
        (4110, 4140, 4108, 4134),
    ]
    for idx, (open_, high, low, close) in enumerate(rows):
        text += f"H4,2026-01-01 {idx:02d}:00,{open_},{high},{low},{close},1000\n"
        text += f"H1,2026-01-02 {idx:02d}:00,{open_ + 20},{high + 20},{low + 20},{close + 20},1000\n"

    client = app.test_client()
    response = client.post(
        "/api/analyze",
        json={"analysis_system": "wave", "symbol": "XAUUSD", "ohlc_csv": text},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["analysis_system"] == "Wave Structure Analyst"
    assert payload["result"]["timeframe"] == "H4"
    assert set(payload["results"]) == {"H4", "H1"}
    assert payload["primary_timeframe"] == "H4"
    if payload["trade_plan"]:
        assert payload["trade_plan"]["action"] in {"ENTER BUY", "ENTER SELL"}
        assert payload["trade_plan"]["entry_point"] == payload["result"]["entry_zone"]
        assert payload["trade_plan"]["entry_point"] != rows[-1][3]
    assert "Wave Structure Analyst Result" in payload["output"]


def test_wave_structure_csv_upload_renders_dashboard() -> None:
    text = "timeframe,timestamp,open,high,low,close,volume\n"
    rows = [
        (4000, 4014, 3995, 4010),
        (4010, 4026, 4008, 4022),
        (4022, 4040, 4020, 4036),
        (4036, 4056, 4034, 4052),
        (4052, 4074, 4050, 4070),
        (4070, 4082, 4064, 4078),
        (4078, 4080, 4058, 4062),
        (4062, 4070, 4048, 4052),
        (4052, 4062, 4046, 4058),
        (4058, 4090, 4056, 4088),
        (4088, 4118, 4077, 4110),
        (4110, 4140, 4108, 4134),
    ]
    for idx, (open_, high, low, close) in enumerate(rows):
        text += f"H4,2026-01-01 {idx:02d}:00,{open_},{high},{low},{close},1000\n"
    client = app.test_client()
    response = client.post(
        "/",
        data={
            "analysis_system": "wave",
            "data_source": "csv",
            "ohlc_data": (BytesIO(text.encode("utf-8")), "wave.csv"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"Wave Structure Analyst Result" in response.data
    assert b"Wave 3 Continuation" in response.data
    assert b"Trading Bias" in response.data
    assert b"Wave Structure Results" in response.data
    assert b"H4 Result" in response.data
    assert b"Swing Highs" not in response.data


def test_wave_structure_shows_h4_and_h1_results() -> None:
    text = "timeframe,timestamp,open,high,low,close,volume\n"
    rows = [
        (4000, 4014, 3995, 4010),
        (4010, 4026, 4008, 4022),
        (4022, 4040, 4020, 4036),
        (4036, 4056, 4034, 4052),
        (4052, 4074, 4050, 4070),
        (4070, 4082, 4064, 4078),
        (4078, 4080, 4058, 4062),
        (4062, 4070, 4048, 4052),
        (4052, 4062, 4046, 4058),
        (4058, 4090, 4056, 4088),
        (4088, 4118, 4077, 4110),
        (4110, 4140, 4108, 4134),
    ]
    for idx, (open_, high, low, close) in enumerate(rows):
        text += f"H4,2026-01-01 {idx:02d}:00,{open_},{high},{low},{close},1000\n"
        text += f"H1,2026-01-02 {idx:02d}:00,{open_ + 30},{high + 30},{low + 30},{close + 30},1000\n"

    client = app.test_client()
    response = client.post(
        "/",
        data={
            "analysis_system": "wave",
            "data_source": "csv",
            "ohlc_data": (BytesIO(text.encode("utf-8")), "wave.csv"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"Wave Structure Results" in response.data
    assert b"H4 Result" in response.data
    assert b"H1 Result" in response.data


def test_wave_template_downloads() -> None:
    client = app.test_client()
    response = client.get("/templates/wave.csv")

    assert response.status_code == 200
    assert b"timeframe,timestamp,open,high,low,close,volume" in response.data
    assert b"H4" in response.data


def test_mt5_direct_mode_shows_waiting_panel(monkeypatch) -> None:
    monkeypatch.delenv("MT5_BRIDGE_URL", raising=False)
    monkeypatch.delenv("MT5_BRIDGE_API_KEY", raising=False)
    client = app.test_client()
    response = client.post(
        "/",
        data={"data_source": "mt5", "analysis_system": "ssa"},
    )

    assert response.status_code == 200
    assert b"Waiting for MT5 data" in response.data or b"Latest MT5 Analysis" in response.data
    assert b"No MT5 push has been received yet" in response.data or b"Latest MT5 Result" in response.data
    assert b"Keep the MT5 on-demand EA running" not in response.data


def test_mt5_direct_mode_creates_on_demand_request(monkeypatch) -> None:
    monkeypatch.delenv("MT5_BRIDGE_URL", raising=False)
    monkeypatch.delenv("MT5_BRIDGE_API_KEY", raising=False)
    client = app.test_client()
    response = client.post("/", data={"data_source": "mt5", "analysis_system": "upas"})
    request_response = client.get("/api/mt5/next-request")

    assert response.status_code == 200
    assert request_response.status_code == 200
    assert request_response.data in {b"upas", b"ssa"}


def test_mt5_direct_mode_creates_wave_on_demand_request(monkeypatch) -> None:
    monkeypatch.delenv("MT5_BRIDGE_URL", raising=False)
    monkeypatch.delenv("MT5_BRIDGE_API_KEY", raising=False)
    client = app.test_client()
    for _ in range(20):
        if client.get("/api/mt5/next-request").data == b"none":
            break

    response = client.post("/", data={"data_source": "mt5", "analysis_system": "wave"})
    request_response = client.get("/api/mt5/next-request")

    assert response.status_code == 200
    assert request_response.status_code == 200
    assert request_response.data == b"wave"


def test_history_rows_are_clickable_after_api_push() -> None:
    text = "timeframe,timestamp,open,high,low,close,volume\n"
    for timeframe, data in [("H4", _bullish_h4()), ("H1", _bullish_h1())]:
        for c in data.candles:
            text += f"{timeframe},{c.timestamp},{c.open},{c.high},{c.low},{c.close},{c.volume}\n"

    client = app.test_client()
    client.post("/api/analyze", json={"analysis_system": "ssa", "symbol": "XAUUSD", "ohlc_csv": text})
    home = client.get("/")

    assert b"/history/" in home.data
    assert b'data-label="Date / Time"' in home.data
    assert b'data-label="Summary"' in home.data

    marker = b'href="/history/'
    start = home.data.find(marker)
    assert start != -1
    start += len(marker)
    end = home.data.find(b'"', start)
    item_id = home.data[start:end].decode("ascii")

    detail = client.get(f"/history/{item_id}")
    assert detail.status_code == 200
    assert b"Analysis History Detail" in detail.data
    assert b"H4 Trend And Wave" in detail.data
    assert b"Six-Condition SSA Checklist" in detail.data
    assert b"Stored raw analysis detail" in detail.data


def test_mt5_direct_mode_shows_latest_full_dashboard_after_push(monkeypatch) -> None:
    monkeypatch.delenv("MT5_BRIDGE_URL", raising=False)
    monkeypatch.delenv("MT5_BRIDGE_API_KEY", raising=False)
    text = "timeframe,timestamp,open,high,low,close,volume\n"
    for timeframe, data in [("H4", _bullish_h4()), ("H1", _bullish_h1())]:
        for c in data.candles:
            text += f"{timeframe},{c.timestamp},{c.open},{c.high},{c.low},{c.close},{c.volume}\n"

    client = app.test_client()
    client.post("/api/analyze", json={"analysis_system": "ssa", "symbol": "XAUUSD", "ohlc_csv": text})
    response = client.post("/", data={"data_source": "mt5", "analysis_system": "ssa"})

    assert response.status_code == 200
    assert b"Latest MT5 Result - Smart System A" in response.data
    assert b"MT5 Data Status" in response.data
    assert b"Roboforex" in response.data
    assert b"MYT" in response.data
    assert b"MT5 SSA H4 Trend And Wave" in response.data
    assert b"MT5 SSA Checklist" in response.data
    assert b"Latest MT5 Result - UPAS Trade Assistant" not in response.data
    assert b"Waiting for MT5 data" not in response.data
    assert b"Keep the MT5 on-demand EA running" not in response.data


def test_mt5_direct_mode_filters_to_selected_upas_system(monkeypatch) -> None:
    monkeypatch.delenv("MT5_BRIDGE_URL", raising=False)
    monkeypatch.delenv("MT5_BRIDGE_API_KEY", raising=False)
    text = "timeframe,timestamp,open,high,low,close,volume\n"
    for timeframe, data in [
        ("MN1", trend_data("MN1")),
        ("W1", trend_data("W1")),
        ("D1", trend_data("D1")),
        ("H4", h4_last_kiss()),
        ("H1", h1_confirmation()),
    ]:
        for c in data.candles:
            text += f"{timeframe},{c.timestamp},{c.open},{c.high},{c.low},{c.close},{c.volume}\n"

    client = app.test_client()
    client.post("/api/analyze", json={"analysis_system": "upas", "symbol": "XAUUSD", "ohlc_csv": text})
    response = client.post("/", data={"data_source": "mt5", "analysis_system": "upas"})

    assert response.status_code == 200
    assert b"Latest MT5 Result - UPAS Trade Assistant" in response.data
    assert b"MT5 UPAS Market Bias" in response.data
    assert b"Latest MT5 Result - Smart System A" not in response.data


def test_mt5_direct_mode_uses_bridge_when_configured(monkeypatch) -> None:
    monkeypatch.setenv("MT5_BRIDGE_URL", "http://bridge.local")
    monkeypatch.setenv("MT5_BRIDGE_API_KEY", "secret")
    monkeypatch.setattr(web_module, "fetch_mt5_bridge_data", lambda timeframes: {"H4": _bullish_h4(), "H1": _bullish_h1()})

    client = app.test_client()
    response = client.post("/", data={"data_source": "mt5", "analysis_system": "ssa"})

    assert response.status_code == 200
    assert b"Waiting for MT5 data" not in response.data
    assert b"H4 Trend And Wave" in response.data
    assert b"Six-Condition SSA Checklist" in response.data


def test_upas_history_detail_shows_dashboard_result(monkeypatch) -> None:
    monkeypatch.delenv("MT5_BRIDGE_URL", raising=False)
    monkeypatch.delenv("MT5_BRIDGE_API_KEY", raising=False)
    text = "timeframe,timestamp,open,high,low,close,volume\n"
    for timeframe, data in [
        ("MN1", trend_data("MN1")),
        ("W1", trend_data("W1")),
        ("D1", trend_data("D1")),
        ("H4", h4_last_kiss()),
        ("H1", h1_confirmation()),
    ]:
        for c in data.candles:
            text += f"{timeframe},{c.timestamp},{c.open},{c.high},{c.low},{c.close},{c.volume}\n"

    client = app.test_client()
    client.post("/api/analyze", json={"analysis_system": "upas", "symbol": "XAUUSD", "ohlc_csv": text})
    home = client.post("/", data={"data_source": "mt5", "analysis_system": "upas"})
    marker = b'href="/history/'
    start = home.data.find(marker)
    assert start != -1
    start += len(marker)
    end = home.data.find(b'"', start)
    item_id = home.data[start:end].decode("ascii")

    detail = client.get(f"/history/{item_id}")
    assert detail.status_code == 200
    assert b"UPAS Market Bias" in detail.data
    assert b"UPAS Confluence Checklist" in detail.data
    assert b"UPAS Trade Plan" in detail.data


def test_why_no_trade_panel_renders_for_invalid_ssa() -> None:
    def csv_bytes() -> BytesIO:
        text = "timeframe,timestamp,open,high,low,close,volume\n"
        for timeframe, data in [("H4", _bullish_h4(volume=False)), ("H1", _bullish_h1(volume=False))]:
            for c in data.candles:
                volume = "" if c.volume is None else c.volume
                text += f"{timeframe},{c.timestamp},{c.open},{c.high},{c.low},{c.close},{volume}\n"
        return BytesIO(text.encode("utf-8"))

    client = app.test_client()
    response = client.post(
        "/",
        data={
            "ohlc_data": (csv_bytes(), "ohlc.csv"),
            "symbol": "XAU/USD",
            "data_source": "csv",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"Why No Trade?" in response.data
    assert b"Volume supports direction" in response.data


def test_live_status_helper_reports_candles_and_volume() -> None:
    status = build_live_status([_bullish_h4(), _bullish_h1()])

    assert status["provider"] == "Twelve Data"
    assert status["status"] == "Loaded"
    assert "H4: 16" in status["total_candles"]
    assert "H1: 13" in status["total_candles"]
    assert status["volume_status"] == "Present"
