# Single-Cell Metabolic State Analysis (QA_R4)

## Overview

This repository contains the analysis of single-cell RNA-seq data from the Choudhury et al. 2022 meningioma study (3CA:20773) using user-supplied metabolic genes to investigate transcriptional metabolic states.

## Dataset

- **Study**: Choudhury et al. 2022 - Meningioma DNA methylation groups identify biological drivers and therapeutic vulnerabilities
- **3CA ID**: 3ca:20773
- **DOI**: 10.1038/s41588-022-01061-8
- **Platform**: 10x Genomics
- **Samples**: 10
- **Cells**: 58,843
- **Genes**: 33,538 (33,514 unique symbols, 24 duplicate symbol rows aggregated)

## Analysis

### User-Supplied Metabolic Genes

The analysis used a user-supplied gene set from `inputs/metabolic_genes_total.csv`:
- **Source gene symbols**: 1,988
- **Global analysis matched genes**: 1,646
- **CD8 T cell subset matched genes**: 1,318

### Analysis Scope

1. **Global Analysis**: All 58,843 cells using 1,646 metabolic genes
   - Clusters identified: 17
   - Conclusion: Inconclusive for discrete metabolic states

2. **CD8 T Cell Subset Analysis**: 3,624 CD8 T cells using 1,318 metabolic genes
   - Clusters identified: 6
   - Conclusion: Inconclusive for discrete metabolic states

## Key Findings

### Question 1: Reproducible Metabolic Groupings Across All Cells

Using the user-supplied metabolic genes across all 58,843 cells, the analysis identified 17 clusters. However, the results are **inconclusive** for defining discrete metabolic states. The clustering is primarily driven by cell type identity and patient/sample structure rather than independent metabolic programs.

### Question 2: Relationship Between Groupings and Cell Types

The clustering shows strong association with cell type and cell subtype metadata:
- **Cell type NMI**: 0.496 (global)
- **Cell subtype NMI**: 0.648 (global)
- **Patient NMI**: 0.518
- **Sample NMI**: 0.548

This indicates that the observed clustering is largely explained by known biological and technical confounders.

### Question 3: Metabolic Groupings Within CD8 T Cells

Within the CD8 T cell subtype (n=3,624), the analysis identified 6 clusters using 1,318 metabolic genes. The results are also **inconclusive** for defining discrete metabolic states. The clustering is driven by patient/sample structure rather than independent metabolic subtypes.

## Limitations

1. **Descriptive Metrics Only**: Cell-level clustering metrics (silhouette, ARI, NMI) are descriptive and do not constitute statistical significance tests.

2. **No Discrete State Proof**: The analysis does not establish discrete biological metabolic states; it only describes observed separation patterns.

3. **Confounder Influence**: Patient and sample confounders strongly influence clustering, limiting biological interpretation.

4. **Not Independent Validation**: Clusters derived from the same expression matrix cannot be used for independent hypothesis testing.

## Artifacts

- `report/main.tex`: LaTeX source document
- `report/main.pdf`: Compiled PDF report
- `results/summary.json`: Global analysis summary
- `results/cd8_analysis/summary.json`: CD8 T cell subset analysis summary
- `results/core_analysis/core_result.json`: Global core analysis results
- `results/cd8_analysis/core_result.json`: CD8 T cell core analysis results
- `results/analysis_manifest.json`: Analysis manifest with metadata
- `figures/clustering_diagnostics.pdf`: Global clustering diagnostics
- `figures/cd8_analysis/clustering_diagnostics.pdf`: CD8 T cell clustering diagnostics

## References

1. Choudhury, A., Magill, S. T., Eaton, C. D., et al. (2022). Meningioma DNA methylation groups identify biological drivers and therapeutic vulnerabilities. *Nature Genetics*, 54(5), 649-659. https://doi.org/10.1038/s41588-022-01061-8

2. Stuart, A. J., Butler, A., Hoffman, P., et al. (2019). Comprehensive integration of single-cell data. *Cell*, 177(7), 1888-1902. https://doi.org/10.1016/j.cell.2019.05.031
