from __future__ import annotations

from smart_system_a.agent import SmartSystemAAgent
from smart_system_a.models import AccountSettings, NoSetupResult, RiskSettings


def test_missing_volume_fails_condition_6_unless_override_enabled(bullish_h4, bullish_h1) -> None:
    agent = SmartSystemAAgent()
    result = agent.analyze(bullish_h4(volume=False), bullish_h1(volume=False), AccountSettings(100000), RiskSettings())

    assert isinstance(result, NoSetupResult)
    assert "Volume supports direction" in result.failed_rules

    override_result = agent.analyze(
        bullish_h4(volume=False),
        bullish_h1(volume=False),
        AccountSettings(100000),
        RiskSettings(volume_override=True),
    )
    assert not isinstance(override_result, NoSetupResult)
