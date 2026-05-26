from __future__ import annotations

from statistics import mean

from .models import Direction, MarketState, OHLCVData
from .volume_validator import VolumeValidator


class WaveDetector:
    def __init__(self, volume_validator: VolumeValidator | None = None) -> None:
        self.volume_validator = volume_validator or VolumeValidator()

    def detect(self, data: OHLCVData, trend: Direction) -> tuple[str, int | None, MarketState, float, float, bool, list[str]]:
        candles = data.candles
        recent = candles[-8:]
        prior = candles[-16:-8] if len(candles) >= 16 else candles[:-8]
        reasons: list[str] = []
        if trend == Direction.NEUTRAL:
            return "Wave unclear", None, MarketState.RANGING, 0.0, 0.0, False, ["H4 trend is unclear."]

        avg_recent_body = mean(c.body for c in recent)
        avg_prior_body = mean(c.body for c in prior) if prior else avg_recent_body
        directional_count = sum(1 for c in recent if c.direction == trend)
        overlap_count = sum(1 for idx in range(1, len(recent)) if recent[idx].low <= recent[idx - 1].high and recent[idx].high >= recent[idx - 1].low)
        impulse_strength = directional_count / len(recent) + (avg_recent_body / avg_prior_body if avg_prior_body else 1.0)
        correction_strength = overlap_count / max(len(recent) - 1, 1)

        volume_supported = self.volume_validator.impulse_beats_pullback(recent[-4:], recent[:4], trend)
        if volume_supported is None:
            reasons.append(VolumeValidator.missing_message)

        if correction_strength > 0.85 and impulse_strength < 1.55:
            return "Ranging", None, MarketState.RANGING, impulse_strength, correction_strength, False, reasons + ["H4 market is ranging."]

        if directional_count >= 6 and impulse_strength >= 1.55 and volume_supported is not False:
            if avg_recent_body >= avg_prior_body * 1.35:
                return "Wave 3 likely", 3, MarketState.EXPANDING, impulse_strength, correction_strength, True, reasons + ["Strong H4 displacement supports Wave 3 continuation."]
            return "Wave 5 likely", 5, MarketState.EXPANDING, impulse_strength, correction_strength, True, reasons + ["H4 continuation remains impulsive but is weaker than Wave 3."]

        if correction_strength >= 0.65 or directional_count <= 4:
            return "Correction likely", None, MarketState.CORRECTING, impulse_strength, correction_strength, False, reasons + ["H4 overlapping candles indicate correction rather than impulse."]

        return "Wave unclear", None, MarketState.CORRECTING, impulse_strength, correction_strength, False, reasons + ["H4 wave count is unclear."]
