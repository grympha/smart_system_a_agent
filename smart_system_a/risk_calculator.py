from __future__ import annotations

from .models import AccountSettings, Direction, RiskSettings, TradeSetup


class RiskCalculator:
    PIP_SIZE = 1.0
    XAUUSD_DOLLARS_PER_PIP_PER_LOT = 100.0

    def resolve_risk_percent(self, settings: RiskSettings, is_wave_3_continuation: bool) -> float:
        if settings.risk_percent != 0.9:
            return settings.risk_percent
        if settings.risk_mode == "high_confidence" and is_wave_3_continuation:
            return 1.2
        return 0.9

    def calculate(
        self,
        direction: Direction,
        entry: float,
        account: AccountSettings,
        settings: RiskSettings,
        confidence_level: str,
        reasoning_summary: str,
        setup_type: str = "MARKET",
        is_wave_3_continuation: bool = False,
    ) -> TradeSetup:
        risk_percent = self.resolve_risk_percent(settings, is_wave_3_continuation)
        sl_pips = settings.sl_pips
        risk_amount = account.balance * risk_percent / 100
        lot_size = risk_amount / (sl_pips * self.XAUUSD_DOLLARS_PER_PIP_PER_LOT)
        if direction == Direction.BULLISH:
            sl = entry - sl_pips * self.PIP_SIZE
            tp1 = entry + sl_pips * self.PIP_SIZE
            tp2 = entry + 2 * sl_pips * self.PIP_SIZE
        elif direction == Direction.BEARISH:
            sl = entry + sl_pips * self.PIP_SIZE
            tp1 = entry - sl_pips * self.PIP_SIZE
            tp2 = entry - 2 * sl_pips * self.PIP_SIZE
        else:
            raise ValueError("Risk calculation requires BUY or SELL direction.")
        return TradeSetup(
            setup_type=setup_type,
            entry=round(entry, 3),
            sl=round(sl, 3),
            tp1=round(tp1, 3),
            tp2=round(tp2, 3),
            pip_distance=sl_pips,
            risk_percent=risk_percent,
            risk_amount=round(risk_amount, 2),
            lot_size=round(lot_size, 3),
            confidence_level=confidence_level,
            reasoning_summary=reasoning_summary,
        )
