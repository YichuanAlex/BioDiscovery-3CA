$ErrorActionPreference = 'Stop'
$workflowRoot = 'C:\Users\User\Desktop\agentic\workflow_codex'
$taskRoot = 'C:\Users\User\Desktop\agentic\3CA\Q1_R11'
$manifestPath = Join-Path $PSScriptRoot 'run-manifest.json'
if (Test-Path -LiteralPath $manifestPath) { throw 'R11 already has a launch manifest; refusing a duplicate.' }
if (-not (Test-Path -LiteralPath $taskRoot)) { New-Item -ItemType Directory -Path $taskRoot | Out-Null }
if (@(Get-ChildItem -LiteralPath $taskRoot -Force).Count -ne 0) { throw 'R11 research workspace is not empty; refusing a contaminated fresh run.' }
$validation = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'engineering-validation.md') -Raw -Encoding UTF8
if (-not $validation.Contains('FULL_TEST_EXIT_CODE=0') -and -not ($validation.Contains('CORE_TEST_EXIT_CODE=0') -and $validation.Contains('R11_DESKTOP_TOOLS=not_exposed'))) { throw 'Research core tests have not completed successfully.' }
$nodePath = Join-Path $workflowRoot '.runtime\node-v24.21.0-win-x64\node.exe'
$nodeVersions = (& $nodePath -p "JSON.stringify({node:process.versions.node,uv:process.versions.uv,v8:process.versions.v8})") | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or $nodeVersions.node -ne '24.21.0' -or $nodeVersions.uv -ne '1.52.1') { throw 'The fixed project-local Node runtime failed identity validation.' }
$activeFiles = @('README.md', 'run-Qwen3.5-4B.ps1', 'start-Qwen3.5-4B-server.ps1', 'codex-cli\bin\codex.js', 'codex-cli\bin\Qwen3.5-4B.js', 'codex-cli\bin\Qwen3.5-4B-threeca.js', 'codex-cli\bin\Qwen3.5-4B-network.js', 'codex-cli\bin\Qwen3.5-4B-computer-use.js', 'codex-cli\bin\test-Qwen3.5-4B-recovery.mjs', 'tools\tool43CA\MCP\server.py', 'tools\tool43CA\SKILL\threeca-access\SKILL.md', 'test-Qwen3.5-4B.ps1', 'test-isolation.ps1', 'codex-local.cmd', 'app-server', 'tools\tool43CA\CLI\src\threeca.py', 'tools\tool43CA\CLI\test_threeca.py', 'tools\tool43CA\CLI\pyproject.toml', 'tools\tool43CA\.venv\Lib\site-packages\threeca.py', 'tools\tool43CA\test_mcp.py')
$frozen = foreach ($file in $activeFiles) {
    $source = Join-Path $workflowRoot $file
    $destination = Join-Path (Join-Path $PSScriptRoot 'frozen-workflow') $file
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination
    @{ file = $file; sha256 = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() }
}
$modelDirectory = 'C:\Users\User\Desktop\agentic\model\Qwen3.5-4B'
$modelIdentity = @((Invoke-RestMethod 'http://127.0.0.1:8000/v1/models').data | Where-Object { $_.id -eq 'Qwen3.5-4B' -and $_.root -eq '/mnt/c/Users/User/Desktop/agentic/model/Qwen3.5-4B' })
if ($modelIdentity.Count -ne 1) { throw 'The actual service does not serve the requested Qwen model path.' }
$modelMetadata = foreach ($file in @('config.json', 'model.safetensors.index.json', 'chat_template.jinja')) { @{ file = $file; sha256 = (Get-FileHash -LiteralPath (Join-Path $modelDirectory $file) -Algorithm SHA256).Hash.ToLowerInvariant() } }
$started = (Get-Date).ToUniversalTime().ToString('o')
$process = Start-Process -FilePath 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -ArgumentList @('-NoProfile', '-File', (Join-Path $PSScriptRoot 'launch-r11.ps1')) -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $PSScriptRoot 'logs\worker.stdout.log') -RedirectStandardError (Join-Path $PSScriptRoot 'logs\worker.stderr.log')
$manifest = @{ started_at = $started; workflow = $workflowRoot; task = $taskRoot; supervisor = $PSScriptRoot; runner_pid = $process.Id; node_runtime = @{ path = $nodePath; sha256 = (Get-FileHash -LiteralPath $nodePath -Algorithm SHA256).Hash.ToLowerInvariant(); versions = $nodeVersions }; model = 'Qwen3.5-4B'; model_directory = $modelDirectory; model_identity = $modelIdentity[0]; model_metadata = @($modelMetadata); max_rounds = 0; run_until_complete = $true; prompt_sha256 = (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'prompt.txt') -Algorithm SHA256).Hash.ToLowerInvariant(); frozen_files = @($frozen); engineering_tests = $(if ($validation.Contains('FULL_TEST_EXIT_CODE=0')) { 'full_passed' } else { 'core_passed_desktop_action_failed' }); desktop_action_test = $(if ($validation.Contains('FULL_TEST_EXIT_CODE=0')) { 'passed' } else { 'failed_activation_not_used_by_R11' }); research_workspace_initially_empty = $true; supervisor_operational_restarts = 0; supervisor_research_interventions = 0; semantic_acceptance = 'pending' }
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
Write-Host "Started project-local Qwen R11 until-complete runner PID $($process.Id)."
