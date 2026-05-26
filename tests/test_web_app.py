from __future__ import annotations

from io import BytesIO

from PIL import Image

from web_app import app


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
