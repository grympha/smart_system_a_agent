from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Direction(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class MarketState(str, Enum):
    EXPANDING = "expanding"
    CORRECTING = "correcting"
    RANGING = "ranging"


@dataclass(frozen=True)
class Candle:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None

    @property
    def body(self) -> float:
        return abs(self.close - self.open)

    @property
    def range(self) -> float:
        return max(self.high - self.low, 0.0)

    @property
    def direction(self) -> Direction:
        if self.close > self.open:
            return Direction.BULLISH
        if self.close < self.open:
            return Direction.BEARISH
        return Direction.NEUTRAL

    @property
    def upper_wick(self) -> float:
        return self.high - max(self.open, self.close)

    @property
    def lower_wick(self) -> float:
        return min(self.open, self.close) - self.low

    @property
    def has_volume(self) -> bool:
        return self.volume is not None


@dataclass(frozen=True)
class OHLCVData:
    candles: list[Candle]
    timeframe: str
    symbol: str = "XAUUSD"

    def recent(self, count: int) -> list[Candle]:
        return self.candles[-count:]

    @property
    def has_volume(self) -> bool:
        return bool(self.candles) and all(c.volume is not None for c in self.candles)


@dataclass(frozen=True)
class H4AnalysisResult:
    trend: Direction
    wave_context: str
    active_wave: Optional[int]
    market_state: MarketState
    impulse_strength: float
    correction_strength: float
    premium_discount_zone: str
    valid_for_continuation: bool
    reasons: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class H1AnalysisResult:
    bos_direction: Direction
    bos_level: Optional[float]
    breakout_strength: str
    pullback_zone_reached: bool
    candle_confirmation: bool
    volume_confirmation: Optional[bool]
    entry_zone: Optional[float]
    reasons: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ChecklistResult:
    condition_1_h4_trend_aligned: bool
    condition_2_wave_position_correct: bool
    condition_3_clean_breakout: bool
    condition_4_pullback_reaches_zone: bool
    condition_5_valid_candle_behavior: bool
    condition_6_volume_supports_direction: bool
    passed: bool
    failed_rules: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RiskSettings:
    sl_pips: float = 40.0
    risk_percent: float = 0.9
    risk_mode: str = "standard"
    volume_override: bool = False


@dataclass(frozen=True)
class AccountSettings:
    balance: float


@dataclass(frozen=True)
class TradeSetup:
    setup_type: str
    entry: float
    sl: float
    tp1: float
    tp2: float
    pip_distance: float
    risk_percent: float
    risk_amount: float
    lot_size: float
    confidence_level: str
    reasoning_summary: str


@dataclass(frozen=True)
class NoSetupResult:
    failed_rules: list[str]
    h4_wave_position: str
    active_wave: Optional[int]
    market_state: MarketState
    what_next: str
    reasoning_summary: str


@dataclass(frozen=True)
class AnalysisSnapshot:
    h4: H4AnalysisResult
    h1: H1AnalysisResult
    checklist: ChecklistResult
    result: TradeSetup | NoSetupResult
