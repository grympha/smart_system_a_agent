# Gold Smart Agent

Gold Smart Agent is a Python/Flask web analysis platform for XAUUSD. It provides strict rule-based analysis only. It does not place trades, connect to execution, or guarantee outcomes.

Current analysis systems:

- Smart System A
- UPAS Trade Assistant
- Wave Structure Analyst
- Elliot Wave 3 Analysis

Hosted app:

```text
https://smart-system-a-agent.onrender.com/
```

## Quick Start From Any Computer

```powershell
git clone https://github.com/grympha/smart_system_a_agent.git
cd smart_system_a_agent
git checkout codex/render-deployment
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m pytest
python web_app.py
```

Open:

```text
http://127.0.0.1:8000
```

If `git` is not recognized on Windows, install Git for Windows or run it from:

```text
C:\Program Files\Git\cmd\git.exe
```

## Project Documents

- `PROJECT_CONTEXT.md` explains the architecture, deployment, MT5 bridge, environment variables, and current caveats.
- `CHANGELOG.md` records important feature updates.
- `TODO.md` lists next improvements and known follow-up work.
- `DEPLOYMENT.md` contains Render deployment guidance.

Read `PROJECT_CONTEXT.md` first when continuing the project from another PC.

## Analysis Systems

### Smart System A

Smart System A analyzes XAUUSD top-down:

- H4 trend, market state, and Elliott Wave context
- H1 BOS, breakout, pullback, candle confirmation, and volume
- Six-condition SSA checklist
- Strict no-setup output when any condition fails
- Mechanical XAUUSD risk, SL, TP, and lot-size calculation only after all rules pass

Required OHLC timeframes:

```text
H4, H1
```

XAUUSD pip rule:

```text
1 pip = 1.00 price movement
4550 to 4560 = 10 pips
1 lot = $100 per pip
```

### UPAS Trade Assistant

UPAS is a pure price-action XAUUSD module. It detects only:

- Kangaroo Tail
- Last Kiss
- Moolah
- Engulfing Trap Bar

It returns `VALID_TRADE`, `NO_TRADE`, `REJECTED_BY_RISK`, or `INSUFFICIENT_DATA`. It prefers no trade over weak setups.

Required OHLC timeframes:

```text
MN1, W1, D1, H4, H1
```

### Wave Structure Analyst

Wave Structure Analyst is an Elliott Wave confirmation layer for XAUUSD. It classifies:

- Wave 3 continuation
- ABC correction
- Wave 5 exhaustion
- Unknown or unclear structure

It does not replace SSA or UPAS and does not force trades. It returns `WAIT` or `NO_VALID_SETUP` when the wave structure is unclear.

Required OHLC timeframes:

```text
H4 or H1
```

Optional context:

```text
D1, M30, M15
```

When both H4 and H1 rows are present, the dashboard shows both Wave Structure results. The sidebar no longer asks for manual wave levels; the module infers price, swings, breakout, retest, and trend from OHLCV data.

### Elliot Wave 3 Analysis

Elliot Wave 3 Analysis is a strict XAUUSD Wave 3 continuation system based on the attached V6 strategy research. It trades no other Elliott Wave pattern.

It checks:

- H4 Wave 1 impulse, Wave 2 pullback, and Wave 3 breakout structure
- Wave 2 Fibonacci retracement from 38.2% to 61.8%, with 55% to 61.8% preferred
- Wave 3 projection of at least 1.272x Wave 1
- H4 ATR impulse filter
- H1 momentum confirmation
- M15 entry trigger and M15 volume expansion
- Minimum setup score of 85/100
- 1:3 risk reward trade plan when valid

Required OHLC timeframes:

```text
H4, H1, M15
```

The system remains analysis-only. It never opens, closes, or modifies trades.

## OHLC CSV Format

The web app uses one combined OHLC CSV file:

```csv
timeframe,timestamp,open,high,low,close,volume
H4,2026-01-01 00:00,4100,4110,4095,4108,1200
H1,2026-01-01 01:00,4108,4112,4101,4105,950
```

Volume is important. If volume is missing, the system reports:

```text
Volume analysis limited - OHLCV volume data missing.
```

Smart System A condition 6 does not automatically pass when volume is missing.

## Web Dashboard

The dashboard uses the same dark premium design for all systems.

Analysis results are shown in framed sections for:

- Market context
- Setup or wave scenario
- Checklist or scoring model
- Trade plan or suggested action
- Decision summary
- Recent analysis history

Each strategy also shows a trade plan panel with the current action, entry point, take profit, and stop loss. When rules are not complete, the action remains `WAIT` and the plan explains what must form before entry.

