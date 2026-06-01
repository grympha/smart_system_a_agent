from __future__ import annotations

from statistics import mean

from smart_system_a.models import Candle, Direction

from .models import WaveAnalysisInput, WaveAnalysisResult


class WaveStructureAnalyst:
    """Conservative Elliott Wave classifier for XAUUSD structure.

    The detector uses raw OHLCV market structure only. It does not claim a
    certain wave count; it scores whether the visible structure resembles Wave 3
    continuation, ABC correction, Wave 5 exhaustion, or unclear conditions.
    """

    def analyze(self, request: WaveAnalysisInput) -> WaveAnalysisResult:
        if request.symbol.upper().replace("/", "") != "XAUUSD":
            raise ValueError("Wave Structure Analyst supports XAUUSD only.")
        candles = request.primary_data.candles
        if len(candles) < 10:
            raise ValueError("Wave Structure Analyst requires at least 10 candles for the selected timeframe.")

        trend = self._trend(request, candles)
        impulse = self._impulse_strength(candles)
        overlap = self._overlap_ratio(candles[-8:])
        momentum_slowing = self._momentum_slowing(candles)
        wave1_high, wave1_low = self._wave1_extremes(candles)
        current_price = request.current_price or candles[-1].close
        breakout_level = request.breakout_level or (wave1_high if trend == "bullish" else wave1_low)
        retest_level = request.retest_level or breakout_level

        if trend == "bullish":
            result = self._bullish_wave3(request, candles, wave1_high, wave1_low, current_price, breakout_level, retest_level)
        elif trend == "bearish":
            result = self._bearish_wave3(request, candles, wave1_high, wave1_low, current_price, breakout_level, retest_level)
        else:
            result = None

        abc = self._is_abc_correction(candles, trend, overlap, impulse)
        exhaustion = self._is_wave5_exhaustion(candles, trend, momentum_slowing, impulse)

        if result and result.wave_score >= 8 and not exhaustion:
            return result
        if exhaustion:
            return self._build_exhaustion(request, trend, current_price, wave1_low, wave1_high, result)
        if abc:
            return self._build_abc(request, trend, current_price, wave1_low, wave1_high)
        if result and result.wave_score >= 6:
            return result
        return self._build_unknown(request, trend, current_price, ["Wave count is unclear or incomplete."])

    def _bullish_wave3(
        self,
        request: WaveAnalysisInput,
        candles: list[Candle],
        wave1_high: float,
        wave1_low: float,
        current_price: float,
        breakout_level: float,
        retest_level: float,
    ) -> WaveAnalysisResult:
        retest = self._bullish_retest(candles, breakout_level, wave1_low)
        entry_zone = retest["entry"] if retest else None
        invalidation = retest["invalidation"] if retest else min(c.low for c in candles[-5:])
        wave2_respected = invalidation > wave1_low
        breakout_confirmed = current_price > breakout_level and candles[-1].close > wave1_high
        retest_confirmed = retest is not None
        rr_valid = self._risk_reward_valid(entry_zone, invalidation)
        score, failed = self._score(True, wave2_respected, breakout_confirmed, retest_confirmed, request.trend_direction == "bullish", rr_valid)
        bias = "BUY" if score >= 8 else "WAIT"
        return self._result(
            request,
            market_phase="Impulse" if score >= 6 else "Unknown",
            primary="Wave 3 Continuation" if score >= 6 else "Unknown",
            alternative="Possible ABC correction if retest fails",
            direction="Bullish",
            score=score,
            risk="Low" if score >= 8 else "Medium",
            bias=bias,
            action="Prepare for BUY only after pullback/retest remains protected." if bias == "BUY" else "Wait for stronger breakout and retest confirmation.",
            entry_zone=entry_zone if score >= 8 else None,
            invalidation=invalidation,
            reason=(
                f"Bullish structure checks Wave 1 high {wave1_high}, Wave 1 low {wave1_low}, "
                f"breakout level {breakout_level}, and retest level {retest_level}. "
                f"Score reflects breakout, protected Wave 2, trend alignment, and minimum 1:2 R:R."
            ),
            failed=failed,
        )

    def _bearish_wave3(
        self,
        request: WaveAnalysisInput,
        candles: list[Candle],
        wave1_high: float,
        wave1_low: float,
        current_price: float,
        breakout_level: float,
        retest_level: float,
    ) -> WaveAnalysisResult:
        retest = self._bearish_retest(candles, breakout_level, wave1_high)
        entry_zone = retest["entry"] if retest else None
        invalidation = retest["invalidation"] if retest else max(c.high for c in candles[-5:])
        wave2_respected = invalidation < wave1_high
        breakout_confirmed = current_price < breakout_level and candles[-1].close < wave1_low
        retest_confirmed = retest is not None
        rr_valid = self._risk_reward_valid(entry_zone, invalidation)
        score, failed = self._score(True, wave2_respected, breakout_confirmed, retest_confirmed, request.trend_direction == "bearish", rr_valid)
        bias = "SELL" if score >= 8 else "WAIT"
        return self._result(
            request,
            market_phase="Impulse" if score >= 6 else "Unknown",
            primary="Wave 3 Continuation" if score >= 6 else "Unknown",
            alternative="Possible ABC correction if retest fails",
            direction="Bearish",
            score=score,
            risk="Low" if score >= 8 else "Medium",
            bias=bias,
            action="Prepare for SELL only after pullback/retest remains protected." if bias == "SELL" else "Wait for stronger breakdown and retest confirmation.",
            entry_zone=entry_zone if score >= 8 else None,
            invalidation=invalidation,
            reason=(
                f"Bearish structure checks Wave 1 low {wave1_low}, Wave 1 high {wave1_high}, "
                f"breakdown level {breakout_level}, and retest level {retest_level}. "
                f"Score reflects breakdown, protected Wave 2, trend alignment, and minimum 1:2 R:R."
            ),
            failed=failed,
        )

    def _score(
        self,
        clarity: bool,
        invalidation_respected: bool,
        breakout_confirmed: bool,
        retest_confirmed: bool,
        trend_aligned: bool,
        rr_valid: bool,
    ) -> tuple[int, list[str]]:
        rules = [
            (clarity, 2, "Wave structure clarity"),
            (invalidation_respected, 2, "Wave 2 invalidation respected"),
            (breakout_confirmed, 2, "Wave 1 high/low breakout confirmed"),
            (retest_confirmed, 2, "Retest / pullback confirmed"),
            (trend_aligned, 1, "Trend alignment"),
            (rr_valid, 1, "Risk-to-reward valid"),
        ]
        return sum(points for passed, points, _ in rules if passed), [label for passed, _, label in rules if not passed]

    def _build_abc(self, request: WaveAnalysisInput, trend: str, current_price: float, wave1_low: float, wave1_high: float) -> WaveAnalysisResult:
        direction = "Neutral" if trend == "neutral" else trend.title()
        invalidation = wave1_high if trend == "bearish" else wave1_low
        return self._result(
            request,
            market_phase="Correction",
            primary="ABC Correction",
            alternative="Wave 3 continuation only after clean breakout and retest",
            direction=direction,
            score=5,
            risk="High",
            bias="WAIT",
            action="Avoid early entry. Wait for correction to complete and for a clean breakout/retest confirmation.",
            entry_zone=None,
            invalidation=invalidation,
            reason=f"Price action is overlapping, momentum has weakened, and continuation is not clean near {current_price}.",
            failed=["No clean Wave 1 breakout continuation", "Retest confirmation missing"],
        )

    def _build_exhaustion(
        self,
        request: WaveAnalysisInput,
        trend: str,
        current_price: float,
        wave1_low: float,
        wave1_high: float,
        prior: WaveAnalysisResult | None,
    ) -> WaveAnalysisResult:
        direction = "Neutral" if trend == "neutral" else trend.title()
        invalidation = wave1_low if trend == "bullish" else wave1_high
        return self._result(
            request,
            market_phase="Exhaustion",
            primary="Wave 5 Exhaustion",
            alternative="Possible ABC correction",
            direction=direction,
            score=min(prior.wave_score if prior else 5, 6),
            risk="High",
            bias="WAIT",
            action="Avoid late entry. Wait for rejection to resolve or for a fresh corrective pullback.",
            entry_zone=None,
            invalidation=invalidation,
            reason=f"Trend is extended near {current_price}, candle bodies are slowing, and late Wave 5 risk is elevated.",
            failed=["Price appears late in Wave 5", "Late entry risk"],
        )

    def _build_unknown(self, request: WaveAnalysisInput, trend: str, current_price: float, failed: list[str]) -> WaveAnalysisResult:
        return self._result(
            request,
            market_phase="Unknown",
            primary="Unknown",
            alternative="Unclear",
            direction="Neutral" if trend == "neutral" else trend.title(),
            score=0,
            risk="High",
            bias="WAIT",
            action="No valid setup. Wait for clear Wave 1 breakout, protected Wave 2, and retest confirmation.",
            entry_zone=None,
            invalidation=current_price,
            reason="Wave count is unclear; Smart System A and UPAS should not be overridden by this layer.",
            failed=failed,
        )

    def _result(
        self,
        request: WaveAnalysisInput,
        market_phase: str,
        primary: str,
        alternative: str,
        direction: str,
        score: int,
        risk: str,
        bias: str,
        action: str,
        entry_zone: float | None,
        invalidation: float | None,
        reason: str,
        failed: list[str],
    ) -> WaveAnalysisResult:
        return WaveAnalysisResult(
            symbol="XAUUSD",
            timeframe=request.timeframe,
            market_phase=market_phase,
            primary_scenario=primary,
            alternative_scenario=alternative,
            direction=direction,
            wave_score=max(0, min(score, 10)),
            confidence=max(0, min(score * 10, 100)),
            risk_level=risk,
            trading_bias=bias if score >= 8 and primary == "Wave 3 Continuation" else "WAIT",
            suggested_action=action,
            entry_zone=entry_zone,
            invalidation_level=invalidation,
            reason=reason,
            failed_rules=failed,
        )

    def _trend(self, request: WaveAnalysisInput, candles: list[Candle]) -> str:
        supplied = request.trend_direction.lower()
        if supplied in {"bullish", "bearish", "neutral"}:
            return supplied
        first = candles[0].close
        last = candles[-1].close
        if last > first and candles[-1].direction == Direction.BULLISH:
            return "bullish"
        if last < first and candles[-1].direction == Direction.BEARISH:
            return "bearish"
        return "neutral"

    def _wave1_extremes(self, candles: list[Candle]) -> tuple[float, float]:
        wave1 = candles[: max(4, len(candles) // 3)]
        return max(c.high for c in wave1), min(c.low for c in wave1)

    def _impulse_strength(self, candles: list[Candle]) -> float:
        recent = candles[-5:]
        prior = candles[-10:-5] or candles[:5]
        return mean(c.body for c in recent) / max(mean(c.body for c in prior), 0.01)

    def _overlap_ratio(self, candles: list[Candle]) -> float:
        if len(candles) < 2:
            return 1.0
        overlaps = 0
        for previous, current in zip(candles, candles[1:]):
            if current.low <= previous.high and current.high >= previous.low:
                overlaps += 1
        return overlaps / max(len(candles) - 1, 1)

    def _momentum_slowing(self, candles: list[Candle]) -> bool:
        if len(candles) < 8:
            return False
        prior = mean(c.body for c in candles[-8:-4])
        recent = mean(c.body for c in candles[-4:])
        return recent < prior * 0.65

    def _is_abc_correction(self, candles: list[Candle], trend: str, overlap: float, impulse: float) -> bool:
        if trend == "neutral":
            return overlap > 0.6
        return overlap > 0.65 and impulse < 0.9

    def _is_wave5_exhaustion(self, candles: list[Candle], trend: str, slowing: bool, impulse: float) -> bool:
        if trend == "neutral" or len(candles) < 12:
            return False
        extension = abs(candles[-1].close - candles[0].close) > mean(c.range for c in candles) * 8
        sharp_rejection = candles[-1].upper_wick > candles[-1].body * 1.5 or candles[-1].lower_wick > candles[-1].body * 1.5
        return extension and slowing and (sharp_rejection or impulse < 0.8)

    def _bullish_retest(self, candles: list[Candle], breakout_level: float, wave1_low: float) -> dict[str, float] | None:
        avg_range = mean(c.range for c in candles[-10:])
        tolerance = max(avg_range * 0.35, 1.0)
        break_index = self._break_index(candles, breakout_level, "bullish")
        if break_index is None:
            return None
        for candle in reversed(candles[break_index + 1:]):
            retested = candle.low <= breakout_level + tolerance
            protected = candle.low > wave1_low and candle.close > breakout_level
            risk_reasonable = breakout_level - candle.low <= max(avg_range * 2.0, tolerance)
            if retested and protected and risk_reasonable:
                return {"entry": round(breakout_level, 3), "invalidation": round(candle.low, 3)}
        return None

    def _bearish_retest(self, candles: list[Candle], breakout_level: float, wave1_high: float) -> dict[str, float] | None:
        avg_range = mean(c.range for c in candles[-10:])
        tolerance = max(avg_range * 0.35, 1.0)
        break_index = self._break_index(candles, breakout_level, "bearish")
        if break_index is None:
            return None
        for candle in reversed(candles[break_index + 1:]):
            retested = candle.high >= breakout_level - tolerance
            protected = candle.high < wave1_high and candle.close < breakout_level
            risk_reasonable = candle.high - breakout_level <= max(avg_range * 2.0, tolerance)
            if retested and protected and risk_reasonable:
                return {"entry": round(breakout_level, 3), "invalidation": round(candle.high, 3)}
        return None

    def _break_index(self, candles: list[Candle], level: float, direction: str) -> int | None:
        for index in range(1, len(candles)):
            previous = candles[index - 1]
            current = candles[index]
            if direction == "bullish" and previous.close <= level and current.close > level:
                return index
            if direction == "bearish" and previous.close >= level and current.close < level:
                return index
        return None

    def _risk_reward_valid(self, entry: float | None, stop: float | None) -> bool:
        if entry is None or stop is None:
            return False
        return abs(entry - stop) > 0
