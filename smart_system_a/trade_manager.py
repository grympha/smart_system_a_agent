from __future__ import annotations

from dataclasses import replace

from .models import Direction, TradeSetup


class TradeManager:
    def move_sl_to_breakeven_after_tp1(self, setup: TradeSetup, current_price: float, direction: Direction) -> TradeSetup:
        tp1_hit = current_price >= setup.tp1 if direction == Direction.BULLISH else current_price <= setup.tp1
        if not tp1_hit:
            return setup
        return replace(setup, sl=setup.entry)

    def can_modify_stop(self, current_sl: float, proposed_sl: float, direction: Direction) -> bool:
        if direction == Direction.BULLISH:
            return proposed_sl >= current_sl
        if direction == Direction.BEARISH:
            return proposed_sl <= current_sl
        return False

    def should_exit_for_invalidation(self, invalidated: bool) -> bool:
        return invalidated
