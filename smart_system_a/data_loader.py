from __future__ import annotations

import csv
from pathlib import Path
from typing import TextIO

from .models import Candle, OHLCVData


class DataLoader:
    REQUIRED_COLUMNS = {"timestamp", "open", "high", "low", "close", "volume"}

    def load_csv(self, path: str | Path, timeframe: str, symbol: str = "XAUUSD") -> OHLCVData:
        csv_path = Path(path)
        with csv_path.open("r", newline="", encoding="utf-8") as handle:
            return self.load_csv_stream(handle, timeframe, symbol)

    def load_csv_stream(self, stream: TextIO, timeframe: str, symbol: str = "XAUUSD") -> OHLCVData:
        reader = csv.DictReader(stream)
        missing = self.REQUIRED_COLUMNS.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV missing required columns: {', '.join(sorted(missing))}")

        candles = []
        for row in reader:
            raw_volume = (row.get("volume") or "").strip()
            candles.append(
                Candle(
                    timestamp=row["timestamp"],
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(raw_volume) if raw_volume else None,
                )
            )

        if len(candles) < 10:
            raise ValueError("SSA analysis requires at least 10 candles per timeframe.")
        return OHLCVData(candles=candles, timeframe=timeframe, symbol=symbol)
