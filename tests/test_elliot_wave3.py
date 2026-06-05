from __future__ import annotations

from io import StringIO

from elliot_wave3 import ElliotWave3Analyzer
from smart_system_a.data_loader import DataLoader
from templates import elliot_wave3_template_csv


def test_elliot_wave3_template_scores_valid_trade() -> None:
    multi = DataLoader().load_multi_timeframe_csv_stream(StringIO(elliot_wave3_template_csv()), "XAUUSD")

    result = ElliotWave3Analyzer().analyze(symbol="XAUUSD", h4=multi["H4"], h1=multi["H1"], m15=multi["M15"])

    assert result.status == "VALID_TRADE"
    assert result.direction == "BUY"
    assert result.score >= 85
    assert result.entry is not None
    assert result.stop_loss is not None
    assert result.take_profit is not None
    assert result.stop_loss < result.entry < result.take_profit
    assert result.wave2_retracement is not None
    assert 38.2 <= result.wave2_retracement <= 61.8
    assert result.wave3_projection is not None
    assert result.wave3_projection >= 1.272


def test_elliot_wave3_rejects_missing_m15_volume() -> None:
    text = elliot_wave3_template_csv().replace(",1800\n", ",\n")
    multi = DataLoader().load_multi_timeframe_csv_stream(StringIO(text), "XAUUSD")

    result = ElliotWave3Analyzer().analyze(symbol="XAUUSD", h4=multi["H4"], h1=multi["H1"], m15=multi["M15"])

    assert result.status == "NO_TRADE"
    assert result.score < 100
    assert result.checklist["volume_confirmation"]["passed"] is False
