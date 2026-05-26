from __future__ import annotations

from smart_system_a.agent import SmartSystemAAgent
from smart_system_a.models import AccountSettings, RiskSettings, TradeSetup


def test_valid_sell_setup(bearish_h4, bearish_h1) -> None:
    result = SmartSystemAAgent().analyze(bearish_h4(), bearish_h1(), AccountSettings(100000), RiskSettings())

    assert isinstance(result, TradeSetup)
    assert result.setup_type == "SELL LIMIT"
    assert result.entry == 4175
    assert result.sl == 4215
    assert result.tp1 == 4135
    assert result.tp2 == 4095
    assert result.risk_percent == 0.9
