# R14 engineering validation

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
- R14_LAUNCH_STATUS=ready

The test establishes tool operability, not the correctness of the future R14 biological conclusion.

At approximately 2026-09-13 16:30 +08:00, the latest complete test-Qwen3.5-4B.ps1 exited 0 after adding exact-hash Python audit enforcement. The focused guard/recovery suite independently exited 0. All 18 external MCP entry points, synthetic core/bundle rejection, live structured sources, model, attachment, file, shell, network and isolation checks passed. The network-smoke transcript is workflow_codex/.runtime/codex-home/sessions/2026/09/13/rollout-2026-09-13T16-29-50-9a3b1726-6e5.jsonl; its generic news content is not scientific evidence.

R12 and R13 are preserved as failed, incomplete rounds. R14 is a new empty workspace with a distinct persisted-task key and no resume. The shared execution layer now blocks a workspace Python script until audit_analysis_code has accepted the exact current file SHA-256; editing it invalidates that authorization. Engineering checks do not establish biological acceptance.
