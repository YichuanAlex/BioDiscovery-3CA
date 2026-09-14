# Paper Card: P014

## Citation

A graph neural network model to estimate cell-wise metabolic flux using single-cell RNA-seq data  
DOI: 10.1101/gr.271205.120

## Benchmark role

- Tier: A
- Role: metabolic_inference_method
- Primary axis: Q1
- Secondary axes: Q2, Q3
- Current status: candidate_requires_independent_reproduction

## Why it was selected

scFEA directly produces cell-wise module flux scores and includes downstream clustering of cells with distinct metabolic states plus matched metabolomic validation.

## Candidate paper-supported claim

scFEA estimates relative cell-wise metabolic module fluxes that recover condition- and cell-group-specific metabolic variation and agree directionally with matched metabolomics.

This sentence is a curation candidate, not a verified gold claim. It remains excluded from official scoring until independent reproduction and sensitivity testing are complete.

## Data and code inventory

- Seeded stable identifiers: None; inspect full text and supplement.
- Automatically extracted candidate identifiers: GSE132581, GSE72056, GSE103322, GSE99305, GSE173433
- Code URLs: https://github.com/changwn/scFEA
- Origin status: full_text_available_si_not_found

## Evidence boundary

RNA expression can support a transcriptional metabolic program or model-inferred metabolic potential. It does not by itself establish enzyme activity, metabolite abundance, exchange flux, or causal metabolic mechanism.

## Next curation actions

1. Materialize the exact permitted input files and freeze checksums.
2. Map the target claim to figures, supplementary tables, code, and data objects.
3. Reproduce the claim in a clean environment with patient/sample-aware statistics.
4. Run at least one reasonable method/threshold sensitivity analysis and an expression-matched random-gene-set control.
5. Complete answerability, leakage, adversarial grader tests, and dual sign-off.
