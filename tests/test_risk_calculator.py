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
    assert setup.sl == 4155
    assert setup.tp1 == 4175
    assert setup.tp2 == 4185


def test_sell_sl_tp_calculation() -> None:
    setup = RiskCalculator().calculate(
        Direction.BEARISH,
        4165,
        AccountSettings(100000),
        RiskSettings(),
        "Standard",
        "test",
    )
    assert setup.sl == 4175
    assert setup.tp1 == 4155
    assert setup.tp2 == 4145


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
    assert setup.lot_size == 0.9
