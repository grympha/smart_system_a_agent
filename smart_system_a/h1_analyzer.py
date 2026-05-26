from __future__ import annotations

from .models import Direction, H1AnalysisResult, OHLCVData
from .structure_detector import StructureDetector
from .volume_validator import VolumeValidator


class H1Analyzer:
    def __init__(
        self,
        structure_detector: StructureDetector | None = None,
        volume_validator: VolumeValidator | None = None,
    ) -> None:
        self.structure_detector = structure_detector or StructureDetector()
        self.volume_validator = volume_validator or VolumeValidator()

    def analyze(self, data: OHLCVData, expected_direction: Direction) -> H1AnalysisResult:
        candles = data.candles
        bos_direction, bos_level, _ = self.structure_detector.detect_bos(candles[:-4], expected_direction, lookback=7) if len(candles) >= 13 else (Direction.NEUTRAL, None, None)
        breakout_slice = candles[:-4]
        clean = self.structure_detector.is_clean_breakout(breakout_slice, bos_level, expected_direction)
        pullback_ok, entry_zone = self.structure_detector.pullback_holds(candles, bos_level, expected_direction)
        candle_ok = self.structure_detector.candle_confirms_from_zone(candles, expected_direction)
        volume_ok = self.volume_validator.impulse_beats_pullback(candles[-8:-4], candles[-4:-1], expected_direction)

        reasons: list[str] = []
        if bos_direction != expected_direction:
            reasons.append("H1 BOS is not aligned with H4 trend.")
        if not clean:
            reasons.append("H1 breakout is weak, wicky, or unclear.")
        if not pullback_ok:
            reasons.append("Pullback does not reach or hold valid SSA retest zone.")
        if not candle_ok:
            reasons.append("Candle behavior shows compression instead of rejection.")
        if volume_ok is None:
            reasons.append(VolumeValidator.missing_message)
        elif not volume_ok:
            reasons.append("Volume does not support the trade direction.")

        return H1AnalysisResult(
            bos_direction=bos_direction,
            bos_level=bos_level,
            breakout_strength="clean" if clean else "weak",
            pullback_zone_reached=pullback_ok,
            candle_confirmation=candle_ok,
            volume_confirmation=volume_ok,
            entry_zone=entry_zone,
            reasons=reasons,
        )
