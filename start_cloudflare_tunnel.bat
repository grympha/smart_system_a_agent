@echo off
setlocal
cd /d "%~dp0"
if "%FLASK_PORT%"=="" set FLASK_PORT=5000
if "%CLOUDFLARED_PATH%"=="" set CLOUDFLARED_PATH=C:\Program Files (x86)\cloudflared\cloudflared.exe
if "%CLOUDFLARE_TUNNEL_CONFIG%"=="" set CLOUDFLARE_TUNNEL_CONFIG=config\cloudflare\tunnel.yml
if exist "%CLOUDFLARE_TUNNEL_CONFIG%" (
  "%CLOUDFLARED_PATH%" tunnel --config "%CLOUDFLARE_TUNNEL_CONFIG%" run
) else (
  "%CLOUDFLARED_PATH%" tunnel --url "http://127.0.0.1:%FLASK_PORT%" --no-autoupdate
)
