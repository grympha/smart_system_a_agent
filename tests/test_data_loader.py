from __future__ import annotations

from io import StringIO

from smart_system_a.data_loader import DataLoader


def test_load_multi_timeframe_csv_stream() -> None:
    rows = ["timeframe,timestamp,open,high,low,close,volume"]
    for timeframe in ["H4", "H1"]:
        for idx in range(10):
            rows.append(f"{timeframe},{idx},100,105,99,104,1000")

    data = DataLoader().load_multi_timeframe_csv_stream(StringIO("\n".join(rows)), "XAUUSD")

    assert set(data) == {"H4", "H1"}
    assert len(data["H4"].candles) == 10
    assert data["H1"].symbol == "XAUUSD"
