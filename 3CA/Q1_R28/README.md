# Q1_R28: Metabolic State Clustering Analysis

## Summary
This analysis investigates whether transcriptional metabolic states can be identified as distinct clusters in single-cell RNA-seq data from meningioma brain samples.

## Dataset
- **Study**: Choudhury et al. 2022 (3CA:20773)
- **Source**: https://www.nature.com/articles/s41588-022-01061-8
- **DOI**: 10.1038/s41588-022-01061-8
- **Cells**: 58,843
- **Genes**: 33,538 (33,514 unique symbols, 24 duplicate symbols aggregated)

## Analysis
- **Gene Set**: Reactome metabolism pathway (R-HSA-1430728, release 97)
- **Matched genes**: 1,984 (after prevalence filtering)
- **Normalization**: Per-cell library size to 10,000, then log1p
- **Clustering**: Leiden with resolution 0.4, 15 clusters

## Key Results
- **Leiden silhouette**: 0.229
- **Stability (mean pairwise ARI)**: 0.980
- **Random controls exceeding metabolic**: 0 of 19
- **Cell-type NMI**: 0.507
- **Cell-subtype NMI**: 0.658

## Questions and Verdicts
1. **Distinct metabolic states?** Candidate partitions observed but distinct metabolic states inconclusive.
2. **Cell-type associations?** Associations are descriptive and non-causal.
3. **CD8 T cell subgroup?** Candidate partitions observed but distinct metabolic states inconclusive.

## Artifacts
- `results/core_analysis/core_result.json` - Core analysis results
- `results/summary.json` - Summary statistics
- `results/analysis_manifest.json` - Analysis manifest
- `report/main.tex` - LaTeX report
- `report/main.pdf` - Compiled PDF report
- `figures/metabolic_umap.pdf` - UMAP visualization
- `figures/clustering_diagnostics.pdf` - Clustering diagnostics

## Validation
Run `validate_research_bundle` to verify all artifacts and PDF rendering.
