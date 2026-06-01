from __future__ import annotations

from smart_system_a.agent import SmartSystemAAgent
from smart_system_a.models import AccountSettings, RiskSettings, TradeSetup


def test_valid_buy_setup(bullish_h4, bullish_h1) -> None:
    result = SmartSystemAAgent().analyze(bullish_h4(), bullish_h1(), AccountSettings(100000), RiskSettings(risk_mode="high_confidence"))

    assert isinstance(result, TradeSetup)
    assert result.setup_type == "BUY LIMIT"
    assert result.entry == 4125
    assert result.sl == 4115
    assert result.tp1 == 4135
    assert result.tp2 == 4145
    assert result.risk_percent == 1.2
    assert result.confidence_level == "High"
