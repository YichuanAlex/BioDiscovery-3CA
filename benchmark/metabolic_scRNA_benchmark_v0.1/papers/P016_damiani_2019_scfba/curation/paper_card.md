# Paper Card: P016

## Citation

Integration of single-cell RNA-seq data into population models to characterize cancer metabolism  
DOI: 10.1371/journal.pcbi.1006733

## Benchmark role

- Tier: A
- Role: metabolic_inference_method
- Primary axis: Q1
- Secondary axes: Q2
- Current status: candidate_requires_independent_reproduction

## Why it was selected

scFBA is an early reference for constructing cell-specific metabolic models and comparing metabolic states while enforcing a network model.

## Candidate paper-supported claim

Single-cell transcriptomes can constrain a network of cell-specific metabolic models that exposes heterogeneous metabolic capabilities and intercellular relationships.

This sentence is a curation candidate, not a verified gold claim. It remains excluded from official scoring until independent reproduction and sensitivity testing are complete.

## Data and code inventory

- Seeded stable identifiers: None; inspect full text and supplement.
- Automatically extracted candidate identifiers: GSE69405, GSE75688
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
