[CmdletBinding()]
param(
    [string]$RuntimeRoot = "",
    [int]$WebPort = 3000,
    [int]$ModelPort = 11435,
    [ValidateRange(4096, 32768)]
    [int]$ContextSize = 16384,
    [ValidateRange(1, 4)]
    [int]$ParallelSlots = 1,
    [switch]$OpenBrowser
)

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
$ModelsRoot = Join-Path $RuntimeRoot "models"
$DataRoot = Join-Path $RuntimeRoot "openwebui-data"
$OpenWebUI = Join-Path $RuntimeRoot "openwebui-venv\Scripts\open-webui.exe"
$ModelPath = Join-Path $ModelsRoot "qwen2.5-3b-instruct-q4_k_m.gguf"
$EmbeddingPath = Join-Path $ModelsRoot "bge-small-zh-v1.5"
$LlamaPathFile = Join-Path $RuntimeRoot "llama-server-path.txt"
$SecretPath = Join-Path $RuntimeRoot "webui-secret.txt"

foreach ($required in @($OpenWebUI, $ModelPath, (Join-Path $EmbeddingPath "model.safetensors"), $LlamaPathFile)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Runtime is incomplete: missing $required. Run scripts\setup-native.ps1 first."
    }
}
$LlamaServer = (Get-Content -LiteralPath $LlamaPathFile -Raw).Trim()
if (-not (Test-Path -LiteralPath $LlamaServer)) {
    throw "llama-server path is invalid: $LlamaServer"
}

$PidRoot = Join-Path $RuntimeRoot "pids"
$LogRoot = Join-Path $RuntimeRoot "logs"
New-Item -ItemType Directory -Force -Path $PidRoot, $LogRoot, $DataRoot | Out-Null

try { $modelHealthy = (Invoke-RestMethod -Uri "http://127.0.0.1:$ModelPort/health" -TimeoutSec 2).status -eq "ok" } catch { $modelHealthy = $false }
if (-not $modelHealthy) {
    $llamaArgs = @(
        "--model", ('"' + $ModelPath + '"'),
        "--alias", "qwen2.5-3b-instruct",
        "--host", "127.0.0.1",
        "--port", "$ModelPort",
        # llama-server divides --ctx-size across parallel slots. A single
        # 16K slot safely fits the course prompt, RAG context and response.
        "--ctx-size", "$ContextSize",
        "--parallel", "$ParallelSlots",
        "--cache-ram", "1024",
        "--jinja", "--no-ui"
    )
    $modelProcess = Start-Process -FilePath $LlamaServer -ArgumentList $llamaArgs -WorkingDirectory $ProjectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $LogRoot "model.out.log") -RedirectStandardError (Join-Path $LogRoot "model.err.log")
    Set-Content -LiteralPath (Join-Path $PidRoot "model.pid") -Value $modelProcess.Id -NoNewline
}

for ($i = 0; $i -lt 90; $i++) {
    try {
        Invoke-RestMethod -Uri "http://127.0.0.1:$ModelPort/health" -TimeoutSec 2 | Out-Null
        break
    } catch {
        if ($i -eq 89) { throw "The local model did not become ready in 90 seconds. Check $LogRoot\model.err.log" }
        Start-Sleep -Seconds 1
    }
}

if (-not (Test-Path -LiteralPath $SecretPath)) {
    $secret = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
    Set-Content -LiteralPath $SecretPath -Value $secret -NoNewline
}
$env:DATA_DIR = $DataRoot
$env:WEBUI_AUTH = "True"
$env:WEBUI_NAME = "Data Structures AI Tutor"
$env:WEBUI_SECRET_KEY = (Get-Content -LiteralPath $SecretPath -Raw).Trim()
$env:OPENAI_API_BASE_URL = "http://127.0.0.1:$ModelPort/v1"
$env:OPENAI_API_KEY = "local-no-key"
$env:ENABLE_OLLAMA_API = "False"
$env:RAG_EMBEDDING_MODEL = $EmbeddingPath
$env:RAG_EMBEDDING_MODEL_AUTO_UPDATE = "False"
$env:OFFLINE_MODE = "True"
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"

try { $webHealthy = (Invoke-RestMethod -Uri "http://127.0.0.1:$WebPort/health" -TimeoutSec 2).status -eq $true } catch { $webHealthy = $false }
if (-not $webHealthy) {
    $webArgs = @("serve", "--host", "127.0.0.1", "--port", "$WebPort")
    $webProcess = Start-Process -FilePath $OpenWebUI -ArgumentList $webArgs -WorkingDirectory $ProjectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $LogRoot "openwebui.out.log") -RedirectStandardError (Join-Path $LogRoot "openwebui.err.log")
    Set-Content -LiteralPath (Join-Path $PidRoot "openwebui.pid") -Value $webProcess.Id -NoNewline
}

for ($i = 0; $i -lt 120; $i++) {
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:$WebPort/health" -TimeoutSec 2
        if ($health.status -eq $true) { break }
    } catch {}
    if ($i -eq 119) { throw "Open WebUI did not become ready in 120 seconds. Check $LogRoot\openwebui.err.log" }
    Start-Sleep -Seconds 1
}

$url = "http://127.0.0.1:$WebPort"
Write-Host "Ready: $url"
Write-Host "Model context: $ContextSize tokens across $ParallelSlots slot(s)"
Write-Host "Stop: powershell -ExecutionPolicy Bypass -File .\scripts\stop-native.ps1"
if ($OpenBrowser) { Start-Process $url }
