# Smart System A Agent

Smart System A Agent is a strict Python analysis tool for XAUUSD. It analyzes H4 trend and Elliott Wave context first, then H1 breakout, pullback, candle behavior, and volume confirmation. It does not place trades and does not mix in other trading strategies or indicators.

## What It Does

- Reads H4 and H1 OHLCV CSV files.
- Determines H4 trend, market state, and a rule-based Elliott Wave approximation.
- Detects H1 BOS, breakout quality, retest zone, candle confirmation, and volume behavior.
- Applies the six-condition Smart System A checklist.
- Returns no setup when any SSA rule fails.
- Calculates XAUUSD SL, TP1, TP2, risk amount, and lot size only after all six conditions pass.
- Applies FTMO-compatible fixed risk mechanics using `1 pip = 1.00 price movement` and `1 lot = $100 per pip`.

## Install

```bash
cd smart_system_a_agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## OHLC CSV Format

The web platform uses one combined OHLC CSV file. It must contain:

```csv
timeframe,timestamp,open,high,low,close,volume
H4,2026-01-01 00:00,4100,4110,4095,4108,1200
H1,2026-01-01 01:00,4108,4112,4101,4105,950
```

Smart System A requires `H4` and `H1` rows. UPAS requires `MN1`, `W1`, `D1`, `H4`, and `H1` rows.

If volume is missing, the agent reports `Volume analysis limited - OHLCV volume data missing.` Condition 6 does not automatically pass unless `--volume-override` is explicitly provided.

## Run

```bash
python main.py --h4 data/xauusd_h4.csv --h1 data/xauusd_h1.csv --balance 100000 --risk-mode standard
```

Optional high-confidence mode:

```bash
python main.py --h4 data/xauusd_h4.csv --h1 data/xauusd_h1.csv --balance 100000 --risk-mode high_confidence --risk-percent 1.2
```

## Run The Web Platform Locally

```bash
python web_app.py
```

Then open:

```text
http://127.0.0.1:8000
```

The web platform lets you upload one combined OHLC CSV file or use the live feed, then receive the same strict setup or no-setup output.

The web platform also accepts PNG, JPG, and WebP chart screenshots for intake. A screenshot by itself does not produce a trade setup because Smart System A requires mechanically verified OHLCV, volume, H4/H1 structure, and checklist data. Upload H4 and H1 CSV files to run the full SSA analysis.

Analysis results are shown in a dashboard with separate sections for H4 trend and wave context, H1 structure and entry behavior, the six-condition SSA checklist, risk metrics, and the exact final SSA output.

## Analysis Systems

The web platform supports two selectable analysis systems:

- **Smart System A**: H4/H1 XAUUSD analysis with SSA wave, BOS, pullback, volume, and risk rules.
- **UPAS Trade Assistant**: pure price-action XAUUSD analysis using MN1, W1, D1, H4, and H1. UPAS detects Kangaroo Tail, Last Kiss, Moolah, and Engulfing Trap Bar setups and returns JSON first, then a short summary.

CSV mode for UPAS requires one OHLC file containing MN1, W1, D1, H4, and H1 rows. Live mode fetches all five timeframes when `TWELVE_DATA_API_KEY` is configured.

## Live XAUUSD Feed

The web platform can fetch live H4 and H1 XAU/USD candles from Twelve Data.

Set this environment variable before using live mode:

```text
TWELVE_DATA_API_KEY=your_api_key
```

On Render, add it under **Environment** for the web service. Then choose **Live XAUUSD Feed** in the app.

Live mode still follows the same strict Smart System A rules. If the provider returns missing volume, condition 6 fails unless volume override is explicitly enabled.

## Deploy Online

This project is ready for a Python web host that supports WSGI apps, such as Render, Railway, Fly.io, or Heroku-style platforms.

For step-by-step publishing instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

Recommended Render settings:

```text
Build Command: pip install -r requirements.txt
Start Command: gunicorn web_app:app
```

The included `Procfile` also supports hosts that detect Heroku-style Python apps:

```text
web: gunicorn web_app:app
```

To make it publicly available, push this project to a Git repository and connect that repository to your hosting provider. The app does not need trading credentials because it does not execute trades.

## Test

```bash
pytest
```

## Example Valid Setup Output

```text
Setup Type: BUY LIMIT
Entry: 4125
SL: 4085
TP1: 4165
TP2: 4205
Pip Distance: 40.0
Risk %: 1.2
Lot Size: 0.3
Confidence Level: High
Reasoning Summary: H4 wave position: Wave 3 likely; active wave: 3; market state: expanding. H1 BOS: bullish at 4125; pullback zone: 4125; candle behavior: confirmed rejection/acceptance; volume behavior: impulse volume exceeds pullback volume; all six SSA conditions passed.
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

This project is an analysis tool only. It is not financial advice, not a signal service, and not an execution bot. It never places trades, never widens SL, never increases risk, and never overrides failed Smart System A rules unless the user explicitly enables the volume override.
