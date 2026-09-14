# Paper Card: P021

## Citation

UCell and pyUCell: single-cell gene signature scoring for R and Python  
DOI: 10.1093/bioinformatics/btag055

## Benchmark role

- Tier: A
- Role: gene_set_scoring_method
- Primary axis: Q1
- Secondary axes: Q2, Q3
- Current status: candidate_requires_independent_reproduction

## Why it was selected

The current cross-language implementation supplies AnnData support, explicit missing-gene handling, signed signatures, and optional score smoothing.

## Candidate paper-supported claim

UCell v2 and pyUCell provide reproducible rank-based signature scoring across R and Python with controlled handling of missing genes and optional kNN score smoothing.

This sentence is a curation candidate, not a verified gold claim. It remains excluded from official scoring until independent reproduction and sensitivity testing are complete.

## Data and code inventory

- Seeded stable identifiers: None; inspect full text and supplement.
- Automatically extracted candidate identifiers: None
- Code URLs: https://github.com/carmonalab/UCell, https://github.com/carmonalab/pyUCell
- Origin status: full_text_available_si_not_found

## Evidence boundary

RNA expression can support a transcriptional metabolic program or model-inferred metabolic potential. It does not by itself establish enzyme activity, metabolite abundance, exchange flux, or causal metabolic mechanism.

## Next curation actions

1. Materialize the exact permitted input files and freeze checksums.
2. Map the target claim to figures, supplementary tables, code, and data objects.
3. Reproduce the claim in a clean environment with patient/sample-aware statistics.
4. Run at least one reasonable method/threshold sensitivity analysis and an expression-matched random-gene-set control.
5. Complete answerability, leakage, adversarial grader tests, and dual sign-off.
