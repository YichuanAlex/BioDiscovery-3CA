[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$sourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$workflowRoot = [IO.Path]::GetFullPath((Join-Path $sourceRoot '..\..'))
$expectedRoot = 'C:\Users\User\Desktop\agentic\workflow_codex'
if (-not $workflowRoot.Equals($expectedRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "This installer is bound to $expectedRoot; current root is $workflowRoot"
}

$venvRoot = Join-Path $sourceRoot '.venv'
$venvPython = Join-Path $venvRoot 'Scripts\python.exe'
$cacheRoot = Join-Path $workflowRoot '.threeca\cache'

New-Item -ItemType Directory -Force -Path $cacheRoot | Out-Null
if (-not (Test-Path -LiteralPath $venvPython)) {
    py -3 -m venv $venvRoot
}

& $venvPython -m pip install --quiet --disable-pip-version-check -r (Join-Path $sourceRoot 'MCP\requirements.txt')
if ($LASTEXITCODE -ne 0) { throw "MCP dependency installation exited with code $LASTEXITCODE." }
& $venvPython -m pip install --quiet --disable-pip-version-check --force-reinstall --no-deps (Join-Path $sourceRoot 'CLI')
if ($LASTEXITCODE -ne 0) { throw "tool43CA CLI installation exited with code $LASTEXITCODE." }
$scienceRequirements = Get-Content -LiteralPath (Join-Path $workflowRoot 'tools\research-quality\science-requirements.txt') | Where-Object { $_.Trim() }
foreach ($requirement in $scienceRequirements) {
    & $venvPython -m pip install --quiet --disable-pip-version-check --no-cache-dir $requirement
    if ($LASTEXITCODE -ne 0) { throw "Scientific dependency installation failed: $requirement" }
}

& $venvPython -m unittest discover -s (Join-Path $sourceRoot 'CLI') -p 'test_*.py'
if ($LASTEXITCODE -ne 0) { throw "tool43CA CLI tests exited with code $LASTEXITCODE." }
& (Join-Path $venvRoot 'Scripts\threeca.exe') --version
if ($LASTEXITCODE -ne 0) { throw "tool43CA CLI version check exited with code $LASTEXITCODE." }
& $venvPython (Join-Path $sourceRoot 'test_mcp.py')
if ($LASTEXITCODE -ne 0) { throw "tool43CA MCP test exited with code $LASTEXITCODE." }
$researchRoot = Join-Path $workflowRoot 'tools\research-quality'
$env:PYTHONPATH = $researchRoot
& $venvPython (Join-Path $researchRoot 'test_research_quality.py')
if ($LASTEXITCODE -ne 0) { throw "research-quality tests exited with code $LASTEXITCODE." }
& $venvPython (Join-Path $researchRoot 'test_metabolic_states.py')
if ($LASTEXITCODE -ne 0) { throw "metabolic-states synthetic regression exited with code $LASTEXITCODE." }
& $venvPython (Join-Path $researchRoot 'test_mcp.py')
if ($LASTEXITCODE -ne 0) { throw "research-quality MCP test exited with code $LASTEXITCODE." }
Write-Host "PASS: tool43CA and research-quality installed locally in $sourceRoot"
