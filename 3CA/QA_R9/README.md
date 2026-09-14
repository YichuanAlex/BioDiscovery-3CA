# QA_R9 Research Analysis

## Summary

This analysis investigates candidate transcriptional metabolic states in single-cell RNA-seq data from the Choudhury et al. 2022 meningioma study (3CA:20773).

## Questions and Answers

### Question 1: Do all cells form distinct, reproducible candidate transcriptional metabolic clusters?

**Answer: Candidate partitions observed but distinct metabolic states inconclusive.**

Global analysis of 58,843 cells using 1,646 matched metabolic genes yielded 17 Leiden clusters at resolution 0.8. Leiden silhouette=0.217, matched-k KMeans silhouette=0.220, and mean pairwise ARI=0.965 across seeds. Random-gene controls (19 total) produced silhouettes with mean=0.210, min=0.199, max=0.222. Only 2 of 19 controls (add-one rank fraction=0.15) exceeded or equaled the metabolic control. The HVG baseline yielded silhouette=0.283, exceeding the metabolic control.

### Question 2: How are those candidate metabolic partitions associated with the supplied cell types and subtypes?

**Answer: Associations are descriptive and non-causal.**

Categorical confounder NMI values show substantial confounding: patient NMI=0.518, sample NMI=0.548, cell_type NMI=0.496, cell_subtype NMI=0.648. High NMI for patient and sample indicates clustering is strongly confounded by sample origin. These associations are descriptive and non-causal.

### Question 3: Within the exact annotated subset `cell_subtype=CD8 T cells`, are there distinct candidate metabolic states?

**Answer: Candidate partitions observed but distinct metabolic states inconclusive.**

Analysis of 3,624 CD8 T cells using 1,318 matched metabolic genes yielded 6 Leiden clusters at resolution 0.4. Leiden silhouette=0.099, matched-k KMeans silhouette=0.095, and mean pairwise ARI=0.759 across seeds. Seventeen of 19 random-gene controls (add-one rank fraction=0.9) exceeded or equaled the metabolic control. The HVG baseline yielded silhouette=0.168, exceeding the metabolic control.

## Limitations

1. Global cell-type separation cannot establish within-cell-type metabolic states.
2. Patient-within sensitivity is not independent-cohort replication.
3. Patient/sample mixing can confound interpretation.
4. No automatic threshold proves independence, multimodality, mechanism, causality, or statistical significance.
5. Candidate partitions are descriptive; conclusions are inconclusive.

## Artifacts

- `report/main.tex` - LaTeX report source
- `report/main.pdf` - Compiled PDF report
- `results/summary.json` - Global analysis summary
- `results/analysis_manifest.json` - Analysis manifest with nested schema
- `results/core_analysis/core_result.json` - Global core analysis results
- `results/cd8_analysis/core_result.json` - CD8 T cell subset core analysis
- `results/cd8_analysis/summary.json` - CD8 T cell subset summary
- `figures/metabolic_umap.pdf` - Global metabolic UMAP
- `figures/clustering_diagnostics.pdf` - Global clustering diagnostics
- `figures/cd8_analysis/metabolic_umap.pdf` - CD8 metabolic UMAP
- `figures/cd8_analysis/clustering_diagnostics.pdf` - CD8 clustering diagnostics

## References

1. Choudhury A, Magill ST, Eaton CD, et al. Meningioma DNA methylation groups identify biological drivers and therapeutic vulnerabilities. Nature Genetics. 2022;54(5):649-659. doi:10.1038/s41588-022-01061-8
2. Gavish A, Tyler M, Greenwald AC, et al. Hallmarks of transcriptional intratumour heterogeneity across a thousand tumours. Nature. 2023;618(7965):598-606. doi:10.1038/s41586-023-06130-4
