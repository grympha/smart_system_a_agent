from __future__ import annotations

from statistics import mean

from .models import Candle, Direction


class StructureDetector:
    def detect_bos(self, candles: list[Candle], direction: Direction, lookback: int = 8) -> tuple[Direction, float | None, Candle | None]:
        if len(candles) < lookback + 2:
            return Direction.NEUTRAL, None, None
        prior = candles[-(lookback + 1):-1]
        latest = candles[-1]
        if direction == Direction.BULLISH:
            level = max(c.high for c in prior)
            return (Direction.BULLISH, level, latest) if latest.close > level else (Direction.NEUTRAL, level, latest)
        if direction == Direction.BEARISH:
            level = min(c.low for c in prior)
            return (Direction.BEARISH, level, latest) if latest.close < level else (Direction.NEUTRAL, level, latest)
        return Direction.NEUTRAL, None, latest

    def is_clean_breakout(self, candles: list[Candle], bos_level: float | None, direction: Direction) -> bool:
        if bos_level is None or len(candles) < 6:
            return False
        candle = candles[-1]
        avg_body = mean(c.body for c in candles[-6:-1])
        closes_beyond = candle.close > bos_level if direction == Direction.BULLISH else candle.close < bos_level
        body_dominant = candle.range > 0 and candle.body / candle.range >= 0.55
        displacement = candle.body >= avg_body * 1.15 if avg_body > 0 else candle.body > 0
        wick_ok = self._wick_ratio_ok(candle, direction)
        return closes_beyond and body_dominant and displacement and wick_ok

    def pullback_holds(self, candles: list[Candle], bos_level: float | None, direction: Direction, tolerance: float = 6.0) -> tuple[bool, float | None]:
        if bos_level is None or len(candles) < 4:
            return False, None
        pullback = candles[-4:-1]
        confirmation = candles[-1]
        if direction == Direction.BULLISH:
            touched_zone = any(c.low <= bos_level + tolerance for c in pullback)
            held = min(c.low for c in pullback) >= bos_level - tolerance
            confirmed = confirmation.close > bos_level and confirmation.direction == Direction.BULLISH
            return touched_zone and held and confirmed, bos_level
        if direction == Direction.BEARISH:
            touched_zone = any(c.high >= bos_level - tolerance for c in pullback)
            held = max(c.high for c in pullback) <= bos_level + tolerance
            confirmed = confirmation.close < bos_level and confirmation.direction == Direction.BEARISH
            return touched_zone and held and confirmed, bos_level
        return False, None

    def candle_confirms_from_zone(self, candles: list[Candle], direction: Direction) -> bool:
        if not candles:
            return False
        candle = candles[-1]
        if candle.range <= 0:
            return False
        if direction == Direction.BULLISH:
            rejection = candle.lower_wick >= candle.body * 0.5 and candle.direction == Direction.BULLISH
            bullish_close = candle.direction == Direction.BULLISH and candle.body / candle.range >= 0.45
            return rejection or bullish_close
        if direction == Direction.BEARISH:
            rejection = candle.upper_wick >= candle.body * 0.5 and candle.direction == Direction.BEARISH
            bearish_close = candle.direction == Direction.BEARISH and candle.body / candle.range >= 0.45
            return rejection or bearish_close
        return False

    def _wick_ratio_ok(self, candle: Candle, direction: Direction) -> bool:
        if candle.range <= 0:
            return False
        if direction == Direction.BULLISH:
            return candle.upper_wick / candle.range <= 0.35
        if direction == Direction.BEARISH:
            return candle.lower_wick / candle.range <= 0.35
        return False
