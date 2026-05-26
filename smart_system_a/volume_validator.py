from __future__ import annotations

from statistics import mean
from typing import Optional

from .models import Candle, Direction


class VolumeValidator:
    missing_message = "Volume analysis limited - OHLCV volume data missing."

    def impulse_beats_pullback(
        self,
        impulse_candles: list[Candle],
        pullback_candles: list[Candle],
        direction: Direction,
    ) -> Optional[bool]:
        if not impulse_candles or not pullback_candles:
            return False
        if any(c.volume is None for c in impulse_candles + pullback_candles):
            return None

        directional_impulse = [c for c in impulse_candles if c.direction == direction]
        if not directional_impulse:
            return False

        impulse_volume = mean(c.volume for c in directional_impulse if c.volume is not None)
        pullback_volume = mean(c.volume for c in pullback_candles if c.volume is not None)
        return impulse_volume > pullback_volume

    def strongly_supports(
        self,
        impulse_candles: list[Candle],
        pullback_candles: list[Candle],
        direction: Direction,
    ) -> bool:
        supported = self.impulse_beats_pullback(impulse_candles, pullback_candles, direction)
        if supported is not True:
            return False
        impulse_avg = mean(c.volume or 0 for c in impulse_candles)
        pullback_avg = mean(c.volume or 0 for c in pullback_candles)
        return impulse_avg >= pullback_avg * 1.2
