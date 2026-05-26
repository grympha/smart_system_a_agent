from __future__ import annotations

import csv
from pathlib import Path
from typing import TextIO

from .models import Candle, OHLCVData


class DataLoader:
    REQUIRED_COLUMNS = {"timestamp", "open", "high", "low", "close", "volume"}
    MULTI_TIMEFRAME_REQUIRED_COLUMNS = REQUIRED_COLUMNS | {"timeframe"}

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

    def load_multi_timeframe_csv_stream(self, stream: TextIO, symbol: str = "XAUUSD") -> dict[str, OHLCVData]:
        reader = csv.DictReader(stream)
        missing = self.MULTI_TIMEFRAME_REQUIRED_COLUMNS.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Multi-timeframe CSV missing required columns: {', '.join(sorted(missing))}")

        candles_by_timeframe: dict[str, list[Candle]] = {}
        for row in reader:
            timeframe = row["timeframe"].strip().upper()
            raw_volume = (row.get("volume") or "").strip()
            candles_by_timeframe.setdefault(timeframe, []).append(
                Candle(
                    timestamp=row["timestamp"],
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(raw_volume) if raw_volume else None,
                )
            )

        data = {
            timeframe: OHLCVData(candles=candles, timeframe=timeframe, symbol=symbol)
            for timeframe, candles in candles_by_timeframe.items()
        }
        for timeframe, ohlcv in data.items():
            if len(ohlcv.candles) < 10:
                raise ValueError(f"{timeframe} requires at least 10 candles.")
        return data
