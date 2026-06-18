# Local Deployment Test Checklist

Use this checklist after setting up Gold Smart Agent on a local Windows PC with Cloudflare Named Tunnel.

Target local defaults:

```text
Flask app:      http://127.0.0.1:5000
MT5 bridge:     http://127.0.0.1:5001
Public URL:     https://agent.my-domain.com
```

## 1. Flask App Startup

1. Open a terminal in the project folder.
2. Confirm dependencies are installed:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

3. Start the Flask app:

```cmd
start_local.bat
```

4. Open:

```text
http://127.0.0.1:5000
```

Expected result:

- Gold Smart Agent dashboard loads.
- Analysis System dropdown is visible.
- Data Source dropdown is visible.

## 2. MT5 Bridge Startup

1. Open MetaTrader 5.
2. Confirm MT5 is logged in.
3. Start the bridge:

```cmd
start_mt5_bridge.bat
```

4. Test bridge status:

```powershell
Invoke-WebRequest -Uri http://127.0.0.1:5001/api/mt5/status -Headers @{ "X-API-Key" = $env:MT5_BRIDGE_API_KEY } -UseBasicParsing
```

Expected result:

- HTTP status is `200`.
- `connected` is `true`.
- `logged_in` is `true`.
- `symbol_available` is `true`.

## 3. Cloudflare Tunnel Startup

1. Confirm `cloudflared` is installed.
2. Confirm `config/cloudflare/tunnel.yml` exists for a named tunnel.
3. Start the tunnel:

```cmd
start_cloudflare_tunnel.bat
```

Expected result:

- Tunnel process remains running.
- Cloudflare hostname points to `http://127.0.0.1:5000`.
- Public URL opens the Gold Smart Agent dashboard.

## 4. `/health` Endpoint

Test locally:

```powershell
Invoke-WebRequest -Uri http://127.0.0.1:5000/health -UseBasicParsing
```

Expected result:

```json
{"ok": true, "status": "READY"}
```

## 5. `/api/status` Endpoint

Test locally:

```powershell
Invoke-WebRequest -Uri http://127.0.0.1:5000/api/status -UseBasicParsing
```

Expected result:

- `ok` is `true`.
- `application.mode` is `local`.
- `database.ok` is `true`.
- `storage.ok` is `true`.
- `screenshots.ok` is `true`.
- `mt5_bridge.status` is `connected`.

## 6. MT5 Direct Mode

1. Open the local dashboard.
2. Select an analysis system.
3. Set Data Source to `MT5 Direct Mode`.
4. Click `Run Analysis`.

Expected result:

- No bridge error appears.
- Result renders for the selected analysis system.
- MT5 Data Status shows 300 candles per required timeframe.
- Recent Analysis History receives a new row.

## 7. Auto-Push EA

1. In MT5, attach `GoldSmartAgent_AutoPushOHLC_EA_V4` to an XAUUSD chart.
2. Set:

```text
InpEndpoint=https://agent.my-domain.com/api/analyze
InpBarsPerTimeframe=300
InpPushIntervalSeconds=300
```

3. In MT5, allow WebRequest for:

```text
https://agent.my-domain.com
```

4. Wait for the first push cycle or reattach the EA with `InpPushOnStart=true`.

Expected result:

- MT5 Experts log shows HTTP status `200`.
- App Recent Analysis History shows pushed results.
- Data Source `MT5 Auto-Push EA` can show the latest pushed result.

## 8. Screenshot Upload

Manual dashboard test:

1. Open the dashboard.
2. Upload a `.png`, `.jpg`, `.jpeg`, or `.webp` chart screenshot.
3. Click `Run Analysis`.

Expected result:

- Screenshot preview renders.
- No server error occurs.

EA/API test:

- Confirm EA pushes `chart_images` with H1 and H4 screenshots.
- Open the latest history detail.

Expected result:

- H1 preview appears.
- H4 preview appears.
- Clicking a chart opens the preview modal.

