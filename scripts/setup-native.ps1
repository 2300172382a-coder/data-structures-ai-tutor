[CmdletBinding()]
param(
    [string]$RuntimeRoot = "",
    [string]$OpenWebUIVersion = "0.11.3"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if (-not $RuntimeRoot) {
    $RuntimeRoot = Join-Path $ProjectRoot ".runtime"
}
$RuntimeRoot = [IO.Path]::GetFullPath($RuntimeRoot)
$ModelsRoot = Join-Path $RuntimeRoot "models"
$VenvRoot = Join-Path $RuntimeRoot "openwebui-venv"
$DataRoot = Join-Path $RuntimeRoot "openwebui-data"

New-Item -ItemType Directory -Force -Path $RuntimeRoot, $ModelsRoot, $DataRoot | Out-Null

$uv = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uv) {
    throw "uv was not found. Install it from https://docs.astral.sh/uv/ and rerun this script."
}

if (-not (Test-Path -LiteralPath (Join-Path $VenvRoot "Scripts\open-webui.exe"))) {
    & $uv.Source venv --python 3.11 $VenvRoot
    & $uv.Source pip install --python (Join-Path $VenvRoot "Scripts\python.exe") "open-webui==$OpenWebUIVersion"
}

$ModelPath = Join-Path $ModelsRoot "qwen2.5-3b-instruct-q4_k_m.gguf"
if (-not (Test-Path -LiteralPath $ModelPath)) {
    $ModelUrl = "https://modelscope.cn/models/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/master/qwen2.5-3b-instruct-q4_k_m.gguf"
    & curl.exe -L --fail --retry 5 --retry-delay 2 -o $ModelPath $ModelUrl
}

$EmbeddingPath = Join-Path $ModelsRoot "bge-small-zh-v1.5"
if (-not (Test-Path -LiteralPath (Join-Path $EmbeddingPath "model.safetensors"))) {
    $git = Get-Command git -ErrorAction SilentlyContinue
    if (-not $git) {
        throw "Git was not found, so the Chinese embedding model cannot be downloaded."
    }
    & $git.Source clone --depth 1 "https://www.modelscope.cn/BAAI/bge-small-zh-v1.5.git" $EmbeddingPath
}

$LlamaCandidates = @(@(
    $env:LLAMA_SERVER_PATH,
    (Join-Path $env:LOCALAPPDATA "Programs\DockerDesktop\resources\model-runner\bin\com.docker.llama-server.exe"),
    (Join-Path $RuntimeRoot "llama-server.exe")
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) })
if (-not $LlamaCandidates) {
    $command = Get-Command llama-server -ErrorAction SilentlyContinue
    if ($command) { $LlamaCandidates = @($command.Source) }
}
if (-not $LlamaCandidates) {
    throw "llama-server was not found. Install Docker Desktop for its local binary (containers are not required), or set LLAMA_SERVER_PATH."
}
Set-Content -LiteralPath (Join-Path $RuntimeRoot "llama-server-path.txt") -Value $LlamaCandidates[0] -NoNewline

$SecretPath = Join-Path $RuntimeRoot "webui-secret.txt"
if (-not (Test-Path -LiteralPath $SecretPath)) {
    $secret = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
    Set-Content -LiteralPath $SecretPath -Value $secret -NoNewline
}

Write-Host "Native runtime is ready: $RuntimeRoot"
Write-Host "Next: powershell -ExecutionPolicy Bypass -File .\scripts\start-native.ps1"
