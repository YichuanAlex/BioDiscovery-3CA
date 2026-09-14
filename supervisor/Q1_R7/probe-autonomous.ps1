param([switch]$Resume)
$ErrorActionPreference = 'Stop'
$workflow = 'C:\Users\User\Desktop\agentic\workflow_codex'
$probe = Join-Path $workflow '.runtime\engineering-r7-probe'
if ($Resume) { & (Join-Path $workflow 'run-Qwen3.5-4B.ps1') --workspace $probe --allow-write --allow-shell --autonomous --max-rounds 12 --resume; return }
if (Test-Path -LiteralPath $probe) { throw 'Probe workspace already exists; refusing overwrite.' }
New-Item -ItemType Directory -Path $probe | Out-Null
& (Join-Path $workflow 'run-Qwen3.5-4B.ps1') --workspace $probe --allow-write --allow-shell --autonomous --max-rounds 12 --require-artifact 'probe.txt' 'This is an engineering smoke test, not a research task. Use write_file to create probe.txt containing exactly ENGINE_R7_OK. Then use run_powershell to read it and check its exact content. Cite that actual verification_call_id in complete_task with artifact probe.txt. Do not call network, 3CA, or desktop tools.'
