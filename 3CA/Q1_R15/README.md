# Transcriptional Metabolic States in Meningioma Single-Cell RNA-seq Data

## Study Overview

This analysis investigates whether transcriptional metabolic states can be identified as distinct clusters in single-cell RNA-seq data from meningioma samples using only Reactome metabolism genes.

## Dataset

- **3CA Study ID**: 3ca:20773
- **Title**: Meningioma DNA methylation groups identify biological drivers and therapeutic vulnerabilities
- **Journal**: Nature Genetics, 54(5):649-659 (2022)
- **DOI**: 10.1038/s41588-022-01061-8
- **Cells**: 58,843
- **Genes**: 33,538 source features (33,514 unique symbols after aggregation)
- **Patients**: 6

## Methods

- **Metabolic Gene Set**: Reactome R-HSA-1430728 (release 97), 1,984 genes matched
- **Clustering**: Leiden algorithm with Scanpy
- **Resolutions tested**: 0.4, 0.8, 1.2
- **Controls**: HVG (highest variance) + 19 size-matched random gene sets
- **Random seeds**: [0, 17, 42, 73, 101]
- **Metrics**: Silhouette, Calinski-Harabasz, Davies-Bouldin, pairwise ARI/NMI

## Key Results

- **Clusters identified**: 17 at resolution 0.4
- **Metabolic silhouette**: 0.216
- **HVG control silhouette**: 0.288 (better than metabolic)
- **Random controls (mean)**: 0.221 (metabolic outperforms random)
- **Confounder NMI**: Patient=0.55, Sample=0.58, Cell subtype=0.65

## Conclusion

While metabolic genes can separate observed cell groups, evidence for discrete biological metabolic states is **inconclusive**. The HVG control outperformed metabolic clustering, and confounders showed substantial association with cluster labels.

## Artifacts

- `report/main.tex` - LaTeX source
- `report/main.pdf` - Compiled PDF
- `results/summary.json` - Analysis summary
- `results/analysis_manifest.json` - Evidence manifest
- `results/core_analysis/core_result.json` - Core analysis results
- `results/core_analysis/cluster_labels.csv` - Per-cell cluster assignments
- `figures/metabolic_umap.pdf` - UMAP visualization
- `figures/clustering_diagnostics.pdf` - Clustering diagnostics
