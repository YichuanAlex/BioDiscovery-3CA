# Metabolic Clustering Analysis of Lung Adenocarcinoma Single-Cell Data

## Overview

This repository contains the analysis of single-cell RNA-seq data from the Bischoff et al. (2021) study on lung adenocarcinoma, investigating whether transcriptional metabolic states form distinct clusters that can be used to partition the single-cell transcriptome.

## Research Question

**Are there distinct clusters of transcriptional metabolic states? Can we use metabolic genes only to cluster or separate groups in the single-cell RNA-seq dataset?**

## Data Source

- **Study**: Bischoff et al. (2021) - "Single-cell RNA sequencing reveals distinct tumor microenvironmental patterns in lung adenocarcinoma"
- **Journal**: Oncogene
- **DOI**: 10.1038/s41388-021-02054-3
- **3CA ID**: 3ca:20764
- **3CA URL**: https://www.weizmann.ac.il/sites/3CA
- **Article URL**: https://www.nature.com/articles/s41388-021-02054-3

## Dataset Summary

| Feature | Value |
|---------|-------|
| Total cells | 120,961 |
| Total genes | 33,514 |
| Samples | 12 patients (10 normal, 10 tumor) |
| Cell types | 14 major types |
| Metabolic program categories | 126 |

## Key Findings

### 1. Clustering Performance

| Clustering Method | Optimal k | Silhouette Score |
|-------------------|-----------|------------------|
| All genes | 5 | 0.694 |
| MP scores only | 20 | 0.555 |

**Conclusion**: Metabolic states do not form the primary organizing structure of the single-cell transcriptome. The silhouette score for all-gene clustering (0.694) is substantially higher than for MP-score clustering (0.555).

### 2. Metabolic Program Distribution

The 126 MP categories show a highly skewed distribution:
- **None (unassigned)**: 91,584 cells (75.7%)
- **Lipid-associated**: 3,283 cells (2.7%)
- **MES/Glycolysis**: 2,352 cells (1.9%)
- **Stress/HSP**: 1,494 cells (1.2%)

### 3. Correlation Analysis

| Feature | Correlation |
|---------|-------------|
| MP scores vs Cell complexity | r = 0.074 |
| MP scores vs UMAP1 | r = 0.125 |
| MP scores vs UMAP2 | r = -0.016 |

**Conclusion**: Metabolic program activity is weakly associated with cell complexity and UMAP embeddings, suggesting it is not simply a function of cell complexity.

## Files

### Report Files
- `report/main.tex` - LaTeX source code (arXiv template)
- `report/main.pdf` - Compiled PDF report

### Data Files
- `data/Exp_data_UMIcounts.mtx` - Expression matrix (33,514 genes × 120,961 cells)
- `data/genes.txt` - Gene list (33,514 genes)
- `data/Cells.csv` - Cell metadata
- `data/MP_scores_Bischoff2021_Lung.csv.gz` - Metabolic program scores
- `data/clustered_cells_all_genes.csv` - Cells clustered by all genes
- `data/clustered_cells_mp_scores.csv` - Cells clustered by MP scores

### Plot Files
- `plots/pca_all_genes.png` - PCA plot colored by all-gene clusters
- `plots/mp_score_by_cluster.png` - MP score distribution by cluster
- `plots/mp_vs_complexity.png` - MP score vs cell complexity
- `plots/mp_by_cell_type.png` - MP scores by cell type

### Results
- `results/summary.json` - Analysis summary with all computed statistics

## Reproducibility

### Data Download (via 3CA)

The data was downloaded from the 3CA cache with the following verification information:

| File | SHA-256 | Downloaded At |
|------|---------|---------------|
| Exp_data_UMIcounts.mtx | 0d4d42f158aaeac7f594ed3b8010d27b3a7b46899edc3925d113f625bc6387b3 | 2026-09-12 10:48:20 UTC |
| MP_scores_Bischoff2021_Lung.csv.gz | 2322b59ad15e743c4b195cbe63fbb586c9c3d832b4bafd6340349d7626666938 | 2026-09-13 02:21:59 UTC |

### Analysis Code

The analysis was performed using Python with the following libraries:
- pandas
- scipy
- scikit-learn
- matplotlib
- seaborn

### Key Analysis Steps

1. **Data Loading**: Load expression matrix, gene list, cell metadata, and MP scores
2. **Clustering**: K-means clustering with Ward linkage for both all-genes and MP scores
3. **Silhouette Score**: Evaluate cluster quality for k ∈ {5, 10, 15, 20, 25}
4. **Correlation Analysis**: Compute correlations between MP scores and other features
5. **Visualization**: Generate PCA plots, MP score distributions, and correlation plots

## Limitations

1. **Sample Size**: The clustering analysis used a sample of 500 cells due to computational constraints. The full dataset (120,961 cells) would require more sophisticated computational resources.

2. **Clustering Method**: Only K-means clustering was explored. Hierarchical clustering or other methods may yield different results.

3. **Feature Selection**: Only MP scores were used for the second clustering approach. Other metabolic gene sets could be explored.

## Conclusion

While metabolic programs represent biologically meaningful states in lung adenocarcinoma, they do not form distinct clusters that can be used to partition the single-cell transcriptome. The primary organizational structure of the data is captured by all genes, with metabolic states representing a subset of the transcriptional variation. Future studies should explore how metabolic programs relate to functional cell states and disease progression.

## References

1. Bischoff, P., Trinks, A., Obermayer, B., Pett, J. P., Wiederspahn, J., Uhlitz, F., Liang, X., Lehmann, A., Jurk, P., et al. (2021). Single-cell RNA sequencing reveals distinct tumor microenvironmental patterns in lung adenocarcinoma. *Oncogene*, 40(34), 2013-2027. https://doi.org/10.1038/s41388-021-02054-3

2. 3CA Curated Cancer Cell Atlas. Bischoff et al. 2021. https://www.weizmann.ac.il/sites/3CA
