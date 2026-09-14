# Paper Card: P015

## Citation

Characterizing cancer metabolism from bulk and single-cell RNA-seq data using METAFlux  
DOI: 10.1038/s41467-023-40457-w

## Benchmark role

- Tier: A
- Role: metabolic_inference_method
- Primary axis: Q2
- Secondary axes: Q1
- Current status: candidate_requires_independent_reproduction

## Why it was selected

METAFlux is cancer-focused, models metabolic activity at cell-cluster/community resolution, and benchmarks predictions against measured metabolite flux.

## Candidate paper-supported claim

METAFlux recovers cancer metabolic heterogeneity and cell-type interactions; its outputs are relative inferred fluxes and are computed for groups rather than literal single-cell measured flux.

This sentence is a curation candidate, not a verified gold claim. It remains excluded from official scoring until independent reproduction and sensitivity testing are complete.

## Data and code inventory

- Seeded stable identifiers: None; inspect full text and supplement.
- Automatically extracted candidate identifiers: GSE135565, GSE107754, GSE111907, GSE131907, GSE190976
- Code URLs: https://github.com/KChen-lab/METAFlux
- Origin status: downloaded_with_si

## Evidence boundary

RNA expression can support a transcriptional metabolic program or model-inferred metabolic potential. It does not by itself establish enzyme activity, metabolite abundance, exchange flux, or causal metabolic mechanism.

## Next curation actions

1. Materialize the exact permitted input files and freeze checksums.
2. Map the target claim to figures, supplementary tables, code, and data objects.
3. Reproduce the claim in a clean environment with patient/sample-aware statistics.
4. Run at least one reasonable method/threshold sensitivity analysis and an expression-matched random-gene-set control.
5. Complete answerability, leakage, adversarial grader tests, and dual sign-off.
