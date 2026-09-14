# Q1_R17: Distinct Clusters of Transcriptional Metabolic States

## Overview
This repository contains the analysis of the Choudhury et al. 2022 meningioma dataset (3CA:20773) to investigate whether transcriptional metabolic states can be used to identify distinct clusters in single-cell RNA-seq data.

## Dataset
- **Study**: Choudhury et al. 2022 - Meningioma DNA methylation groups identify biological drivers and therapeutic vulnerabilities
- **3CA ID**: 3ca:20773
- **Samples**: 10
- **Cells**: 58,843
- **Genes**: 33,538
- **Technology**: 10x Genomics

## Analysis Summary
- **Metabolic Gene Set**: Reactome metabolism (R-HSA-1430728)
- **Matched Genes**: 1,984 of 2,197 Reactome genes
- **Clusters**: 17 (resolution 0.4)
- **Conclusion**: Inconclusive regarding discrete biological metabolic states

## Key Results
- **Cluster size range**: 152 - 9,017 cells
- **Silhouette coefficient**: 0.216
- **Mean pairwise ARI**: 0.955
- **Random controls exceeding metabolic clustering**: 0/19
- **Patient NMI**: 0.551
- **Within-replicate ARI range**: 0.148 - 0.795

## Files
- `report/main.tex` - LaTeX source document
- `report/main.pdf` - Compiled PDF report
- `results/summary.json` - Summary of analysis results
- `results/analysis_manifest.json` - Analysis manifest with schema version 1
- `README.md` - This file

## References
1. Choudhury et al. (2022). *Nature Genetics* 54(5):649-659. DOI: 10.1038/s41588-022-01061-8
