# Q1_R24: Metabolic State Clustering Analysis

## Study Overview
This analysis investigates whether transcriptional metabolic states can be used to cluster or separate groups in single-cell RNA-seq data from the Choudhury et al. 2022 meningioma dataset (3CA:20773).

## Data Source
- **Study ID**: 3ca:20773
- **Title**: Meningioma DNA methylation groups identify biological drivers and therapeutic vulnerabilities
- **Journal**: Nature Genetics, 2022
- **DOI**: 10.1038/s41588-022-01061-8
- **Cells**: 58,843
- **Genes**: 33,538 (33,514 unique symbols, 24 duplicate symbol rows aggregated)

## Analysis Summary
- **Metabolic genes**: 1,984 (from Reactome R-HSA-1430728, release 97)
- **Clustering method**: Leiden with resolution 0.4
- **Seeds**: [0, 17, 42, 73, 101]
- **Clusters**: 15 (sizes: 1,002--8,985 cells)
- **Silhouette score**: 0.229
- **Conclusion**: Inconclusive - candidate partitions observed but distinct metabolic states not proven

## Key Findings
1. **Random control comparison**: 0 of 19 random controls exceeded or equal to metabolic clustering (add-one rank fraction: 0.05)
2. **HVG baseline**: Silhouette 0.295 (metabolic: 0.247, random min: 0.206, random mean: 0.221)
3. **Confounders checked**: patient, sample, source, cell_type, cell_subtype, cell_cycle_phase, complexity
4. **Within-replicate sensitivity**: Weakest replicate (patient 3, 3,287 cells) with ARI range 0.106--0.813

## Required Artifacts
- `results/core_analysis/core_result.json` - Core analysis results
- `results/summary.json` - Summary statistics
- `results/analysis_manifest.json` - Analysis manifest
- `report/main.tex` - LaTeX report
- `report/main.pdf` - Compiled PDF report
- `README.md` - This file

## Verification
Run `validate_research_bundle` to verify all artifacts and PDF rendering.
