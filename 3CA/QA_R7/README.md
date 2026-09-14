# QA_R7: Metabolic Gene Clustering Analysis

## Overview

This repository contains the analysis of metabolic gene clustering on the 3CA study 3ca:20773 (Choudhury et al. 2022), using user-supplied metabolic genes from `inputs/metabolic_genes_total.csv`.

## Dataset

- **Study ID**: 3ca:20773
- **Title**: Meningioma DNA methylation groups identify biological drivers and therapeutic vulnerabilities
- **DOI**: 10.1038/s41588-022-01061-8
- **Source**: 3CA Curated Cancer Cell Atlas
- **Cells**: 58,843
- **Genes**: 33,538 (original), 1,646 matched metabolic genes

## Analysis Summary

### Question 1: Reproducible metabolic groupings across all cells?

**Verdict: inconclusive**

Using 1,646 matched metabolic genes on 58,843 cells at resolution 0.8, Leiden clustering produced 17 clusters (714-8,806 cells). The silhouette score (0.217) is comparable to random controls (2/19 exceeded, add-one rank: 0.15) and lower than HVG-based clustering (0.283).

### Question 2: Relationship to cell type and cell subtype?

**Verdict: descriptive**

The clustering shows moderate association with cell type (NMI = 0.496) and stronger association with cell subtype (NMI = 0.648). These associations are consistent with clusters being driven by cell identity rather than independent metabolic states.

### Question 3: Within CD8 T cells, are there distinct metabolic groupings?

**Verdict: inconclusive**

For 3,624 CD8 T cells at resolution 0.4, Leiden clustering produced 6 clusters (55-2,002 cells). The silhouette score (0.099) is very low and comparable to random controls (17/19 exceeded, add-one rank: 0.9).

## Deliverables

- `report/main.tex` - LaTeX report
- `report/main.pdf` - Rendered PDF report
- `results/summary.json` - Global analysis summary
- `results/analysis_manifest.json` - Analysis manifest with hashes and references
- `results/core_analysis/core_result.json` - Global core analysis results
- `results/cd8_analysis/core_result.json` - CD8 T cell subset analysis results
- `results/cd8_analysis/summary.json` - CD8 T cell subset summary

## References

1. Choudhury et al. *Meningioma DNA methylation groups identify biological drivers and therapeutic vulnerabilities*. Nature Genetics 54, 649-659 (2022). \doi{10.1038/s41588-022-01061-8}
2. Gavish et al. *Hallmarks of transcriptional intratumour heterogeneity across a thousand tumours*. Nature 618, 598-606 (2023). \doi{10.1038/s41586-023-06130-4}
