# Project Context

This file is the main handoff document for continuing Gold Smart Agent from another computer.

## Identity

Project name:

```text
Gold Smart Agent
```

Repository:

```text
https://github.com/grympha/smart_system_a_agent.git
```

Main working branch:

```text
codex/render-deployment
```

Primary runtime:

```text
Local Windows PC + Cloudflare Named Tunnel
```

Optional Render URL:

```text
https://smart-system-a-agent.onrender.com/
```

Purpose:

```text
XAUUSD rule-based analysis only.
```

The app must not execute trades.

## Current Architecture

Core files:

- `app_config.py` - local-first environment configuration and public URL helpers.
- `web_app.py` - Flask web app, routes, analysis orchestration, MT5 endpoints.
- `templates.py` - HTML/CSS dashboard templates.
- `history_store.py` - SQLite-backed recent analysis history.
- `main.py` - Smart System A CLI entry point.
- `smart_system_a/` - Smart System A analyzers, models, risk, checklist, output.
- `upas/` - UPAS Trade Assistant logic.
- `wave_structure/` - Wave Structure Analyst logic.
- `elliot_wave3/` - Strict XAUUSD Elliot Wave 3 continuation analyzer.
- `mt5_bridge.py` - Local read-only Python Flask API that connects to MetaTrader 5 desktop.
- `mt5/` - MetaTrader 5 EA/script files.
- `tests/` - Unit tests for all current engines.

Generated or local-only files:

- `analysis_history.db`
- `*.log`
- `tools/cloudflared.exe`
- `config/cloudflare/tunnel.yml`
- packaged MT5 zip/folders

These should normally stay uncommitted.

## Analysis Options

### Smart System A

Required timeframes:

```text
H4, H1
```

Main logic:

- H4 trend and Elliott Wave context
- H1 BOS, breakout, pullback, candle behavior, and volume
- Six-condition checklist
- No setup if any condition fails
- XAUUSD-specific pip, SL, TP, risk, and lot-size math

### UPAS Trade Assistant

Required timeframes:

```text
MN1, W1, D1, H4, H1
```

Main logic:

- Pure price-action only
- Kangaroo Tail
- Last Kiss
- Moolah
- Engulfing Trap Bar
- Confluence score must be 4/5 or higher
- Minimum reward:risk is 1:2

### Wave Structure Analyst

Required timeframes:

```text
H4 or H1
```

Optional timeframes:

```text
D1, M30, M15
```

Main logic:

- Wave 3 continuation
- ABC correction
- Wave 5 exhaustion
- Unknown or unclear structure
- Score out of 10
- WAIT or NO_VALID_SETUP when the structure is unclear

Manual wave input fields were removed. The result should be inferred from OHLCV data.

### Elliot Wave 3 Analysis

Required timeframes:

```text
H4, H1, M15
```

Main logic:

- XAUUSD only
- Wave 3 continuation after valid Wave 2 pullback only
- H4 trend, Wave 1 impulse, Wave 2 pullback, and Wave 3 breakout
- Wave 2 retracement must be 38.2% - 61.8%; 55% - 61.8% is preferred
- Wave 3 projection must be at least 1.272x Wave 1
- H1 momentum confirmation
- M15 trigger confirmation
- M15 volume must be at least 1.20x average volume
- Wave 1 impulse must be at least 1.20x H4 ATR
- Score is out of 100; only score >= 85 is tradeable
- Valid trade plan uses SL at Wave 2 invalidation and TP at 1:3 R:R

This module is analysis-only and does not execute trades.

## Web App Behavior

The sidebar has:

1. Analysis System
2. Data Source
3. OHLC Data
4. Chart Screenshot

Risk settings were removed from the visible UI. The app keeps strict default analysis behavior.

Supported data sources:

- CSV Upload
- Live XAUUSD Feed
- MT5 Direct Mode

CSV upload expects one combined CSV:

```csv
timeframe,timestamp,open,high,low,close,volume
H4,2026-01-01 00:00,4100,4110,4095,4108,1200
H1,2026-01-01 01:00,4108,4112,4101,4105,950
```

Chart screenshot upload is currently preview/intake only. It does not replace OHLCV analysis.

MT5/API screenshot payloads can include both H1 and H4 previews:

```json
{
  "chart_images": {
    "H1": "base64_png",
    "H4": "base64_png"
  }
}
```

The dashboard displays both previews when both are available. A single legacy `chart_image` payload still works.

If MT5 Direct Mode has OHLCV candle data but no screenshot payload, the app generates H1/H4 candlestick preview images from the latest OHLCV candles using Pillow and stores them in the same screenshot store.

History rows should be clickable and show the full dashboard result, not raw JSON-only output.

The UI should remain mobile friendly, dark themed, and premium-looking.

