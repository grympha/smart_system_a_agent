from __future__ import annotations

from .checklist_validator import ChecklistValidator
from .data_loader import DataLoader
from .h1_analyzer import H1Analyzer
from .h4_analyzer import H4Analyzer
from .models import AccountSettings, Direction, NoSetupResult, OHLCVData, RiskSettings, TradeSetup
from .output_formatter import OutputFormatter
from .risk_calculator import RiskCalculator


class SmartSystemAAgent:
    def __init__(
        self,
        h4_analyzer: H4Analyzer | None = None,
        h1_analyzer: H1Analyzer | None = None,
        checklist_validator: ChecklistValidator | None = None,
        risk_calculator: RiskCalculator | None = None,
    ) -> None:
        self.h4_analyzer = h4_analyzer or H4Analyzer()
        self.h1_analyzer = h1_analyzer or H1Analyzer()
        self.checklist_validator = checklist_validator or ChecklistValidator()
        self.risk_calculator = risk_calculator or RiskCalculator()
        self.formatter = OutputFormatter()
        self.loader = DataLoader()

    def analyze_csv(
        self,
        h4_path: str,
        h1_path: str,
        balance: float,
        risk_mode: str = "standard",
        symbol: str = "XAUUSD",
        risk_percent: float | None = None,
        volume_override: bool = False,
    ) -> TradeSetup | NoSetupResult:
        h4 = self.loader.load_csv(h4_path, "H4", symbol)
        h1 = self.loader.load_csv(h1_path, "H1", symbol)
        settings = RiskSettings(risk_mode=risk_mode, risk_percent=risk_percent or 0.9, volume_override=volume_override)
        return self.analyze(h4, h1, AccountSettings(balance=balance), settings)

    def analyze(
        self,
        h4_data: OHLCVData,
        h1_data: OHLCVData,
        account: AccountSettings,
        settings: RiskSettings | None = None,
    ) -> TradeSetup | NoSetupResult:
        settings = settings or RiskSettings()
        h4 = self.h4_analyzer.analyze(h4_data)
        expected = h4.trend if h4.trend in {Direction.BULLISH, Direction.BEARISH} else Direction.NEUTRAL
        h1 = self.h1_analyzer.analyze(h1_data, expected)
        checklist = self.checklist_validator.validate(h4, h1, expected, settings)

        reasoning = self._reasoning_summary(h4, h1, checklist.passed)
        if not checklist.passed:
            return NoSetupResult(
                failed_rules=checklist.failed_rules,
                h4_wave_position=h4.wave_context,
                active_wave=h4.active_wave,
                market_state=h4.market_state,
                what_next=self._what_next(checklist.failed_rules, h4.trend),
                reasoning_summary=reasoning,
            )

        confidence = self._confidence(h4, h1)
        setup_type = "BUY LIMIT" if expected == Direction.BULLISH else "SELL LIMIT"
        entry = h1.entry_zone if h1.entry_zone is not None else h1_data.candles[-1].close
        return self.risk_calculator.calculate(
            direction=expected,
            entry=entry,
            account=account,
            settings=settings,
            confidence_level=confidence,
            reasoning_summary=reasoning,
            setup_type=setup_type,
            is_wave_3_continuation=h4.active_wave == 3,
        )

    def format_result(self, result: TradeSetup | NoSetupResult) -> str:
        if isinstance(result, TradeSetup):
            return self.formatter.format_trade(result)
        return self.formatter.format_no_setup(result)

    def _confidence(self, h4, h1) -> str:
        if (
            h4.active_wave == 3
            and h4.valid_for_continuation
            and h1.breakout_strength == "clean"
            and h1.pullback_zone_reached
            and h1.candle_confirmation
            and h1.volume_confirmation is True
        ):
            return "High"
        return "Standard"

    def _reasoning_summary(self, h4, h1, passed: bool) -> str:
        verdict = "all six SSA conditions passed" if passed else "one or more SSA conditions failed"
        return (
            f"H4 wave position: {h4.wave_context}; active wave: {h4.active_wave or 'unidentifiable'}; "
            f"market state: {h4.market_state.value}. H1 BOS: {h1.bos_direction.value} at {h1.bos_level}; "
            f"pullback zone: {h1.entry_zone if h1.entry_zone is not None else 'not valid'}; "
            f"candle behavior: {'confirmed rejection/acceptance' if h1.candle_confirmation else 'invalid compression or no rejection'}; "
            f"volume behavior: {self._volume_text(h1.volume_confirmation)}; {verdict}."
        )

    def _volume_text(self, volume_confirmation: bool | None) -> str:
        if volume_confirmation is True:
            return "impulse volume exceeds pullback volume"
        if volume_confirmation is False:
            return "volume does not support direction"
        return "Volume analysis limited - OHLCV volume data missing"

    def _what_next(self, failed_rules: list[str], trend: Direction) -> str:
        direction_text = "BUY" if trend == Direction.BULLISH else "SELL" if trend == Direction.BEARISH else "directional"
        return (
            f"Wait for a clear H4 Wave 3 or Wave 5 continuation, clean H1 BOS, valid retest zone, "
            f"rejection candle, and volume expansion supporting the {direction_text} direction."
        )
