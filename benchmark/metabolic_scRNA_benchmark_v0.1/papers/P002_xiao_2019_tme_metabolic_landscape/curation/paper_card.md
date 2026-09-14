# Paper Card: P002

## Citation

Metabolic landscape of the tumor microenvironment at single cell resolution  
DOI: 10.1038/s41467-019-11738-0

## Benchmark role

- Tier: A
- Role: direct_biological_benchmark
- Primary axis: Q1
- Secondary axes: Q2, Q3
- Current status: candidate_requires_independent_reproduction

## Why it was selected

This is the closest published precedent to clustering cells using metabolic-gene expression and testing whether metabolic profiles distinguish malignant, immune, and stromal compartments.

## Candidate paper-supported claim

Metabolic-gene expression separates cell populations in melanoma and HNSCC; mitochondrial programs are a major source of heterogeneity and immune/stromal cells can be distinguished by metabolic features.

This sentence is a curation candidate, not a verified gold claim. It remains excluded from official scoring until independent reproduction and sensitivity testing are complete.

## Data and code inventory

- Seeded stable identifiers: GSE72056, GSE103322
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
