# Project Cleanup And Production Readiness Report

## Structure Review

- `web_app.py`: Flask dashboard, APIs, analysis orchestration, health/status endpoints.
- `mt5_bridge.py`: Windows-only local read-only MT5 bridge.
- `history_store.py`: SQLite analysis history.
- `screenshot_store.py`: SQLite screenshot persistence and pruning.
- `smart_system_a/`: Smart System A rules.
- `upas/`: UPAS price-action analysis.
- `wave_structure/`: Wave Structure Analyst.
- `elliot_wave3/`: Elliott Wave 3 module.
- `mt5/`: MQL5 push and auto-push scripts.
- `config/cloudflare/`: Named tunnel examples.

## Cleanup Performed

- Centralized local/cloud environment handling in `app_config.py`.
- Added local-first default ports and public base URL handling.
- Replaced Render defaults in MT5 EA files with configurable local-domain defaults.
- Added `/health` and `/api/status`.
- Added Windows startup scripts for app, bridge, tunnel, and full stack.
- Kept Render files as optional deployment assets.

## Dead Code / Duplicate Review

No large code removals were made in this pass. The analysis modules are actively referenced by `web_app.py` and tests. The older EA files remain intentionally as backups/manual options.

Potential future cleanup:

- Split `web_app.py` into route, template, MT5, notification, and analysis modules.
- Move the large inline HTML templates into `templates/`.
- Consider removing legacy on-demand MT5 request flow if the EA option fully replaces it.

## Production Readiness Review

### Flask Routes

Routes are functional. New health endpoints allow monitoring without scraping pages.

Recommendation:

- Add rate limiting before exposing the app publicly.
- Add optional basic authentication or Cloudflare Access for the dashboard.

### Error Handling

User-facing errors are mostly clear for MT5 bridge failures, CSV validation, and API upload failures.

Recommendation:

- Replace broad `except Exception` blocks with narrower exception types over time.
- Log traceback details to a local file while keeping UI messages concise.

### API Validation

`/api/analyze` validates missing OHLCV payloads and supports chart image payloads.

Recommendation:

- Add request-size and schema checks per analysis system.
- Add an API key for `/api/analyze` if public EA push should be private.

### SQLite Usage

SQLite is appropriate for local-first single-PC deployment.

Recommendation:

- Back up `analysis_history.db` regularly.
- Avoid multi-machine writes to the same database.
- Consider WAL mode if concurrent reads/writes become heavy.

### Screenshot Storage

Screenshots are stored in SQLite base64 payloads and pruned by analysis system.

Recommendation:

- Move screenshots to filesystem storage if DB size grows too quickly.
- Keep pruning enabled for public deployment.

### Logging

Current logging is mostly console/process output.

Recommendation:

- Add rotating file logs for app, bridge, and tunnel startup scripts.
- Keep MT5 EA logs reviewed for push errors.

## Security Recommendations

- Use a strong `MT5_BRIDGE_API_KEY`.
- Do not expose the MT5 bridge directly to the internet.
- Expose only the Flask app through Cloudflare Named Tunnel.
- Protect the public hostname with Cloudflare Access if possible.
- Keep `.env`, `analysis_history.db`, logs, and tunnel credentials out of Git.
- Rotate API keys if a quick tunnel URL or key was shared publicly.