Hourly monitoring runs through `/api/auto-analysis/hourly`. While the page is open, the browser calls it every hour and can show a browser notification when Smart System A, UPAS, or Elliot Wave 3 Analysis returns `VALID_TRADE`, or Wave Structure Analyst returns `WAVE_CONFIRMED`. Browser notifications require the user to click `Enable Hourly Alerts` and allow notifications.

Telegram notifications are also supported. When `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are configured, the hourly endpoint sends a Telegram message for each alert result. Use `POST /api/notifications/telegram/test` to verify the server can send Telegram messages.

## Environment Variables

Main web app:

```text
APP_MODE=local
PUBLIC_BASE_URL=https://agent.my-domain.com
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
TWELVE_DATA_API_KEY=your_twelve_data_key
MT5_BRIDGE_URL=http://127.0.0.1:5001
MT5_BRIDGE_API_KEY=your_bridge_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

Local MT5 bridge:

```text
MT5_BRIDGE_API_KEY=your_bridge_key
MT5_BRIDGE_HOST=127.0.0.1
MT5_BRIDGE_PORT=5001
MT5_TERMINAL_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
MT5_LOGIN=optional_login
MT5_PASSWORD=optional_password
MT5_SERVER=optional_server
```

If MT5 is already open and logged in, the bridge can usually connect without login/password.

## MT5 Bridge Notes

The local Python MT5 bridge must run on the same Windows PC as MetaTrader 5.

Start it:

```powershell
pip install -r requirements-mt5-bridge.txt
$env:MT5_BRIDGE_API_KEY="change-this-secret"
python mt5_bridge.py
```

Optional helper:

```powershell
.\start_mt5_bridge.ps1
```

For public access, expose the local Flask app through a Cloudflare Named Tunnel.

Cloudflare tunnel helper:

```powershell
.\start_cloudflare_tunnel.ps1
```

Use a named tunnel and your own hostname for stable daily use.

## MT5 Auto-Push EA Notes

Latest all-system EA:

```text
mt5/GoldSmartAgent_AutoPushOHLC_EA_V4.mq5
```

V3 backup EA:

```text
mt5/GoldSmartAgent_AutoPushOHLC_EA_V3.mq5
```

This file is copied from the active MetaTrader workspace EA:

```text
C:\Users\User\AppData\Roaming\MetaQuotes\Terminal\5FFA568149E88FCD5B44D926DCFEAA79\MQL5\Experts\Advisors\GoldSmartAgent_AutoPushOHLC_EA_V3.mq5
```

Current V4 behavior:

- Auto-pushes every 5 minutes by default with `InpPushIntervalSeconds = 300`.
- Pushes 300 OHLCV candles per timeframe by default with `InpBarsPerTimeframe = 300`.
- Pushes on EA start when `InpPushOnStart = true`.
- Default endpoint is `https://agent.my-domain.com/api/analyze`; set `InpEndpoint` to your Cloudflare hostname.
- Pushes Smart System A with H4 and H1 rows.
- Pushes UPAS with MN1, W1, D1, H4, and H1 rows.
- Pushes Wave Structure Analyst with D1, H4, and H1 rows.
- Pushes Elliot Wave 3 Analysis with H4, H1, and M15 rows.
- Captures and sends both H1 and H4 chart previews under the `chart_images` payload.
- Keeps the legacy single `chart_image` field as a fallback, preferring H1 when available.

MT5 Direct Mode also requests 300 OHLCV candles per timeframe by default from the local bridge.

V3 remains available as the last backup EA before Elliot Wave 3 auto-push support.

## Render Deployment

Recommended Render settings:

```text
Language: Python 3
Branch: codex/render-deployment
Build Command: pip install -r requirements.txt
Start Command: gunicorn web_app:app
```

Do not set `Root Directory` to `render.yaml`. If a root directory is needed, it should be a folder path, not a file.

## Local Development Checklist

1. Clone repository.
2. Checkout `codex/render-deployment`.
3. Create and activate Python virtual environment.
4. Install `requirements.txt`.
5. Run `python -m pytest`.
6. Run `start_all.bat`.
7. Open `http://127.0.0.1:5000`.
8. For public access, run Cloudflare Named Tunnel.

## Testing

Use:

```powershell
python -m pytest
```

The exact test count can change as systems are added. A clean local run should pass without failures.

## Security Notes

- Keep `MT5_BRIDGE_API_KEY` private.
- Do not commit `.env` files, logs, database files, or local tunnel binaries.
- The MT5 bridge is read-only and should remain read-only unless a future explicit task adds execution.
- If the bridge URL was shared publicly, rotate the bridge API key.

## Known Caveats

- Live feed quality depends on Twelve Data response and volume availability.
- MT5 Direct Mode needs a running local bridge or a working EA push.
- Screenshot analysis is not OCR/AI chart reading yet.
- SQLite history is simple local persistence. Render filesystem persistence may reset depending on service behavior.
- Wave Structure Analyst is a conservative rule-based approximation, not a certainty engine.
