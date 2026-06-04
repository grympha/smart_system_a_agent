from __future__ import annotations

import base64
import json
import sqlite3
from typing import Any

from history_store import DB_PATH, malaysia_now_text


def init_screenshots() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chart_screenshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                symbol TEXT NOT NULL,
                analysis_system TEXT NOT NULL,
                market_timestamp TEXT NOT NULL,
                current_price TEXT,
                filename TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                image_base64 TEXT NOT NULL,
                image_source TEXT NOT NULL DEFAULT 'api',
                metadata_json TEXT
            )
            """
        )


def add_chart_screenshot(
    *,
    symbol: str,
    analysis_system: str,
    market_timestamp: str,
    current_price: float | str | None,
    filename: str,
    image_base64: str,
    mime_type: str = "image/png",
    image_source: str = "api",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    init_screenshots()
    cleaned = _strip_data_url(image_base64)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO chart_screenshots
            (created_at, symbol, analysis_system, market_timestamp, current_price, filename, mime_type, image_base64, image_source, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                malaysia_now_text(),
                symbol,
                analysis_system,
                market_timestamp,
                "" if current_price is None else str(current_price),
                filename,
                mime_type,
                cleaned,
                image_source,
                json.dumps(metadata or {}, default=str),
            ),
        )
        screenshot_id = int(cursor.lastrowid)
        _prune_old_screenshots(conn, analysis_system, keep=20)
    return get_chart_screenshot_metadata(screenshot_id) or {}


def get_chart_screenshot(screenshot_id: int) -> dict[str, Any] | None:
    init_screenshots()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT id, created_at, symbol, analysis_system, market_timestamp, current_price, filename, mime_type, image_base64, image_source, metadata_json
            FROM chart_screenshots
            WHERE id = ?
            """,
            (screenshot_id,),
        ).fetchone()
    return _decode_row(row) if row else None


def latest_chart_screenshot(symbol: str | None = None, analysis_system: str | None = None) -> dict[str, Any] | None:
    init_screenshots()
    query = """
        SELECT id, created_at, symbol, analysis_system, market_timestamp, current_price, filename, mime_type, image_base64, image_source, metadata_json
        FROM chart_screenshots
    """
    filters = []
    params: list[str] = []
    if symbol:
        filters.append("symbol = ?")
        params.append(symbol)
    if analysis_system:
        filters.append("analysis_system = ?")
        params.append(analysis_system)
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY id DESC LIMIT 1"
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(query, params).fetchone()
    return _decode_row(row) if row else None


def latest_chart_screenshots(
    symbol: str | None = None,
    analysis_system: str | None = None,
    timeframes: list[str] | None = None,
) -> list[dict[str, Any]]:
    init_screenshots()
    selected = {timeframe.upper() for timeframe in (timeframes or [])}
    query = """
        SELECT id, created_at, symbol, analysis_system, market_timestamp, current_price, filename, mime_type, image_base64, image_source, metadata_json
        FROM chart_screenshots
    """
    filters = []
    params: list[str] = []
    if symbol:
        filters.append("symbol = ?")
        params.append(symbol)
    if analysis_system:
        filters.append("analysis_system = ?")
        params.append(analysis_system)
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY id DESC"
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()

    latest_by_timeframe: dict[str, dict[str, Any]] = {}
    for row in rows:
        item = _decode_row(row)
        timeframe = str((item.get("metadata") or {}).get("timeframe") or "").upper()
        if selected and timeframe not in selected:
            continue
        if timeframe and timeframe not in latest_by_timeframe:
            item.pop("image_base64", None)
            item["image_url"] = f"/screenshots/{item['id']}"
            latest_by_timeframe[timeframe] = item
        if selected and selected.issubset(latest_by_timeframe):
            break

    ordered = []
    for timeframe in (timeframes or []):
        item = latest_by_timeframe.get(timeframe.upper())
        if item:
            ordered.append(item)
    if not timeframes:
        ordered = list(latest_by_timeframe.values())
    return ordered


def get_chart_screenshot_metadata(screenshot_id: int) -> dict[str, Any] | None:
    item = get_chart_screenshot(screenshot_id)
    if not item:
        return None
    item.pop("image_base64", None)
    item["image_url"] = f"/screenshots/{screenshot_id}"
    return item


def _prune_old_screenshots(conn: sqlite3.Connection, analysis_system: str, keep: int) -> None:
    rows = conn.execute(
        """
        SELECT id
        FROM chart_screenshots
        WHERE analysis_system = ?
        ORDER BY id DESC
        LIMIT -1 OFFSET ?
        """,
        (analysis_system, keep),
    ).fetchall()
    old_ids = [row[0] for row in rows]
    if old_ids:
        placeholders = ",".join("?" for _ in old_ids)
        conn.execute(f"DELETE FROM chart_screenshots WHERE id IN ({placeholders})", old_ids)


def _decode_row(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    try:
        item["metadata"] = json.loads(item.get("metadata_json") or "{}")
    except json.JSONDecodeError:
        item["metadata"] = {}
    return item


def _strip_data_url(value: str) -> str:
    if "," in value and value.strip().lower().startswith("data:"):
        return value.split(",", 1)[1]
    return value.strip()


def screenshot_bytes(item: dict[str, Any]) -> bytes:
    return base64.b64decode(item["image_base64"])
