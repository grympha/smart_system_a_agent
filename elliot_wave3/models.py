from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ElliotWave3Result:
    symbol: str
    status: str
    direction: str
    setup_name: str
    score: int
    rating: str
    trend: str
    wave1_origin: float | None
    wave1_end: float | None
    wave2_level: float | None
    wave2_retracement: float | None
    wave3_projection: float | None
    atr_value: float | None
    impulse_atr_multiple: float | None
    h1_momentum: str
    m15_trigger: str
    volume_ratio: float | None
    entry: float | None
    stop_loss: float | None
    take_profit: float | None
    risk_reward: float
    checklist: dict[str, dict[str, object]]
    failed_rules: list[str] = field(default_factory=list)
    summary: str = ""

    @property
    def is_trade(self) -> bool:
        return self.status == "VALID_TRADE"

