from __future__ import annotations

from smart_system_a.models import AccountSettings, Direction, RiskSettings
from smart_system_a.risk_calculator import RiskCalculator


def test_buy_sl_tp_calculation() -> None:
    setup = RiskCalculator().calculate(
        Direction.BULLISH,
        4165,
        AccountSettings(100000),
        RiskSettings(),
        "Standard",
        "test",
    )
    assert setup.sl == 4125
    assert setup.tp1 == 4205
    assert setup.tp2 == 4245


def test_sell_sl_tp_calculation() -> None:
    setup = RiskCalculator().calculate(
        Direction.BEARISH,
        4165,
        AccountSettings(100000),
        RiskSettings(),
        "Standard",
        "test",
    )
    assert setup.sl == 4205
    assert setup.tp1 == 4125
    assert setup.tp2 == 4085


def test_lot_size_calculation() -> None:
    setup = RiskCalculator().calculate(
        Direction.BULLISH,
        4165,
        AccountSettings(100000),
        RiskSettings(risk_percent=0.9),
        "Standard",
        "test",
    )
    assert setup.risk_amount == 900
    assert setup.lot_size == 0.225
