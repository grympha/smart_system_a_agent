param(
    [string]$BridgeUrl = "http://127.0.0.1:5000",
    [string]$CloudflaredPath = ".\tools\cloudflared.exe",
    [ValidateSet("http2", "quic", "auto")]
    [string]$Protocol = "http2"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

if (-not (Test-Path $CloudflaredPath)) {
    throw "cloudflared.exe not found at $CloudflaredPath. Download it from https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
}

$args = @("tunnel", "--url", $BridgeUrl, "--no-autoupdate")
if ($Protocol -ne "auto") {
    $args += @("--protocol", $Protocol)
}

& $CloudflaredPath @args
