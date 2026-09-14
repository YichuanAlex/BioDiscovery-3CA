# QA_R6: Metabolic State Analysis of Meningioma Single-Cell Data

## Overview

This repository contains the analysis of single-cell RNA-seq data from the Choudhury et al. 2022 meningioma study (3CA:20773) using a user-supplied set of metabolic genes to investigate transcriptional metabolic states.

## Data Source

- **Study ID**: 3ca:20773
- **Title**: Meningioma DNA methylation groups identify biological drivers and therapeutic vulnerabilities
- **Journal**: Nature Genetics
- **DOI**: 10.1038/s41588-022-01061-8
- **3CA Category**: Brain (Meningioma)
- **Technology**: 10x Genomics
- **Samples**: 10
- **Total Cells**: 58,843

## Analysis Deliverables

### Core Analysis Results

- **Global Analysis** (`results/core_analysis/`):
  - Cells analyzed: 58,843
  - Metabolic genes used: 1,646
  - Resolution: 0.8
  - Clusters: 17 (714-8,806 cells)
  - Leiden silhouette: 0.217
  - Matched-k KMeans: 0.220
  - Random controls >= metabolic: 2/19
  - Add-one rank fraction: 0.15
  - Patient NMI: 0.518
  - Cell type NMI: 0.496
  - Cell subtype NMI: 0.648
  - Conclusion: inconclusive

- **CD8 T Cell Subset Analysis** (`results/cd8_analysis/`):
  - Cells analyzed: 3,624
  - Metabolic genes used: 1,318
  - Resolution: 0.4
  - Clusters: 6 (55-2,002 cells)
  - Leiden silhouette: 0.099
  - Matched-k KMeans: 0.095
  - Random controls >= metabolic: 17/19
  - Add-one rank fraction: 0.9
  - Patient NMI: 0.393
  - Conclusion: inconclusive

### Reports and Manifests

- **Main Report**: `report/main.tex` and `report/main.pdf`
- **Analysis Manifest**: `results/analysis_manifest.json`
- **Summary**: `results/summary.json`

## Key Findings

### Question 1: Reproducible Metabolic Grouping

Using the user-supplied metabolic genes across all cells, the analysis did not identify reproducible transcriptional metabolic states. The clustering results show:

- Only 2 out of 19 random gene sets performed as well as or better than the metabolic gene set (add-one rank fraction: 0.15)
- The conclusion is marked as **inconclusive** due to the descriptive nature of the metrics and the presence of confounding factors

### Question 2: Relationship to Cell Types and Subtypes

The clustering shows moderate association with cell type and subtype annotations:

- **Cell type NMI**: 0.496
- **Cell subtype NMI**: 0.648
- **Patient NMI**: 0.518

These values suggest that the observed clustering is partially driven by cell type and subtype annotations rather than representing independent metabolic states.

### Question 3: CD8 T Cell Subset Analysis

Within the CD8 T cell subset specifically:

- Cells analyzed: 3,624
- Clusters: 6 (resolution 0.4)
- Patient NMI: 0.393
- Conclusion: **inconclusive**

The analysis within this specific cell type also does not provide evidence for discrete metabolic states.

## References

1. Choudhury A, Magill ST, Eaton CD, et al. Meningioma DNA methylation groups identify biological drivers and therapeutic vulnerabilities. *Nature Genetics*. 2022;54(5):649-659. DOI: 10.1038/s41588-022-01061-8

2. Gavish A, Tyler M, Greenwald AC, et al. Hallmarks of transcriptional intratumour heterogeneity across a thousand tumours. *Nature*. 2023;618(7965):598-606. DOI: 10.1038/s41586-023-06130-4

## Methodology

The analysis used the `analyze_metabolic_states` tool with:
- User-supplied metabolic genes from `inputs/metabolic_genes_total.csv`
- Scanpy Leiden clustering on the metabolic gene subset
- Matched-k KMeans controls for comparison
- Random gene set controls (19 total)
- Confounder analysis for patient, cell type, and cell subtype

## Limitations

1. Cell-level metrics (NMI, ARI, silhouette) are descriptive and do not constitute statistical significance testing
2. The presence of confounding factors (cell type, patient, sample) limits interpretation of metabolic states
3. The inconclusive verdict reflects the evidence boundary, not the absence of biological signal
4. No causal claims or mechanistic interpretations are made

## Validation

The research bundle has been validated through:
- Crossref verification of cited DOIs
- LaTeX compilation and PDF rendering
- Bundle validation via `validate_research_bundle`
