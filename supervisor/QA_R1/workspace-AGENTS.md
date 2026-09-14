# QA_R1 research rules

- This is the only research workspace. Do not read, copy, resume, or modify any `Q1_R*` or other `QA_R*` research artifacts.
- `inputs/metabolic_genes_total.csv` is an immutable user-supplied input. Use it directly; do not replace it with Reactome, uppercase it, or delete unmatched genes. Review the native gene-set mapping audit.
- Use only public raw-count data materialized through the 3CA tools and `prepare_3ca_dataset`. A verified hash-addressed public cache may be reused.
- Execute bounded phases in order: input/source audit; global core; exact CD8 subset core; literature verification; report/manifest; native report build; final validation; completion. A reflection step must repair a concrete artifact or validation error and then advance.
- Run `analyze_metabolic_states` first on all cells at `results/core_analysis`, then on the observed metadata value `cell_subtype=CD8 T cells` at `results/cd8_analysis`. Do not derive the CD8 subset from metabolic clusters.
- Treat cells as nested within patients/samples. Cell-level NMI, ARI, silhouette, and cluster composition are descriptive; they do not create independent biological replicates or prove discrete states.
- Preserve native core files and summaries. Write report claims only from their saved facts and hashes. Keep global separation, cell-type association, and CD8-internal separation as three separate answers.
- After the last TeX edit, call `build_research_report`. Then call `validate_research_bundle` and pass its final `verification_call_id` to `complete_task`.
