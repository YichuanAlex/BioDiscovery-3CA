# QA_R11 execution contract

- Work only in `/Users/bytedance/Downloads/BioDiscovery-3CA/3CA/QA_R11`. Never read, copy, resume, or modify any `Q1_R*`, `QA_R10`, or other `QA_R*` research artifact.
- `inputs/metabolic_genes_total.csv` is immutable user input. Use the native mapping audit; preserve exact and unique case-insensitive matching outcomes and prevalence filtering.
- Obtain public raw counts through native 3CA tools. Reuse is limited to the verified hash-addressed public cache.
- Run the native global metabolic-state core first, then the exact metadata subset `cell_subtype=CD8 T cells`. Do not write or run custom analysis code.
- Treat cells as nested within patients and samples. NMI, ARI, silhouette, cluster composition, and random-set ranks are descriptive evidence, not independent-replicate significance tests or causal evidence.
- Installed optional Skills and anonymous MCPs may support literature or methodology lookup, but they must not replace the deterministic native 3CA/core/validator tools.
- Preserve native core outputs. Copy report and manifest facts only from saved results and hashes.
- Use the exact normalization represented by the native core: per-cell library size to 10,000 followed by log1p. Never use median UMI as the denominator.
- During report repair, edit only the deliverable named by the engine. After every TeX edit, rebuild before validating again.
- Finish only after `validate_research_bundle` returns `valid=true`; pass that call's `verification_call_id` to `complete_task`.
