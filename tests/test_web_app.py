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
    assert b"Smart System A Agent" in response.data
    assert b"Analyze SSA Setup" in response.data


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
    def csv_bytes(data) -> BytesIO:
        text = "timestamp,open,high,low,close,volume\n"
        for c in data.candles:
            text += f"{c.timestamp},{c.open},{c.high},{c.low},{c.close},{c.volume}\n"
        return BytesIO(text.encode("utf-8"))

    client = app.test_client()
    response = client.post(
        "/",
        data={
            "h4": (csv_bytes(_bullish_h4()), "h4.csv"),
            "h1": (csv_bytes(_bullish_h1()), "h1.csv"),
            "balance": "100000",
            "risk_mode": "standard",
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
    def csv_bytes(data) -> BytesIO:
        text = "timestamp,open,high,low,close,volume\n"
        for c in data.candles:
            text += f"{c.timestamp},{c.open},{c.high},{c.low},{c.close},{c.volume}\n"
        return BytesIO(text.encode("utf-8"))

    client = app.test_client()
    response = client.post(
        "/",
        data={
            "analysis_system": "upas",
            "data_source": "csv",
            "mn1": (csv_bytes(trend_data("MN1")), "mn1.csv"),
            "w1": (csv_bytes(trend_data("W1")), "w1.csv"),
            "d1": (csv_bytes(trend_data("D1")), "d1.csv"),
            "h4": (csv_bytes(h4_last_kiss()), "h4.csv"),
            "h1": (csv_bytes(h1_confirmation()), "h1.csv"),
            "balance": "100000",
            "symbol": "XAUUSD",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"UPAS Market Bias" in response.data
    assert b"UPAS Confluence Checklist" in response.data
    assert b"UPAS Trade Assistant" in response.data
