from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from flask import Flask, Response, jsonify, request

try:
    from flask_cors import CORS
except Exception:  # pragma: no cover - fallback for minimal installs
    CORS = None


SYMBOL = "XAUUSD"
SUPPORTED_TIMEFRAMES = {"MN1", "W1", "D1", "H4", "H1", "M15"}


def create_bridge_app() -> Flask:
    app = Flask(__name__)
    if CORS:
        CORS(app, resources={r"/api/*": {"origins": os.getenv("MT5_BRIDGE_ALLOWED_ORIGINS", "*")}})

    @app.after_request
    def add_cors_headers(response: Response) -> Response:
        if not CORS:
            response.headers["Access-Control-Allow-Origin"] = os.getenv("MT5_BRIDGE_ALLOWED_ORIGINS", "*")
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key, Authorization"
            response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        return response

    @app.before_request
    def protect_api() -> tuple[Response, int] | None:
        if request.method == "OPTIONS":
            return None
        if not request.path.startswith("/api/"):
            return None
        expected_key = os.getenv("MT5_BRIDGE_API_KEY")
        if not expected_key:
            return jsonify_error("MT5_BRIDGE_API_KEY is not configured on the bridge.", 500)
        supplied_key = request.headers.get("X-API-Key") or _bearer_token(request.headers.get("Authorization", ""))
        if supplied_key != expected_key:
            return jsonify_error("Unauthorized. Provide the bridge API key in X-API-Key or Authorization: Bearer.", 401)
        return None

    @app.get("/api/mt5/status")
    def mt5_status() -> Response | tuple[Response, int]:
        mt5, error = _load_mt5()
        if error:
            return jsonify({"ok": False, "connected": False, "symbol": SYMBOL, "error": error}), 503
        connected, error = _initialize(mt5)
        if not connected:
            return jsonify({"ok": False, "connected": False, "symbol": SYMBOL, "error": error}), 503
        terminal_info = mt5.terminal_info()
        account_info = mt5.account_info()
        symbol_info = mt5.symbol_info(SYMBOL)
        symbol_available = bool(symbol_info and symbol_info.visible)
        return jsonify(
            {
                "ok": True,
                "connected": True,
                "terminal_open": terminal_info is not None,
                "logged_in": account_info is not None,
                "broker": getattr(account_info, "company", None) if account_info else None,
                "server": getattr(account_info, "server", None) if account_info else None,
                "account_login": getattr(account_info, "login", None) if account_info else None,
                "symbol": SYMBOL,
                "symbol_available": symbol_available,
                "read_only": True,
            }
        )

    @app.get("/api/mt5/account")
    def mt5_account() -> Response | tuple[Response, int]:
        mt5, error = _ready_mt5()
        if error:
            return jsonify_error(error, 503)
        account_info = mt5.account_info()
        if account_info is None:
            return jsonify_error("MT5 is open but not logged in. Log in to your RoboForex demo account.", 503)
        return jsonify(
            {
                "ok": True,
                "read_only": True,
                "login": account_info.login,
                "server": account_info.server,
                "company": account_info.company,
                "name": account_info.name,
                "currency": account_info.currency,
                "balance": account_info.balance,
                "equity": account_info.equity,
                "margin": account_info.margin,
                "margin_free": account_info.margin_free,
                "leverage": account_info.leverage,
            }
        )

    @app.get("/api/mt5/xauusd/candles")
    def mt5_xauusd_candles() -> Response | tuple[Response, int]:
        timeframe_name = request.args.get("timeframe", "H1").upper()
        limit_raw = request.args.get("limit", "100")
        if timeframe_name not in SUPPORTED_TIMEFRAMES:
            return jsonify_error("Unsupported timeframe. Use MN1, W1, D1, H4, H1, or M15.", 400)
        try:
            limit = int(limit_raw)
        except ValueError:
            return jsonify_error("Invalid limit. Use a whole number between 10 and 1000.", 400)
        limit = max(10, min(limit, 1000))

        mt5, error = _ready_mt5()
        if error:
            return jsonify_error(error, 503)
        symbol_error = _ensure_symbol(mt5, SYMBOL)
        if symbol_error:
            return jsonify_error(symbol_error, 503)

        timeframe = _timeframe_value(mt5, timeframe_name)
        rates = mt5.copy_rates_from_pos(SYMBOL, timeframe, 0, limit)
        if rates is None or len(rates) == 0:
            return jsonify_error(f"No candles returned for {SYMBOL} {timeframe_name}. Check MT5 chart/history availability.", 503)

        candles = [_rate_to_candle(rate) for rate in rates]
        return jsonify(
            {
                "ok": True,
                "read_only": True,
                "symbol": SYMBOL,
                "timeframe": timeframe_name,
                "limit": limit,
                "count": len(candles),
                "columns": ["timeframe", "timestamp", "open", "high", "low", "close", "volume"],
                "ohlcv_csv": _candles_to_csv(timeframe_name, candles),
                "candles": [{"timeframe": timeframe_name, **candle} for candle in candles],
            }
        )

    @app.get("/api/mt5/xauusd/snapshot")
    def mt5_xauusd_snapshot() -> Response | tuple[Response, int]:
        mt5, error = _ready_mt5()
        if error:
            return jsonify_error(error, 503)
        symbol_error = _ensure_symbol(mt5, SYMBOL)
        if symbol_error:
            return jsonify_error(symbol_error, 503)

        tick = mt5.symbol_info_tick(SYMBOL)
        if tick is None:
            return jsonify_error(f"No current tick returned for {SYMBOL}.", 503)
        current_price = float(tick.bid or tick.last or tick.ask or 0)
        timestamp = datetime.fromtimestamp(int(tick.time)).strftime("%Y-%m-%dT%H:%M:%S")
        return jsonify(
            {
                "ok": True,
                "read_only": True,
                "symbol": SYMBOL,
                "current_price": current_price,
                "timestamp": timestamp,
                "chart_available": False,
            }
        )

    return app


