from __future__ import annotations

from io import BytesIO

from PIL import Image

from web_app import app
from tests.conftest import _bullish_h1, _bullish_h4
from tests.test_upas_agent import h1_confirmation, h4_last_kiss, trend_data


def test_home_page_loads() -> None:
    client = app.test_client()
    response = client.get("/")

    assert response.status_code == 200
    assert b"Gold Smart Agent" in response.data
    assert b"Run Analysis" in response.data
    assert b"Risk Settings" not in response.data


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
    assert b"UPAS Decision Summary" in response.data
    assert b"View raw UPAS JSON" in response.data
