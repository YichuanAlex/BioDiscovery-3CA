$ErrorActionPreference = 'Stop'
$expectedRoot = 'C:\Users\User\Desktop\agentic\workflow_codex'
$workflowRoot = [IO.Path]::GetFullPath($PSScriptRoot)
if (-not $workflowRoot.Equals($expectedRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "This workflow must run from $expectedRoot; current root is $workflowRoot"
}

& (Join-Path $PSScriptRoot 'start-Qwen3.5-4B-server.ps1')

$nodePath = 'C:\Program Files\nodejs\node.exe'
if (-not (Test-Path -LiteralPath $nodePath)) {
    $node = Get-Command node -ErrorAction SilentlyContinue
    $nodePath = if ($node) { $node.Source } else { $null }
}
if (-not $nodePath) {
    throw 'Node.js 22+ is required to run the project-local Qwen3.5-4B agent.'
}

$isolatedEnvironment = @{
    CODEX_HOME = (Join-Path $PSScriptRoot '.runtime\codex-home')
    CODEX_CLI_PATH = (Join-Path $PSScriptRoot 'codex-local.cmd')
    THREECA_CACHE = (Join-Path $PSScriptRoot '.threeca\cache')
    PYTHONNOUSERSITE = '1'
    NODE_REPL_DISABLE_ANALYTICS = '1'
    BROWSER_USE_DISABLE_AMBIENT_NETWORK = '1'
}
$localAppServer = Join-Path $PSScriptRoot 'app-server'
$localCodexEntry = Join-Path $PSScriptRoot 'codex-local.cmd'
if (-not (Test-Path -LiteralPath $localAppServer -PathType Leaf) -or -not (Test-Path -LiteralPath $localCodexEntry -PathType Leaf)) {
    throw 'Project-local Computer Use app-server entry is missing.'
}
$previousEnvironment = @{}
foreach ($name in $isolatedEnvironment.Keys) {
    $previousEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
    [Environment]::SetEnvironmentVariable($name, $isolatedEnvironment[$name], 'Process')
}
New-Item -ItemType Directory -Force -Path $isolatedEnvironment.CODEX_HOME, $isolatedEnvironment.THREECA_CACHE | Out-Null

Push-Location $PSScriptRoot
try {
    $taskArguments = @($args)
    $attemptLimit = if ($taskArguments -contains '--autonomous') { 3 } else { 1 }
    for ($attempt = 1; $attempt -le $attemptLimit; $attempt++) {
        & $nodePath (Join-Path $PSScriptRoot 'codex-cli\bin\codex.js') --allow-network @taskArguments
        if ($LASTEXITCODE -eq 0) { break }
        $workerExitCode = $LASTEXITCODE
        $workspaceIndex = [Array]::IndexOf($taskArguments, '--workspace')
        $taskWorkspace = if ($workspaceIndex -ge 0) { (Resolve-Path -LiteralPath $taskArguments[$workspaceIndex + 1]).Path } else { $PSScriptRoot }
        $checkpoint = Get-ChildItem -LiteralPath (Join-Path $isolatedEnvironment.CODEX_HOME 'tasks') -Filter '*.json' -File -ErrorAction SilentlyContinue |
            ForEach-Object { Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json } |
            Where-Object { $_.workspace -eq $taskWorkspace } | Select-Object -First 1
        if ($attempt -ge $attemptLimit -or -not $checkpoint -or $checkpoint.status -ne 'interrupted' -or $checkpoint.last_error -notmatch 'API (429|5\d\d)|fetch failed|timeout|abort|ECONN|socket|network|ENOSPC|EBUSY|EPERM') {
            throw "Local Qwen3.5-4B agent exited with code $workerExitCode; checkpoint status: $($checkpoint.status)."
        }
        Write-Host "Recoverable local-model interruption; resuming the same persisted task (attempt $($attempt + 1)/$attemptLimit)."
        if ($taskArguments -notcontains '--resume') { $taskArguments += '--resume' }
        Start-Sleep -Seconds 3
        & (Join-Path $PSScriptRoot 'start-Qwen3.5-4B-server.ps1')
    }
} finally {
    Pop-Location
    foreach ($name in $isolatedEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($name, $previousEnvironment[$name], 'Process')
    }
}
