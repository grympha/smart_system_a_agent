@echo off
setlocal
cd /d "%~dp0"
if "%MT5_BRIDGE_API_KEY%"=="" set MT5_BRIDGE_API_KEY=change-this-local-secret
start "Gold Smart Agent - MT5 Bridge" cmd /k "%~dp0start_mt5_bridge.bat"
timeout /t 3 /nobreak >nul
start "Gold Smart Agent - Flask App" cmd /k "%~dp0start_local.bat"
timeout /t 3 /nobreak >nul
start "Gold Smart Agent - Cloudflare Tunnel" cmd /k "%~dp0start_cloudflare_tunnel.bat"
