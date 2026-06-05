from __future__ import annotations

from statistics import mean

from smart_system_a.models import Candle, Direction, OHLCVData

from .models import ElliotWave3Result


class ElliotWave3Analyzer:
    """Strict XAUUSD Elliott Wave Wave 3 continuation analyzer.

    Implements the PDF strategy as analysis-only rules:
    H4 structure, H1 momentum, M15 trigger, Wave 2 Fibonacci retracement,
    Wave 3 projection, M15 volume expansion, H4 ATR impulse strength, and 1:3 R:R.
    """

    MIN_SCORE = 85
    RISK_REWARD = 3.0
    MIN_WAVE2_RETRACEMENT = 38.2
    MAX_WAVE2_RETRACEMENT = 61.8
    PREFERRED_WAVE2_RETRACEMENT = 55.0
    MIN_WAVE3_PROJECTION = 1.272
    VOLUME_AVERAGE_PERIOD = 20
    VOLUME_MULTIPLIER = 1.20
    ATR_PERIOD = 14
    MIN_IMPULSE_ATR = 1.20

    def analyze(
        self,
        *,
        symbol: str,
        h4: OHLCVData,
        h1: OHLCVData,
        m15: OHLCVData,
        current_price: float | None = None,
    ) -> ElliotWave3Result:
        if symbol.upper().replace("/", "") != "XAUUSD":
            raise ValueError("Elliot Wave 3 Analysis supports XAUUSD only.")
        if len(h4.candles) < 10 or len(h1.candles) < 10 or len(m15.candles) < 10:
            raise ValueError("Elliot Wave 3 Analysis requires at least 10 candles each for H4, H1, and M15.")

        price = current_price or m15.candles[-1].close
        bullish = self._build_bullish_setup(h4.candles, h1.candles, m15.candles, price)
        bearish = self._build_bearish_setup(h4.candles, h1.candles, m15.candles, price)
        selected = self._select_setup(bullish, bearish)
        return self._result(symbol, selected)

    def _build_bullish_setup(
        self,
        h4: list[Candle],
        h1: list[Candle],
        m15: list[Candle],
        current_price: float,
    ) -> dict[str, object]:
        wave1_origin_index, wave1_end_index, wave2_index = self._best_bullish_wave_points(h4, current_price)
        origin = h4[wave1_origin_index].low
        wave1_end = h4[wave1_end_index].high
        wave2 = h4[wave2_index].low
        wave1_length = wave1_end - origin
        retracement = ((wave1_end - wave2) / wave1_length * 100) if wave1_length > 0 else None
        projection = ((current_price - wave2) / wave1_length) if wave1_length > 0 else None
        atr = self._atr(h4)
        impulse_multiple = wave1_length / atr if atr and atr > 0 else None
        entry = current_price
        stop = wave2
        take_profit = entry + self.RISK_REWARD * (entry - stop) if entry > stop else None
        return self._score_setup(
            direction="BUY",
            trend_ok=self._h4_bullish_trend(h4),
            wave_ok=(
                wave1_length > 0
                and wave2 > origin
                and current_price > wave1_end
                and impulse_multiple is not None
                and impulse_multiple >= self.MIN_IMPULSE_ATR
            ),
            fib_value=retracement,
            projection_value=projection,
            h1_ok=self._h1_bullish_momentum(h1, wave1_end),
            m15_ok=self._m15_bullish_trigger(m15, wave2, wave1_end),
            volume_ratio=self._volume_ratio(m15),
            rr_ok=take_profit is not None,
            wave1_origin=origin,
            wave1_end=wave1_end,
            wave2_level=wave2,
            atr=atr,
            impulse_multiple=impulse_multiple,
            h1_momentum="Bullish" if self._h1_bullish_momentum(h1, wave1_end) else "Not confirmed",
            m15_trigger="Bullish trigger" if self._m15_bullish_trigger(m15, wave2, wave1_end) else "Not confirmed",
            entry=entry if take_profit is not None else None,
            stop=stop if take_profit is not None else None,
            take_profit=take_profit,
        )

    def _build_bearish_setup(
        self,
        h4: list[Candle],
        h1: list[Candle],
        m15: list[Candle],
        current_price: float,
    ) -> dict[str, object]:
        wave1_origin_index, wave1_end_index, wave2_index = self._best_bearish_wave_points(h4, current_price)
        origin = h4[wave1_origin_index].high
        wave1_end = h4[wave1_end_index].low
        wave2 = h4[wave2_index].high
        wave1_length = origin - wave1_end
        retracement = ((wave2 - wave1_end) / wave1_length * 100) if wave1_length > 0 else None
        projection = ((wave2 - current_price) / wave1_length) if wave1_length > 0 else None
        atr = self._atr(h4)
        impulse_multiple = wave1_length / atr if atr and atr > 0 else None
        entry = current_price
        stop = wave2
        take_profit = entry - self.RISK_REWARD * (stop - entry) if stop > entry else None
        return self._score_setup(
            direction="SELL",
            trend_ok=self._h4_bearish_trend(h4),
            wave_ok=(
                wave1_length > 0
                and wave2 < origin
                and current_price < wave1_end
                and impulse_multiple is not None
                and impulse_multiple >= self.MIN_IMPULSE_ATR
            ),
            fib_value=retracement,
            projection_value=projection,
            h1_ok=self._h1_bearish_momentum(h1, wave1_end),
            m15_ok=self._m15_bearish_trigger(m15, wave2, wave1_end),
            volume_ratio=self._volume_ratio(m15),
            rr_ok=take_profit is not None,
            wave1_origin=origin,
            wave1_end=wave1_end,
            wave2_level=wave2,
            atr=atr,
            impulse_multiple=impulse_multiple,
            h1_momentum="Bearish" if self._h1_bearish_momentum(h1, wave1_end) else "Not confirmed",
            m15_trigger="Bearish trigger" if self._m15_bearish_trigger(m15, wave2, wave1_end) else "Not confirmed",
            entry=entry if take_profit is not None else None,
            stop=stop if take_profit is not None else None,
            take_profit=take_profit,
        )

    def _score_setup(
        self,
        *,
        direction: str,
        trend_ok: bool,
        wave_ok: bool,
        fib_value: float | None,
        projection_value: float | None,
        h1_ok: bool,
        m15_ok: bool,
        volume_ratio: float | None,
        rr_ok: bool,
        wave1_origin: float,
        wave1_end: float,
        wave2_level: float,
        atr: float | None,
        impulse_multiple: float | None,
        h1_momentum: str,
        m15_trigger: str,
        entry: float | None,
        stop: float | None,
        take_profit: float | None,
    ) -> dict[str, object]:
        fib_ok = fib_value is not None and self.MIN_WAVE2_RETRACEMENT <= fib_value <= self.MAX_WAVE2_RETRACEMENT
        projection_ok = projection_value is not None and projection_value >= self.MIN_WAVE3_PROJECTION
        volume_ok = volume_ratio is not None and volume_ratio >= self.VOLUME_MULTIPLIER
        checklist = {
            "trend_alignment": self._check(trend_ok, 20, f"H4 trend supports {direction}."),
            "elliott_wave_rule": self._check(wave_ok and projection_ok, 25, "Wave 1, Wave 2, Wave 3 breakout, ATR impulse, and projection are valid."),
            "fibonacci_confirmation": self._check(fib_ok, 20, "Wave 2 retracement is inside 38.2% - 61.8%."),
            "momentum_confirmation": self._check(h1_ok and m15_ok, 15, "H1 momentum and M15 trigger confirm continuation."),
            "volume_confirmation": self._check(volume_ok, 10, "M15 tick volume expands at least 1.20x above average."),
            "risk_reward_valid": self._check(rr_ok, 10, "Trade plan has valid 1:3 risk reward geometry."),
        }
        score = sum(int(item["points"]) for item in checklist.values() if item["passed"])
        critical_ok = all(item["passed"] for item in checklist.values())
        rating = self._rating(score)
        failed = [item["reason"] for item in checklist.values() if not item["passed"]]
        if fib_value is not None and fib_value >= self.PREFERRED_WAVE2_RETRACEMENT and fib_ok:
            checklist["fibonacci_confirmation"]["reason"] = "Wave 2 is in the preferred 55% - 61.8% zone."
        if projection_value is not None and projection_value >= 2.0:
            checklist["elliott_wave_rule"]["reason"] = "Wave 3 projection is elite: above 2.00x Wave 1."
        return {
            "direction": direction,
            "score": score,
            "rating": rating,
            "status": "VALID_TRADE" if critical_ok and score >= self.MIN_SCORE else "NO_TRADE",
            "checklist": checklist,
            "failed_rules": failed,
            "wave1_origin": wave1_origin,
            "wave1_end": wave1_end,
            "wave2_level": wave2_level,
            "wave2_retracement": fib_value,
            "wave3_projection": projection_value,
            "atr_value": atr,
            "impulse_atr_multiple": impulse_multiple,
            "h1_momentum": h1_momentum,
            "m15_trigger": m15_trigger,
            "volume_ratio": volume_ratio,
            "entry": entry,
            "stop_loss": stop,
            "take_profit": take_profit,
        }

    def _select_setup(self, bullish: dict[str, object], bearish: dict[str, object]) -> dict[str, object]:
        if bullish["status"] == "VALID_TRADE" and bearish["status"] != "VALID_TRADE":
            return bullish
        if bearish["status"] == "VALID_TRADE" and bullish["status"] != "VALID_TRADE":
            return bearish
        if bullish["status"] == "VALID_TRADE" and bearish["status"] == "VALID_TRADE":
            return bullish if int(bullish["score"]) >= int(bearish["score"]) else bearish
        return bullish if int(bullish["score"]) >= int(bearish["score"]) else bearish

    def _best_bullish_wave_points(self, candles: list[Candle], current_price: float) -> tuple[int, int, int]:
        best: tuple[float, int, int, int] | None = None
        fallback_origin = min(range(max(3, len(candles) // 2)), key=lambda idx: candles[idx].low)
        fallback_high = max(range(fallback_origin + 1, len(candles) - 2), key=lambda idx: candles[idx].high)
        fallback_wave2 = min(range(fallback_high + 1, len(candles) - 1), key=lambda idx: candles[idx].low)
        for origin_idx in range(0, len(candles) - 4):
            origin = candles[origin_idx].low
            for high_idx in range(origin_idx + 1, len(candles) - 2):
                high = candles[high_idx].high
                wave1_length = high - origin
                if wave1_length <= 0 or current_price <= high:
                    continue
                for wave2_idx in range(high_idx + 1, len(candles) - 1):
                    wave2 = candles[wave2_idx].low
                    retracement = (high - wave2) / wave1_length * 100
                    if wave2 <= origin or not (self.MIN_WAVE2_RETRACEMENT <= retracement <= self.MAX_WAVE2_RETRACEMENT):
                        continue
                    projection = (current_price - wave2) / wave1_length
                    score = wave1_length * 3 + min(projection, 2.618) * 20 + (20 if retracement >= self.PREFERRED_WAVE2_RETRACEMENT else 0)
                    if best is None or score > best[0]:
                        best = (score, origin_idx, high_idx, wave2_idx)
        return (best[1], best[2], best[3]) if best else (fallback_origin, fallback_high, fallback_wave2)

    def _best_bearish_wave_points(self, candles: list[Candle], current_price: float) -> tuple[int, int, int]:
        best: tuple[float, int, int, int] | None = None
        fallback_origin = max(range(max(3, len(candles) // 2)), key=lambda idx: candles[idx].high)
        fallback_low = min(range(fallback_origin + 1, len(candles) - 2), key=lambda idx: candles[idx].low)
        fallback_wave2 = max(range(fallback_low + 1, len(candles) - 1), key=lambda idx: candles[idx].high)
        for origin_idx in range(0, len(candles) - 4):
            origin = candles[origin_idx].high
            for low_idx in range(origin_idx + 1, len(candles) - 2):
                low = candles[low_idx].low
                wave1_length = origin - low
                if wave1_length <= 0 or current_price >= low:
                    continue
                for wave2_idx in range(low_idx + 1, len(candles) - 1):
                    wave2 = candles[wave2_idx].high
                    retracement = (wave2 - low) / wave1_length * 100
                    if wave2 >= origin or not (self.MIN_WAVE2_RETRACEMENT <= retracement <= self.MAX_WAVE2_RETRACEMENT):
                        continue
                    projection = (wave2 - current_price) / wave1_length
                    score = wave1_length * 3 + min(projection, 2.618) * 20 + (20 if retracement >= self.PREFERRED_WAVE2_RETRACEMENT else 0)
                    if best is None or score > best[0]:
                        best = (score, origin_idx, low_idx, wave2_idx)
        return (best[1], best[2], best[3]) if best else (fallback_origin, fallback_low, fallback_wave2)

    def _result(self, symbol: str, setup: dict[str, object]) -> ElliotWave3Result:
        direction = str(setup["direction"]) if setup["status"] == "VALID_TRADE" else "WAIT"
        setup_name = f"Elliot Wave 3 {setup['direction']} Continuation" if setup["status"] == "VALID_TRADE" else "None"
        summary = (
            f"{setup['status']} - score {setup['score']}/100. "
            "Only strong Wave 3 continuation setups with score >= 85 are tradeable."
        )
        return ElliotWave3Result(
            symbol=symbol.upper().replace("/", ""),
            status=str(setup["status"]),
            direction=direction,
            setup_name=setup_name,
            score=int(setup["score"]),
            rating=str(setup["rating"]),
            trend=str(setup["direction"]) if setup["checklist"]["trend_alignment"]["passed"] else "Unconfirmed",
            wave1_origin=self._rounded(setup["wave1_origin"]),
            wave1_end=self._rounded(setup["wave1_end"]),
            wave2_level=self._rounded(setup["wave2_level"]),
            wave2_retracement=self._rounded(setup["wave2_retracement"]),
            wave3_projection=self._rounded(setup["wave3_projection"]),
            atr_value=self._rounded(setup["atr_value"]),
            impulse_atr_multiple=self._rounded(setup["impulse_atr_multiple"]),
            h1_momentum=str(setup["h1_momentum"]),
            m15_trigger=str(setup["m15_trigger"]),
            volume_ratio=self._rounded(setup["volume_ratio"]),
            entry=self._rounded(setup["entry"]) if setup["status"] == "VALID_TRADE" else None,
            stop_loss=self._rounded(setup["stop_loss"]) if setup["status"] == "VALID_TRADE" else None,
            take_profit=self._rounded(setup["take_profit"]) if setup["status"] == "VALID_TRADE" else None,
            risk_reward=self.RISK_REWARD,
            checklist=dict(setup["checklist"]),
            failed_rules=list(setup["failed_rules"]),
            summary=summary,
        )

    def _h4_bullish_trend(self, candles: list[Candle]) -> bool:
        recent = candles[-6:]
        return recent[-1].close > recent[0].close and max(c.high for c in recent[-3:]) > max(c.high for c in recent[:3])

    def _h4_bearish_trend(self, candles: list[Candle]) -> bool:
        recent = candles[-6:]
        return recent[-1].close < recent[0].close and min(c.low for c in recent[-3:]) < min(c.low for c in recent[:3])

    def _h1_bullish_momentum(self, candles: list[Candle], breakout_level: float) -> bool:
        last = candles[-1]
        previous = candles[-2]
        return last.direction == Direction.BULLISH and (last.close > previous.high or last.close > breakout_level)

    def _h1_bearish_momentum(self, candles: list[Candle], breakout_level: float) -> bool:
        last = candles[-1]
        previous = candles[-2]
        return last.direction == Direction.BEARISH and (last.close < previous.low or last.close < breakout_level)

    def _m15_bullish_trigger(self, candles: list[Candle], wave2_level: float, breakout_level: float) -> bool:
        last = candles[-1]
        previous = candles[-2]
        rejection = last.low <= wave2_level and last.close > last.open
        return last.direction == Direction.BULLISH and (last.close > previous.high or last.close > breakout_level or rejection)

    def _m15_bearish_trigger(self, candles: list[Candle], wave2_level: float, breakout_level: float) -> bool:
        last = candles[-1]
        previous = candles[-2]
        rejection = last.high >= wave2_level and last.close < last.open
        return last.direction == Direction.BEARISH and (last.close < previous.low or last.close < breakout_level or rejection)

    def _volume_ratio(self, candles: list[Candle]) -> float | None:
        if len(candles) < self.VOLUME_AVERAGE_PERIOD + 1:
            return None
        recent = candles[-self.VOLUME_AVERAGE_PERIOD - 1:-1]
        if not all(c.volume is not None for c in recent) or candles[-1].volume is None:
            return None
        average = mean(float(c.volume or 0) for c in recent)
        if average <= 0:
            return None
        return float(candles[-1].volume or 0) / average

    def _atr(self, candles: list[Candle]) -> float | None:
        if len(candles) < self.ATR_PERIOD + 1:
            return None
        ranges = []
        for previous, current in zip(candles[-self.ATR_PERIOD - 1:-1], candles[-self.ATR_PERIOD:]):
            ranges.append(max(current.high - current.low, abs(current.high - previous.close), abs(current.low - previous.close)))
        return mean(ranges) if ranges else None

    def _check(self, passed: bool, points: int, reason: str) -> dict[str, object]:
        return {"passed": bool(passed), "points": points, "reason": reason}

    def _rating(self, score: int) -> str:
        if score >= 85:
            return "Strong setup"
        if score >= 70:
            return "Medium setup"
        return "Weak setup"

    def _rounded(self, value: object) -> float | None:
        if value is None:
            return None
        return round(float(value), 3)
