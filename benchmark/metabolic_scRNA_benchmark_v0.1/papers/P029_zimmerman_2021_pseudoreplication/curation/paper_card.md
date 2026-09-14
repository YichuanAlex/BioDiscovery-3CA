# Paper Card: P029

## Citation

A practical solution to pseudoreplication bias in single-cell studies  
DOI: 10.1038/s41467-021-21038-1

## Benchmark role

- Tier: A
- Role: statistical_guardrail
- Primary axis: Q2
- Secondary axes: Q3
- Current status: candidate_requires_independent_reproduction

## Why it was selected

Supplies a focused benchmark for false precision caused by cell-level pseudoreplication and supports donor-aware mixed or aggregated analyses.

## Candidate paper-supported claim

Treating cells as independent replicates inflates significance; donor-aware hierarchical analysis controls pseudoreplication bias.

This sentence is a curation candidate, not a verified gold claim. It remains excluded from official scoring until independent reproduction and sensitivity testing are complete.

## Data and code inventory

- Seeded stable identifiers: None; inspect full text and supplement.
- Automatically extracted candidate identifiers: GSE81861, GSE72056, E-MTAB-5061, EGAS00001004082
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
