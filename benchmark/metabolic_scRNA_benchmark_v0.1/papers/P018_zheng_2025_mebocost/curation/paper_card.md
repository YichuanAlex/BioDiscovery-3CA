# Paper Card: P018

## Citation

MEBOCOST maps metabolite-mediated intercellular communications using single-cell RNA-seq  
DOI: 10.1093/nar/gkaf569

## Benchmark role

- Tier: B
- Role: metabolic_communication_method
- Primary axis: Q2
- Secondary axes: None
- Current status: candidate_requires_independent_reproduction

## Why it was selected

Extends cell-type metabolic states to metabolite-mediated communication and includes simulation, spatial, CRISPR, and clinical validation.

## Candidate paper-supported claim

MEBOCOST infers candidate metabolite-mediated sender-receiver relationships from enzyme, sensor, and optional flux information; the result is an association requiring orthogonal validation.

This sentence is a curation candidate, not a verified gold claim. It remains excluded from official scoring until independent reproduction and sensitivity testing are complete.

## Data and code inventory

- Seeded stable identifiers: 10.6084/m9.figshare.28291367.v1, 10.6084/m9.figshare.28291850.v1
- Automatically extracted candidate identifiers: SCP1376, GSE160585
- Code URLs: https://github.com/kaifuchenlab/MEBOCOST, https://github.com/kaifuchenlab/mebocost_paper_scripts
- Origin status: full_text_available_si_not_found

## Evidence boundary

RNA expression can support a transcriptional metabolic program or model-inferred metabolic potential. It does not by itself establish enzyme activity, metabolite abundance, exchange flux, or causal metabolic mechanism.

## Next curation actions

1. Materialize the exact permitted input files and freeze checksums.
2. Map the target claim to figures, supplementary tables, code, and data objects.
3. Reproduce the claim in a clean environment with patient/sample-aware statistics.
4. Run at least one reasonable method/threshold sensitivity analysis and an expression-matched random-gene-set control.
5. Complete answerability, leakage, adversarial grader tests, and dual sign-off.
