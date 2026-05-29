from __future__ import annotations

import os
import sqlite3
import json
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
                summary TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'web',
                detail_json TEXT,
                raw_output TEXT
            )
            """
        )
        _ensure_column(conn, "source", "TEXT NOT NULL DEFAULT 'web'")
        _ensure_column(conn, "detail_json", "TEXT")
        _ensure_column(conn, "raw_output", "TEXT")


def _ensure_column(conn: sqlite3.Connection, column: str, definition: str) -> None:
    columns = [row[1] for row in conn.execute("PRAGMA table_info(analysis_history)").fetchall()]
    if column not in columns:
        conn.execute(f"ALTER TABLE analysis_history ADD COLUMN {column} {definition}")


def add_history(
    system_used: str,
    status: str,
    setup_name: str,
    score: str,
    summary: str,
    source: str = "web",
    detail: dict[str, Any] | None = None,
    raw_output: str | None = None,
) -> None:
    init_history()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO analysis_history
            (created_at, system_used, status, setup_name, score, summary, source, detail_json, raw_output)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                system_used,
                status,
                setup_name,
                score,
                summary,
                source,
                json.dumps(detail or {}, default=str),
                raw_output,
            ),
        )


def recent_history(limit: int = 10) -> list[dict[str, Any]]:
    init_history()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, created_at, system_used, status, setup_name, score, summary, source
            FROM analysis_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def latest_history(source: str | None = None) -> dict[str, Any] | None:
    init_history()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        if source:
            row = conn.execute(
                """
                SELECT id, created_at, system_used, status, setup_name, score, summary, source, detail_json, raw_output
                FROM analysis_history
                WHERE source = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (source,),
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT id, created_at, system_used, status, setup_name, score, summary, source, detail_json, raw_output
                FROM analysis_history
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()
    return _decode_row(row) if row else None


def get_history_item(item_id: int) -> dict[str, Any] | None:
    init_history()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT id, created_at, system_used, status, setup_name, score, summary, source, detail_json, raw_output
            FROM analysis_history
            WHERE id = ?
            """,
            (item_id,),
        ).fetchone()
    return _decode_row(row) if row else None


def _decode_row(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    try:
        item["detail"] = json.loads(item.get("detail_json") or "{}")
    except json.JSONDecodeError:
        item["detail"] = {}
    return item
