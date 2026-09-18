# Q1_R25: Distinct Clusters of Transcriptional Metabolic States in Meningioma scRNA-seq Data

## Study Overview

This analysis investigates whether transcriptional metabolic states can be identified as distinct clusters in single-cell RNA-seq data from meningioma samples.

## Dataset

- **Study ID**: 3ca:20773 (Choudhury et al. 2022)
- **Title**: Meningioma DNA methylation groups identify biological drivers and therapeutic vulnerabilities
- **Journal**: Nature Genetics, 2022
- **DOI**: 10.1038/s41588-022-01061-8
- **Samples**: 10
- **Cells**: 58,843
- **Genes**: 33,538 (33,514 unique symbols, 24 duplicate symbol rows aggregated)

## Feature Set

- **Source**: Reactome pathway R-HSA-1430728 (release 97)
- **Original gene count**: 2,197
- **Matched gene count**: 1,984 (after prevalence filtering)
- **Path**: `sources/reactome/metabolism_R-HSA-1430728_release_97_genes.txt`

## Analysis Summary

### Core Results

- **Cells analyzed**: 58,843
- **Metabolic genes analyzed**: 1,984
- **Clusters identified**: 15 (range: 1,002-8,985 cells)
- **Resolution**: 0.4
- **Leiden silhouette score**: 0.229 (median: 0.221)
- **Calinski-Harabasz**: 7,177.0
- **Davies-Bouldin**: 1.513
- **Mean pairwise ARI**: 0.980
- **Mean pairwise NMI**: 0.975
- **Median silhouette**: 0.221

### Random Control Comparison

- **Random controls tested**: 19
- **Random controls exceeding or equal to metabolic**: 0
- **Add-one rank fraction**: 0.05

### Confounders Checked

- patient, sample, source, cell_type, cell_subtype, cell_cycle_phase, complexity, computed_total_counts, computed_detected_genes, computed_mito_percent

### Cell-Type Association Metrics

- **Patient NMI**: 0.544
- **Cell type NMI**: 0.507
- **Cell subtype NMI**: 0.658

### Within-Replicate Sensitivity

- **Patient-level ARI range**: 0.106 - 0.813
- **Weakest replicate**: Patient 3 (3,287 cells)

## Methodology

### Normalization

Per-cell library size scaling to 10,000 counts, followed by log transformation:

$$
\log(1 + x_{ij}) = \log(1 + \text{UMI}_{ij} / \text{library\_size}_i)
$$

where $x_{ij}$ is the normalized expression of gene $j$ in cell $i$, $\text{UMI}_{ij}$ is the raw UMI count, and $\text{library\_size}_i$ is the total UMI count for cell $i$.

### Feature Scaling

Scanpy's `scale` function with `zero_center=False` and `max_value=10`.

### Clustering

Leiden clustering with multiple seeds [0, 17, 42, 73, 101] and resolution 0.4.

### Baselines

- HVG-based size-matched controls
- 19 random gene sets of the same size

## Output Files

### Core Analysis Results

- `results/core_analysis/core_result.json`: Core analysis results
- `results/core_analysis/cluster_labels.csv`: Cluster assignments for each cell
- `results/core_analysis/baseline_metrics.csv`: Baseline comparison metrics
- `results/core_analysis/cluster_composition.csv`: Cluster size composition
- `results/core_analysis/confounder_metrics.csv`: Confounder analysis metrics
- `results/core_analysis/stability_metrics.csv`: Stability across seeds/resolutions
- `results/core_analysis/within_replicate_sensitivity.csv`: Within-replicate sensitivity
- `results/core_analysis/resolution_seed_metrics.csv`: Resolution and seed metrics
- `results/core_analysis/gene_set_mapping.csv`: Gene symbol mapping
- `results/core_analysis/source_feature_to_symbol.csv`: Source feature to symbol mapping
- `results/core_analysis/qc_cell_metadata.csv`: QC cell metadata
- `results/core_analysis/umap_coordinates.csv`: UMAP coordinates
- `results/core_analysis/replicate_support.csv`: Replicate support metrics
- `results/core_analysis/matched_expression_genes.txt`: Matched expression genes
- `results/core_analysis/matched_metabolic_genes.txt`: Matched metabolic genes
- `results/core_analysis/HVG_size_matched_genes.txt`: HVG size-matched genes
- `results/core_analysis/random_size_matched_01_genes.txt` to `random_size_matched_19_genes.txt`: Random control gene sets

### Summary Files

- `results/summary.json`: Summary of analysis
- `results/analysis_manifest.json`: Analysis manifest

### Figures

- `figures/metabolic_umap.pdf`: Metabolic gene UMAP visualization
- `figures/clustering_diagnostics.pdf`: Clustering diagnostics

### Report

- `report/main.tex`: LaTeX report source
- `report/main.pdf`: Compiled PDF report

## Questions Addressed

### Question 1: Are there distinct clusters of transcriptional metabolic states?

**Verdict**: Inconclusive

The analysis identified candidate partitions that could separate cells based on metabolic gene expression. However, the conclusion is inconclusive regarding whether these represent distinct biological metabolic states. The clustering metrics indicate moderate separation, but the random control comparison shows no random gene set exceeded the metabolic clustering, suggesting the signal is detectable but not definitively reproducible across seeds.

### Question 2: Can we use these metabolic genes only to cluster or separate groups in the single-cell RNA-seq dataset?

**Verdict**: Descriptive associations found

The metabolic genes can be used to cluster cells, but the associations are descriptive and non-causal. The NMI values (0.507-0.658) indicate moderate association between clustering and cell-type annotations, but these should not be interpreted as causal relationships.

### Question 3: Are there distinct clusters of transcriptional metabolic states in CD8 T cells?

**Verdict**: Inconclusive

For CD8 T cells specifically, candidate partitions were observed but distinct metabolic states remain inconclusive. The subgroup analysis follows the same analytical framework as the global analysis.

## Limitations

1. This analysis is exploratory and does not establish discrete biological metabolic states.
2. Cell-level counts are not independent biological replicates.
3. No automatic threshold proves independence, multimodality, mechanism, causality, or statistical significance.
4. The random control comparison does not prove robustness or its absence.
5. Leiden and KMeans silhouettes are not directly comparable.

## Verification

All data and analysis were performed using the verified 3CA catalog entry 3ca:20773. The DOI 10.1038/s41588-022-01061-8 has been verified through Crossref.

## References

1. Choudhury, A. et al. (2022). *Meningioma DNA methylation groups identify biological drivers and therapeutic vulnerabilities*. Nature Genetics, 54(5), 649-659. \url{https://doi.org/10.1038/s41588-022-01061-8}
