# Q1_R30: Transcriptional Metabolic States in Meningioma Brain Single-Cell Data

## Study Information

- **3CA Study ID**: 3ca:20773
- **Title**: Choudhury et al. 2022 - Meningioma DNA methylation groups identify biological drivers and therapeutic vulnerabilities
- **Journal**: Nature Genetics, Volume 54, Issue 5, Pages 649-659, 2022
- **DOI**: 10.1038/s41588-022-01061-8

## Dataset

- **Total cells**: 58,843
- **Total genes**: 33,538 (33,514 unique symbols, 24 duplicate symbol rows aggregated)
- **Samples**: 10
- **Technology**: 10x Genomics

## Analysis

### Feature Set
- **Source**: Reactome pathway R-HSA-1430728 (release 97)
- **Original gene count**: 2,197
- **Matched gene count (after prevalence)**: 1,984
- **Genes path**: `sources/reactome/metabolism_R-HSA-1430728_release_97_genes.txt`

### Methods
- **Normalization**: Per-cell library size scaling to 10,000, then log1p transformation
- **Feature scaling**: Scanpy scale(zero_center=False, max_value=10)
- **Clustering**: Leiden clustering with seeds [0, 17, 42, 73, 101]
- **Resolution**: 0.4 (selected to maximize median silhouette among candidates passing mean pairwise ARI stability filter)

### Confounders Checked
- patient, sample, source, cell_type, cell_subtype, cell_cycle_phase, complexity, computed_total_counts, computed_detected_genes, computed_mito_percent

## Results Summary

### Core Analysis
- **Number of clusters**: 15 (ranging from 1,002 to 8,985 cells)
- **Leiden silhouette score**: 0.229
- **Calinski-Harabasz index**: 7,177.0
- **Davies-Bouldin index**: 1.513
- **Mean pairwise ARI**: 0.980
- **Min pairwise ARI**: 0.973
- **Median silhouette**: 0.221

### Random Control Comparison
- **Random controls exceeding or equal to metabolic**: 0 of 19
- **Add-one rank fraction**: 0.05 (descriptive, not an inferential p-value)

### Cell Type Associations
- **Patient within-replicate ARI range**: 0.106 - 0.813
- **Weakest patient**: 3 (3,287 cells)
- **Patient NMI**: 0.544
- **Cell type NMI**: 0.507
- **Cell subtype NMI**: 0.658

### Conclusion
The analysis is **inconclusive** regarding whether distinct biological metabolic states exist. While candidate partitions were observed, the presence of clusters does not prove distinct biological metabolic states.

## Output Files

- `report/main.tex` - LaTeX report
- `report/main.pdf` - Compiled PDF report
- `results/core_analysis/core_result.json` - Core analysis results
- `results/summary.json` - Summary of analysis
- `results/analysis_manifest.json` - Analysis manifest with schema version 1
- `figures/metabolic_umap.pdf` - UMAP embedding figure
- `figures/clustering_diagnostics.pdf` - Clustering diagnostics figure

## Verification

The DOI `3ca:20773` has been verified through Crossref REST API.

## References

1. Choudhury, A., Magill, S. T., Eaton, C. D., et al. (2022). Meningioma DNA methylation groups identify biological drivers and therapeutic vulnerabilities. *Nature Genetics*, 54(5), 649-659. https://doi.org/10.1038/s41588-022-01061-8
