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

$runtimePython = Join-Path ([IO.Path]::GetFullPath($RuntimeRoot)) "openwebui-venv\Scripts\python.exe"
$python = if (Test-Path -LiteralPath $runtimePython) {
    $runtimePython
} else {
    $command = Get-Command python -ErrorAction SilentlyContinue
    if (-not $command) {
        throw "Python was not found. Run scripts\setup-native.ps1 first."
    }
    $command.Source
}

Push-Location $ProjectRoot
try {
    & $python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw "Unit tests failed." }

    & $python scripts\validate_data.py
    if ($LASTEXITCODE -ne 0) { throw "Data validation failed." }

    & $python -m py_compile `
        openwebui-tools\data_structures_question_bank.py `
        scripts\bootstrap_openwebui.py `
        scripts\run_acceptance.py `
        scripts\render_acceptance_report.py `
        scripts\validate_data.py
    if ($LASTEXITCODE -ne 0) { throw "Python syntax validation failed." }

    & $python scripts\render_acceptance_report.py
    if ($LASTEXITCODE -ne 0) { throw "Acceptance report rendering failed." }

    Write-Host "All project checks passed."
} finally {
    Pop-Location
}
