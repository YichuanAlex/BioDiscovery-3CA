# R7 engineering validation

Validated at 2026-09-13 01:10:59 +08:00, before formal research launch.

FULL_TEST_EXIT_CODE=0

- Actual hidden PowerShell test process PID 18684 exited with code 0; stdout ends with `PASS: workflow_codex functional test completed.`
- Isolation and environment restoration passed. No global Codex/agent configuration, installed model code, or model weights were changed.
- Existing recovery integration test passed, including new structured-action/raw-response persistence, missing-content rejection before mkdir, current-tool availability, bounded discovery cooldown, preserved catalog IDs and budgets, actual PowerShell validation, exit-75 resume, and exclusive-lock release.
- Empty JSON and fake PDF completion remain rejected. Completion still requires validation after the latest mutation.
- Actual project-local 3CA MCP initialized, listed ten tools, and completed a call.
- Actual Computer Use listed, launched, selected, observed, acted, and re-observed. This run did not SKIP input actions.
- Real local-model tool protocol, attachments, file read/write/list, live network, shell, rollout logging, and environment isolation passed.
- Node syntax check passed. R7 mirrored-original audit regression separately exited 0.

The real autonomous engineering probe resumed after a retained API-400 compatibility failure (`System message must be at the beginning.`). Runtime state was merged into the initial system message and rechecked. Actual retry process PID 24996 exited 0; three model rounds produced write_file, run_powershell, and complete_task, with actual reasoning 3/3 and structured JSON actions 3/3. The provider's raw JSON was retained separately from decoded actions. Independent readback confirmed exact `ENGINE_R7_OK`, 12 bytes, SHA-256 27da47dcffa241e2856a1fce5334b9ad8c545763a6d1cf2feea289f2c2f4c379. Probe checkpoint: workflow `.runtime/codex-home/tasks/763e1457bc338589f2b22b05.json`; mirrored original session: `logs/engineering-autonomous-probe.jsonl`.

Evidence: `logs/engineering-full.stdout.log`, `logs/engineering-full.stderr.log`, `logs/schema-probe.json`, the first and retry `autonomous-probe*.stdout.log`/stderr, and the mirrored probe JSONL. Informational MCP request lines in full-test stderr are not a failed test. The engineering probe contains no research data, dataset choice, analysis code, or R7 research artifact. Engineering success does not establish autonomous scientific quality.
