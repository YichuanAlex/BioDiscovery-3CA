# Paper Card: P022

## Citation

GSVA: gene set variation analysis for microarray and RNA-Seq data  
DOI: 10.1186/1471-2105-14-7

## Benchmark role

- Tier: A
- Role: gene_set_scoring_method
- Primary axis: Q1
- Secondary axes: None
- Current status: candidate_requires_independent_reproduction

## Why it was selected

GSVA/ssGSEA-style scoring remains a widely used magnitude-aware baseline and is necessary for method-family sensitivity comparisons.

## Candidate paper-supported claim

GSVA transforms gene-level expression into sample-wise pathway scores in an unsupervised manner; application to sparse single-cell data requires explicit benchmarking rather than assumption of equivalence.

This sentence is a curation candidate, not a verified gold claim. It remains excluded from official scoring until independent reproduction and sensitivity testing are complete.

## Data and code inventory

- Seeded stable identifiers: None; inspect full text and supplement.
- Automatically extracted candidate identifiers: GSE10927, GSE7792
- Code URLs: https://bioconductor.org/packages/GSVA
- Origin status: full_text_available_si_not_found

## Evidence boundary

RNA expression can support a transcriptional metabolic program or model-inferred metabolic potential. It does not by itself establish enzyme activity, metabolite abundance, exchange flux, or causal metabolic mechanism.

## Next curation actions

1. Materialize the exact permitted input files and freeze checksums.
2. Map the target claim to figures, supplementary tables, code, and data objects.
3. Reproduce the claim in a clean environment with patient/sample-aware statistics.
4. Run at least one reasonable method/threshold sensitivity analysis and an expression-matched random-gene-set control.
5. Complete answerability, leakage, adversarial grader tests, and dual sign-off.
