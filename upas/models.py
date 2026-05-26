from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_system_a.models import Direction, OHLCVData


@dataclass(frozen=True)
class UPASInput:
    mn1: OHLCVData
    w1: OHLCVData
    d1: OHLCVData
    h4: OHLCVData
    h1: OHLCVData
    account_balance: float = 100000.0
    current_daily_loss: float = 0.0
    use_atr: bool = False


@dataclass(frozen=True)
class UPASSetupCandidate:
    name: str
    direction: Direction
    entry: float | None
    stop_loss: float | None
    take_profit: float | None
    invalidation: str
    reason: str


@dataclass(frozen=True)
class UPASAnalysis:
    payload: dict[str, Any]
    summary: str
