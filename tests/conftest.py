from __future__ import annotations

import pytest

from smart_system_a.models import Candle, OHLCVData


def candle(idx: int, open_: float, high: float, low: float, close: float, volume: float | None = 1000) -> Candle:
    return Candle(timestamp=f"2026-01-01 {idx:02d}:00", open=open_, high=high, low=low, close=close, volume=volume)


@pytest.fixture
def bullish_h4():
    return _bullish_h4


@pytest.fixture
def bearish_h4():
    return _bearish_h4


@pytest.fixture
def bullish_h1():
    return _bullish_h1


@pytest.fixture
def bearish_h1():
    return _bearish_h1


def _bullish_h4(volume: bool = True) -> OHLCVData:
    vols = [1000, 980, 970, 960, 1200, 1250, 1300, 1350, 1600, 1700, 1800, 1900, 2200, 2300, 2400, 2500]
    candles = []
    price = 4000.0
    for idx in range(16):
        body = 6 if idx < 8 else 12
        open_ = price
        close = price + body
        candles.append(candle(idx, open_, close + 3, open_ - 2, close, vols[idx] if volume else None))
        price = close - 2
    return OHLCVData(candles=candles, timeframe="H4")


def _bearish_h4(volume: bool = True) -> OHLCVData:
    vols = [1000, 980, 970, 960, 1200, 1250, 1300, 1350, 1600, 1700, 1800, 1900, 2200, 2300, 2400, 2500]
    candles = []
    price = 4300.0
    for idx in range(16):
        body = 6 if idx < 8 else 12
        open_ = price
        close = price - body
        candles.append(candle(idx, open_, open_ + 2, close - 3, close, vols[idx] if volume else None))
        price = close + 2
    return OHLCVData(candles=candles, timeframe="H4")


def _bullish_h1(volume: bool = True) -> OHLCVData:
    vols = [900, 920, 930, 940, 950, 960, 970, 980, 2200, 1050, 1000, 980, 2100]
    candles = [
        candle(0, 4100, 4108, 4098, 4106, vols[0] if volume else None),
        candle(1, 4106, 4112, 4102, 4110, vols[1] if volume else None),
        candle(2, 4110, 4115, 4107, 4112, vols[2] if volume else None),
        candle(3, 4112, 4118, 4110, 4116, vols[3] if volume else None),
        candle(4, 4116, 4120, 4112, 4118, vols[4] if volume else None),
        candle(5, 4118, 4122, 4114, 4120, vols[5] if volume else None),
        candle(6, 4120, 4124, 4118, 4122, vols[6] if volume else None),
        candle(7, 4122, 4125, 4119, 4123, vols[7] if volume else None),
        candle(8, 4123, 4142, 4122, 4140, vols[8] if volume else None),
        candle(9, 4140, 4141, 4135, 4137, vols[9] if volume else None),
        candle(10, 4137, 4138, 4133, 4135, vols[10] if volume else None),
        candle(11, 4135, 4136, 4131, 4134, vols[11] if volume else None),
        candle(12, 4133, 4146, 4130, 4144, vols[12] if volume else None),
    ]
    return OHLCVData(candles=candles, timeframe="H1")


def _bearish_h1(volume: bool = True) -> OHLCVData:
    vols = [900, 920, 930, 940, 950, 960, 970, 980, 2200, 1050, 1000, 980, 2100]
    candles = [
        candle(0, 4200, 4202, 4192, 4194, vols[0] if volume else None),
        candle(1, 4194, 4198, 4188, 4190, vols[1] if volume else None),
        candle(2, 4190, 4193, 4185, 4188, vols[2] if volume else None),
        candle(3, 4188, 4190, 4182, 4184, vols[3] if volume else None),
        candle(4, 4184, 4188, 4180, 4182, vols[4] if volume else None),
        candle(5, 4182, 4186, 4178, 4180, vols[5] if volume else None),
        candle(6, 4180, 4182, 4176, 4178, vols[6] if volume else None),
        candle(7, 4178, 4181, 4175, 4177, vols[7] if volume else None),
        candle(8, 4177, 4178, 4158, 4160, vols[8] if volume else None),
        candle(9, 4160, 4165, 4159, 4163, vols[9] if volume else None),
        candle(10, 4163, 4167, 4162, 4165, vols[10] if volume else None),
        candle(11, 4165, 4169, 4164, 4166, vols[11] if volume else None),
        candle(12, 4167, 4170, 4154, 4156, vols[12] if volume else None),
    ]
    return OHLCVData(candles=candles, timeframe="H1")
