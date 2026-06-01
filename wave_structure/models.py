from __future__ import annotations

from dataclasses import dataclass, field

from smart_system_a.models import OHLCVData


@dataclass(frozen=True)
class WaveAnalysisInput:
    symbol: str
    timeframe: str
    primary_data: OHLCVData
    h4: OHLCVData | None = None
    h1: OHLCVData | None = None
    d1: OHLCVData | None = None
    m30: OHLCVData | None = None
    m15: OHLCVData | None = None
    current_price: float | None = None
    swing_highs: list[float] = field(default_factory=list)
    swing_lows: list[float] = field(default_factory=list)
    breakout_level: float | None = None
    retest_level: float | None = None
    trend_direction: str = "neutral"
    smart_system_a_score: str | None = None
    upas_score: str | None = None


@dataclass(frozen=True)
class WaveAnalysisResult:
    symbol: str
    timeframe: str
    market_phase: str
    primary_scenario: str
    alternative_scenario: str
    direction: str
    wave_score: int
    confidence: int
    risk_level: str
    trading_bias: str
    suggested_action: str
    invalidation_level: float | None
    reason: str
    failed_rules: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.trading_bias in {"BUY", "SELL"} and self.wave_score >= 8:
            return "WAVE_CONFIRMED"
        if self.wave_score >= 6:
            return "WAIT"
        return "NO_VALID_SETUP"
