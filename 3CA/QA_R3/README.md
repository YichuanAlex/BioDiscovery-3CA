# QA_R3: Metabolic State Analysis of 3CA Study 3ca:20773

## Overview

This workspace contains the analysis of single-cell RNA-seq data from the Choudhury et al. 2022 meningioma study (3CA study ID: 3ca:20773) using a user-supplied set of 1,988 metabolic genes. The analysis addresses three research questions:

1. **Global metabolic grouping**: Do all cells form reproducible transcriptional metabolic clusters when analyzed using only the supplied metabolic genes?
2. **Cell-type association**: How do these metabolic clusters relate to known cell types and subtypes?
3. **Within-cell-type states**: Within CD8 T cells specifically, are there distinct metabolic states?

## Data Sources

### 3CA Study (3ca:20773)
- **Title**: Meningioma DNA methylation groups identify biological drivers and therapeutic vulnerabilities
- **Journal**: Nature Genetics, 2022
- **DOI**: 10.1038/s41588-022-01061-8
- **Category**: Brain (Meningioma)
- **Technology**: 10x Genomics
- **Samples**: 10
- **Total cells**: 58,843

**Verification**: Crossref metadata verified via `verify_doi(3ca:20773)`
- Citation URL: https://www.nature.com/articles/s41588-022-01061-8
- Crossref source: https://api.crossref.org/v1/works/10.1038/s41588-022-01061-8

### User-Supplied Metabolic Genes
- **File**: `inputs/metabolic_genes_total.csv`
- **SHA-256**: 7503180d29693bd1e654ea93281db0e3ec4177ff44842c8b02f6a098402e41a9
- **Source rows**: 1,988
- **Matched to expression symbols**: 1,646 (after prevalence filtering)
- **Unmatched symbols**: 190

### Expression Matrix
- **File**: `inputs/Exp_data_UMIcounts.mtx`
- **SHA-256**: 51bf0452d166511fecca3f32d89f9fd0f631d173143173d143173d82115f49cdaaa6c1d
- **Dimensions**: 33,538 genes × 58,843 cells
- **Matrix orientation**: genes_by_cells

## Analysis Results

### Question 1: Global Metabolic Grouping (All Cells)

**Analysis scope**: 58,843 cells across all cell types

| Metric | Value |
|--------|-------|
| Metabolic genes analyzed | 1,646 |
| Number of clusters | 17 |
| Selected resolution | 0.8 |
| Silhouette (median) | 0.222 |
| Mean pairwise ARI | 0.965 |
| Mean pairwise NMI | 0.968 |

**Cluster size range**: 714 – 8,806 cells

**Random control comparison** (19 size-matched controls):
- Metabolic matched-KMeans silhouette: 0.220
- Random controls exceeding or equal: 2 of 19
- Add-one rank fraction: 0.15 (descriptive only, not a P value)

**HVG control comparison**:
- HVG silhouette: 0.283
- Random controls (min-max): 0.20 – 0.22

**Confounder NMI values**:
- Patient: 0.518
- Sample: 0.548
- Cell type: 0.496
- Cell subtype: 0.648

**Conclusion**: The analysis is **inconclusive** regarding discrete metabolic states. While 17 clusters were identified at resolution 0.8, the high NMI values for patient (0.518), sample (0.548), and cell subtype (0.648) indicate that cluster assignment is substantially confounded by these factors. The random control comparison shows only 2 of 19 controls exceeded the metabolic clustering silhouette, but this is a descriptive benchmark, not statistical significance.

**Key figures**:
- `figures/metabolic_umap.pdf`: UMAP embedding of all cells colored by metabolic cluster
- `figures/clustering_diagnostics.pdf`: Clustering quality metrics and stability analysis

---

### Question 2: Cell-Type Association

**Global cell-type association**: The NMI between metabolic clusters and cell type is 0.496 (global), with within-replicate NMI ranging from 0.379 to 0.745 (median: 0.592). This indicates moderate association between metabolic clusters and cell type, but the clusters are not perfectly aligned with cell types.

**Cell-subtype association**: The NMI between metabolic clusters and cell subtype is 0.648 (global), with within-replicate NMI ranging from 0.224 to 0.680 (median: 0.636). This indicates stronger association with cell subtype than with broad cell type.

**Replicate sensitivity**: Across 6 patients (biological replicates), the global-vs-within-replicate ARI ranges from 0.071 to 0.676, with patient 3 being the weakest replicate (3,287 cells). This variability suggests that metabolic clustering is not consistently reproducible within individual patients.

**Conclusion**: Metabolic clusters show moderate-to-strong association with cell subtype (NMI = 0.648) but weaker association with broad cell type (NMI = 0.496). The substantial confounding by patient (NMI = 0.518) and sample (NMI = 0.548) indicates that metabolic clustering is heavily influenced by batch effects and patient-specific factors rather than reflecting universal metabolic states.

