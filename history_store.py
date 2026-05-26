from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DB_PATH = Path(os.getenv("ANALYSIS_HISTORY_DB", "analysis_history.db"))


def init_history() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                system_used TEXT NOT NULL,
                status TEXT NOT NULL,
                setup_name TEXT NOT NULL,
                score TEXT NOT NULL,
                summary TEXT NOT NULL
            )
            """
        )


def add_history(system_used: str, status: str, setup_name: str, score: str, summary: str) -> None:
    init_history()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO analysis_history (created_at, system_used, status, setup_name, score, summary)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                system_used,
                status,
                setup_name,
                score,
                summary,
            ),
        )


def recent_history(limit: int = 10) -> list[dict[str, Any]]:
    init_history()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT created_at, system_used, status, setup_name, score, summary
            FROM analysis_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
