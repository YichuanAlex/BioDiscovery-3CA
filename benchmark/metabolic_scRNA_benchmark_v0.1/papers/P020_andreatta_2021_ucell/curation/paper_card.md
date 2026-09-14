# Paper Card: P020

## Citation

UCell: Robust and scalable single-cell gene signature scoring  
DOI: 10.1016/j.csbj.2021.06.043

## Benchmark role

- Tier: A
- Role: gene_set_scoring_method
- Primary axis: Q1
- Secondary axes: Q2, Q3
- Current status: candidate_requires_independent_reproduction

## Why it was selected

UCell offers composition-robust, rank-based per-cell scoring and is a strong baseline for the fixed 1,988-gene list.

## Candidate paper-supported claim

UCell scores depend on within-cell gene ranks and are robust to dataset size and composition while scaling to large single-cell datasets.

This sentence is a curation candidate, not a verified gold claim. It remains excluded from official scoring until independent reproduction and sensitivity testing are complete.

## Data and code inventory

- Seeded stable identifiers: None; inspect full text and supplement.
- Automatically extracted candidate identifiers: None
- Code URLs: https://github.com/carmonalab/UCell
- Origin status: full_text_available_si_not_found

## Evidence boundary

RNA expression can support a transcriptional metabolic program or model-inferred metabolic potential. It does not by itself establish enzyme activity, metabolite abundance, exchange flux, or causal metabolic mechanism.

## Next curation actions

1. Materialize the exact permitted input files and freeze checksums.
2. Map the target claim to figures, supplementary tables, code, and data objects.
3. Reproduce the claim in a clean environment with patient/sample-aware statistics.
4. Run at least one reasonable method/threshold sensitivity analysis and an expression-matched random-gene-set control.
5. Complete answerability, leakage, adversarial grader tests, and dual sign-off.
