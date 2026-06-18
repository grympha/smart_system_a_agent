@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3.11 -m venv .venv
)
set APP_MODE=local
if "%FLASK_HOST%"=="" set FLASK_HOST=127.0.0.1
if "%FLASK_PORT%"=="" set FLASK_PORT=5000
if "%MT5_BRIDGE_HOST%"=="" set MT5_BRIDGE_HOST=127.0.0.1
if "%MT5_BRIDGE_PORT%"=="" set MT5_BRIDGE_PORT=5001
if "%MT5_BRIDGE_URL%"=="" set MT5_BRIDGE_URL=http://%MT5_BRIDGE_HOST%:%MT5_BRIDGE_PORT%
if "%MT5_BRIDGE_API_KEY%"=="" set MT5_BRIDGE_API_KEY=change-this-local-secret
".venv\Scripts\python.exe" web_app.py
