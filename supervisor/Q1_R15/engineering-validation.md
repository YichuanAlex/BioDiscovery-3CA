# R15 engineering validation

Validated on 2026-09-13 before launch.

- FULL_TEST_EXIT_CODE=0
- Workflow isolation: passed
- Agent recovery and until-complete regressions: passed
- `complete_task` research-manifest hook rejection: passed
- 3CA CLI and all ten actual MCP calls: passed (live catalog refresh, study/page/cached search, one-page engineering crawl, asset plan, metadata download/extraction, inspection and SHA-256 verification)
- research-quality CLI and all eight actual MCP calls: passed (including synthetic core analysis and live Reactome/PubMed/Crossref)
- Ruff 0.16.7 undefined-name and scientific anti-pattern audit: passed
- Synthetic full-cell metabolic-state pipeline: passed after circular-inference correction (360 cells, 3 simulated patients; true labels, conditional seed stability, size-matched controls, descriptive within-replicate checks, figures)
- Complete valid bundle passes, modified single-label output and fabricated metric fail: passed
- Genuine cached 3CA raw-count staging: passed (58,843 unique cells, 33,538 source rows, 24 duplicate symbol rows retained)
- Duplicate-symbol sum preserves cell libraries and source-row mapping: passed
- Reactome release/gene extraction: passed (release 97; 2,197 unique genes in the live smoke test)
- NCBI PubMed E-utilities: passed
- Crossref DOI metadata: passed; an intentionally invalid DOI returned 404
- Scanpy/AnnData/Leiden/SciPy/scikit-learn/statsmodels/GSEApy/pypdf/Ruff imports or executable checks: passed
- Local Qwen native function-call protocol: passed
- Workflow Computer Use integration: absent
- Changed-workspace bundle/code/core-analysis reruns: passed (actual native function calls; unchanged-input duplicate guards retained)
- Current local 3CA source loaded by MCP and publication-anchor verification via stable study ID: passed
- Factual method metadata, baseline seed separation and vector PDF figure text: passed in the synthetic full-pipeline regression
- research-quality and local threeca-access Skill format checks: passed
- Research core-first Python guard: passed
- Empty-directory workspace-state invalidation: passed
- R15_LAUNCH_STATUS=ready

The test establishes tool operability, not the correctness of the future R15 biological conclusion.

At approximately 2026-09-13 16:42 +08:00, the latest complete test-Qwen3.5-4B.ps1 exited 0 after adding the research core-first Python guard, audit-triggered workspace invalidation and empty-directory state tracking. The focused guard/recovery suite independently exited 0. All 18 external MCP entry points, synthetic core/bundle rejection, live structured sources, model, attachment, file, shell, network and isolation checks passed. The network-smoke transcript is workflow_codex/.runtime/codex-home/sessions/2026/09/13/rollout-2026-09-13T16-42-33-97186f86-ace.jsonl; its generic news content is not scientific evidence.

R12, R13 and R14 are preserved as failed, incomplete rounds. R15 is a new empty workspace with a distinct persisted-task key and no resume. For research runs, the shared execution layer blocks custom workspace Python until the vetted core result exists; after that it still requires audit_analysis_code to accept the exact current file SHA-256, and editing invalidates authorization. Engineering checks do not establish biological acceptance.
