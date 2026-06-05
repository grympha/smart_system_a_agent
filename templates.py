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


def elliot_wave3_template_csv() -> str:
    rows = ["timeframe,timestamp,open,high,low,close,volume"]
    h4_rows = [
        (4300, 4310, 4295, 4308, 1200),
        (4308, 4322, 4305, 4318, 1250),
        (4318, 4338, 4314, 4332, 1400),
        (4332, 4358, 4328, 4350, 1600),
        (4350, 4384, 4348, 4378, 1900),
        (4378, 4402, 4370, 4396, 2100),
        (4396, 4404, 4378, 4385, 1300),
        (4385, 4390, 4360, 4368, 1200),
        (4368, 4378, 4348, 4358, 1250),
        (4358, 4372, 4342, 4364, 1250),
        (4364, 4388, 4360, 4380, 1600),
        (4380, 4410, 4375, 4405, 2200),
        (4405, 4445, 4400, 4438, 2800),
        (4438, 4475, 4432, 4468, 3200),
        (4468, 4510, 4462, 4502, 3600),
        (4502, 4555, 4498, 4542, 4200),
    ]
    for idx, row in enumerate(h4_rows):
        rows.append(f"H4,2026-01-01 {idx:02d}:00,{row[0]},{row[1]},{row[2]},{row[3]},{row[4]}")
    h1_price = 4438
    for idx in range(20):
        close = h1_price + (8 if idx == 19 else 3)
        rows.append(f"H1,2026-01-02 {idx:02d}:00,{h1_price},{close + 4},{h1_price - 2},{close},{1500 + idx * 20}")
        h1_price = close - 1
    m15_price = 4488
    for idx in range(21):
        volume = 1200 if idx < 20 else 1800
        close = m15_price + (5 if idx == 20 else 1.5)
        rows.append(f"M15,2026-01-03 {idx:02d}:00,{m15_price},{close + 2},{m15_price - 1},{close},{volume}")
        m15_price = close - 0.5
    return "\n".join(rows) + "\n"
