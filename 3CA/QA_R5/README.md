# QA_R5: Metabolic State Analysis Using User-Supplied Metabolic Genes

## Overview

This repository contains the analysis of metabolic gene expression patterns using the user-supplied gene set `metabolic_genes_total.csv` applied to the Choudhury et al. 2022 meningioma single-cell RNA-seq dataset (3CA:20773) from the Curated Cancer Cell Atlas.

## Research Questions

1. **Question 1**: Using only the user-supplied metabolic genes, do all cells form reproducible transcriptional metabolic groupings?
2. **Question 2**: What is the relationship between these groupings and known cell types and cell subtypes?
3. **Question 3**: Within the same cell type, specifically for `cell_subtype=CD8 T cells`, are there still distinct metabolic groupings?

## Deliverables

- `report/main.tex` - LaTeX report with analysis results
- `report/main.pdf` - Compiled PDF report
- `results/summary.json` - Global analysis summary
- `results/analysis_manifest.json` - Analysis manifest with metadata
- `results/core_analysis/core_result.json` - Global core analysis results
- `results/cd8_analysis/core_result.json` - CD8 T cells subset analysis results
- `results/cd8_analysis/summary.json` - CD8 T cells analysis summary
- `README.md` - This file

## Key Findings

### Question 1: Reproducible Metabolic Groupings Across All Cells

The global analysis of 58,843 cells using 1,646 metabolic genes yielded 17 clusters at resolution 0.8.

- **Leiden silhouette**: 0.217
- **Matched-k KMeans**: 0.220
- **Random control comparison**: 2 of 19 random controls exceeded metabolic clustering (add-one rank fraction: 0.15)
- **HVG vs random controls**: HVG silhouette (0.283) exceeded random control range [0.199, 0.222]

The metabolic gene clustering is comparable to matched-k KMeans but lower than HVG-based clustering. The random control comparison indicates the metabolic clustering is not significantly better than random.

### Question 2: Relationship to Cell Types and Subtypes

The clustering is strongly associated with cell subtype (NMI: 0.648), patient (NMI: 0.518), and sample (NMI: 0.548). Cell type shows moderate association (NMI: 0.496).

### Question 3: Metabolic Groupings Within CD8 T Cells

The CD8 T cells subset analysis included 3,624 cells and 1,318 metabolic genes, yielding 6 clusters at resolution 0.4.

- **Leiden silhouette**: 0.099
- **Matched-k KMeans**: 0.095
- **Random control comparison**: 17 of 19 random controls exceeded metabolic clustering (add-one rank fraction: 0.9)
- **HVG vs random controls**: HVG silhouette (0.168) exceeded random control range [0.092, 0.131]

The CD8 T cells analysis shows very weak clustering structure, substantially worse than random.

## Citations

1. Choudhury et al. (2022). *Meningioma DNA methylation groups identify biological drivers and therapeutic vulnerabilities*. Nature Genetics. DOI: 10.1038/s41588-022-01061-8
2. Gavish et al. (2023). *Hallmarks of transcriptional intratumour heterogeneity across a thousand tumours*. Nature. DOI: 10.1038/s41586-023-06130-4

## Limitations

- Cell-level clustering metrics are descriptive and do not establish discrete biological states.
- The analysis treats cells as nested within patients/samples; cell-level NMI, ARI, silhouette, and cluster composition are descriptive statistics.
- Random control comparisons use add-one rank fraction as a descriptive metric, not a biological P value.
- The clustering resolution was selected based on silhouette and ARI criteria, not biological validation.
- No automatic threshold proves independence from confounders.
- The same matrix-derived cluster labels cannot be used for cell-level significance testing.
