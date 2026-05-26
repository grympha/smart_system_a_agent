from __future__ import annotations

from io import BytesIO

from PIL import Image

from smart_system_a.image_input import ImageInputValidator


def test_image_upload_is_accepted_for_intake() -> None:
    buffer = BytesIO()
    Image.new("RGB", (640, 360), color="white").save(buffer, format="PNG")
    buffer.seek(0)

    result = ImageInputValidator().validate(buffer, "chart.png")

    assert result.image_format == "PNG"
    assert result.width == 640
    assert "No setup" in result.message
