# QA_R11: Metabolic State Clustering Analysis

## Summary

This repository contains the analysis of whether transcriptional metabolic states can be identified as distinct clusters in single-cell RNA-seq data using only metabolic genes.

## Dataset

- **Study**: Choudhury et al. 2022 (3ca:20773)
- **Source**: https://www.nature.com/articles/s41588-022-01061-8
- **DOI**: 10.1038/s41588-022-01061-8
- **Data**: 58,843 cells, 33,538 genes (33,514 unique symbols after aggregation)

## Analysis

### Global Analysis (All Cells)

- **Cells analyzed**: 58,843
- **Metabolic genes**: 1,984 (from Reactome R-HSA-1430728, release 97)
- **Clusters identified**: 15 (Leiden, resolution=0.4)
- **Silhouette score**: 0.229
- **Mean pairwise ARI**: 0.980
- **Random control exceedance**: 0 of 19

### CD8 T Cell Subset Analysis

- **Cells analyzed**: 3,624
- **Metabolic genes**: 1,642
- **Clusters identified**: 6 (Leiden, resolution=0.4)
- **Silhouette score**: 0.155
- **Mean pairwise ARI**: 0.681
- **Random control exceedance**: 11 of 19

## Key Findings

1. **Computational clustering**: Metabolic genes can form computational clusters in both global and CD8 T cell subsets.

2. **Stability**: Cluster composition shows high stability (mean pairwise ARI = 0.980 for global, 0.681 for CD8).

3. **Random controls**: No random gene set exceeded the metabolic gene clustering performance in the global analysis (0 of 19).

4. **Confounders**: Cell subtype NMI = 0.658 indicates some association between metabolic clustering and cell subtype.

5. **Within-replicate sensitivity**: The weakest replicate (patient 3) had 3,287 cells with global vs within ARI = 0.106.

## Conclusion

The analysis is **inconclusive** regarding whether distinct biological metabolic states exist. While metabolic genes can form stable computational clusters, the clustering does not strongly separate cells into discrete metabolic states. The high stability of cluster composition suggests robust clustering, but the moderate silhouette scores and association with cell subtype indicate that metabolic genes alone do not define distinct biological metabolic states.

## Files

- `report/main.tex` - LaTeX report
- `report/main.pdf` - Rendered PDF report
- `results/summary.json` - Global analysis summary
- `results/analysis_manifest.json` - Complete analysis manifest
- `results/core_analysis/core_result.json` - Global core results
- `results/cd8_analysis/core_result.json` - CD8 T cell subset core results
- `results/cd8_analysis/summary.json` - CD8 T cell subset summary
- `README.md` - This file

## References

1. Choudhury A, Magill ST, Eaton CD, et al. Meningioma DNA methylation groups identify biological drivers and therapeutic vulnerabilities. Nature Genetics. 2022;54(5):649-659. \url{https://doi.org/10.1038/s41588-022-01061-8}

2. Wang AZ, Bowman-Kirigin JA, Desai R, et al. Single-cell profiling of human dura and meningioma reveals cellular meningeal landscape and insights into meningioma immune response. Genome Med. 2022;14(1):49. \url{https://doi.org/10.1186/s13073-022-01051-9}

## Methodology

- **Normalization**: Per-cell library size to 10,000, then log1p
- **Feature scaling**: Scanpy scale(zero_center=False, max_value=10)
- **Clustering**: Leiden algorithm with randomization
- **Random controls**: 19 size-matched random gene sets
- **Resolution selection**: Maximize median silhouette with mean pairwise ARI as tie-breaker
