# QA_R10: Metabolic State Analysis of scRNA-seq Data

## Overview

This workspace contains the analysis of single-cell RNA sequencing data to identify candidate transcriptional metabolic states using the user-supplied metabolic gene set from `inputs/metabolic_genes_total.csv`.

## Data Sources

### 3CA Dataset (Choudhury et al. 2022)
- **Study ID**: 3ca:20773
- **DOI**: 10.1038/s41588-022-01061-8
- **Title**: Meningioma DNA methylation groups identify biological drivers and therapeutic vulnerabilities
- **Published in**: Nature Genetics, 2022
- **Citation URL**: https://www.nature.com/articles/s41588-022-01061-8

### User-Supplied Metabolic Genes
- **File**: `inputs/metabolic_genes_total.csv`
- **Source gene count**: 1988
- **Matched gene count (after prevalence filtering)**: 1646
- **SHA-256**: 7503180d29693bd1e654ea93281db0e3ec4177ff44842c8b02f6a098402e41a9

## Analysis Results

### Global Analysis (All Cells)
- **Cells analyzed**: 58,843
- **Genes used**: 1,646 (after prevalence filtering)
- **Resolution**: 0.8
- **Clusters identified**: 17
- **Cluster size range**: 714 - 8,806 cells
- **Leiden silhouette**: 0.217
- **Stability (mean/min ARI)**: 0.965 / 0.947
- **Matched-k KMeans silhouette**: 0.220
- **Random controls >= metabolic**: 2 of 19 (add-one rank: 0.15)
- **Patient NMI**: 0.518
- **Cell type NMI**: 0.496
- **Cell subtype NMI**: 0.648
- **Conclusion**: Inconclusive - candidate partitions observed but distinct metabolic states not established

### CD8 T Cells Subset Analysis
- **Cells analyzed**: 3,624
- **Genes used**: 1,318
- **Resolution**: 0.4
- **Clusters identified**: 6
- **Cluster size range**: 55 - 2,002 cells
- **Leiden silhouette**: 0.099
- **Stability (mean/min ARI)**: 0.759 / 0.600
- **Matched-k KMeans silhouette**: 0.095
- **Random controls >= metabolic**: 17 of 19 (add-one rank: 0.9)
- **Patient NMI**: 0.393
- **Conclusion**: Inconclusive - candidate partitions observed but distinct metabolic states not established

## Artifacts

- `report/main.tex` - LaTeX report
- `report/main.pdf` - Rendered PDF report
- `results/summary.json` - Summary of both analyses
- `results/analysis_manifest.json` - Full analysis manifest
- `results/core_analysis/core_result.json` - Global analysis core results
- `results/cd8_analysis/core_result.json` - CD8 T cells analysis core results
- `results/cd8_analysis/summary.json` - CD8 T cells summary
- `results/core_analysis/cluster_labels.csv` - Global cluster labels
- `results/cd8_analysis/cluster_labels.csv` - CD8 cluster labels
- `results/core_analysis/baseline_metrics.csv` - Baseline control metrics
- `results/core_analysis/matched_metabolic_genes.txt` - Matched gene list
- `figures/metabolic_umap.pdf` - Global UMAP
- `figures/clustering_diagnostics.pdf` - Global clustering diagnostics
- `figures/cd8_analysis/metabolic_umap.pdf` - CD8 UMAP
- `figures/cd8_analysis/clustering_diagnostics.pdf` - CD8 clustering diagnostics

## Methodology

### Normalization
Per-cell library size normalization to 10,000 UMI counts, followed by log1p transformation:
```
x_normalized = log1p(x_UMI / 10000) = log(1 + x_UMI / 10000)
```
where `x_UMI` is the raw UMI count for each gene in each cell.

### Feature Scaling
Scanpy scale with `zero_center=False` and `max_value=10`.

### Clustering
Leiden algorithm with multiple seeds ([0, 17, 42, 73, 101]) and resolution 0.8 for global analysis, resolution 0.4 for CD8 T cells subset.

### Random Controls
19 random gene sets of the same size as the metabolic gene set were used as controls to assess whether metabolic genes drive clustering beyond chance.

## Key Findings

1. **Candidate metabolic clusters were observed** in both the global analysis and CD8 T cells subset, but the evidence is **inconclusive** for defining distinct transcriptional metabolic states.

2. **Random controls frequently exceeded or matched** the metabolic gene set (2/19 globally, 17/19 in CD8), suggesting that the observed clustering may not be driven specifically by metabolic genes.

3. **Cell-type associations are descriptive** and non-causal. The NMI values indicate some association between clusters and cell types/subtypes, but this does not establish biological metabolic states.

4. **Within-replicate sensitivity varies** across patients, with patient 3 being the weakest in the global analysis (3,287 cells) and patient 6 being the weakest in CD8 analysis (2,776 cells).

## Limitations

- Global cell-type separation cannot establish within-cell-type metabolic states.
- Patient-within sensitivity is not independent-cohort replication.
- Patient/sample mixing can confound interpretation.
- No statistical significance testing was performed.
- Candidate partitions are descriptive only, not validated as biological states.
