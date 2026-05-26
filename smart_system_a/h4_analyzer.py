from __future__ import annotations

from statistics import mean

from .models import Direction, H4AnalysisResult, OHLCVData
from .wave_detector import WaveDetector


class H4Analyzer:
    def __init__(self, wave_detector: WaveDetector | None = None) -> None:
        self.wave_detector = wave_detector or WaveDetector()

    def analyze(self, data: OHLCVData) -> H4AnalysisResult:
        candles = data.candles
        recent = candles[-8:]
        closes = [c.close for c in recent]
        ranges = [c.high - c.low for c in recent]
        if closes[-1] > closes[0] and mean(ranges[-4:]) >= mean(ranges[:4]) * 0.85:
            trend = Direction.BULLISH
            zone = "discount"
        elif closes[-1] < closes[0] and mean(ranges[-4:]) >= mean(ranges[:4]) * 0.85:
            trend = Direction.BEARISH
            zone = "premium"
        else:
            trend = Direction.NEUTRAL
            zone = "none"

        wave_context, active_wave, market_state, impulse, correction, valid, reasons = self.wave_detector.detect(data, trend)
        if trend == Direction.BULLISH:
            reasons.insert(0, "H4 trend is bullish; SSA looks for BUY setups from discount zones.")
        elif trend == Direction.BEARISH:
            reasons.insert(0, "H4 trend is bearish; SSA looks for SELL setups from premium zones.")
        else:
            reasons.insert(0, "H4 trend is unclear.")
        return H4AnalysisResult(
            trend=trend,
            wave_context=wave_context,
            active_wave=active_wave,
            market_state=market_state,
            impulse_strength=impulse,
            correction_strength=correction,
            premium_discount_zone=zone,
            valid_for_continuation=valid,
            reasons=reasons,
        )
