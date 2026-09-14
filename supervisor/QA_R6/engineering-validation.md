# QA_R6 engineering validation

- Validated at: 2026-09-14 09:25 +08:00
- Local model: Qwen3.5-4B at `http://127.0.0.1:8000`
- Node runtime: project-local Node 24.21.0 / libuv 1.52.1
- Focused Python tests, py_compile, Ruff F and Skill validation: passed
- Recovery suite including exact repair-path enforcement and three-identical-state stop: passed
- Fixed-study, all-prompt-DOI, build-repair and semantic-report routing: passed
- Full `test-Qwen3.5-4B.ps1`: passed
- 3CA MCP: all 10 tools actually called
- Research-quality MCP: all 9 tools actually called, including synthetic global/subset analysis, native report build and bundle validation
- Final local-model, path, attachment, file, shell and network protocol smoke checks: passed
- `Qwen3.5-4B.js` SHA-256: `a892702a87a933bcfb53ec1e59ea11ef0c69018bf53fe4b81a187c5f9236461b`
- `test-Qwen3.5-4B-recovery.mjs` SHA-256: `bc81ea7dac796b2e84f8592484a9a0e05652c2a03ff78c758875a2a229b347fa`
- `research_quality.py` SHA-256: `6bcb6d131d256546cf0e377807fbcdaa0b3bc3958b0382d6a8d573ea0524f446`
- `research-quality SKILL.md` SHA-256: `40cecf9f67fc2af46271f912e1aab5d364de4cefaccf9d6ae108fcc5c3ac3e88`
- `analysis-manifest.md` SHA-256: `25da511632d27a9a322a7a64da171defb0fa8219e0020390fdf916c31cb57eaa`
- `test-Qwen3.5-4B.ps1` SHA-256: `34a585653a4cbbc525eaa2a2d8b8aed078c8df8c343105d304bab9eba8554ed6`

The broader all-rule Ruff audit reported pre-existing style recommendations; no automatic fixes were applied. The required Ruff F gate passed.

`FULL_TEST_EXIT_CODE=0`
