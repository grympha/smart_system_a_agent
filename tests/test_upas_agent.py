from __future__ import annotations

import json

from smart_system_a.models import Candle, OHLCVData
from upas import UPASAgent
from upas.models import UPASInput


def c(idx: int, open_: float, high: float, low: float, close: float) -> Candle:
    return Candle(str(idx), open_, high, low, close, 1000)


def trend_data(timeframe: str, start: float = 100.0) -> OHLCVData:
    candles = []
    price = start
    for idx in range(10):
        candles.append(c(idx, price, price + 6, price - 2, price + 4))
        price += 3
    return OHLCVData(candles, timeframe, "XAUUSD")


def h4_last_kiss() -> OHLCVData:
    candles = [
        c(0, 100, 102, 98, 101),
        c(1, 101, 103, 99, 102),
        c(2, 102, 104, 100, 103),
        c(3, 103, 105, 101, 104),
        c(4, 104, 106, 102, 105),
        c(5, 105, 114, 104, 113),
        c(6, 113, 116, 110, 115),
        c(7, 115, 118, 112, 116),
        c(8, 116, 119, 113, 117),
        c(9, 108, 116, 103, 115),
    ]
    return OHLCVData(candles, "H4", "XAUUSD")


def h1_confirmation() -> OHLCVData:
    candles = [
        c(0, 105, 107, 104, 106),
        c(1, 106, 108, 105, 107),
        c(2, 107, 109, 106, 108),
        c(3, 108, 110, 107, 109),
        c(4, 109, 111, 108, 110),
        c(5, 110, 112, 109, 111),
        c(6, 111, 113, 110, 112),
        c(7, 112, 114, 111, 113),
        c(8, 113, 115, 112, 114),
        c(9, 114, 121, 113, 120),
    ]
    return OHLCVData(candles, "H1", "XAUUSD")


def test_upas_returns_json_first_valid_trade() -> None:
    analysis = UPASAgent().analyze(
        UPASInput(
            mn1=trend_data("MN1"),
            w1=trend_data("W1"),
            d1=trend_data("D1"),
            h4=h4_last_kiss(),
            h1=h1_confirmation(),
        )
    )

    payload_text = analysis.summary.split("\n\n", 1)[0]
    payload = json.loads(payload_text)

    assert payload["module"] == "UPAS Trade Assistant"
    assert payload["symbol"] == "XAUUSD"
    assert payload["setup"]["name"] in {"Last Kiss", "Moolah"}
    assert payload["setup"]["confluence_score"] >= 4
    assert payload["trade_plan"]["reward_risk_ratio"] >= 2
