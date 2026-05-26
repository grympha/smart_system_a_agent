from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO

from PIL import Image, UnidentifiedImageError


ALLOWED_IMAGE_FORMATS = {"PNG", "JPEG", "WEBP"}


@dataclass(frozen=True)
class ImageIntakeResult:
    filename: str
    image_format: str
    width: int
    height: int
    message: str


class ImageInputValidator:
    def validate(self, stream: BinaryIO, filename: str) -> ImageIntakeResult:
        try:
            image = Image.open(stream)
            image.verify()
        except UnidentifiedImageError as exc:
            raise ValueError("Uploaded screenshot is not a supported image file.") from exc

        image_format = (image.format or "").upper()
        if image_format not in ALLOWED_IMAGE_FORMATS:
            allowed = ", ".join(sorted(ALLOWED_IMAGE_FORMATS))
            raise ValueError(f"Unsupported image format '{image_format}'. Use {allowed}.")

        return ImageIntakeResult(
            filename=filename,
            image_format=image_format,
            width=image.width,
            height=image.height,
            message=(
                "Screenshot accepted for review intake. No setup - OHLCV CSV data is required "
                "to mechanically verify H4 trend, Elliott Wave context, H1 BOS, pullback, candle "
                "behavior, and volume support under Smart System A."
            ),
        )
