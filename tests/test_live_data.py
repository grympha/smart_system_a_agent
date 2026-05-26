from __future__ import annotations

import json
from io import BytesIO

import pytest

from smart_system_a.live_data import LiveDataError, TwelveDataClient


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_live_data_requires_api_key() -> None:
    client = TwelveDataClient(api_key=None)
    client.api_key = None

    with pytest.raises(LiveDataError):
        client.fetch_ohlcv("XAU/USD", "1h")


def test_live_data_parses_time_series(monkeypatch) -> None:
    payload = {
        "status": "ok",
        "values": [
            {"datetime": "2026-01-01 02:00:00", "open": "4110", "high": "4120", "low": "4100", "close": "4115", "volume": "1200"},
            {"datetime": "2026-01-01 01:00:00", "open": "4100", "high": "4112", "low": "4095", "close": "4110", "volume": "1000"},
        ],
    }

    def fake_urlopen(*_args, **_kwargs):
        return FakeResponse(payload)

    monkeypatch.setattr("smart_system_a.live_data.urlopen", fake_urlopen)
    data = TwelveDataClient(api_key="test").fetch_ohlcv("XAU/USD", "1h", 2)

    assert data.timeframe == "H1"
    assert data.candles[0].timestamp == "2026-01-01 01:00:00"
    assert data.candles[1].close == 4115
    assert data.candles[1].volume == 1200
