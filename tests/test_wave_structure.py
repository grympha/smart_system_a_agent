from __future__ import annotations

from smart_system_a.models import Candle, OHLCVData
from wave_structure import WaveAnalysisInput, WaveStructureAnalyst


def c(idx: int, open_: float, high: float, low: float, close: float) -> Candle:
    return Candle(f"2026-01-01 {idx:02d}:00", open_, high, low, close, 1000)


def bullish_wave3_data() -> OHLCVData:
    candles = [
        c(0, 4000, 4014, 3995, 4010),
        c(1, 4010, 4026, 4008, 4022),
        c(2, 4022, 4040, 4020, 4036),
        c(3, 4036, 4056, 4034, 4052),
        c(4, 4052, 4074, 4050, 4070),
        c(5, 4070, 4082, 4064, 4078),
        c(6, 4078, 4080, 4058, 4062),
        c(7, 4062, 4070, 4048, 4052),
        c(8, 4052, 4062, 4046, 4058),
        c(9, 4058, 4090, 4056, 4088),
        c(10, 4088, 4118, 4077, 4110),
        c(11, 4110, 4140, 4108, 4134),
    ]
    return OHLCVData(candles, "H4")


def overlapping_correction_data() -> OHLCVData:
    candles = [
        c(0, 4100, 4110, 4090, 4108),
        c(1, 4108, 4112, 4095, 4100),
        c(2, 4100, 4108, 4092, 4104),
        c(3, 4104, 4110, 4097, 4102),
        c(4, 4102, 4107, 4094, 4098),
        c(5, 4098, 4106, 4090, 4101),
        c(6, 4101, 4105, 4093, 4099),
        c(7, 4099, 4104, 4091, 4097),
        c(8, 4097, 4102, 4089, 4095),
        c(9, 4095, 4100, 4088, 4094),
    ]
    return OHLCVData(candles, "H4")


def test_bullish_wave3_scores_strong_confirmation() -> None:
    data = bullish_wave3_data()
    result = WaveStructureAnalyst().analyze(
        WaveAnalysisInput(
            symbol="XAUUSD",
            timeframe="H4",
            primary_data=data,
            current_price=4134,
            breakout_level=4082,
            retest_level=4082,
            trend_direction="bullish",
        )
    )

    assert result.primary_scenario == "Wave 3 Continuation"
    assert result.trading_bias == "BUY"
    assert result.wave_score >= 8
    assert result.entry_zone == 4082


def test_unclear_or_corrective_structure_returns_wait() -> None:
    data = overlapping_correction_data()
    result = WaveStructureAnalyst().analyze(
        WaveAnalysisInput(symbol="XAUUSD", timeframe="H4", primary_data=data, trend_direction="neutral")
    )

    assert result.trading_bias == "WAIT"
    assert result.primary_scenario in {"ABC Correction", "Unknown"}
    assert result.wave_score <= 5


def test_bearish_wave_rejects_wide_old_swing_as_retest_zone() -> None:
    candles = [
        c(0, 4540, 4560, 4500, 4510),
        c(1, 4510, 4520, 4420, 4430),
        c(2, 4430, 4460, 4366.25, 4380),
        c(3, 4380, 4400, 4360, 4370),
        c(4, 4370, 4380, 4340, 4350),
        c(5, 4350, 4545.98, 4300, 4310),
        c(6, 4310, 4330, 4260, 4270),
        c(7, 4270, 4290, 4220, 4230),
        c(8, 4230, 4250, 4180, 4190),
        c(9, 4190, 4210, 4140, 4150),
        c(10, 4150, 4170, 4100, 4110),
        c(11, 4110, 4130, 4060, 4070),
    ]
    result = WaveStructureAnalyst().analyze(
        WaveAnalysisInput(
            symbol="XAUUSD",
            timeframe="H4",
            primary_data=OHLCVData(candles, "H4"),
            current_price=4070,
            breakout_level=4366.25,
            retest_level=4366.25,
            trend_direction="bearish",
        )
    )

    assert result.status != "WAVE_CONFIRMED"
    assert result.entry_zone is None
    assert "Retest / pullback confirmed" in result.failed_rules


def test_bearish_wave_rejects_sell_retest_below_current_price() -> None:
    candles = [
        c(0, 4540, 4560, 4520, 4530),
        c(1, 4530, 4540, 4490, 4500),
        c(2, 4500, 4510, 4440, 4450),
        c(3, 4450, 4460, 4420, 4430),
        c(4, 4430, 4458, 4400, 4410),
        c(5, 4410, 4447, 4390, 4400),
        c(6, 4400, 4420, 4380, 4390),
        c(7, 4390, 4410, 4370, 4380),
        c(8, 4380, 4400, 4360, 4370),
        c(9, 4370, 4390, 4350, 4360),
    ]
    result = WaveStructureAnalyst().analyze(
        WaveAnalysisInput(
            symbol="XAUUSD",
            timeframe="H4",
            primary_data=OHLCVData(candles, "H4"),
            current_price=4532.9,
            breakout_level=4447.34,
            retest_level=4447.34,
            trend_direction="bearish",
        )
    )

    assert result.trading_bias == "WAIT"
    assert result.status != "WAVE_CONFIRMED"
    assert result.entry_zone is None
    assert "retest" in " ".join(result.failed_rules).lower()
