# Q1_R26: Metabolic State Clustering Analysis

## Study Overview

This analysis investigates whether transcriptional metabolic states can be used to cluster or separate groups in the single-cell RNA-seq dataset from the Choudhury et al. 2022 study (3CA:20773).

## Data Source

- **Study ID**: 3ca:20773
- **Title**: Meningioma DNA methylation groups identify biological drivers and therapeutic vulnerabilities
- **Journal**: Nature Genetics, Volume 54, Issue 5, Pages 649-659, Published 2022
- **DOI**: 10.1038/s41588-022-01061-8
- **3CA Category**: Brain (Meningioma)
- **Technology**: 10x Genomics

## Analysis Summary

### Dataset Information

| Metric | Value |
|--------|-------|
| Cells analyzed | 58,843 |
| Total genes | 33,538 |
| Unique gene symbols | 33,514 |
| Duplicate symbol rows (summed) | 24 |
| Metabolic genes (Reactome R-HSA-1430728) | 2,197 |
| Matched metabolic genes (after prevalence filter) | 1,984 |

### Analysis Methods

1. **Normalization**: Per-cell library size to 10,000, then log1p
2. **Feature Scaling**: Scanpy scale(zero_center=False, max_value=10)
3. **Clustering**: Leiden algorithm with resolution selection
4. **Random Controls**: 19 size-matched KMeans baselines
5. **HVG Control**: Highest variance genes among prevalence-passing non-mitochondrial symbols

### Clustering Results

- **Selected Resolution**: 0.4
- **Number of Clusters**: 15
- **Cluster Size Range**: 1,002 - 8,985 cells
- **Leiden Silhouette**: 0.229
- **Calinski-Harabasz**: 7,177
- **Davies-Bouldin**: 1.513

### Confounders Checked

The analysis checked for confounding effects from:
- Patient (NMI: 0.544)
- Sample (NMI: 0.567)
- Source (NMI: 0.197)
- Cell type (NMI: 0.507)
- Cell subtype (NMI: 0.658)
- Cell cycle phase (NMI: 0.195)

### Random Control Comparison

- **Random controls exceeding or equal to metabolic**: 0 of 19
- **Add-one rank fraction**: 0.05
- **HVG silhouette**: 0.295
- **Random control mean silhouette**: 0.221

## Key Findings

### Question 1: Are there distinct clusters of transcriptional metabolic states?

**Verdict**: Inconclusive

The analysis shows that metabolic genes can form clusters (15 clusters observed), but the conclusion is inconclusive regarding whether these represent distinct biological metabolic states. The clustering is highly stable across seeds (mean pairwise ARI: 0.980), suggesting the clusters are reproducible. However, the categorical NMI for cell type (0.507) and cell subtype (0.658) indicates that cell-type associations are present, which may confound the interpretation of metabolic states.

### Question 2: Can we use metabolic genes only to cluster or separate groups?

**Verdict**: Descriptive clustering observed, but biological interpretation limited

The metabolic genes alone can produce clusters with reasonable silhouette score (0.229), comparable to HVG-based clustering (0.295). However, the presence of cell-type associations (NMI: 0.507 for cell type, 0.658 for cell subtype) suggests that the clusters may reflect cell-type composition rather than distinct metabolic states.

### Question 3: Within-cell-type metabolic states?

**Verdict**: Not analyzed separately

The global analysis was performed on all cells. Within-cell-type analysis would require a separate call to `analyze_metabolic_states` with the appropriate subset parameters.

## Limitations

1. **Cell-level tests do not create biological replicates**: The analysis is at the cell level, not at the biological replicate level.
2. **No statistical significance testing**: The metrics are descriptive, not inferential.
3. **Cell-type associations present**: The presence of cell-type associations in the clustering suggests that the clusters may reflect cell-type composition rather than distinct metabolic states.
4. **No independent validation**: The analysis was performed on a single dataset without independent validation.

## Files

- `results/core_analysis/core_result.json`: Core analysis results
- `results/summary.json`: Summary of analysis
- `results/analysis_manifest.json`: Analysis manifest with all metadata
- `report/main.tex`: LaTeX report
- `report/main.pdf`: Compiled PDF report
- `README.md`: This file

## References

1. Choudhury A, Magill ST, Eaton CD, et al. "Meningioma DNA methylation groups identify biological drivers and therapeutic vulnerabilities." Nature Genetics 54.5 (2022): 649-659. DOI: 10.1038/s41588-022-01061-8
