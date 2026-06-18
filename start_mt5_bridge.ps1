param(
    [Parameter(Mandatory = $true)]
    [string]$ApiKey,

    [string]$TerminalPath = "C:\Program Files\RoboForex MT5 Terminal\terminal64.exe",
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 5001
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

$env:MT5_BRIDGE_API_KEY = $ApiKey
$env:MT5_TERMINAL_PATH = $TerminalPath
$env:MT5_BRIDGE_HOST = $HostAddress
$env:MT5_BRIDGE_PORT = [string]$Port

Set-Location $ProjectRoot
python mt5_bridge.py
