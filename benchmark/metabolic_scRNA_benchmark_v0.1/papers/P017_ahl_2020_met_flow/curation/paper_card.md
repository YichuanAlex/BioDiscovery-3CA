# Paper Card: P017

## Citation

Met-Flow, a strategy for single-cell metabolic analysis highlights dynamic changes in immune subpopulations  
DOI: 10.1038/s42003-020-1027-9

## Benchmark role

- Tier: C
- Role: orthogonal_biological_validation
- Primary axis: Q2
- Secondary axes: Q3
- Current status: reference_only_non_scrna_input

## Why it was selected

Met-Flow measures metabolic proteins at single-cell resolution and is retained as an orthogonal comparator, not as an scRNA-seq leaderboard task.

## Candidate paper-supported claim

A targeted panel of metabolic proteins distinguishes immune-cell subsets and detects dynamic metabolic remodeling, but represents metabolic capacity rather than direct flux.

This sentence is a curation candidate, not a verified gold claim. It remains excluded from official scoring until independent reproduction and sensitivity testing are complete.

## Data and code inventory

- Seeded stable identifiers: None; inspect full text and supplement.
- Automatically extracted candidate identifiers: None
- Code URLs: None recorded
- Origin status: downloaded_with_si

## Evidence boundary

RNA expression can support a transcriptional metabolic program or model-inferred metabolic potential. It does not by itself establish enzyme activity, metabolite abundance, exchange flux, or causal metabolic mechanism.

## Next curation actions

1. Materialize the exact permitted input files and freeze checksums.
2. Map the target claim to figures, supplementary tables, code, and data objects.
3. Reproduce the claim in a clean environment with patient/sample-aware statistics.
4. Run at least one reasonable method/threshold sensitivity analysis and an expression-matched random-gene-set control.
5. Complete answerability, leakage, adversarial grader tests, and dual sign-off.
