# Paper Card: P026

## Citation

Inferring pathway activity from single-cell and spatial transcriptomics data with PaaSc  
DOI: 10.1371/journal.pcbi.1013666

## Benchmark role

- Tier: A
- Role: gene_set_scoring_method
- Primary axis: Q1
- Secondary axes: Q2, Q3
- Current status: candidate_requires_independent_reproduction

## Why it was selected

A recent peer-reviewed pathway-activity method benchmarked on multimodal and cancer datasets with versioned Zenodo source data and code.

## Candidate paper-supported claim

PaaSc infers pathway activity in a joint cell-gene latent space and reports robustness to batch effects across single-cell, spatial, and multimodal benchmarks.

This sentence is a curation candidate, not a verified gold claim. It remains excluded from official scoring until independent reproduction and sensitivity testing are complete.

## Data and code inventory

- Seeded stable identifiers: 10.5281/zenodo.17138447, 10.5281/zenodo.17136774
- Automatically extracted candidate identifiers: GSE175533, GSE102090, GSE119807, GSE115301, GSE100501, GSE96583
- Code URLs: https://github.com/yoyoong/PaaSc
- Origin status: downloaded_with_si

## Evidence boundary

RNA expression can support a transcriptional metabolic program or model-inferred metabolic potential. It does not by itself establish enzyme activity, metabolite abundance, exchange flux, or causal metabolic mechanism.

## Next curation actions

1. Materialize the exact permitted input files and freeze checksums.
2. Map the target claim to figures, supplementary tables, code, and data objects.
3. Reproduce the claim in a clean environment with patient/sample-aware statistics.
4. Run at least one reasonable method/threshold sensitivity analysis and an expression-matched random-gene-set control.
5. Complete answerability, leakage, adversarial grader tests, and dual sign-off.
