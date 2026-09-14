# QA_R4 engineering validation

- Validated at: 2026-09-13 23:07:28 +08:00
- Local model: Qwen3.5-4B at `http://127.0.0.1:8000`
- Node runtime: project-local Node 24.21.0 / libuv 1.52.1
- Artifact milestone recovery regression: passed
- Fixed-study source-routing regression: passed
- Build-failure repair-routing regression: passed
- Recovery suite: passed
- Full `test-Qwen3.5-4B.ps1`: passed
- 3CA MCP: all 10 tools actually called
- Research-quality MCP: all 9 tools actually called, including synthetic global/subset analysis, native report build and bundle validation
- Final local-model, path, attachment, file, shell and network protocol smoke checks: passed
- `Qwen3.5-4B.js` SHA-256: `7b4eb50e23757607a596fc26aeadc280914f7387c812f793cbab3270fa8446c6`
- `test-Qwen3.5-4B-recovery.mjs` SHA-256: `f43dd42195e96662013fb7c063aa9e897919da7533125687149a6b0482d93512`

The first full-suite output was truncated by the executor after the test process started, so it was not counted as proof of success. The suite was rerun with output redirected to `tmp/qa-r4-full-test.log`; the rerun exited 0 and ended with the marker below.

`FULL_TEST_EXIT_CODE=0`
