from __future__ import annotations

from history_store import _display_malaysia_time, malaysia_now_text


def test_malaysia_now_text_uses_myt_label() -> None:
    assert malaysia_now_text().endswith(" MYT")


def test_utc_history_display_converts_to_malaysia_time() -> None:
    assert _display_malaysia_time("2026-05-29 14:00:00 UTC") == "2026-05-29 22:00:00 MYT"
