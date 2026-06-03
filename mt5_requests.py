from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from history_store import DB_PATH

MALAYSIA_TZ = ZoneInfo("Asia/Kuala_Lumpur")


def init_requests() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS mt5_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                analysis_system TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
            )
            """
        )


def create_mt5_request(analysis_system: str) -> dict[str, Any]:
    init_requests()
    created_at = datetime.now(MALAYSIA_TZ).strftime("%Y-%m-%d %H:%M:%S MYT")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE mt5_requests SET status = 'superseded' WHERE status = 'pending'")
        cursor = conn.execute(
            """
            INSERT INTO mt5_requests (created_at, analysis_system, status)
            VALUES (?, ?, 'pending')
            """,
            (created_at, analysis_system),
        )
    return {"id": cursor.lastrowid, "created_at": created_at, "analysis_system": analysis_system, "status": "pending"}


def consume_next_mt5_request() -> dict[str, Any] | None:
    init_requests()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT id, created_at, analysis_system, status
            FROM mt5_requests
            WHERE status = 'pending'
            ORDER BY id ASC
            LIMIT 1
            """
        ).fetchone()
        if not row:
            return None
        conn.execute("UPDATE mt5_requests SET status = 'consumed' WHERE id = ?", (row["id"],))
    return dict(row)
