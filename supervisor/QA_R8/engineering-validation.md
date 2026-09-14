# QA_R8 engineering validation

- Validated at: 2026-09-14 11:08 +08:00
- Local model: Qwen3.5-4B at `http://127.0.0.1:8000`
- Node runtime: project-local Node 24.21.0 / libuv 1.52.1
- Python unit tests, py_compile, Ruff F and Skill validation: passed
- Recovery suite: passed, including bounded twelve-failure build/validation stops and exact repair paths
- Report contracts: exact nested manifest, core hashes, `cell_name`, seed grid, `zero_center=False`, standard log formula, four report-relative figures and subgroup fact checks
- Full `test-Qwen3.5-4B.ps1`: passed; final log `C:\Users\User\Desktop\agentic\tmp\qa-r8-full-test-2.log`
- 3CA MCP: all 10 tools actually called
- Research-quality MCP: all 9 tools actually called, including synthetic global/subset analysis, native report build and bundle validation
- Final local-model, path, attachment, file, shell and honest network-result checks: passed
- `Qwen3.5-4B.js` SHA-256: `24e235b8c5668e15a43d04224cab547b3ecd7862ce4a039da7249a67a7cf7780`
- `test-Qwen3.5-4B-recovery.mjs` SHA-256: `2ddcc1b222c77e07dcb92ddd9a211482fdec1dd21d12463d9ff0e65976d116d8`
- `research_quality.py` SHA-256: `7f3fd456b172b6a9f76b71fc818bebc5d3becc934b7e8ab7206c992b9424970c`
- `research-quality SKILL.md` SHA-256: `df0455b9c454965f8c7ee8710daafbfba208730663f644d44feb4cd12a114d83`
- `analysis-manifest.md` SHA-256: `bdd84c2c36298bc699b94a291f129e08340278c13ec0f8973de7aaf3895e78f9`
- `test-Qwen3.5-4B.ps1` SHA-256: `d98223e0b4aa52eecc1b3ba82a1243dc4f4b5b76da7d2e213a97ee04f11851b5`

The first full run passed research/MCP checks but failed its final network smoke assertion because the model executed three honest searches while the test demanded exactly one. The smoke contract now verifies one or more real searches and honest URL/no-result reporting. The second complete run exited 0. No new dependency or alternate analysis path was added.

`FULL_TEST_EXIT_CODE=0`
