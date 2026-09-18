# Q1_R29: Metabolic State Clustering Analysis

## Study Overview

This analysis investigates whether transcriptional metabolic states can form distinct clusters in the Choudhury et al. 2022 single-cell RNA-seq dataset (3CA:20773).

## Dataset Information

- **Study**: Choudhury et al. 2022 - "Meningioma DNA methylation groups identify biological drivers and therapeutic vulnerabilities"
- **3CA ID**: 3ca:20773
- **Publication**: Nature Genetics, Volume 54, Issue 5, Pages 649-659, 2022
- **DOI**: 10.1038/s41588-022-01061-8

### Data Sources

- **Expression Matrix**: `inputs/Exp_data_UMIcounts.mtx` (33,538 genes × 58,843 cells)
- **Cell Metadata**: `inputs/Cells.csv`
- **Gene Names**: `inputs/Genes.txt`
- **Metabolic Genes**: Reactome R-HSA-1430728 (Release 97) - 2,197 genes

## Analysis Summary

### Methods

1. **Normalization**: Per-cell library size to 10,000, then log1p transformation
2. **Feature Scaling**: Scanpy scale(zero_center=False, max_value=10)
3. **Clustering**: Leiden algorithm with resolution selection
4. **Baselines**: HVG and 19 size-matched random gene controls

### Key Results

- **Cells Analyzed**: 58,843
- **Metabolic Genes Used**: 1,984 (after prevalence filtering)
- **Clusters Identified**: 15 (cluster sizes: 1,002 - 8,985 cells)
- **Selected Resolution**: 0.4
- **Leiden Silhouette**: 0.229
- **Mean Pairwise ARI**: 0.980
- **Random Control Comparison**: 0 of 19 random controls exceeded metabolic clustering

### Confounders Checked

- patient, sample, source, cell_type, cell_subtype, cell_cycle_phase, complexity, computed_total_counts, computed_detected_genes, computed_mito_percent

### Conclusions

The analysis found candidate partitions of observed groups but **distinct metabolic states remain inconclusive**. The observed random-control exceedance count was 0 of 19; the add-one rank fraction is descriptive, not an inferential p-value.

## Deliverables

- `results/core_analysis/core_result.json` - Core analysis results
- `results/summary.json` - Summary statistics
- `results/analysis_manifest.json` - Analysis manifest
- `report/main.tex` - LaTeX report
- `report/main.pdf` - Compiled PDF report
- `README.md` - This file

## Verification

All results are derived from the authoritative `core_result.json` file. The analysis was performed using the `workflow_research_quality_metabolic_states_v2` engine with seeds [0, 17, 42, 73, 101].
