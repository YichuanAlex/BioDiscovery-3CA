param([int]$Attempt = 1, [switch]$Resume, [switch]$Probe)
$ErrorActionPreference = 'Stop'
$taskRoot = 'C:\Users\User\Desktop\agentic\3CA\Q1_R2'
$workflowRoot = 'C:\Users\User\Desktop\agentic\workflow_codex'
$started = (Get-Date).ToUniversalTime().ToString('o')
try {
    [string[]]$resumeArgument = @()
    if ($Resume) { $resumeArgument = @('--resume') }
    if ($Probe) {
        $forwardedArguments = @(& { $args } @resumeArgument)
        if ($Resume -and ($forwardedArguments.Count -ne 1 -or $forwardedArguments[0] -ne '--resume')) { throw 'Resume must reach the agent as one argument, not characters.' }
        Write-Output "attempt=$Attempt resume=$Resume forwarded=$($forwardedArguments -join ',')"
        return
    }
    & (Join-Path $workflowRoot 'run-Qwen3.5-4B.ps1') --workspace $taskRoot --allow-write --allow-shell --autonomous --max-rounds 240 --prompt-file (Join-Path $PSScriptRoot 'prompt.txt') --require-artifact 'report/main.tex' --require-artifact 'report/main.pdf' --require-artifact 'results/summary.json' --require-artifact 'README.md' @resumeArgument
    $result = @{ started_at = $started; ended_at = (Get-Date).ToUniversalTime().ToString('o'); runner_success = $true; semantic_acceptance = 'pending_independent_review' }
} catch {
    $result = @{ started_at = $started; ended_at = (Get-Date).ToUniversalTime().ToString('o'); runner_success = $false; error = $_.Exception.Message; semantic_acceptance = 'not_accepted' }
}
$result.attempt = $Attempt
$resultPath = if ($Attempt -eq 1) { 'runner-result.json' } else { "runner-result-attempt$Attempt.json" }
$result | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot $resultPath) -Encoding UTF8
if (-not $result.runner_success) { exit 1 }