## 9. OHLCV Payload Validation

Valid CSV/API payload must include:

```text
timeframe,timestamp,open,high,low,close,volume
```

Test each system:

- Smart System A: `H4`, `H1`
- UPAS: `MN1`, `W1`, `D1`, `H4`, `H1`
- Wave Structure Analyst: `D1`, `H4`, `H1`
- Elliot Wave 3 Analysis: `H4`, `H1`, `M15`

Expected result:

- Valid OHLCV payload returns `ok=true` through `/api/analyze`.
- Missing timeframe produces a clear input error.
- Invalid CSV columns produce a clear validation error.

## 10. SQLite History Save

1. Run any analysis.
2. Confirm Recent Analysis History updates.
3. Open a history row.

Expected result:

- `/history/<id>` opens.
- Raw detail is present.
- Dashboard sections render.

Optional local database check:

```powershell
.\.venv\Scripts\python.exe -c "import sqlite3; c=sqlite3.connect('analysis_history.db'); print(c.execute('select count(*) from analysis_history').fetchone()[0])"
```

## 11. Public Cloudflare URL Test

Replace the sample domain with your hostname:

```powershell
Invoke-WebRequest -Uri https://agent.my-domain.com/health -UseBasicParsing
Invoke-WebRequest -Uri https://agent.my-domain.com/api/status -UseBasicParsing
```

Expected result:

- Public `/health` returns ready.
- Public `/api/status` returns app and bridge status.
- Dashboard loads in a browser from the public URL.

## Common Troubleshooting

### Flask App Does Not Open

- Confirm `start_local.bat` is running.
- Confirm port `5000` is free.
- Check `.env` for `FLASK_PORT`.

### MT5 Bridge Unreachable

- Confirm MT5 is open and logged in.
- Confirm `start_mt5_bridge.bat` is running.
- Confirm `MT5_BRIDGE_API_KEY` matches the app.
- Test `http://127.0.0.1:5001/api/mt5/status`.

### MT5 Direct Mode Fails

- Check `/api/status`.
- Confirm `MT5_BRIDGE_URL=http://127.0.0.1:5001`.
- Confirm `MT5_BRIDGE_API_KEY` is set in both app and bridge.
- Confirm XAUUSD is visible in MT5 Market Watch.

### Public URL Fails

- Confirm Cloudflare tunnel is running.
- Confirm `tunnel.yml` points to `http://127.0.0.1:5000`.
- Confirm DNS hostname is routed to the named tunnel.

### Auto-Push EA Fails

- Confirm `InpEndpoint` is the public `/api/analyze` URL.
- Confirm MT5 WebRequest allows the public base URL.
- Check MT5 Experts log for HTTP status and error codes.
- Reattach EA after changing inputs.

### Screenshots Missing

- Confirm EA is V4.
- Confirm chart screenshot calls are not blocked in MT5.
- Open latest history detail and check chart preview section.

## Final Pass/Fail Table

| Check | Expected Result | Pass/Fail | Notes |
|---|---|---|---|
| Flask app startup | Dashboard opens on `127.0.0.1:5000` |  |  |
| MT5 bridge startup | `/api/mt5/status` returns connected |  |  |
| Cloudflare tunnel startup | Public hostname opens dashboard |  |  |
| `/health` endpoint | Returns `ok=true`, `READY` |  |  |
| `/api/status` endpoint | App, DB, storage, screenshot, bridge statuses visible |  |  |
| MT5 Direct Mode | Analysis runs from local bridge data |  |  |
| Auto-Push EA | MT5 logs HTTP `200`, history updates |  |  |
| Screenshot upload | Preview renders and saves |  |  |
| OHLCV validation | Valid payload works, invalid payload errors clearly |  |  |
| SQLite history save | New analysis appears in history |  |  |
| Public Cloudflare URL | Public `/health` and dashboard work |  |  |
| Security review | Strong keys, private `.env`, Cloudflare protection considered |  |  |
