# QA_R3 engineering validation

- Validated at: 2026-09-13 22:35:04 +08:00
- Local model: Qwen3.5-4B at `http://127.0.0.1:8000`
- Node runtime: project-local Node 24.21.0 / libuv 1.52.1
- Artifact milestone recovery regression: passed
- Fixed-study source-routing regression: passed
- Recovery suite: passed
- Full `test-Qwen3.5-4B.ps1`: passed
- 3CA MCP: all 10 tools actually called
- Research-quality MCP: all 9 tools actually called, including synthetic global/subset analysis, native report build and bundle validation
- Final local-model, path, attachment, file, shell and network protocol smoke checks: passed
- `Qwen3.5-4B.js` SHA-256: `58a75aa566cc88e2462a37a2927292eb438049630edb2a961addeab5779a830b`
- `test-Qwen3.5-4B-recovery.mjs` SHA-256: `365a7fdd65c4777548b7983ecf7590cdb91bc8050ff17da7898b1aa3185520fe`

The first attempt to invoke the final test passed an invalid executor working-directory string and created no process. The corrected invocation ran the full suite and exited 0. This failed harness call was not counted as a test pass.

`FULL_TEST_EXIT_CODE=0`
