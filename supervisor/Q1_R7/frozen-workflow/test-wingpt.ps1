$ErrorActionPreference = 'Stop'

$environmentNames = @('CODEX_HOME', 'CODEX_CLI_PATH', 'THREECA_CACHE', 'PYTHONNOUSERSITE', 'NODE_REPL_DISABLE_ANALYTICS', 'BROWSER_USE_DISABLE_AMBIENT_NETWORK')
$environmentBefore = @{}
foreach ($name in $environmentNames) {
    $environmentBefore[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}

& (Join-Path $PSScriptRoot 'test-isolation.ps1')
& 'C:\Program Files\nodejs\node.exe' (Join-Path $PSScriptRoot 'codex-cli\bin\test-Qwen3.5-4B-recovery.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Agent recovery regression failed.' }
$toolRoot = Join-Path $PSScriptRoot 'tools\tool43CA'
& (Join-Path $toolRoot '.venv\Scripts\python.exe') (Join-Path $toolRoot 'test_mcp.py')
if ($LASTEXITCODE -ne 0) { throw "tool43CA MCP test exited with code $LASTEXITCODE." }

if (-not ('WorkflowCodex.ForegroundWindow' -as [type])) {
    Add-Type -Namespace WorkflowCodex -Name ForegroundWindow -MemberDefinition '[DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow(); [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);'
}
$foregroundPid = 0
[void][WorkflowCodex.ForegroundWindow]::GetWindowThreadProcessId([WorkflowCodex.ForegroundWindow]::GetForegroundWindow(), [ref]$foregroundPid)
$desktopLocked = (Get-Process -Id $foregroundPid -ErrorAction SilentlyContinue).ProcessName -eq 'LockApp'
$computerUseArgs = @((Join-Path $PSScriptRoot 'tools\computer-use\test-computer-use.mjs'))
if (-not $desktopLocked) { $computerUseArgs += '--require-action' }
& 'C:\Program Files\nodejs\node.exe' @computerUseArgs
if ($LASTEXITCODE -ne 0) { throw "Computer Use test exited with code $LASTEXITCODE." }
if ($desktopLocked) { Write-Host 'SKIP: Computer Use input action requires an unlocked Windows desktop; runtime/list/observe checks passed.' }
& (Join-Path $PSScriptRoot 'run-Qwen3.5-4B.ps1') --self-test --allow-write --allow-shell
& (Join-Path $PSScriptRoot 'run-Qwen3.5-4B.ps1') '请你给我联网搜索最新的新闻'

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

foreach ($name in $environmentNames) {
    $after = [Environment]::GetEnvironmentVariable($name, 'Process')
    if ([string]$after -ne [string]$environmentBefore[$name]) { throw "Environment leaked from workflow: $name" }
}
& (Join-Path $PSScriptRoot 'test-isolation.ps1')

Write-Host 'PASS: workflow_codex functional test completed.'
