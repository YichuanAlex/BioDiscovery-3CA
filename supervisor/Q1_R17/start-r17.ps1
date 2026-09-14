$ErrorActionPreference = 'Stop'
$workflowRoot = 'C:\Users\User\Desktop\agentic\workflow_codex'
$taskRoot = 'C:\Users\User\Desktop\agentic\3CA\Q1_R17'
$manifestPath = Join-Path $PSScriptRoot 'run-manifest.json'
if (Test-Path -LiteralPath $manifestPath) { throw 'R17 already has a launch manifest; refusing a duplicate.' }
if (-not (Test-Path -LiteralPath $taskRoot -PathType Container)) { throw 'R17 task workspace is missing.' }
if (@(Get-ChildItem -LiteralPath $taskRoot -Force).Count -ne 0) { throw 'R17 research workspace is not empty.' }
$validation = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'engineering-validation.md') -Raw -Encoding UTF8
if (-not $validation.Contains('FULL_TEST_EXIT_CODE=0')) { throw 'Full workflow tests have not passed.' }
$nodePath = Join-Path $workflowRoot '.runtime\node-v24.21.0-win-x64\node.exe'
$versions = (& $nodePath -p "JSON.stringify({node:process.versions.node,uv:process.versions.uv})") | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or $versions.node -ne '24.21.0' -or $versions.uv -ne '1.52.1') { throw 'Project-local Node identity check failed.' }
$activeFiles = @('run-Qwen3.5-4B.ps1','start-Qwen3.5-4B-server.ps1','codex-cli\bin\codex.js','codex-cli\bin\Qwen3.5-4B.js','codex-cli\bin\Qwen3.5-4B-network.js','codex-cli\bin\Qwen3.5-4B-threeca.js','codex-cli\bin\Qwen3.5-4B-research.js','codex-cli\bin\test-Qwen3.5-4B-recovery.mjs','tools\tool43CA\CLI\src\threeca.py','tools\tool43CA\MCP\server.py','tools\tool43CA\SKILL\threeca-access\SKILL.md','tools\research-quality\research_quality.py','tools\research-quality\metabolic_states.py','tools\research-quality\mcp_server.py','tools\research-quality\SKILL.md','tools\research-quality\references\analysis-manifest.md','tools\research-quality\science-requirements.txt')
$frozen = foreach ($file in $activeFiles) {
    $source = Join-Path $workflowRoot $file
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Missing active workflow file: $file" }
    @{ file = $file; sha256 = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() }
}
$modelIdentity = @((Invoke-RestMethod 'http://127.0.0.1:8000/v1/models').data | Where-Object { $_.id -eq 'Qwen3.5-4B' -and $_.root -eq '/mnt/c/Users/User/Desktop/agentic/model/Qwen3.5-4B' })
if ($modelIdentity.Count -ne 1) { throw 'The requested local Qwen model is not served.' }
$started = (Get-Date).ToUniversalTime().ToString('o')
New-Item -ItemType Directory -Path (Join-Path $PSScriptRoot 'logs') -Force | Out-Null
$process = Start-Process -FilePath 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -ArgumentList @('-NoProfile','-File',(Join-Path $PSScriptRoot 'launch-r17.ps1')) -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $PSScriptRoot 'logs\worker.stdout.log') -RedirectStandardError (Join-Path $PSScriptRoot 'logs\worker.stderr.log')
$manifest = @{ started_at=$started; workflow=$workflowRoot; task=$taskRoot; supervisor=$PSScriptRoot; runner_pid=$process.Id; node_runtime=@{path=$nodePath;versions=$versions;sha256=(Get-FileHash -LiteralPath $nodePath -Algorithm SHA256).Hash.ToLowerInvariant()}; model='Qwen3.5-4B'; model_identity=$modelIdentity[0]; max_rounds=0; run_until_complete=$true; prompt_sha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'prompt.txt') -Algorithm SHA256).Hash.ToLowerInvariant(); frozen_files=@($frozen); engineering_tests='full_passed'; computer_use='removed'; research_gate='results/analysis_manifest.json required'; research_workspace_initially_empty=$true; semantic_acceptance='pending' }
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
Write-Host "Started project-local Qwen R17 until-complete runner PID $($process.Id)."
