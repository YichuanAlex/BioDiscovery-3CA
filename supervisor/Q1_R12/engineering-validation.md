# R12 engineering validation

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
- R12_LAUNCH_STATUS=ready_after_user_cleanup

The test establishes tool operability, not the correctness of the future R12 biological conclusion.

As checked at 2026-09-13 15:20:37 +08:00, the latest full test had exited 0 after the source-bootstrap, publication-anchor, factual-method/vector-figure and changed-workspace rerun fixes. All 18 external MCP tool entry points were actually called in this latest complete run. The network-smoke transcript is workflow_codex/.runtime/codex-home/sessions/2026/09/13/rollout-2026-09-13T15-19-07-0ae6c074-cc1.jsonl. Generic web search again returned promotional/low-quality material; this passes connectivity/protocol checks only, not scientific retrieval quality or factual certification. Research citations use PubMed and exact Crossref/Reactome provenance.

The prior R12 trial was stopped and incomplete. Local policy rejected deletion, and no alternate mechanism was used. The user has now removed the old R12 directory; its absence and the absence of old R12 processes were verified. Only the exact R12 stale task/lock and launch/audit state were cleared. A new empty R12 may be created for this user-authorized retry without resuming or reusing old computations. Future similar cleanup/state conflicts must use the next unused round folder under the root AGENTS.md rule rather than deleting or reusing the old workspace. Engineering checks do not establish biological acceptance.
