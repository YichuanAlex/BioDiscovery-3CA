# QA_R12 execution contract

- Work only in `/Users/bytedance/Downloads/BioDiscovery-3CA/3CA/QA_R12`. Never read, copy, resume, or modify any `Q1_R*`, `QA_R10`, `QA_R11`, or other `QA_R*` research artifact.
- `inputs/metabolic_genes_total.csv` is the only metabolic feature-set source. It is immutable user input; preserve its SHA-256 and native mapping audit. Do not call Reactome or substitute another gene set.
- Obtain public raw counts through native 3CA tools. Reuse is limited to the verified hash-addressed public cache.
- Run the native global metabolic-state core first, then the exact metadata subset `cell_subtype=CD8 T cells`; both calls must use `inputs/metabolic_genes_total.csv`. Do not write or run custom analysis code.
- Treat cells as nested within patients and samples. NMI, ARI, silhouette, cluster composition, and random-set ranks are descriptive evidence, not independent-replicate significance tests or causal evidence.
- Preserve native core outputs. Report and manifest facts must come only from the saved core results and hashes.
- Use per-cell library-size normalization to 10,000 followed by log1p. Never use median UMI as the denominator.
- During report repair, edit only the deliverable named by the engine. After every TeX edit, rebuild before validating again.
- Finish only after `validate_research_bundle` returns `valid=true`; pass that call's `verification_call_id` to `complete_task`.
