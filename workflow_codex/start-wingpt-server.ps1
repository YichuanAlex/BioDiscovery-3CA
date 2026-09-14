param([switch]$Stop)

$ErrorActionPreference = 'Stop'
$expectedRoot = 'C:\Users\User\Desktop\agentic\workflow_codex'
$workflowRoot = [IO.Path]::GetFullPath($PSScriptRoot)
if (-not $workflowRoot.Equals($expectedRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "This workflow must run from $expectedRoot; current root is $workflowRoot"
}
$distro = 'Ubuntu-22.04'
$modelName = 'Qwen3.5-4B'
$windowsModel = 'C:\Users\User\Desktop\agentic\model\Qwen3.5-4B'
$wslModel = '/mnt/c/Users/User/Desktop/agentic/model/Qwen3.5-4B'
$venv = '/home/jiangzixi/.venvs/wingpt4'
$healthUrl = 'http://127.0.0.1:8000/health'
$logRoot = Join-Path $workflowRoot '.runtime\logs'
$startupId = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$stdoutLog = Join-Path $logRoot "qwen35-vllm-$startupId.stdout.log"
$stderrLog = Join-Path $logRoot "qwen35-vllm-$startupId.stderr.log"
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null

function Test-WiNGPTHealth {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -TimeoutSec 2
        if ($response.StatusCode -ne 200) { return $false }
        $models = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/v1/models' -TimeoutSec 2
        return @($models.data | Where-Object { $_.id -eq $modelName -and $_.root -eq $wslModel }).Count -eq 1
    } catch {
        return $false
    }
}

function Invoke-WslQuiet([string[]]$Arguments) {
    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = 'SilentlyContinue'
    try {
        & wsl.exe @Arguments 2>$null
        return $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorAction
    }
}

$startupMutex = [Threading.Mutex]::new($false, 'Local\WorkflowCodexWiNGPT8000')
$ownsStartupMutex = $false
try {
try { $ownsStartupMutex = $startupMutex.WaitOne() } catch [Threading.AbandonedMutexException] { $ownsStartupMutex = $true }
if (-not $ownsStartupMutex) { throw 'Another project-local startup/stop is still running; no duplicate server was launched.' }

if ($Stop) {
    [void](Invoke-WslQuiet @('-d', $distro, '--exec', '/usr/bin/pkill', '-f', "$venv/bin/vllm serve $wslModel"))
    Write-Host "$modelName local server stopped."
    exit 0
}

if (Test-WiNGPTHealth) {
    Write-Host "$modelName local server is ready: $healthUrl"
    exit 0
}

if (-not (Test-Path -LiteralPath $windowsModel)) {
    throw "Model directory not found: $windowsModel"
}

$wslExitCode = Invoke-WslQuiet @('-d', $distro, '--exec', '/usr/bin/test', '-x', "$venv/bin/vllm")
if ($wslExitCode -ne 0) {
    throw "vLLM environment not found: $venv"
}

$wslArgs = @(
    '-d', $distro, '--exec', '/usr/bin/env',
    'HOME=/home/jiangzixi',
    "PATH=$venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
    'HF_HUB_OFFLINE=1',
    'TRANSFORMERS_OFFLINE=1',
    'VLLM_USE_FLASHINFER_SAMPLER=0',
    "$venv/bin/vllm", 'serve', $wslModel,
    '--served-model-name', $modelName,
    '--host', '127.0.0.1',
    '--port', '8000',
    '--language-model-only',
    '--max-model-len', '262144',
    '--gpu-memory-utilization', '0.92',
    '--kv-cache-dtype', 'fp8',
    '--max-num-seqs', '1',
    '--attention-backend', 'TRITON_ATTN',
    '--enable-auto-tool-choice',
    '--tool-call-parser', 'qwen3_coder',
    '--reasoning-parser', 'qwen3',
    '--generation-config', 'vllm'
)

$existingServer = & wsl.exe -d $distro --exec /usr/bin/pgrep -af "$venv/bin/vllm serve $wslModel"
$process = $null
if ($LASTEXITCODE -eq 0 -and $existingServer) {
    Write-Host "An existing $modelName server is initializing; waiting instead of launching a duplicate."
} else {
    Write-Host "Starting $modelName from the requested local weights; waiting for health and model identity..."
    $process = Start-Process -FilePath 'wsl.exe' -ArgumentList $wslArgs -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog
}

while ($true) {
    if (Test-WiNGPTHealth) {
        Write-Host "$modelName local server is ready: $healthUrl"
        exit 0
    }
    if ($process -and $process.HasExited) { break }
    if (-not $process) {
        & wsl.exe -d $distro --exec /usr/bin/pgrep -f "$venv/bin/vllm serve $wslModel" 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) { break }
    }
    Start-Sleep -Seconds 2
}

$details = if (Test-Path -LiteralPath $stderrLog) {
    (Get-Content -LiteralPath $stderrLog -Tail 30) -join [Environment]::NewLine
} else {
    'No error log was generated.'
}
throw "$modelName server failed to start; no duplicate replacement launched. Log: $stderrLog`nExisting process: $existingServer`n$details"
} finally {
    if ($ownsStartupMutex) { $startupMutex.ReleaseMutex() }
    $startupMutex.Dispose()
}
