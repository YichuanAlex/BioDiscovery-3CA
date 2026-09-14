$ErrorActionPreference = 'Stop'
$workflowRoot = 'C:\Users\User\Desktop\agentic\workflow_codex'
$taskRoot = 'C:\Users\User\Desktop\agentic\3CA\Q1_R5'
$manifestPath = Join-Path $PSScriptRoot 'run-manifest.json'
if (Test-Path -LiteralPath $manifestPath) { throw 'R5 already has a launch manifest; refusing a duplicate.' }
if (@(Get-ChildItem -LiteralPath $taskRoot -Force).Count -ne 0) { throw 'R5 research workspace is not empty; refusing a contaminated fresh run.' }
$validation = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'engineering-validation.md') -Raw -Encoding UTF8
if (-not $validation.Contains('FULL_TEST_EXIT_CODE=0')) { throw 'Final full integration test has not completed successfully.' }
$activeFiles = @('README.md', 'run-Qwen3.5-4B.ps1', 'start-Qwen3.5-4B-server.ps1', 'codex-cli\bin\codex.js', 'codex-cli\bin\Qwen3.5-4B.js', 'codex-cli\bin\Qwen3.5-4B-threeca.js', 'codex-cli\bin\Qwen3.5-4B-network.js', 'codex-cli\bin\Qwen3.5-4B-computer-use.js', 'codex-cli\bin\test-Qwen3.5-4B-recovery.mjs', 'tools\tool43CA\MCP\server.py', 'tools\tool43CA\SKILL\threeca-access\SKILL.md')
$frozen = foreach ($file in $activeFiles) {
    $source = Join-Path $workflowRoot $file
    $destination = Join-Path (Join-Path $PSScriptRoot 'frozen-workflow') $file
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination
    @{ file = $file; sha256 = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() }
}
$process = Start-Process -FilePath 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -ArgumentList @('-NoProfile', '-File', (Join-Path $PSScriptRoot 'launch-r5.ps1')) -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $PSScriptRoot 'logs\worker.stdout.log') -RedirectStandardError (Join-Path $PSScriptRoot 'logs\worker.stderr.log')
$manifest = @{ started_at = (Get-Date).ToUniversalTime().ToString('o'); workflow = $workflowRoot; task = $taskRoot; supervisor = $PSScriptRoot; runner_pid = $process.Id; model = 'Qwen3.5-4B'; max_rounds = 0; run_until_complete = $true; prompt_sha256 = (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'prompt.txt') -Algorithm SHA256).Hash.ToLowerInvariant(); frozen_files = @($frozen); engineering_tests = 'passed'; research_workspace_initially_empty = $true; supervisor_operational_restarts = 0; supervisor_research_interventions = 0; semantic_acceptance = 'pending' }
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
Write-Host "Started project-local Qwen3.5-4B R5 until-complete runner PID $($process.Id)."
