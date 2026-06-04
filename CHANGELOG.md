# Changelog

All notable project changes should be recorded here.

## 2026-06-04

### Added

- Added H1/H4 chart preview support for MT5/API screenshot payloads.
- Added automatic H1/H4 OHLCV-generated candlestick previews when MT5 does not provide screenshot images.
- Added browser-based hourly auto-analysis monitor endpoint and notification trigger for valid setups or confirmed Wave Structure results.

## 2026-06-03

### Added

- Added portable project documentation:
  - `README.md`
  - `PROJECT_CONTEXT.md`
  - `CHANGELOG.md`
  - `TODO.md`

### Fixed

- MT5 on-demand requests now supersede older pending requests so the latest selected analysis system is picked up first.

## 2026-06-02

### Added

- Added Wave Structure Analyst as the third analysis option.
- Added rule-based wave classification for:
  - Wave 3 continuation
  - ABC correction
  - Wave 5 exhaustion
  - Unknown or unclear structure
- Added Wave Structure tests and sample behavior.

### Changed

- Removed manual Wave Structure Analyst sidebar inputs.
- Wave Structure Analyst now infers current price, timeframe, trend, swing highs/lows, breakout, and retest context from OHLCV data.

## 2026-06-01

### Added

- Added local read-only Python MT5 Bridge API:
  - `/api/mt5/status`
  - `/api/mt5/account`
  - `/api/mt5/xauusd/candles`
- Added CORS and API key protection for the bridge.
- Added startup helper:
  - `start_mt5_bridge.ps1`
- Added Cloudflare tunnel helper:
  - `start_cloudflare_tunnel.ps1`

### Changed

- Reverted MT5 EA workflow back to auto-push every 5 minutes.
- MT5 status displays Malaysia time in the web dashboard.

## 2026-05-30

### Added

- Added MT5 Direct Mode option.
- Added MT5 latest pushed result display.
- Added clickable recent analysis history.
- Added mobile-friendly dashboard improvements.
- Added MT5 data status panel:
  - Provider
  - Status
  - Total candles
  - Volume data

### Changed

- MT5 Direct Mode now respects the selected analysis system.
- Selecting Smart System A shows SSA result only.
- Selecting UPAS shows UPAS result only.

## 2026-05-29

### Added

- Added UPAS Trade Assistant as a second analysis option.
- Added UPAS dashboard rendering similar to Smart System A.
- Added user-friendly dark premium dashboard.
- Added chart screenshot preview.
- Added local analysis history storage.
- Added live data provider status display.

### Changed

- Renamed web app title from Smart System A Agent to Gold Smart Agent.
- Removed visible risk settings from the sidebar.
- Reworked upload flow to use one combined OHLC CSV file.

## Initial Build

### Added

- Created Smart System A Python project.
- Added strict H4/H1 XAUUSD analysis.
- Added Elliott Wave context approximation.
- Added H1 BOS, breakout, pullback, candle, and volume analysis.
- Added six-condition SSA checklist.
- Added XAUUSD risk calculator and trade manager.
- Added CLI and Flask web app.
- Added Render deployment support.
