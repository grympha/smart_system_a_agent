from __future__ import annotations

import json
from statistics import mean
from typing import Any

from smart_system_a.models import Candle, Direction, OHLCVData

from .models import UPASAnalysis, UPASInput, UPASSetupCandidate


class UPASAgent:
    MODULE = "UPAS Trade Assistant"
    TIMEFRAMES = ["MN1", "W1", "D1", "H4", "H1"]
    CONTRACT_VALUE_PER_LOT = 100.0
    RISK_PERCENT = 1.0
    MAX_DAILY_DRAWDOWN_PERCENT = 4.0
    MIN_RR = 2.0

    def analyze(self, data: UPASInput) -> UPASAnalysis:
        if not self._has_enough_data(data):
            payload = self._base_payload(data, status="INSUFFICIENT_DATA")
            payload["reasoning"] = "Latest candles are insufficient for MN1, W1, D1, H4, and H1 UPAS analysis."
            payload["summary"] = "INSUFFICIENT_DATA - upload enough candles for every UPAS timeframe."
            return UPASAnalysis(payload, self.format(payload))

        biases = {
            "MN1": self._trend(data.mn1),
            "W1": self._trend(data.w1),
            "D1": self._trend(data.d1),
            "H4": self._trend(data.h4),
            "H1": self._trend(data.h1),
        }
        setup = self._detect_setup(data.h4)
        h1_confirmed, h1_reason = self._h1_confirms(data.h1, setup.direction)
        near_sr, sr_reason = self._near_support_resistance(data)
        trend_ok, trend_reason = self._trend_alignment_ok(biases, setup.direction)
        rejection_ok, rejection_reason = self._rejection_ok(data.h4, setup.direction)
        trap_ok = setup.direction in {Direction.BULLISH, Direction.BEARISH}
        trap_reason = setup.reason if trap_ok else "H4 has no valid UPAS setup."

        checklist = {
            "support_resistance_proximity": {"passed": near_sr, "reason": sr_reason},
            "trend_alignment": {"passed": trend_ok, "reason": trend_reason},
            "rejection_candle": {"passed": rejection_ok, "reason": rejection_reason},
            "trap_fakeout_structure": {"passed": trap_ok, "reason": trap_reason},
            "h1_confirmation": {"passed": h1_confirmed, "reason": h1_reason},
        }
        score = sum(1 for item in checklist.values() if item["passed"])
        payload = self._base_payload(data, status="NO_TRADE")
        payload["market_bias"] = {key: value.value for key, value in biases.items()}
        payload["setup"] = {
            "name": setup.name,
            "direction": self._direction_text(setup.direction),
            "confluence_score": score,
            "checklist": checklist,
        }

        risk_plan = self._risk_plan(data, setup)
        payload["trade_plan"] = risk_plan
        payload["invalidation"] = setup.invalidation

        if score < 4:
            payload["reasoning"] = "Confluence score is below 4/5. UPAS prefers NO_TRADE over weak setups."
            payload["summary"] = f"NO_TRADE - confluence score {score}/5 is below the UPAS minimum."
            return UPASAnalysis(payload, self.format(payload))

        if not risk_plan["reward_risk_ratio"] or risk_plan["reward_risk_ratio"] < self.MIN_RR:
            payload["reasoning"] = "Reward:risk is below the UPAS minimum 1:2 requirement."
            payload["summary"] = "NO_TRADE - reward:risk is below 1:2."
            return UPASAnalysis(payload, self.format(payload))

        daily_after = risk_plan["daily_drawdown_after_trade_percent"]
        if daily_after is not None and daily_after > self.MAX_DAILY_DRAWDOWN_PERCENT:
            payload["status"] = "REJECTED_BY_RISK"
            payload["reasoning"] = "Potential loss would violate the 4% maximum daily drawdown rule."
            payload["summary"] = "REJECTED_BY_RISK - daily drawdown limit would be exceeded."
            return UPASAnalysis(payload, self.format(payload))

        payload["status"] = "VALID_TRADE"
        payload["reasoning"] = (
            f"{setup.name} passed UPAS confluence with {score}/5 conditions and minimum 1:2 reward:risk."
        )
        payload["summary"] = f"VALID_TRADE - {setup.name} {self._direction_text(setup.direction)} setup passed UPAS rules."
        return UPASAnalysis(payload, self.format(payload))

    def format(self, payload: dict[str, Any]) -> str:
        return json.dumps(payload, indent=2) + "\n\n" + payload["summary"]

    def _base_payload(self, data: UPASInput, status: str) -> dict[str, Any]:
        risk_amount = data.account_balance * self.RISK_PERCENT / 100
        return {
            "module": self.MODULE,
            "symbol": "XAUUSD",
            "status": status,
            "indicators_used": {
                "default": "None",
                "optional": "ATR(14) for volatility filter only, if enabled" if data.use_atr else "None",
            },
            "timeframes_used": self.TIMEFRAMES,
            "market_bias": {"MN1": "", "W1": "", "D1": "", "H4": "", "H1": ""},
            "setup": {
                "name": "None",
                "direction": "NONE",
                "confluence_score": 0,
                "checklist": {
                    "support_resistance_proximity": {"passed": False, "reason": ""},
                    "trend_alignment": {"passed": False, "reason": ""},
                    "rejection_candle": {"passed": False, "reason": ""},
                    "trap_fakeout_structure": {"passed": False, "reason": ""},
                    "h1_confirmation": {"passed": False, "reason": ""},
                },
            },
            "trade_plan": {
                "entry": None,
                "stop_loss": None,
                "take_profit": None,
                "risk_points": None,
                "reward_points": None,
                "reward_risk_ratio": None,
                "risk_amount_usd": risk_amount,
                "lot_size": None,
                "daily_drawdown_after_trade_percent": None,
            },
            "invalidation": "",
            "reasoning": "",
            "summary": "",
        }

    def _has_enough_data(self, data: UPASInput) -> bool:
        return all(len(tf.candles) >= 8 for tf in [data.mn1, data.w1, data.d1, data.h4, data.h1])

    def _trend(self, data: OHLCVData) -> Direction:
        candles = data.candles[-8:]
        highs_up = candles[-1].high > candles[-4].high > candles[-7].high
        lows_up = candles[-1].low > candles[-4].low > candles[-7].low
        highs_down = candles[-1].high < candles[-4].high < candles[-7].high
        lows_down = candles[-1].low < candles[-4].low < candles[-7].low
        if highs_up and lows_up:
            return Direction.BULLISH
        if highs_down and lows_down:
            return Direction.BEARISH
        return Direction.NEUTRAL

    def _detect_setup(self, h4: OHLCVData) -> UPASSetupCandidate:
        candles = h4.candles
        latest = candles[-1]
        prior = candles[-8:-1]
        support = min(c.low for c in prior)
        resistance = max(c.high for c in prior)

        kangaroo = self._kangaroo_tail(latest, support, resistance)
        if kangaroo.direction != Direction.NEUTRAL:
            return kangaroo

        engulfing = self._engulfing_trap(candles[-2], latest, support, resistance)
        if engulfing.direction != Direction.NEUTRAL:
            return engulfing

        moolah = self._moolah(candles, support, resistance)
        if moolah.direction != Direction.NEUTRAL:
            return moolah

        last_kiss = self._last_kiss(candles)
        if last_kiss.direction != Direction.NEUTRAL:
            return last_kiss

        return UPASSetupCandidate("None", Direction.NEUTRAL, None, None, None, "", "H4 has no valid UPAS setup.")

    def _kangaroo_tail(self, candle: Candle, support: float, resistance: float) -> UPASSetupCandidate:
        if candle.range <= 0:
            return UPASSetupCandidate("None", Direction.NEUTRAL, None, None, None, "", "")
        if candle.low < support and candle.close > support and candle.lower_wick / candle.range >= 0.55:
            entry = candle.high
            stop = candle.low
            return UPASSetupCandidate("Kangaroo Tail", Direction.BULLISH, entry, stop, entry + 2 * (entry - stop), "Below rejection wick.", "Bullish tail sweeps support and closes back above it.")
        if candle.high > resistance and candle.close < resistance and candle.upper_wick / candle.range >= 0.55:
            entry = candle.low
            stop = candle.high
            return UPASSetupCandidate("Kangaroo Tail", Direction.BEARISH, entry, stop, entry - 2 * (stop - entry), "Above rejection wick.", "Bearish tail sweeps resistance and closes back below it.")
        return UPASSetupCandidate("None", Direction.NEUTRAL, None, None, None, "", "")

    def _engulfing_trap(self, previous: Candle, latest: Candle, support: float, resistance: float) -> UPASSetupCandidate:
        bullish_engulf = latest.low < support and latest.close > previous.open and latest.open < previous.close and latest.direction == Direction.BULLISH
        bearish_engulf = latest.high > resistance and latest.close < previous.open and latest.open > previous.close and latest.direction == Direction.BEARISH
        if bullish_engulf:
            entry = latest.high
            stop = latest.low
            return UPASSetupCandidate("Engulfing Trap Bar", Direction.BULLISH, entry, stop, entry + 2 * (entry - stop), "Below engulfing trap low.", "Bullish engulfing candle traps sellers below support.")
        if bearish_engulf:
            entry = latest.low
            stop = latest.high
            return UPASSetupCandidate("Engulfing Trap Bar", Direction.BEARISH, entry, stop, entry - 2 * (stop - entry), "Above engulfing trap high.", "Bearish engulfing candle traps buyers above resistance.")
        return UPASSetupCandidate("None", Direction.NEUTRAL, None, None, None, "", "")

    def _moolah(self, candles: list[Candle], support: float, resistance: float) -> UPASSetupCandidate:
        second = candles[-1]
        first = candles[-5]
        tolerance = max(mean(c.range for c in candles[-8:]) * 0.35, 1.0)
        if abs(first.low - second.low) <= tolerance and second.low <= first.low and second.direction == Direction.BULLISH:
            entry = second.high
            stop = second.low
            return UPASSetupCandidate("Moolah", Direction.BULLISH, entry, stop, entry + 2 * (entry - stop), "Below second bottom.", "Second low sweeps/retests first low and rejects.")
        if abs(first.high - second.high) <= tolerance and second.high >= first.high and second.direction == Direction.BEARISH:
            entry = second.low
            stop = second.high
            return UPASSetupCandidate("Moolah", Direction.BEARISH, entry, stop, entry - 2 * (stop - entry), "Above second top.", "Second high sweeps/retests first high and rejects.")
        return UPASSetupCandidate("None", Direction.NEUTRAL, None, None, None, "", "")

    def _last_kiss(self, candles: list[Candle]) -> UPASSetupCandidate:
        if len(candles) < 10:
            return UPASSetupCandidate("None", Direction.NEUTRAL, None, None, None, "", "")
        prior = candles[-10:-5]
        breakout = candles[-5]
        retest = candles[-1]
        resistance = max(c.high for c in prior)
        support = min(c.low for c in prior)
        tolerance = max(mean(c.range for c in candles[-10:]) * 0.35, 1.0)
        if breakout.close > resistance and retest.low <= resistance + tolerance and retest.close > resistance and retest.direction == Direction.BULLISH:
            entry = retest.high
            stop = retest.low
            return UPASSetupCandidate("Last Kiss", Direction.BULLISH, entry, stop, entry + 2 * (entry - stop), "Below retest support.", "Resistance broke and retested as support.")
        if breakout.close < support and retest.high >= support - tolerance and retest.close < support and retest.direction == Direction.BEARISH:
            entry = retest.low
            stop = retest.high
            return UPASSetupCandidate("Last Kiss", Direction.BEARISH, entry, stop, entry - 2 * (stop - entry), "Above retest resistance.", "Support broke and retested as resistance.")
        return UPASSetupCandidate("None", Direction.NEUTRAL, None, None, None, "", "")

    def _h1_confirms(self, h1: OHLCVData, direction: Direction) -> tuple[bool, str]:
        if direction == Direction.NEUTRAL:
            return False, "No H4 UPAS direction to confirm."
        latest = h1.candles[-1]
        prior = h1.candles[-6:-1]
        if direction == Direction.BULLISH:
            broke = latest.close > max(c.high for c in prior)
            strong = latest.direction == Direction.BULLISH and latest.body / latest.range >= 0.45 if latest.range else False
            return broke and strong, "H1 breaks minor structure with a strong bullish close." if broke and strong else "H1 confirmation is missing."
        broke = latest.close < min(c.low for c in prior)
        strong = latest.direction == Direction.BEARISH and latest.body / latest.range >= 0.45 if latest.range else False
        return broke and strong, "H1 breaks minor structure with a strong bearish close." if broke and strong else "H1 confirmation is missing."

    def _near_support_resistance(self, data: UPASInput) -> tuple[bool, str]:
        price = data.h4.candles[-1].close
        zones = []
        for tf in [data.mn1, data.w1, data.d1, data.h4]:
            recent = tf.candles[-8:]
            zones.extend([min(c.low for c in recent), max(c.high for c in recent)])
        avg_range = mean(c.range for c in data.h4.candles[-8:])
        nearest = min(abs(price - zone) for zone in zones)
        passed = nearest <= avg_range * 1.5
        reason = "Price is near a valid support/resistance zone." if passed else "Price is not near valid support/resistance."
        return passed, reason

    def _trend_alignment_ok(self, biases: dict[str, Direction], direction: Direction) -> tuple[bool, str]:
        if direction == Direction.NEUTRAL:
            return False, "No UPAS setup direction."
        opposing = Direction.BEARISH if direction == Direction.BULLISH else Direction.BULLISH
        if biases["W1"] == direction and biases["D1"] == direction and biases["H4"] == direction:
            return True, "W1, D1, and H4 agree."
        if biases["W1"] == Direction.NEUTRAL and biases["D1"] == direction and biases["H4"] == direction:
            return True, "D1 and H4 agree while W1 is neutral."
        if biases["W1"] == opposing and biases["D1"] == opposing:
            return False, "Setup trades directly into strong higher-timeframe momentum."
        return False, "W1/D1/H4 trend conflict is too strong."

    def _rejection_ok(self, h4: OHLCVData, direction: Direction) -> tuple[bool, str]:
        latest = h4.candles[-1]
        if latest.range <= 0:
            return False, "Latest H4 candle has no usable range."
        if direction == Direction.BULLISH:
            passed = latest.lower_wick / latest.range >= 0.35 and latest.close > latest.open
            return passed, "Bullish rejection candle confirms the level." if passed else "Bullish rejection candle is missing."
        if direction == Direction.BEARISH:
            passed = latest.upper_wick / latest.range >= 0.35 and latest.close < latest.open
            return passed, "Bearish rejection candle confirms the level." if passed else "Bearish rejection candle is missing."
        return False, "No rejection candle because no UPAS setup direction was detected."

    def _risk_plan(self, data: UPASInput, setup: UPASSetupCandidate) -> dict[str, Any]:
        risk_amount = data.account_balance * self.RISK_PERCENT / 100
        plan = {
            "entry": setup.entry,
            "stop_loss": setup.stop_loss,
            "take_profit": setup.take_profit,
            "risk_points": None,
            "reward_points": None,
            "reward_risk_ratio": None,
            "risk_amount_usd": risk_amount,
            "lot_size": None,
            "daily_drawdown_after_trade_percent": None,
        }
        if setup.entry is None or setup.stop_loss is None or setup.take_profit is None:
            return plan
        risk_points = abs(setup.entry - setup.stop_loss)
        reward_points = abs(setup.take_profit - setup.entry)
        if risk_points <= 0:
            return plan
        plan["risk_points"] = round(risk_points, 3)
        plan["reward_points"] = round(reward_points, 3)
        plan["reward_risk_ratio"] = round(reward_points / risk_points, 2)
        plan["lot_size"] = round(risk_amount / (risk_points * self.CONTRACT_VALUE_PER_LOT), 2)
        plan["daily_drawdown_after_trade_percent"] = round((data.current_daily_loss + risk_amount) / data.account_balance * 100, 2)
        return plan

    def _direction_text(self, direction: Direction) -> str:
        if direction == Direction.BULLISH:
            return "BUY"
        if direction == Direction.BEARISH:
            return "SELL"
        return "NONE"
