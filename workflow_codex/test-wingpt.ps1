$ErrorActionPreference = 'Stop'
$nodePath = Join-Path $PSScriptRoot '.runtime\node-v24.21.0-win-x64\node.exe'
if (-not (Test-Path -LiteralPath $nodePath -PathType Leaf)) { throw 'Project-local Node.js v24.21.0 runtime is missing.' }

$environmentNames = @('CODEX_HOME', 'THREECA_CACHE', 'PYTHONNOUSERSITE', 'NODE_REPL_DISABLE_ANALYTICS', 'WINGPT_CONTEXT_TOKENS')
$environmentBefore = @{}
foreach ($name in $environmentNames) {
    $environmentBefore[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}

& (Join-Path $PSScriptRoot 'test-isolation.ps1')
& $nodePath (Join-Path $PSScriptRoot 'codex-cli\bin\test-wingpt-recovery.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Agent recovery regression failed.' }
$toolRoot = Join-Path $PSScriptRoot 'tools\tool43CA'
& (Join-Path $toolRoot '.venv\Scripts\python.exe') (Join-Path $toolRoot 'CLI\test_threeca.py')
if ($LASTEXITCODE -ne 0) { throw 'Shared threeca inspection and archive safety regression failed.' }
& (Join-Path $toolRoot '.venv\Scripts\python.exe') (Join-Path $toolRoot 'test_mcp.py')
if ($LASTEXITCODE -ne 0) { throw "tool43CA MCP test exited with code $LASTEXITCODE." }
$researchRoot = Join-Path $PSScriptRoot 'tools\research-quality'
$env:PYTHONPATH = $researchRoot
& (Join-Path $toolRoot '.venv\Scripts\python.exe') (Join-Path $researchRoot 'test_research_quality.py')
if ($LASTEXITCODE -ne 0) { throw "research-quality test exited with code $LASTEXITCODE." }
& (Join-Path $toolRoot '.venv\Scripts\python.exe') (Join-Path $researchRoot 'test_metabolic_states.py')
if ($LASTEXITCODE -ne 0) { throw "metabolic-states synthetic regression exited with code $LASTEXITCODE." }
& (Join-Path $toolRoot '.venv\Scripts\python.exe') (Join-Path $researchRoot 'test_mcp.py')
if ($LASTEXITCODE -ne 0) { throw "research-quality MCP test exited with code $LASTEXITCODE." }
$researchSmoke = Join-Path $PSScriptRoot '.runtime\research-quality-smoke'
New-Item -ItemType Directory -Force -Path $researchSmoke | Out-Null
$researchCli = Join-Path $researchRoot 'research_quality.py'
& (Join-Path $toolRoot '.venv\Scripts\python.exe') $researchCli --workspace $researchSmoke reactome-metabolic-genes | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Reactome live tool test exited with code $LASTEXITCODE." }
& (Join-Path $toolRoot '.venv\Scripts\python.exe') $researchCli --workspace $researchSmoke pubmed-search 'single cell metabolism' --max-results 1 | Out-Null
if ($LASTEXITCODE -ne 0) { throw "PubMed live tool test exited with code $LASTEXITCODE." }
& (Join-Path $toolRoot '.venv\Scripts\python.exe') $researchCli --workspace $researchSmoke verify-doi '10.1038/s41586-020-2649-2' | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Crossref live tool test exited with code $LASTEXITCODE." }
& (Join-Path $PSScriptRoot 'run-wingpt.ps1') --self-test --allow-write --allow-shell
& (Join-Path $PSScriptRoot 'run-wingpt.ps1') --max-rounds 6 'This is a network engineering smoke test. Call web_search for current news and do not call read_webpage. Then report the retrieval date, actual results, and their source links. If the search has no verifiable result, say so.'

$sessionRoot = Join-Path $PSScriptRoot '.runtime\codex-home\sessions'
$sessionFile = Get-ChildItem -LiteralPath $sessionRoot -Filter '*.jsonl' -Recurse -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if (-not $sessionFile) { throw 'Session transcript was not created under the workflow.' }
$sessionEvents = @(
    Get-Content -LiteralPath $sessionFile.FullName -Encoding UTF8 |
        Where-Object { $_.Trim() } |
        ForEach-Object { $_ | ConvertFrom-Json }
)
$requiredRolloutTypes = @('session_meta', 'response_item', 'event_msg')
foreach ($rolloutType in $requiredRolloutTypes) {
    if (-not ($sessionEvents.type -contains $rolloutType)) { throw "Session transcript is missing rollout type: $rolloutType" }
}
$workflowEvents = @($sessionEvents | ForEach-Object { $_.payload.workflow.event } | Where-Object { $_ })
$requiredWorkflowEvents = @('session_start', 'user_message', 'assistant_response', 'tool_call', 'tool_result', 'turn_complete', 'session_end')
foreach ($eventType in $requiredWorkflowEvents) {
    if (-not ($workflowEvents -contains $eventType)) { throw "Session transcript is missing workflow event: $eventType" }
}
if (-not $sessionFile.FullName.StartsWith($sessionRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Session transcript escaped the workflow runtime.'
}
Write-Host "PASS: session transcript $($sessionFile.FullName)"
$finishedTurn = @($sessionEvents | Where-Object { $_.payload.workflow.event -eq 'turn_complete' })[-1].payload.workflow
if ($finishedTurn.tool_round_limit -or $finishedTurn.stalled -or -not $finishedTurn.assistant_text) { throw 'Network smoke test did not finish within its bounded action contract.' }
$returnedSearches = @($sessionEvents | Where-Object { $_.payload.workflow.event -eq 'tool_result' -and $_.payload.workflow.name -eq 'web_search' -and $_.payload.workflow.result -notmatch 'not currently advertised|identical tool call' })
if ($returnedSearches.Count -lt 1) { throw 'Network smoke test did not execute a live search.' }
$searchFailed = @($returnedSearches | Where-Object { $_.payload.workflow.result -match 'no parseable results|returned no usable results|ERROR:' }).Count -gt 0
$hasSearchUrl = @($returnedSearches | Where-Object { $_.payload.workflow.result -match 'URL: https?://' }).Count -gt 0
$reportedNoVerifiableResult = $finishedTurn.assistant_text -match 'no parseable results|no verifiable result|did not return usable|cannot provide|not currently available'
if ($searchFailed -or $reportedNoVerifiableResult) {
    if ($finishedTurn.assistant_text -notmatch 'no parseable results|no verifiable result|did not return usable|cannot provide|not currently available') { throw 'Network smoke test hid the actual search failure.' }
} elseif (-not $hasSearchUrl -or $finishedTurn.assistant_text -notmatch 'https?://') {
    throw 'Network smoke test did not preserve actual source links.'
}

foreach ($name in $environmentNames) {
    $after = [Environment]::GetEnvironmentVariable($name, 'Process')
    if ([string]$after -ne [string]$environmentBefore[$name]) { throw "Environment leaked from workflow: $name" }
}
& (Join-Path $PSScriptRoot 'test-isolation.ps1')

Write-Host 'PASS: workflow_codex functional test completed.'
