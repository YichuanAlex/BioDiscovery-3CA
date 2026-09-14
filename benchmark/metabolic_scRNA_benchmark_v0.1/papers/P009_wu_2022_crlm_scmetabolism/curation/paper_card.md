# Paper Card: P009

## Citation

Spatiotemporal Immune Landscape of Colorectal Cancer Liver Metastasis at Single-Cell Level  
DOI: 10.1158/2159-8290.CD-21-0316

## Benchmark role

- Tier: B
- Role: direct_biological_benchmark
- Primary axis: Q2
- Secondary axes: Q1
- Current status: candidate_requires_independent_reproduction

## Why it was selected

This paper introduced the scMetabolism package in a tumour atlas and directly compared metabolic activities across immune-cell states and anatomical sites.

## Candidate paper-supported claim

MRC1+ CCL18+ macrophages in colorectal liver metastases show a highly active metabolic transcriptional profile, especially in metastatic tumours.

This sentence is a curation candidate, not a verified gold claim. It remains excluded from official scoring until independent reproduction and sensitivity testing are complete.

## Data and code inventory

- Seeded stable identifiers: OEP001756
- Automatically extracted candidate identifiers: GSE41568
- Code URLs: https://github.com/wu-yc/scMetabolism
- Origin status: full_text_available_si_not_found

## Evidence boundary

RNA expression can support a transcriptional metabolic program or model-inferred metabolic potential. It does not by itself establish enzyme activity, metabolite abundance, exchange flux, or causal metabolic mechanism.

## Next curation actions

1. Materialize the exact permitted input files and freeze checksums.
2. Map the target claim to figures, supplementary tables, code, and data objects.
3. Reproduce the claim in a clean environment with patient/sample-aware statistics.
4. Run at least one reasonable method/threshold sensitivity analysis and an expression-matched random-gene-set control.
5. Complete answerability, leakage, adversarial grader tests, and dual sign-off.
