# QA_R1 engineering validation

Validated on 2026-09-13 before launch.

- `python -m py_compile` for `metabolic_states.py`, `research_quality.py`, and `mcp_server.py`: exit 0.
- Project-local Node `--check` for `Qwen3.5-4B.js`, `Qwen3.5-4B-research.js`, and `audit-qa-r1.mjs`: exit 0.
- PowerShell parser checks for `start-qa-r1.ps1`, `launch-qa-r1.ps1`, and `test-Qwen3.5-4B.ps1`: exit 0.
- Ruff `--select F` over the research-quality implementation and tests: exit 0, `All checks passed!`.
- Skill Creator `quick_validate.py workflow_codex/tools/research-quality`: exit 0.
- `test_metabolic_states.py`: exit 0. The synthetic pipeline exercised CSV `symbol` parsing, a unique case-insensitive match, global analysis, a separately named exact metadata-subset analysis, non-overwritten global summary, matched controls, replicate outputs, figures, and bundle validation.
- `test-Qwen3.5-4B-recovery.mjs`: exit 0. Completion, duplicate/recovery, Python-audit, core-first, stale-state and research-quality hooks passed.
- `test_mcp.py`: exit 0. All nine research-quality MCP tools were actually called, including the native report builder, synthetic analysis, 3CA staging boundary and live PubMed/Crossref/Reactome calls.
- Final `workflow_codex/test-Qwen3.5-4B.ps1`: exit 0 in 224 seconds. It reported all 10 tool43CA MCP tools and all nine research-quality MCP tools actually called; model/path/read/list/function protocol/network/write/shell checks passed. The live search returned no parseable results and the agent preserved that failure without inventing links, which the corrected smoke-test contract accepts.

`FULL_TEST_EXIT_CODE=0`

This establishes that the frozen engineering entrypoints executed successfully. It does not establish the scientific answers for QA_R1; those require the new run outputs and independent review.
