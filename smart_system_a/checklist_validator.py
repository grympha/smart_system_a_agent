from __future__ import annotations

from .models import Direction, H1AnalysisResult, H4AnalysisResult, ChecklistResult, RiskSettings


class ChecklistValidator:
    RULES = {
        "h4": "H4 trend aligned",
        "wave": "Correct Elliott Wave position, preferably Wave 3 or Wave 5 continuation",
        "breakout": "Clean H1 breakout structure",
        "pullback": "Pullback reaches the correct SSA zone",
        "candle": "Valid candle confirmation or rejection behavior",
        "volume": "Volume supports direction",
    }

    def validate(
        self,
        h4: H4AnalysisResult,
        h1: H1AnalysisResult,
        expected_direction: Direction,
        settings: RiskSettings | None = None,
    ) -> ChecklistResult:
        settings = settings or RiskSettings()
        c1 = h4.trend == expected_direction and h1.bos_direction == expected_direction
        c2 = h4.valid_for_continuation and h4.active_wave in {3, 5}
        c3 = h1.breakout_strength == "clean"
        c4 = h1.pullback_zone_reached
        c5 = h1.candle_confirmation
        c6 = h1.volume_confirmation is True or settings.volume_override

        failed = []
        if not c1:
            failed.append(self.RULES["h4"])
        if not c2:
            failed.append(self.RULES["wave"])
        if not c3:
            failed.append(self.RULES["breakout"])
        if not c4:
            failed.append(self.RULES["pullback"])
        if not c5:
            failed.append(self.RULES["candle"])
        if not c6:
            failed.append(self.RULES["volume"])

        passed = all([c1, c2, c3, c4, c5, c6])
        return ChecklistResult(c1, c2, c3, c4, c5, c6, passed, failed)
