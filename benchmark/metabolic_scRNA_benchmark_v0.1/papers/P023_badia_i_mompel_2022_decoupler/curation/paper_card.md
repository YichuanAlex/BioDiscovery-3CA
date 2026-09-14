# Paper Card: P023

## Citation

decoupleR: ensemble of computational methods to infer biological activities from omics data  
DOI: 10.1093/bioadv/vbac016

## Benchmark role

- Tier: A
- Role: gene_set_scoring_method
- Primary axis: Q1
- Secondary axes: Q2
- Current status: candidate_requires_independent_reproduction

## Why it was selected

Provides a common interface and consensus framework for comparing several enrichment/statistical methods under one data contract.

## Candidate paper-supported claim

Method consensus can improve robustness of inferred activities, but performance depends jointly on the scoring statistic and prior-knowledge resource.

This sentence is a curation candidate, not a verified gold claim. It remains excluded from official scoring until independent reproduction and sensitivity testing are complete.

## Data and code inventory

- Seeded stable identifiers: 10.5281/zenodo.5645208
- Automatically extracted candidate identifiers: None
- Code URLs: https://github.com/saezlab/decoupleR
- Origin status: full_text_available_si_not_found

## Evidence boundary

RNA expression can support a transcriptional metabolic program or model-inferred metabolic potential. It does not by itself establish enzyme activity, metabolite abundance, exchange flux, or causal metabolic mechanism.

## Next curation actions

1. Materialize the exact permitted input files and freeze checksums.
2. Map the target claim to figures, supplementary tables, code, and data objects.
3. Reproduce the claim in a clean environment with patient/sample-aware statistics.
4. Run at least one reasonable method/threshold sensitivity analysis and an expression-matched random-gene-set control.
5. Complete answerability, leakage, adversarial grader tests, and dual sign-off.
