# Paper Card: P025

## Citation

Robustness and applicability of transcription factor and pathway analysis tools on single-cell RNA-seq data  
DOI: 10.1186/s13059-020-1949-z

## Benchmark role

- Tier: A
- Role: method_benchmark
- Primary axis: Q1
- Secondary axes: Q2
- Current status: candidate_requires_independent_reproduction

## Why it was selected

Uses perturbation-based ground truth to separate the value of gene-set resources from the scoring algorithms applied to single-cell data.

## Candidate paper-supported claim

Pathway and regulator activities can preserve biologically meaningful single-cell variation, and performance is often more sensitive to the prior-knowledge resource than to the enrichment statistic.

This sentence is a curation candidate, not a verified gold claim. It remains excluded from official scoring until independent reproduction and sensitivity testing are complete.

## Data and code inventory

- Seeded stable identifiers: None; inspect full text and supplement.
- Automatically extracted candidate identifiers: GSM2396858, GSM2396859, GSM3630200, GSM3630201, GSM3630202, GSM3630203, GSE133549
- Code URLs: https://github.com/saezlab/ConservedFootprints
- Origin status: full_text_available_si_not_found

## Evidence boundary

RNA expression can support a transcriptional metabolic program or model-inferred metabolic potential. It does not by itself establish enzyme activity, metabolite abundance, exchange flux, or causal metabolic mechanism.

## Next curation actions

1. Materialize the exact permitted input files and freeze checksums.
2. Map the target claim to figures, supplementary tables, code, and data objects.
3. Reproduce the claim in a clean environment with patient/sample-aware statistics.
4. Run at least one reasonable method/threshold sensitivity analysis and an expression-matched random-gene-set control.
5. Complete answerability, leakage, adversarial grader tests, and dual sign-off.
