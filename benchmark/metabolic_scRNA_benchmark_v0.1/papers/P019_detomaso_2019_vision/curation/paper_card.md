# Paper Card: P019

## Citation

Functional interpretation of single cell similarity maps  
DOI: 10.1038/s41467-019-12235-0

## Benchmark role

- Tier: A
- Role: gene_set_scoring_method
- Primary axis: Q1
- Secondary axes: Q2, Q3
- Current status: candidate_requires_independent_reproduction

## Why it was selected

VISION is the default engine used by scMetabolism and directly annotates variation over a cell-cell similarity graph.

## Candidate paper-supported claim

VISION detects and scores biological signatures over single-cell similarity maps without requiring predefined clusters.

This sentence is a curation candidate, not a verified gold claim. It remains excluded from official scoring until independent reproduction and sensitivity testing are complete.

## Data and code inventory

- Seeded stable identifiers: None; inspect full text and supplement.
- Automatically extracted candidate identifiers: GSE25088, GSE100866, GSE96583, GSE116256, GSE89754, GSM2388072
- Code URLs: https://github.com/YosefLab/VISION
- Origin status: downloaded_with_si

## Evidence boundary

RNA expression can support a transcriptional metabolic program or model-inferred metabolic potential. It does not by itself establish enzyme activity, metabolite abundance, exchange flux, or causal metabolic mechanism.

## Next curation actions

1. Materialize the exact permitted input files and freeze checksums.
2. Map the target claim to figures, supplementary tables, code, and data objects.
3. Reproduce the claim in a clean environment with patient/sample-aware statistics.
4. Run at least one reasonable method/threshold sensitivity analysis and an expression-matched random-gene-set control.
5. Complete answerability, leakage, adversarial grader tests, and dual sign-off.
