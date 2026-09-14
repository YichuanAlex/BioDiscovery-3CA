param([switch]$Stop)

$ErrorActionPreference = 'Stop'
$expectedRoot = 'C:\Users\User\Desktop\agentic\workflow_codex'
$workflowRoot = [IO.Path]::GetFullPath($PSScriptRoot)
if (-not $workflowRoot.Equals($expectedRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "This workflow must run from $expectedRoot; current root is $workflowRoot"
}
$distro = 'Ubuntu-22.04'
$modelName = 'Qwen3.5-4B'
$windowsModel = 'C:\Users\User\Desktop\Winning Health\winning_Qwen3.5-4B\Qwen3.5-4B4\model\Qwen3.5-4B'
$wslModelSource = '/mnt/c/Users/User/Desktop/Winning Health/winning_Qwen3.5-4B/Qwen3.5-4B4/model/Qwen3.5-4B'
$wslModel = '/home/jiangzixi/Qwen3.5-4B'
$venv = '/home/jiangzixi/.venvs/Qwen3.5-4B4'
$healthUrl = 'http://127.0.0.1:8000/health'
$logRoot = Join-Path $workflowRoot '.runtime\logs'
$startupId = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$stdoutLog = Join-Path $logRoot "Qwen3.5-4B4-vllm-$startupId.stdout.log"
$stderrLog = Join-Path $logRoot "Qwen3.5-4B4-vllm-$startupId.stderr.log"
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null

function Test-Qwen3.5-4BHealth {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -TimeoutSec 2
        if ($response.StatusCode -ne 200) { return $false }
        $models = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/v1/models' -TimeoutSec 2
        return @($models.data.id) -contains $modelName
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

$startupMutex = [Threading.Mutex]::new($false, 'Local\WorkflowCodexQwen3.5-4B8000')
$ownsStartupMutex = $false
try {
try { $ownsStartupMutex = $startupMutex.WaitOne(360000) } catch [Threading.AbandonedMutexException] { $ownsStartupMutex = $true }
if (-not $ownsStartupMutex) { throw 'Another project-local startup/stop is still running; no duplicate server was launched.' }

if ($Stop) {
    [void](Invoke-WslQuiet @('-d', $distro, '--exec', '/usr/bin/pkill', '-f', "$venv/bin/vllm serve $wslModel"))
    Write-Host 'Qwen3.5-4B local server stopped.'
    exit 0
}

if (Test-Qwen3.5-4BHealth) {
    Write-Host "Qwen3.5-4B local server is ready: $healthUrl"
    exit 0
}

if (-not (Test-Path -LiteralPath $windowsModel)) {
    throw "Model directory not found: $windowsModel"
}

$wslExitCode = Invoke-WslQuiet @('-d', $distro, '--exec', '/usr/bin/test', '-x', "$venv/bin/vllm")
if ($wslExitCode -ne 0) {
    throw "vLLM environment not found: $venv"
}

$wslExitCode = Invoke-WslQuiet @('-d', $distro, '--exec', '/bin/ln', '-sfn', $wslModelSource, $wslModel)
if ($wslExitCode -ne 0) {
    throw "Could not create the WSL model link: $wslModel"
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
    '--max-model-len', '65536',
    '--gpu-memory-utilization', '0.92',
    '--kv-cache-dtype', 'fp8',
    '--max-num-seqs', '1',
    '--attention-backend', 'TRITON_ATTN',
    '--enable-auto-tool-choice',
    '--tool-call-parser', 'qwen3_xml',
    '--reasoning-parser', 'qwen3',
    '--generation-config', 'vllm'
)

$existingServer = & wsl.exe -d $distro --exec /usr/bin/pgrep -af "$venv/bin/vllm serve $wslModel"
$process = $null
if ($LASTEXITCODE -eq 0 -and $existingServer) {
    Write-Host 'An existing Qwen3.5-4B server is initializing; waiting instead of launching a duplicate.'
} else {
    Write-Host 'Starting Qwen3.5-4B; first startup usually takes about two minutes...'
    $process = Start-Process -FilePath 'wsl.exe' -ArgumentList $wslArgs -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog
}

for ($attempt = 0; $attempt -lt 180; $attempt++) {
    if (Test-Qwen3.5-4BHealth) {
        Write-Host "Qwen3.5-4B local server is ready: $healthUrl"
        exit 0
    }
    if ($process -and $process.HasExited) { break }
    Start-Sleep -Seconds 2
}

$details = if (Test-Path -LiteralPath $stderrLog) {
    (Get-Content -LiteralPath $stderrLog -Tail 30) -join [Environment]::NewLine
} else {
    'No error log was generated.'
}
throw "Qwen3.5-4B server failed to start; no duplicate replacement launched. Log: $stderrLog`nExisting process: $existingServer`n$details"
} finally {
    if ($ownsStartupMutex) { $startupMutex.ReleaseMutex() }
    $startupMutex.Dispose()
}