Chart screenshot upload currently supports PNG, JPG, and WebP preview/intake. Screenshot upload alone does not replace OHLCV analysis.

## Run CLI Analysis

Smart System A CLI:

```powershell
python main.py --h4 data/xauusd_h4.csv --h1 data/xauusd_h1.csv --balance 100000 --risk-mode standard
```

High-confidence Wave 3 mode, only when explicitly selected:

```powershell
python main.py --h4 data/xauusd_h4.csv --h1 data/xauusd_h1.csv --balance 100000 --risk-mode high_confidence --risk-percent 1.2
```

## Run Web App

```powershell
python web_app.py
```

Production start command:

```text
gunicorn web_app:app
```

Render build command:

```text
pip install -r requirements.txt
```

## Live XAUUSD Feed

Live mode uses Twelve Data.

Environment variable:

```text
TWELVE_DATA_API_KEY=your_key
```

If the provider returns missing or partial volume, strict analysis can still reject the setup.

## Telegram Notifications

Gold Smart Agent can send Telegram alerts when hourly MT5 auto-analysis finds:

- Smart System A `VALID_TRADE`
- UPAS `VALID_TRADE`
- Wave Structure Analyst `WAVE_CONFIRMED`
- Elliot Wave 3 Analysis `VALID_TRADE`

Set these environment variables on Render:

```text
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
PUBLIC_APP_URL=https://smart-system-a-agent.onrender.com
```

Test endpoint:

```text
POST /api/notifications/telegram/test
```

Telegram is optional. If the token or chat ID is missing, alerts are skipped and the analysis still runs.

## MT5 Direct Mode

MT5 Direct Mode has two workflows.

### Local Python MT5 Bridge

The bridge runs on the Windows PC where MetaTrader 5 is installed and logged in.

```powershell
pip install -r requirements-mt5-bridge.txt
$env:MT5_BRIDGE_API_KEY="change-this-secret"
python mt5_bridge.py
```

Bridge endpoints:

```text
GET /api/mt5/status
GET /api/mt5/account
GET /api/mt5/xauusd/candles?timeframe=H1&limit=100
GET /api/mt5/xauusd/candles?timeframe=H4&limit=100
GET /api/mt5/xauusd/candles?timeframe=M15&limit=100
```

Required request header:

```text
X-API-Key: your_key
```

Render cannot call `127.0.0.1` on your PC. To use the bridge from the hosted app, expose it through a secure public URL such as Cloudflare Tunnel, then set:

```text
MT5_BRIDGE_URL=https://your-public-bridge-url
MT5_BRIDGE_API_KEY=your_key
```

### MT5 Auto-Push EA

The EA can push OHLCV data from MT5 to the hosted app every 5 minutes:

```text
mt5/GoldSmartAgent_AutoPushOHLC_EA.mq5
```

Default interval:

```text
InpPushIntervalSeconds = 300
```

The EA can push all three analysis systems:

- Smart System A: H4 and H1
- UPAS: MN1, W1, D1, H4, and H1
- Wave Structure Analyst: H4 and H1
- Elliot Wave 3 Analysis: H4, H1, and M15

The EA payload can also include screenshot metadata for future image-AI modules:

- screenshot filename such as `XAUUSD_H1_20260601_153000.png`
- base64 PNG screenshot in the JSON payload

Image-AI modules such as Elliott Wave recognition, SNR detection, trendline detection, breakout detection, candlestick pattern detection, and price-action validation are not active yet.

The Python MT5 bridge is the cleaner long-term path.

## Useful Commands

Run tests:

```powershell
python -m pytest
```

Check git status:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' status --short
```

Commit and push:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add .
& 'C:\Program Files\Git\cmd\git.exe' commit -m "Your message"
& 'C:\Program Files\Git\cmd\git.exe' push
```

## Example No Setup Output

```text
No setup - Volume supports direction
Current H4 wave position: Wave 3 likely
Active wave number: 3
Market state: expanding
What must happen next: Wait for a clear H4 Wave 3 or Wave 5 continuation, clean H1 BOS, valid retest zone, rejection candle, and volume expansion supporting the BUY direction.
Reasoning Summary: H4 wave position: Wave 3 likely; active wave: 3; market state: expanding. H1 BOS: bullish at 4125; pullback zone: 4125; candle behavior: confirmed rejection/acceptance; volume behavior: Volume analysis limited - OHLCV volume data missing; one or more SSA conditions failed.
```

## Risk Warning

Gold Smart Agent is an analysis tool only. It is not financial advice, not a signal service, and not an execution bot. It does not place trades, widen stop loss, increase risk, or override failed setup rules.
