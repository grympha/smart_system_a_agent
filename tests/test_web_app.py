from __future__ import annotations

from io import BytesIO

from PIL import Image

from web_app import app, build_live_status
from tests.conftest import _bullish_h1, _bullish_h4
from tests.test_upas_agent import h1_confirmation, h4_last_kiss, trend_data


def test_home_page_loads() -> None:
    client = app.test_client()
    response = client.get("/")

    assert response.status_code == 200
    assert b"Gold Smart Agent" in response.data
    assert b"Run Analysis" in response.data
    assert b"Risk Settings" not in response.data
    assert b"SSA CSV Template" in response.data
    assert b"UPAS CSV Template" in response.data


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
    assert "output" in payload


def test_mt5_direct_mode_shows_waiting_panel() -> None:
    client = app.test_client()
    response = client.post(
        "/",
        data={"data_source": "mt5", "analysis_system": "ssa"},
    )

    assert response.status_code == 200
    assert b"Waiting for MT5 data" in response.data
    assert b"No MT5 push has been received yet" in response.data or b"Latest MT5 Result" in response.data


def test_history_rows_are_clickable_after_api_push() -> None:
    text = "timeframe,timestamp,open,high,low,close,volume\n"
    for timeframe, data in [("H4", _bullish_h4()), ("H1", _bullish_h1())]:
        for c in data.candles:
            text += f"{timeframe},{c.timestamp},{c.open},{c.high},{c.low},{c.close},{c.volume}\n"

    client = app.test_client()
    client.post("/api/analyze", json={"analysis_system": "ssa", "symbol": "XAUUSD", "ohlc_csv": text})
    home = client.get("/")

    assert b"/history/" in home.data

    marker = b'href="/history/'
    start = home.data.find(marker)
    assert start != -1
    start += len(marker)
    end = home.data.find(b'"', start)
    item_id = home.data[start:end].decode("ascii")

    detail = client.get(f"/history/{item_id}")
    assert detail.status_code == 200
    assert b"Analysis History Detail" in detail.data
    assert b"Stored analysis detail" in detail.data


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
