param([switch]$Probe)
$ErrorActionPreference = 'Stop'
$taskRoot = 'C:\Users\User\Desktop\agentic\3CA\Q1_R4'
$workflowRoot = 'C:\Users\User\Desktop\agentic\workflow_codex'
$started = (Get-Date).ToUniversalTime().ToString('o')
try {
    if ($Probe) {
        Write-Output "workflow=$workflowRoot task=$taskRoot"
        return
    }
    & (Join-Path $workflowRoot 'run-Qwen3.5-4B.ps1') --workspace $taskRoot --allow-write --allow-shell --autonomous --max-rounds 240 --prompt-file (Join-Path $PSScriptRoot 'prompt.txt') --require-artifact 'report/main.tex' --require-artifact 'report/main.pdf' --require-artifact 'results/summary.json' --require-artifact 'README.md'
    $result = @{ started_at = $started; ended_at = (Get-Date).ToUniversalTime().ToString('o'); runner_success = $true; semantic_acceptance = 'pending_independent_review' }
} catch {
    $result = @{ started_at = $started; ended_at = (Get-Date).ToUniversalTime().ToString('o'); runner_success = $false; error = $_.Exception.Message; semantic_acceptance = 'not_accepted' }
}
$result | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'runner-result.json') -Encoding UTF8
if (-not $result.runner_success) { exit 1 }
