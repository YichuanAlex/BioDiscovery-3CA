# QA_R7 engineering validation

- Validated at: 2026-09-14 10:13 +08:00
- Local model: Qwen3.5-4B at `http://127.0.0.1:8000`
- Node runtime: project-local Node 24.21.0 / libuv 1.52.1
- Python unit tests, py_compile, Ruff F and Skill validation: passed
- Recovery suite: passed, including six-failed-build stop, six-invalid-validation stop, exact repair paths and same-state recovery stop
- Report contracts: exact core hashes, `cell_name`, seed grid, `zero_center=False`, standard log formula and four report-relative figure paths
- Full `test-Qwen3.5-4B.ps1`: passed; log `C:\Users\User\Desktop\agentic\tmp\qa-r7-full-test.log`
- 3CA MCP: all 10 tools actually called
- Research-quality MCP: all 9 tools actually called, including synthetic global/subset analysis, native report build and bundle validation
- Final local-model, path, attachment, file, shell and network protocol smoke checks: passed
- `Qwen3.5-4B.js` SHA-256: `060ba747ae52b86261c4f2215db678d4ac8a04b26c24ab83e1779e962455d722`
- `test-Qwen3.5-4B-recovery.mjs` SHA-256: `df17260a7113341f76eb9aaa887f053be12ba6eef834e843928bac1e69f636d7`
- `research_quality.py` SHA-256: `a9876670c9f0b1457c4f1b50d37185b9cda3cf72df177af452dc1ebd39b08574`
- `research-quality SKILL.md` SHA-256: `e0fc29890123d7dc4e50a3b09c6dbdb961d3e6854f2b923eb4de7f6254c849fd`
- `analysis-manifest.md` SHA-256: `2c7f8190625199204cf86525040a71cb269da1228cf18586ab63970d62b3303e`
- `test-Qwen3.5-4B.ps1` SHA-256: `34a585653a4cbbc525eaa2a2d8b8aed078c8df8c343105d304bab9eba8554ed6`

The broader all-rule Ruff audit from the preceding round reported historical style suggestions; the required Ruff F gate passed. No new dependency or alternate analysis path was added.

`FULL_TEST_EXIT_CODE=0`
