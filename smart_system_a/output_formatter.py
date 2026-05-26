from __future__ import annotations

from .models import NoSetupResult, TradeSetup


class OutputFormatter:
    def format_trade(self, setup: TradeSetup) -> str:
        return "\n".join(
            [
                f"Setup Type: {setup.setup_type}",
                f"Entry: {setup.entry}",
                f"SL: {setup.sl}",
                f"TP1: {setup.tp1}",
                f"TP2: {setup.tp2}",
                f"Pip Distance: {setup.pip_distance}",
                f"Risk %: {setup.risk_percent}",
                f"Lot Size: {setup.lot_size}",
                f"Confidence Level: {setup.confidence_level}",
                f"Reasoning Summary: {setup.reasoning_summary}",
            ]
        )

    def format_no_setup(self, result: NoSetupResult) -> str:
        failed = "; ".join(result.failed_rules)
        return "\n".join(
            [
                f"No setup - {failed}",
                f"Current H4 wave position: {result.h4_wave_position}",
                f"Active wave number: {result.active_wave if result.active_wave is not None else 'unidentifiable'}",
                f"Market state: {result.market_state.value}",
                f"What must happen next: {result.what_next}",
                f"Reasoning Summary: {result.reasoning_summary}",
            ]
        )