def _load_mt5() -> tuple[Any | None, str | None]:
    try:
        import MetaTrader5 as mt5
    except ImportError:
        return None, "MetaTrader5 Python package is not installed. Run: pip install MetaTrader5"
    return mt5, None


def _ready_mt5() -> tuple[Any | None, str | None]:
    mt5, error = _load_mt5()
    if error:
        return None, error
    connected, error = _initialize(mt5)
    if not connected:
        return None, error
    if mt5.account_info() is None:
        return None, "MT5 terminal is open but not logged in. Log in to your RoboForex demo account."
    return mt5, None


def _initialize(mt5: Any) -> tuple[bool, str | None]:
    path = os.getenv("MT5_TERMINAL_PATH")
    login = os.getenv("MT5_LOGIN")
    password = os.getenv("MT5_PASSWORD")
    server = os.getenv("MT5_SERVER")
    kwargs: dict[str, Any] = {}
    if path:
        kwargs["path"] = path
    if login and password and server:
        kwargs.update({"login": int(login), "password": password, "server": server})
    if mt5.initialize(**kwargs):
        return True, None
    last_error = mt5.last_error()
    return False, f"MT5 is not open or cannot initialize. Open MetaTrader 5 and log in first. MT5 error: {last_error}"


def _ensure_symbol(mt5: Any, symbol: str) -> str | None:
    info = mt5.symbol_info(symbol)
    if info is None:
        return f"Symbol {symbol} is unavailable in MT5 Market Watch. Add XAUUSD in RoboForex symbols."
    if not info.visible and not mt5.symbol_select(symbol, True):
        return f"Symbol {symbol} exists but cannot be selected in MT5 Market Watch."
    return None


def _timeframe_value(mt5: Any, timeframe_name: str) -> Any:
    return {
        "MN1": mt5.TIMEFRAME_MN1,
        "W1": mt5.TIMEFRAME_W1,
        "D1": mt5.TIMEFRAME_D1,
        "H4": mt5.TIMEFRAME_H4,
        "H1": mt5.TIMEFRAME_H1,
        "M15": mt5.TIMEFRAME_M15,
    }[timeframe_name]


def _rate_to_candle(rate: Any) -> dict[str, Any]:
    timestamp = datetime.fromtimestamp(int(rate["time"])).strftime("%Y-%m-%d %H:%M:%S")
    return {
        "timestamp": timestamp,
        "open": float(rate["open"]),
        "high": float(rate["high"]),
        "low": float(rate["low"]),
        "close": float(rate["close"]),
        "volume": float(rate["tick_volume"]),
    }


def _candles_to_csv(timeframe_name: str, candles: list[dict[str, Any]]) -> str:
    rows = ["timeframe,timestamp,open,high,low,close,volume"]
    for candle in candles:
        rows.append(
            f"{timeframe_name},{candle['timestamp']},{candle['open']},{candle['high']},"
            f"{candle['low']},{candle['close']},{candle['volume']}"
        )
    return "\n".join(rows) + "\n"


def _bearer_token(value: str) -> str:
    prefix = "Bearer "
    if value.startswith(prefix):
        return value[len(prefix):]
    return ""


def jsonify_error(message: str, status_code: int) -> tuple[Response, int]:
    return jsonify({"ok": False, "error": message, "read_only": True}), status_code


app = create_bridge_app()


if __name__ == "__main__":
    app.run(host=os.getenv("MT5_BRIDGE_HOST", "127.0.0.1"), port=int(os.getenv("MT5_BRIDGE_PORT", "5055")), debug=False)