---

### Question 3: Within CD8 T Cells

**Analysis scope**: 3,624 CD8 T cells (subset by `cell_subtype = "CD8 T cells"`)

| Metric | Value |
|--------|-------|
| Metabolic genes analyzed | 1,318 |
| Number of clusters | 6 |
| Selected resolution | 0.4 |
| Silhouette (median) | 0.117 |
| Mean pairwise ARI | 0.759 |
| Mean pairwise NMI | 0.750 |

**Cluster size range**: 55 – 2,002 cells

**Random control comparison** (19 size-matched controls):
- Metabolic matched-KMeans silhouette: 0.095
- Random controls exceeding or equal: 17 of 19
- Add-one rank fraction: 0.9 (descriptive only, not a P value)

**HVG control comparison**:
- HVG silhouette: 0.168
- Random controls (min-max): 0.092 – 0.131

**Confounder NMI values**:
- Patient: 0.393
- Sample: 0.443
- Source: 0.347
- Cell cycle phase: 0.274

**Within-replicate sensitivity**: Across 3 patients, the global-vs-within-replicate ARI ranges from 0.511 to 0.845, with patient 6 being the weakest replicate (2,776 cells).

**Conclusion**: The analysis is **inconclusive** regarding discrete metabolic states within CD8 T cells. While 6 clusters were identified at resolution 0.4, the random control comparison shows 17 of 19 controls exceeded the metabolic clustering silhouette, indicating that the observed clustering is not significantly better than random. The low silhouette value (0.117) and high random control exceedance suggest that metabolic clustering within CD8 T cells is not robustly supported by the data.

**Key figures**:
- `figures/cd8_analysis/metabolic_umap.pdf`: UMAP embedding of CD8 T cells colored by metabolic cluster
- `figures/cd8_analysis/clustering_diagnostics.pdf`: Clustering quality metrics and stability analysis

---

## Normalization Method

The analysis used the following normalization pipeline:

```
1. Per-cell library size normalization to 10,000 UMI counts
2. Log1p transformation: log1p(x) = log(x + 1)
3. Feature scaling: zero_center=False, max_value=10
```

**Formula**: 
```
normalized_expression = log1p(UMI_count / total_UMIs_in_cell * 10000)
```

where:
- `UMI_count` = raw UMI count for a gene in a cell
- `total_UMIs_in_cell` = sum of all UMI counts in the cell
- `log1p(x)` = natural logarithm of (x + 1)

---

## Limitations

1. **Descriptive only**: All clustering metrics (silhouette, ARI, NMI) are descriptive statistics computed on a fixed random subset of cells. They do not constitute statistical significance tests.

2. **No independent validation**: Clusters were derived from the same data used for evaluation. Within-replicate reclustering is descriptive, not held-out donor validation.

3. **Random controls are size-matched only**: Random gene controls were matched in size to the metabolic gene set, not in expression mean or dispersion. Their exceedance fraction is a descriptive benchmark, not a biological P value.

4. **Confounder NMI thresholds do not prove independence**: An NMI threshold (e.g., ≥0.5) does not establish that clusters are independent of confounders. Independent validation, QC/batch sensitivity analysis, and continuum-versus-discrete comparison are required.

5. **Symbol-level aggregation**: Identical source gene symbols were summed before QC/normalization. This preserves library counts but does not disambiguate stable gene IDs or distinct loci.

6. **Resolution selection on same data**: Resolution was selected using the same dataset. ARI/NMI assess Leiden randomization conditional on the fixed PCA/neighbor graph, not all preprocessing uncertainty.

---

## Required Artifacts

| File | Description |
|------|-------------|
| `report/main.tex` | LaTeX report with figures, tables, and prose |
| `report/main.pdf` | Compiled PDF report |
| `results/summary.json` | Global analysis summary |
| `results/analysis_manifest.json` | Analysis manifest with schema version 1 |
| `results/core_analysis/core_result.json` | Global core analysis results |
| `results/cd8_analysis/core_result.json` | CD8 T cell subset core analysis |
| `results/cd8_analysis/summary.json` | CD8 T cell subset summary |
| `README.md` | This file |

---

## Key References

1. **Choudhury et al. 2022**. *Meningioma DNA methylation groups identify biological drivers and therapeutic vulnerabilities*. Nature Genetics. DOI: 10.1038/s41588-022-01061-8. Verified via Crossref.

2. **Co-Scientist framework**: The analysis follows the Co-Scientist framework for evidence-grounded single-cell research, with bounded reflection phases and deterministic validation gates.

---

## Verification Call ID

The final validation call ID (to be obtained after `build_research_report` and `validate_research_bundle`) should be cited in the completion step.
