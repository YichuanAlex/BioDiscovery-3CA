# QA_R12: Metabolic State Clustering Analysis

## Summary

This repository contains the analysis of transcriptional metabolic states using single-cell RNA-seq data from the Choudhury et al. 2022 dataset (3ca:20773).

## Dataset

- **Source**: Choudhury et al. 2022, Nature Genetics
- **DOI**: 10.1038/s41588-022-01061-8
- **3CA ID**: 3ca:20773
- **Cells**: 58,843 (global), 3,624 (CD8 T cells subset)
- **Genes**: 33,538 total, 1,646 matched metabolic genes

## Analysis

### Global Analysis
- **Method**: Scanpy Leiden clustering on metabolic genes
- **Resolution**: 0.4
- **Clusters**: 13 (cluster sizes: 1,051-9,041 cells)
- **Silhouette score**: 0.218
- **Mean pairwise ARI**: 0.951
- **Random controls**: 5/19 exceeded or equal metabolic genes (add-one rank: 0.3)

### CD8 T Cell Subset Analysis
- **Method**: Scanpy Leiden clustering on metabolic genes
- **Resolution**: 0.4
- **Clusters**: 6 (cluster sizes: 55-1,872 cells)
- **Silhouette score**: 0.093
- **Mean pairwise ARI**: 0.736
- **Random controls**: 17/19 exceeded or equal metabolic genes (add-one rank: 0.9)

## Deliverables

- `report/main.tex` - LaTeX report
- `report/main.pdf` - Compiled PDF report
- `results/summary.json` - Analysis summary
- `results/analysis_manifest.json` - Analysis manifest
- `results/core_analysis/core_result.json` - Global core results
- `results/cd8_analysis/core_result.json` - CD8 T cell core results
- `results/cd8_analysis/summary.json` - CD8 T cell summary
- `README.md` - This file

## Questions Answered

1. **Are there distinct clusters of transcriptional metabolic states?**
   - Verdict: Candidate partitions observed, but distinct metabolic states inconclusive

2. **Can metabolic genes separate groups in the single-cell dataset?**
   - Verdict: Associations are descriptive and non-causal

3. **Can metabolic genes separate CD8 T cells?**
   - Verdict: Candidate partitions observed, but distinct metabolic states inconclusive

## Methodology

- **Normalization**: Per-cell library size to 10,000, then log1p
- **Feature scaling**: Scanpy scale(zero_center=False, max_value=10)
- **Clustering**: Leiden algorithm with resolution 0.4
- **Random seeds**: [0, 17, 42, 73, 101]
- **Random baselines**: 19 size-matched controls

## References

1. Choudhury A, Magill ST, Eaton CD, et al. Meningioma DNA methylation groups identify biological drivers and therapeutic vulnerabilities. Nature Genetics. 2022;54(5):649-659. DOI: 10.1038/s41588-022-01061-8

2. Wolf FA, Angerer P, Theis FJ. SCANPY: large-scale single-cell gene expression data analysis. Genome Biology. 2018;19(1):1-15. DOI: 10.1186/s13059-017-1382-0
