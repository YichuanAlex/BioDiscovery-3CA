$ErrorActionPreference = 'Stop'
$expectedRoot = 'C:\Users\User\Desktop\agentic\workflow_codex'
$workflowRoot = [IO.Path]::GetFullPath($PSScriptRoot)
if (-not $workflowRoot.Equals($expectedRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "This workflow must run from $expectedRoot; current root is $workflowRoot"
}

& (Join-Path $PSScriptRoot 'start-wingpt-server.ps1')

$nodePath = Join-Path $PSScriptRoot '.runtime\node-v24.21.0-win-x64\node.exe'
if (-not (Test-Path -LiteralPath $nodePath -PathType Leaf)) {
    throw 'Project-local Node.js v24.21.0 runtime is missing.'
}

$isolatedEnvironment = @{
    CODEX_HOME = (Join-Path $PSScriptRoot '.runtime\codex-home')
    THREECA_CACHE = (Join-Path $PSScriptRoot '.threeca\cache')
    PYTHONNOUSERSITE = '1'
    NODE_REPL_DISABLE_ANALYTICS = '1'
    WINGPT_CONTEXT_TOKENS = '262144'
}
$previousEnvironment = @{}
foreach ($name in $isolatedEnvironment.Keys) {
    $previousEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
    [Environment]::SetEnvironmentVariable($name, $isolatedEnvironment[$name], 'Process')
}
New-Item -ItemType Directory -Force -Path $isolatedEnvironment.CODEX_HOME, $isolatedEnvironment.THREECA_CACHE | Out-Null

Push-Location $PSScriptRoot
$runnerLock = $null
try {
    $taskArguments = @($args)
    $maxRoundsIndex = [Array]::IndexOf($taskArguments, '--max-rounds')
    $runUntilComplete = $taskArguments -contains '--autonomous' -and ($maxRoundsIndex -lt 0 -or $taskArguments[$maxRoundsIndex + 1] -eq '0')
    $attemptLimit = if ($taskArguments -contains '--autonomous') { 3 } else { 1 }
    $workspaceIndex = [Array]::IndexOf($taskArguments, '--workspace')
    $taskWorkspace = if ($workspaceIndex -ge 0) { (Resolve-Path -LiteralPath $taskArguments[$workspaceIndex + 1]).Path } else { $PSScriptRoot }
    $sha = [Security.Cryptography.SHA256]::Create()
    try { $taskHash = ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($taskWorkspace.ToLowerInvariant())))).Replace('-', '').ToLowerInvariant().Substring(0, 24) } finally { $sha.Dispose() }
    $checkpointPath = Join-Path $isolatedEnvironment.CODEX_HOME "tasks\$taskHash.json"
    if ($taskArguments -contains '--autonomous') {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $checkpointPath) | Out-Null
        $runnerLock = [IO.File]::Open("$checkpointPath.runner.lock", [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    }
    $attempt = 0
    while ($true) {
        $attempt++
        & $nodePath --no-maglev (Join-Path $PSScriptRoot 'codex-cli\bin\codex.js') --allow-network @taskArguments
        if ($LASTEXITCODE -eq 0) { break }
        $workerExitCode = $LASTEXITCODE
        $checkpoint = if (Test-Path -LiteralPath $checkpointPath) { Get-Content -LiteralPath $checkpointPath -Raw -Encoding UTF8 | ConvertFrom-Json } else { $null }
        $persistedInterruption = $checkpoint.status -eq 'interrupted' -and $checkpoint.last_error -match 'API (429|5\d\d)|fetch failed|timeout|abort|ECONN|socket|network|ENOSPC|EBUSY|EPERM'
        $retryableWorkerExit = $workerExitCode -eq 75
        if ((-not $runUntilComplete -and $attempt -ge $attemptLimit) -or -not $checkpoint -or (-not $persistedInterruption -and -not $retryableWorkerExit)) {
            throw "Local wingpt agent exited with code $workerExitCode; checkpoint status: $($checkpoint.status)."
        }
        $attemptLabel = if ($runUntilComplete) { "attempt $($attempt + 1), until complete" } else { "attempt $($attempt + 1)/$attemptLimit" }
        Write-Host "Recoverable local-model interruption; resuming the same persisted task ($attemptLabel)."
        if ($taskArguments -notcontains '--resume') { $taskArguments += '--resume' }
        Start-Sleep -Seconds 3
        & (Join-Path $PSScriptRoot 'start-wingpt-server.ps1')
    }
} finally {
    if ($runnerLock) { $runnerLock.Dispose() }
    Pop-Location
    foreach ($name in $isolatedEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($name, $previousEnvironment[$name], 'Process')
    }
}
