# Paper Card: P024

## Citation

Benchmarking algorithms for pathway activity transformation of single-cell RNA-seq data  
DOI: 10.1016/j.csbj.2020.10.007

## Benchmark role

- Tier: A
- Role: method_benchmark
- Primary axis: Q1
- Secondary axes: Q2
- Current status: candidate_requires_independent_reproduction

## Why it was selected

Directly evaluates whether pathway-transformed representations preserve cell-type structure and support clustering across 32 datasets.

## Candidate paper-supported claim

Pathway activity transformations can retain cell-type heterogeneity, but accuracy, dropout stability, and scalability differ substantially among methods and dataset technologies.

This sentence is a curation candidate, not a verified gold claim. It remains excluded from official scoring until independent reproduction and sensitivity testing are complete.

## Data and code inventory

- Seeded stable identifiers: None; inspect full text and supplement.
- Automatically extracted candidate identifiers: None
- Code URLs: None recorded
- Origin status: full_text_available_si_not_found

## Evidence boundary

RNA expression can support a transcriptional metabolic program or model-inferred metabolic potential. It does not by itself establish enzyme activity, metabolite abundance, exchange flux, or causal metabolic mechanism.

## Next curation actions

1. Materialize the exact permitted input files and freeze checksums.
2. Map the target claim to figures, supplementary tables, code, and data objects.
3. Reproduce the claim in a clean environment with patient/sample-aware statistics.
4. Run at least one reasonable method/threshold sensitivity analysis and an expression-matched random-gene-set control.
5. Complete answerability, leakage, adversarial grader tests, and dual sign-off.
