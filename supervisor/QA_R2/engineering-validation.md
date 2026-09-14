# QA_R2 engineering validation

- Validated at: 2026-09-13 22:22:45 +08:00
- Local model: Qwen3.5-4B at `http://127.0.0.1:8000`
- Node runtime: project-local Node 24.21.0 / libuv 1.52.1
- New milestone recovery regression: passed
- Recovery suite: passed
- Full `test-Qwen3.5-4B.ps1`: passed
- 3CA MCP: all 10 tools actually called
- Research-quality MCP: all 9 tools actually called, including synthetic global/subset analysis, native report build and bundle validation
- Final local-model, path, attachment, file, shell and network protocol smoke checks: passed
- `Qwen3.5-4B.js` SHA-256: `f1cb50de07cb245ab02c85af8cc05afe9bf32d8a98f1476242758c074754f32b`
- `test-Qwen3.5-4B-recovery.mjs` SHA-256: `2877f30eac566d23e4d7bf77c3f09c5b599cb372f6c778af815bfb37ea3e8f47`

The first syntax-check invocation used a mistyped Node directory (`node-v24.21.0-win-x.1-x64`) and failed before running Node. The corrected path passed. The first focused recovery run exposed a missing `--allow-shell` flag in the new test fixture; the fixture was corrected and the full recovery suite then exited 0. These failed checks were not counted as passes.

`FULL_TEST_EXIT_CODE=0`
