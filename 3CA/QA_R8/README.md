# QA_R8: Metabolic State Analysis of Choudhury et al. 2022 Brain Data

## Overview

This repository contains the analysis of single-cell RNA-seq data from the Choudhury et al. 2022 study (3CA:20773), focusing on metabolic gene expression patterns across cell types and within CD8 T cells.

## Data Source

- **Study ID**: 3ca:20773
- **Title**: Meningioma DNA methylation groups identify biological drivers and therapeutic vulnerabilities
- **Journal**: Nature Genetics
- **DOI**: 10.1038/s41588-022-01061-8
- **Technology**: 10x Genomics
- **Samples**: 10
- **Total Cells**: 58,843

## User-Supplied Gene Set

- **File**: `inputs/metabolic_genes_total.csv`
- **SHA-256**: 7503180d29693bd1e654ea93281db0e3ec4177ff44842c8b02f6a098402e41a9
- **Source Gene Count**: 1,988
- **Matched Gene Count**: 900 (after case-insensitive matching)

## Analysis Results

### Question 1: Global Metabolic Grouping

**Verdict**: Candidate partitions observed but distinct metabolic states inconclusive

- **Cells Analyzed**: 58,843
- **Metabolic Genes**: 1,646 (matched)
- **Resolution**: 0.8
- **Clusters**: 17 (714-8,806 cells)
- **Leiden Silhouette**: 0.217
- **Stability (mean/min ARI)**: 0.965 / 0.947
- **Matched-k KMeans**: 0.220
- **Random Controls (>= metabolic)**: 2/19 (add-one rank: 0.15)
- **Patient NMI**: 0.518
- **Cell Type NMI**: 0.496
- **Cell Subtype NMI**: 0.648

### Question 2: Association with Cell Types/Subtypes

**Verdict**: Associations are descriptive and non-causal

- **Patient NMI**: 0.518 (strongest confounder)
- **Cell Type NMI**: 0.496
- **Cell Subtype NMI**: 0.648
- **Patient-within ARI Range**: 0.071 - 0.676
- **Weakest Patient**: 3 (3,287 cells)

### Question 3: CD8 T Cells Subgroup Analysis

**Verdict**: CD8 candidate partitions observed but distinct metabolic states inconclusive

- **Cells Analyzed**: 3,624
- **Metabolic Genes**: 1,318 (matched)
- **Resolution**: 0.4
- **Clusters**: 6 (55-2,002 cells)
- **Leiden Silhouette**: 0.099
- **Stability (mean/min ARI)**: 0.759 / 0.600
- **Matched-k KMeans**: 0.095
- **Random Controls (>= metabolic)**: 17/19 (add-one rank: 0.9)
- **Patient NMI**: 0.393
- **Cell Type NMI**: undefined
- **Cell Subtype NMI**: undefined

## Deliverables

| File | Description |
|------|-------------|
| `report/main.tex` | LaTeX source for research report |
| `report/main.pdf` | Compiled research report |
| `results/summary.json` | Global analysis summary |
| `results/analysis_manifest.json` | Analysis manifest with hashes |
| `results/core_analysis/core_result.json` | Global core analysis results |
| `results/cd8_analysis/core_result.json` | CD8 T cells core analysis results |
| `results/cd8_analysis/summary.json` | CD8 T cells summary |

## Figures

- `figures/metabolic_umap.pdf` - Global metabolic UMAP
- `figures/clustering_diagnostics.pdf` - Global clustering diagnostics
- `figures/cd8_analysis/metabolic_umap.pdf` - CD8 T cells metabolic UMAP
- `figures/cd8_analysis/clustering_diagnostics.pdf` - CD8 T cells clustering diagnostics

## References

1. Choudhury A, Magill ST, Eaton CD, et al. Meningioma DNA methylation groups identify biological drivers and therapeutic vulnerabilities. Nature Genetics. 2022;54(5):649-659. DOI: 10.1038/s41588-022-01061-8

2. Gavish A, Tyler M, Greenwald AC, et al. Hallmarks of transcriptional intratumour heterogeneity across a thousand tumours. Nature. 2023;618(7965):598-606. DOI: 10.1038/s41586-023-06130-4

## Methodology

- **Normalization**: Per-cell library size to 10,000, then log1p
- **Feature Scaling**: Scanpy scale(zero_center=False, max_value=10)
- **Clustering**: Leiden algorithm with seeds [0, 17, 42, 73, 101]
- **Baselines**: HVG and 19 random size-matched gene controls

## Important Notes

- Cell-level metrics are descriptive only; cells are nested within patients/samples
- No discrete metabolic states are claimed; all conclusions are descriptive
- Patient/sample confounders are explicitly reported
- Random control comparisons are descriptive, not statistical significance tests
