[CmdletBinding()]
param([string]$RuntimeRoot = "")

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if (-not $RuntimeRoot) {
    $marker = Join-Path $ProjectRoot ".runtime-path"
    $RuntimeRoot = if (Test-Path -LiteralPath $marker) {
        (Get-Content -LiteralPath $marker -Raw).Trim()
    } else {
        Join-Path $ProjectRoot ".runtime"
    }
}
$RuntimeRoot = [IO.Path]::GetFullPath($RuntimeRoot)
$PidRoot = Join-Path $RuntimeRoot "pids"

foreach ($name in @("openwebui", "model")) {
    $pidFile = Join-Path $PidRoot "$name.pid"
    if (-not (Test-Path -LiteralPath $pidFile)) { continue }
    $processId = [int](Get-Content -LiteralPath $pidFile -Raw)
    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
    if ($process) {
        Stop-Process -Id $processId
        Write-Host "Stopped $name (PID $processId)"
    }
    Remove-Item -LiteralPath $pidFile -Force
}
