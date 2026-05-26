from __future__ import annotations

from smart_system_a.checklist_validator import ChecklistValidator
from smart_system_a.models import Direction, H1AnalysisResult, H4AnalysisResult, MarketState, RiskSettings


def test_if_one_condition_fails_passed_is_false() -> None:
    h4 = H4AnalysisResult(Direction.BULLISH, "Wave 3 likely", 3, MarketState.EXPANDING, 2.0, 0.2, "discount", True, [])
    h1 = H1AnalysisResult(Direction.BULLISH, 4125, "weak", True, True, True, 4125, [])

    result = ChecklistValidator().validate(h4, h1, Direction.BULLISH, RiskSettings())

    assert result.passed is False
    assert "Clean H1 breakout structure" in result.failed_rules
