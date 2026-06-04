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

Hosted Render URL:

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

- `web_app.py` - Flask web app, routes, analysis orchestration, MT5 endpoints.
- `templates.py` - HTML/CSS dashboard templates.
- `history_store.py` - SQLite-backed recent analysis history.
- `main.py` - Smart System A CLI entry point.
- `smart_system_a/` - Smart System A analyzers, models, risk, checklist, output.
- `upas/` - UPAS Trade Assistant logic.
- `wave_structure/` - Wave Structure Analyst logic.
- `mt5_bridge.py` - Local read-only Python Flask API that connects to MetaTrader 5 desktop.
- `mt5/` - MetaTrader 5 EA/script files.
- `tests/` - Unit tests for all current engines.

Generated or local-only files:

- `analysis_history.db`
- `*.log`
- `tools/cloudflared.exe`
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

History rows should be clickable and show the full dashboard result, not raw JSON-only output.

The UI should remain mobile friendly, dark themed, and premium-looking.

Hourly monitoring is browser-based in the first version. While the page is open, the browser calls `/api/auto-analysis/hourly` every hour and can show a browser notification when Smart System A or UPAS returns `VALID_TRADE`, or Wave Structure Analyst returns `WAVE_CONFIRMED`. Browser notifications require the user to click `Enable Hourly Alerts` and allow notifications.

## Environment Variables

Main web app:

```text
TWELVE_DATA_API_KEY=your_twelve_data_key
MT5_BRIDGE_URL=https://your-public-mt5-bridge-url
MT5_BRIDGE_API_KEY=your_bridge_key
```

Local MT5 bridge:

```text
MT5_BRIDGE_API_KEY=your_bridge_key
MT5_BRIDGE_HOST=127.0.0.1
MT5_BRIDGE_PORT=5055
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

The hosted Render app cannot call your local PC directly. Use a public HTTPS tunnel or a real hosted bridge.

Cloudflare quick tunnel helper:

```powershell
.\start_cloudflare_tunnel.ps1
```

Important caveat:

- Quick Cloudflare tunnel URLs change when restarted.
- A stable named tunnel needs a Cloudflare domain/zone and correct account permissions.

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
6. Run `python web_app.py`.
7. Open `http://127.0.0.1:8000`.
8. For MT5 work, install `requirements-mt5-bridge.txt` and run MT5 desktop first.

## Testing

Use:

```powershell
python -m pytest
```

Expected current test count after Wave Structure Analyst work:

```text
37 passed
```

If the number changes because new tests are added, update this file.

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
