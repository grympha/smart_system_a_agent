from __future__ import annotations


def ssa_template_csv() -> str:
    rows = ["timeframe,timestamp,open,high,low,close,volume"]
    for idx in range(10):
        rows.append(f"H4,2026-01-01 {idx:02d}:00,4100,4110,4095,4108,1200")
    for idx in range(10):
        rows.append(f"H1,2026-01-01 {idx:02d}:00,4108,4112,4101,4105,950")
    return "\n".join(rows) + "\n"


def upas_template_csv() -> str:
    rows = ["timeframe,timestamp,open,high,low,close,volume"]
    for timeframe in ["MN1", "W1", "D1", "H4", "H1"]:
        for idx in range(10):
            rows.append(f"{timeframe},2026-01-01 {idx:02d}:00,4100,4110,4095,4108,1200")
    return "\n".join(rows) + "\n"


def wave_template_csv() -> str:
    rows = ["timeframe,timestamp,open,high,low,close,volume"]
    price = 4300
    for idx in range(12):
        rows.append(f"H4,2026-01-01 {idx:02d}:00,{price},{price + 10},{price - 4},{price + 8},1500")
        price += 6
    for idx in range(12, 18):
        rows.append(f"H4,2026-01-01 {idx:02d}:00,{price},{price + 4},{price - 7},{price - 4},1100")
        price -= 3
    for idx in range(18, 24):
        rows.append(f"H4,2026-01-01 {idx:02d}:00,{price},{price + 14},{price - 3},{price + 12},2200")
        price += 10
    price = 4360
    for idx in range(24):
        rows.append(f"H1,2026-01-02 {idx:02d}:00,{price},{price + 6},{price - 2},{price + 5},1300")
        price += 4
    return "\n".join(rows) + "\n"
