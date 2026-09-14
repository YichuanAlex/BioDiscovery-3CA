# QA_R5 engineering validation

- Validated at: 2026-09-14 08:46:03 +08:00
- Local model: Qwen3.5-4B at `http://127.0.0.1:8000`
- Node runtime: project-local Node 24.21.0 / libuv 1.52.1
- Focused Python/static/Skill validation: passed
- Recovery suite including three-identical-state stop: passed
- Fixed-study and all-prompt-DOI routing: passed
- Focused LaTeX diagnostic routing: passed
- Full `test-Qwen3.5-4B.ps1`: passed
- 3CA MCP: all 10 tools actually called
- Research-quality MCP: all 9 tools actually called, including synthetic global/subset analysis, native report build and bundle validation
- Final local-model, path, attachment, file, shell and network protocol smoke checks: passed
- `Qwen3.5-4B.js` SHA-256: `207c0e139e55a50a67a25c55debd34db5084825bbf2ac268aef45cae86489d1f`
- `test-Qwen3.5-4B-recovery.mjs` SHA-256: `96c5f28150b6b38601b715d38447d79331140079bf73d5ecd99a0a582e724a6d`
- `research_quality.py` SHA-256: `8eab47c512ccdf1b73100d90b05cfa947fd95eea8fbad57aeb129d66f5992d3d`
- `research-quality SKILL.md` SHA-256: `3e2f533c34886dae9018363dbc06ea5a0a2691f19fc7f1830d38e1bf3750ab9e`
- `test-Qwen3.5-4B.ps1` SHA-256: `34a585653a4cbbc525eaa2a2d8b8aed078c8df8c343105d304bab9eba8554ed6`

The first full-suite run reached the network smoke check and exited 1 because the model honestly rejected unrelated search results while the test required their links. The smoke contract was narrowed: a claimed result still requires actual URLs; an explicit no-verifiable-result outcome may omit unrelated links. The corrected full rerun exited 0.

`FULL_TEST_EXIT_CODE=0`
