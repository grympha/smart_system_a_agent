@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3.11 -m venv .venv
)
set APP_MODE=local
if "%MT5_BRIDGE_HOST%"=="" set MT5_BRIDGE_HOST=127.0.0.1
if "%MT5_BRIDGE_PORT%"=="" set MT5_BRIDGE_PORT=5001
if "%MT5_BRIDGE_API_KEY%"=="" set MT5_BRIDGE_API_KEY=change-this-local-secret
if "%MT5_TERMINAL_PATH%"=="" set MT5_TERMINAL_PATH=C:\Program Files\RoboForex MT5 Terminal\terminal64.exe
".venv\Scripts\python.exe" mt5_bridge.py
