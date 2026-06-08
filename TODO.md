# TODO

This file tracks practical next steps for Gold Smart Agent.

## Highest Priority

- Configure a stable MT5 bridge URL.
  - Best option: Cloudflare named tunnel.
  - Requirement: Cloudflare account with a domain/zone and tunnel write permissions.
  - Then set `MT5_BRIDGE_URL` and `MT5_BRIDGE_API_KEY` on Render.

- Confirm MT5 Direct Mode from hosted Render app.
  - Start MT5 desktop.
  - Start `mt5_bridge.py`.
  - Start public tunnel.
  - Run SSA and UPAS from the hosted app.
  - Verify latest candles, total candles, and volume status.

- Keep the MT5 bridge read-only.
  - Do not add trade execution unless explicitly requested later.

## UI Improvements

- Improve mobile history detail view for very long summaries.
- Add clearer loading state after pressing Run Analysis.
- Add a small refresh button for MT5 status/result.
- Add copy/download button for full analysis result.
- Add filter tabs for history:
  - All
  - Smart System A
  - UPAS
  - Wave Structure Analyst

## Data Improvements

- Add stronger CSV validation messages:
  - Missing timeframe rows
  - Invalid timestamp
  - Non-numeric OHLC values
  - Missing volume
- Add candle count requirements per system directly in the UI.
- Add sample CSV files under a `data/` folder.
- Add optional import from MT5 bridge for all Wave Structure optional timeframes.

## MT5 Work

- Package the MT5 bridge startup flow into a simpler Windows guide.
- Build a future `GoldSmartAgent_AutoPushOHLC_EA_V4.mq5` that can push Elliot Wave 3 Analysis with H4, H1, and M15 rows.
- Add health-check script for:
  - MT5 open
  - MT5 logged in
  - XAUUSD available
  - Bridge reachable
  - API key accepted
- Add automatic bridge log rotation.
- Add stable named Cloudflare tunnel documentation after a domain is connected.

## Analysis Engine Improvements

- Strengthen Wave Structure Analyst with more tests for:
  - Clean bullish Wave 3
  - Clean bearish Wave 3
  - ABC correction
  - Wave 5 exhaustion
  - Ranging market
- Add future confirmation-layer integration:
  - SSA can display Wave Structure Analyst as optional confirmation.
  - UPAS can display Wave Structure Analyst as optional confirmation.
- Keep each system independent. Do not let Wave Structure override SSA or UPAS rules.

## Screenshot Intake

- Current screenshot upload is preview/intake only.
- Future option: add OCR/chart extraction or AI vision.
- Any screenshot-based result should be clearly labeled as image-assisted and lower certainty unless OHLCV confirms it.

## Security And Deployment

- Rotate `MT5_BRIDGE_API_KEY` if it was exposed.
- Avoid committing:
  - `.env`
  - logs
  - `analysis_history.db`
  - local tunnel binaries
  - packaged zip artifacts
- Consider moving history to a managed database if Render persistence becomes important.
- Add basic user authentication if the hosted app should be private.

## Documentation Maintenance

- Update `CHANGELOG.md` after every meaningful change.
- Update `PROJECT_CONTEXT.md` when deployment, environment variables, or MT5 flow changes.
- Update `README.md` when quick-start commands change.
