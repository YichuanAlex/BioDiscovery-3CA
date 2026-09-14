# Paper Card: P027

## Citation

Benchmarking atlas-level data integration in single-cell genomics  
DOI: 10.1038/s41592-021-01336-8

## Benchmark role

- Tier: A
- Role: quality_control_benchmark
- Primary axis: Q2
- Secondary axes: Q3
- Current status: candidate_requires_independent_reproduction

## Why it was selected

Defines biology-conservation and batch-removal metrics needed to prevent metabolic clusters from merely rediscovering study, donor, chemistry, or tumour batch.

## Candidate paper-supported claim

Single-cell integration methods trade off batch removal and biological conservation; no method dominates all tasks and datasets.

This sentence is a curation candidate, not a verified gold claim. It remains excluded from official scoring until independent reproduction and sensitivity testing are complete.

## Data and code inventory

- Seeded stable identifiers: None; inspect full text and supplement.
- Automatically extracted candidate identifiers: GSE81076, GSE85241, GSE86469, GSE84133, GSE81608, E-MTAB-5061, GSE120221, GSE107727, GSE115189, GSE128066, GSE94820, GSE130148, GSE110823, GSE111586
- Code URLs: https://github.com/theislab/scib
- Origin status: downloaded_with_si

## Evidence boundary

RNA expression can support a transcriptional metabolic program or model-inferred metabolic potential. It does not by itself establish enzyme activity, metabolite abundance, exchange flux, or causal metabolic mechanism.

## Next curation actions

1. Materialize the exact permitted input files and freeze checksums.
2. Map the target claim to figures, supplementary tables, code, and data objects.
3. Reproduce the claim in a clean environment with patient/sample-aware statistics.
4. Run at least one reasonable method/threshold sensitivity analysis and an expression-matched random-gene-set control.
5. Complete answerability, leakage, adversarial grader tests, and dual sign-off.
