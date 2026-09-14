$ErrorActionPreference = 'Stop'
$workflowRoot = 'C:\Users\User\Desktop\agentic\workflow_codex'
$taskRoot = 'C:\Users\User\Desktop\agentic\3CA\QA_R2'
$inputSource = 'C:\Users\User\Desktop\agentic\material\QuestionAll\metabolic genes total.csv'
$manifestPath = Join-Path $PSScriptRoot 'run-manifest.json'
if (Test-Path -LiteralPath $manifestPath) { throw 'QA_R2 already has a launch manifest; refusing a duplicate.' }
if (-not (Test-Path -LiteralPath $taskRoot -PathType Container)) { throw 'QA_R2 task workspace is missing.' }
if (@(Get-ChildItem -LiteralPath $taskRoot -Force).Count -ne 0) { throw 'QA_R2 research workspace is not empty before supplied-input staging.' }
if (-not (Test-Path -LiteralPath $inputSource -PathType Leaf)) { throw 'User metabolic-gene CSV is missing.' }
$validation = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'engineering-validation.md') -Raw -Encoding UTF8
if (-not $validation.Contains('FULL_TEST_EXIT_CODE=0')) { throw 'Full workflow tests have not passed.' }
$nodePath = Join-Path $workflowRoot '.runtime\node-v24.21.0-win-x64\node.exe'
$versions = (& $nodePath -p "JSON.stringify({node:process.versions.node,uv:process.versions.uv})") | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or $versions.node -ne '24.21.0' -or $versions.uv -ne '1.52.1') { throw 'Project-local Node identity check failed.' }
$activeFiles = @('run-Qwen3.5-4B.ps1','start-Qwen3.5-4B-server.ps1','test-Qwen3.5-4B.ps1','codex-cli\bin\codex.js','codex-cli\bin\Qwen3.5-4B.js','codex-cli\bin\Qwen3.5-4B-network.js','codex-cli\bin\Qwen3.5-4B-threeca.js','codex-cli\bin\Qwen3.5-4B-research.js','codex-cli\bin\test-Qwen3.5-4B-recovery.mjs','tools\tool43CA\CLI\src\threeca.py','tools\tool43CA\MCP\server.py','tools\tool43CA\SKILL\threeca-access\SKILL.md','tools\research-quality\research_quality.py','tools\research-quality\metabolic_states.py','tools\research-quality\mcp_server.py','tools\research-quality\SKILL.md','tools\research-quality\references\analysis-manifest.md','tools\research-quality\science-requirements.txt','tools\research-quality\test_metabolic_states.py','tools\research-quality\test_mcp.py')
$frozen = foreach ($file in $activeFiles) {
    $source = Join-Path $workflowRoot $file
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Missing active workflow file: $file" }
    @{ file=$file; sha256=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() }
}
$modelIdentity = @((Invoke-RestMethod 'http://127.0.0.1:8000/v1/models').data | Where-Object { $_.id -eq 'Qwen3.5-4B' -and $_.root -eq '/mnt/c/Users/User/Desktop/agentic/model/Qwen3.5-4B' })
if ($modelIdentity.Count -ne 1) { throw 'The requested local Qwen model is not served.' }
$inputs = New-Item -ItemType Directory -Path (Join-Path $taskRoot 'inputs')
$stagedInput = Join-Path $inputs 'metabolic_genes_total.csv'
Copy-Item -LiteralPath $inputSource -Destination $stagedInput
$inputHash = (Get-FileHash -LiteralPath $inputSource -Algorithm SHA256).Hash.ToLowerInvariant()
if ((Get-FileHash -LiteralPath $stagedInput -Algorithm SHA256).Hash.ToLowerInvariant() -ne $inputHash) { throw 'Staged user input hash mismatch.' }
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'workspace-AGENTS.md') -Destination (Join-Path $taskRoot 'AGENTS.md')
$provenance = @{ source_path=$inputSource; staged_path='inputs/metabolic_genes_total.csv'; sha256=$inputHash; bytes=(Get-Item -LiteralPath $stagedInput).Length; staged_at=(Get-Date).ToUniversalTime().ToString('o'); role='immutable_user_supplied_gene_set' }
$provenance | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $inputs 'input-provenance.json') -Encoding UTF8
$started = (Get-Date).ToUniversalTime().ToString('o')
New-Item -ItemType Directory -Path (Join-Path $PSScriptRoot 'logs') -Force | Out-Null
$process = Start-Process -FilePath 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -ArgumentList @('-NoProfile','-File',(Join-Path $PSScriptRoot 'launch-qa-r2.ps1')) -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $PSScriptRoot 'logs\worker.stdout.log') -RedirectStandardError (Join-Path $PSScriptRoot 'logs\worker.stderr.log')
$manifest = @{ started_at=$started; workflow=$workflowRoot; task=$taskRoot; supervisor=$PSScriptRoot; runner_pid=$process.Id; runner_expected=@{name='powershell.exe'; command_fragment='launch-qa-r2.ps1'}; node_runtime=@{path=$nodePath;versions=$versions;sha256=(Get-FileHash -LiteralPath $nodePath -Algorithm SHA256).Hash.ToLowerInvariant()}; model='Qwen3.5-4B'; model_identity=$modelIdentity[0]; max_rounds=0; run_until_complete=$true; prompt_sha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'prompt.txt') -Algorithm SHA256).Hash.ToLowerInvariant(); seeded_inputs=@($provenance,@{staged_path='AGENTS.md';sha256=(Get-FileHash -LiteralPath (Join-Path $taskRoot 'AGENTS.md') -Algorithm SHA256).Hash.ToLowerInvariant();role='round_execution_contract'}); frozen_files=@($frozen); engineering_tests='full_passed'; research_gate='final validate_research_bundle verification required'; research_workspace_initially_empty_before_supplied_input=$true; semantic_acceptance='pending' }
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
Write-Host "Started project-local Qwen QA_R2 until-complete runner PID $($process.Id)."
