from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


def load_env_file(path: str | Path = ".env") -> None:
    env_path = Path(path)
    if not env_path.is_absolute():
        env_path = PROJECT_ROOT / env_path
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


load_env_file()


@dataclass(frozen=True)
class AppConfig:
    app_mode: str
    flask_host: str
    flask_port: int
    public_base_url: str
    mt5_bridge_host: str
    mt5_bridge_port: int
    mt5_bridge_url: str
    mt5_bridge_api_key: str
    mt5_terminal_path: str
    database_path: Path

    @property
    def is_local(self) -> bool:
        return self.app_mode == "local"


def int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def get_config() -> AppConfig:
    app_mode = os.getenv("APP_MODE", "local").strip().lower() or "local"
    flask_host = os.getenv("FLASK_HOST", "127.0.0.1")
    flask_port = int_env("FLASK_PORT", 5000)
    mt5_bridge_host = os.getenv("MT5_BRIDGE_HOST", "127.0.0.1")
    mt5_bridge_port = int_env("MT5_BRIDGE_PORT", 5001)
    default_bridge_url = f"http://{mt5_bridge_host}:{mt5_bridge_port}" if app_mode == "local" else ""
    mt5_bridge_url = (os.getenv("MT5_BRIDGE_URL") or default_bridge_url).rstrip("/")
    public_base_url = (
        os.getenv("PUBLIC_BASE_URL")
        or os.getenv("PUBLIC_APP_URL")
        or (f"http://127.0.0.1:{flask_port}" if app_mode == "local" else "")
    ).rstrip("/")
    database_path = Path(os.getenv("ANALYSIS_HISTORY_DB", "analysis_history.db"))
    if not database_path.is_absolute():
        database_path = PROJECT_ROOT / database_path
    return AppConfig(
        app_mode=app_mode,
        flask_host=flask_host,
        flask_port=flask_port,
        public_base_url=public_base_url,
        mt5_bridge_host=mt5_bridge_host,
        mt5_bridge_port=mt5_bridge_port,
        mt5_bridge_url=mt5_bridge_url,
        mt5_bridge_api_key=os.getenv("MT5_BRIDGE_API_KEY", ""),
        mt5_terminal_path=os.getenv("MT5_TERMINAL_PATH", r"C:\Program Files\RoboForex MT5 Terminal\terminal64.exe"),
        database_path=database_path,
    )


def public_url(path: str = "") -> str:
    base_url = get_config().public_base_url
    if not path:
        return base_url
    return f"{base_url}/{path.lstrip('/')}" if base_url else path
