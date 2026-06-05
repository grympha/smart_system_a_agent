from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from .models import Candle, OHLCVData


class LiveDataError(RuntimeError):
    """Raised when live market data cannot be loaded."""


class TwelveDataClient:
    BASE_URL = "https://api.twelvedata.com/time_series"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("TWELVE_DATA_API_KEY")

    def fetch_ohlcv(self, symbol: str, interval: str, outputsize: int = 80) -> OHLCVData:
        if not self.api_key:
            raise LiveDataError(
                "Live data requires TWELVE_DATA_API_KEY. Add it in Render Environment variables."
            )

        params = urlencode(
            {
                "symbol": symbol,
                "interval": interval,
                "outputsize": outputsize,
                "apikey": self.api_key,
            }
        )
        try:
            with urlopen(f"{self.BASE_URL}?{params}", timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise LiveDataError(f"Live data HTTP error: {exc.code}") from exc
        except URLError as exc:
            raise LiveDataError(f"Live data connection error: {exc.reason}") from exc
        except TimeoutError as exc:
            raise LiveDataError("Live data request timed out.") from exc

        if payload.get("status") == "error":
            raise LiveDataError(f"Live data provider error: {payload.get('message', 'unknown error')}")

        values = payload.get("values")
        if not values:
            raise LiveDataError("Live data provider returned no candles.")

        candles = []
        for row in reversed(values):
            raw_volume = row.get("volume")
            candles.append(
                Candle(
                    timestamp=str(row["datetime"]),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(raw_volume) if raw_volume not in (None, "") else None,
                )
            )

        timeframe_map = {
            "1month": "MN1",
            "1week": "W1",
            "1day": "D1",
            "4h": "H4",
            "1h": "H1",
            "15min": "M15",
        }
        timeframe = timeframe_map.get(interval, interval)
        return OHLCVData(candles=candles, timeframe=timeframe, symbol=symbol)


class LiveXAUUSDFeed:
    def __init__(self, client: TwelveDataClient | None = None) -> None:
        self.client = client or TwelveDataClient()

    def fetch_h4_h1(self, symbol: str = "XAU/USD", outputsize: int = 80) -> tuple[OHLCVData, OHLCVData]:
        h4 = self.client.fetch_ohlcv(symbol, "4h", outputsize)
        h1 = self.client.fetch_ohlcv(symbol, "1h", outputsize)
        return h4, h1

    def fetch_upas(self, symbol: str = "XAU/USD", outputsize: int = 80) -> tuple[OHLCVData, OHLCVData, OHLCVData, OHLCVData, OHLCVData]:
        mn1 = self.client.fetch_ohlcv(symbol, "1month", outputsize)
        w1 = self.client.fetch_ohlcv(symbol, "1week", outputsize)
        d1 = self.client.fetch_ohlcv(symbol, "1day", outputsize)
        h4 = self.client.fetch_ohlcv(symbol, "4h", outputsize)
        h1 = self.client.fetch_ohlcv(symbol, "1h", outputsize)
        return mn1, w1, d1, h4, h1

    def fetch_elliot_wave3(self, symbol: str = "XAU/USD", outputsize: int = 120) -> tuple[OHLCVData, OHLCVData, OHLCVData]:
        h4 = self.client.fetch_ohlcv(symbol, "4h", outputsize)
        h1 = self.client.fetch_ohlcv(symbol, "1h", outputsize)
        m15 = self.client.fetch_ohlcv(symbol, "15min", outputsize)
        return h4, h1, m15
