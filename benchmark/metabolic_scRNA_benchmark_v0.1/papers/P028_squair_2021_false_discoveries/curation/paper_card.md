# Paper Card: P028

## Citation

Confronting false discoveries in single-cell differential expression  
DOI: 10.1038/s41467-021-25960-2

## Benchmark role

- Tier: A
- Role: statistical_guardrail
- Primary axis: Q3
- Secondary axes: Q2
- Current status: candidate_requires_independent_reproduction

## Why it was selected

Establishes the hard requirement to model biological replicates rather than treating cells as independent observations in state comparisons.

## Candidate paper-supported claim

Methods that ignore between-replicate variation can report large numbers of false differential-expression findings when no biological difference exists.

This sentence is a curation candidate, not a verified gold claim. It remains excluded from official scoring until independent reproduction and sensitivity testing are complete.

## Data and code inventory

- Seeded stable identifiers: None; inspect full text and supplement.
- Automatically extracted candidate identifiers: GSE124872, GSE101901, GSE118918, E-MTAB-7716, GSE124952, GSE141552, GSE130653, GSE141115, GSE134174, GSE129150, GSE92332, E-MTAB-6754, E-MTAB-6773, E-MTAB-7051, GSE102827, GSE118257, GSE96583, GSE144136, GSE148339, SCP548, GSE122960, GSE103892, GSE138266, GSE142245, GSE137398, SCP509, GSE112294, GSE130664, GSE131776, GSE103976, SCP263, GSE165003
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
