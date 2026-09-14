param([switch]$RetryAfterInfrastructureFailure)
$ErrorActionPreference = 'Stop'
$workflowRoot = 'C:\Users\User\Desktop\agentic\workflow_codex'
$taskRoot = 'C:\Users\User\Desktop\agentic\3CA\Q1_R2'
$attempt = 1
if ($RetryAfterInfrastructureFailure) {
    $latestManifest = Get-ChildItem -LiteralPath $PSScriptRoot -Filter 'run-manifest*.json' -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    $latest = Get-Content -LiteralPath $latestManifest.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
    $attempt = if ($latest.attempt) { [int]$latest.attempt + 1 } else { 2 }
    if ($attempt -gt 3) { throw 'Pre-research infrastructure retry limit exhausted; do not hide repeated launch failures.' }
}
$manifestName = if ($attempt -eq 1) { 'run-manifest.json' } else { "run-manifest-attempt$attempt.json" }
$manifestPath = Join-Path $PSScriptRoot $manifestName
if (Test-Path -LiteralPath $manifestPath) { throw 'R2 already has a launch manifest; do not launch a duplicate.' }
if ($RetryAfterInfrastructureFailure) {
    $previousResultName = if ($attempt -eq 2) { 'runner-result.json' } else { "runner-result-attempt$($attempt - 1).json" }
    $previousLogName = if ($attempt -eq 2) { 'worker' } else { "worker-attempt$($attempt - 1)" }
    $previous = Get-Content -LiteralPath (Join-Path $PSScriptRoot $previousResultName) -Raw -Encoding UTF8 | ConvertFrom-Json
    $previousErrors = Get-Content -LiteralPath (Join-Path $PSScriptRoot "logs\$previousLogName.stderr.log") -Raw -Encoding UTF8
    if ($previous.runner_success -or $previousErrors -notmatch 'ENOSPC|A persisted task already exists') { throw 'This retry is restricted to the recorded pre-research infrastructure failures.' }
}
if (@(Get-ChildItem -LiteralPath $taskRoot -Force).Count -ne 0) { throw 'R2 research workspace is not empty; refusing a contaminated fresh run.' }
$testOutput = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'logs\engineering-tests.stdout.log') -Raw -Encoding UTF8
if (-not $testOutput.Contains('PASS: workflow_codex functional test completed.')) { throw 'Final full integration test has not completed successfully.' }
$activeFiles = @('run-Qwen3.5-4B.ps1', 'start-Qwen3.5-4B-server.ps1', 'codex-cli\bin\codex.js', 'codex-cli\bin\Qwen3.5-4B.js', 'codex-cli\bin\Qwen3.5-4B-threeca.js', 'codex-cli\bin\Qwen3.5-4B-network.js', 'codex-cli\bin\Qwen3.5-4B-computer-use.js', 'codex-cli\bin\test-Qwen3.5-4B-recovery.mjs', 'tools\tool43CA\MCP\server.py', 'tools\tool43CA\SKILL\threeca-access\SKILL.md')
$frozen = foreach ($file in $activeFiles) {
    $source = Join-Path $workflowRoot $file
    $frozenName = if ($attempt -eq 1) { 'frozen-workflow' } else { "frozen-workflow-attempt$attempt" }
    $destination = Join-Path (Join-Path $PSScriptRoot $frozenName) $file
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination
    @{ file = $file; sha256 = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() }
}
$workerName = if ($attempt -eq 1) { 'worker' } else { "worker-attempt$attempt" }
$launchArguments = @('-NoProfile', '-File', (Join-Path $PSScriptRoot 'launch-r2.ps1'), '-Attempt', $attempt)
if ($RetryAfterInfrastructureFailure) { $launchArguments += '-Resume' }
$process = Start-Process -FilePath 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -ArgumentList $launchArguments -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $PSScriptRoot "logs\$workerName.stdout.log") -RedirectStandardError (Join-Path $PSScriptRoot "logs\$workerName.stderr.log")
$manifest = @{ started_at = (Get-Date).ToUniversalTime().ToString('o'); workflow = $workflowRoot; task = $taskRoot; supervisor = $PSScriptRoot; runner_pid = $process.Id; model = 'Qwen3.5-4B'; prompt_sha256 = (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'prompt.txt') -Algorithm SHA256).Hash.ToLowerInvariant(); frozen_files = @($frozen); engineering_tests = 'passed'; research_workspace_initially_empty = $true; supervisor_research_interventions = 0; semantic_acceptance = 'pending' }
$manifest.attempt = $attempt
$manifest.supervisor_operational_restarts = $attempt - 1
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
Write-Host "Started project-local Qwen3.5-4B R2 runner PID $($process.Id)."
