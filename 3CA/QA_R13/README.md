# QA_R13: Metabolic-state clustering in 3CA study 3ca:20773

## Question

Are there distinct clusters of transcriptional metabolic states? In other words, can the
user-supplied metabolic genes alone cluster or separate groups in the single-cell RNA-seq
dataset? The same question is repeated on the exact metadata subset `cell_subtype = CD8 T cells`.

## Data and inputs

- Public study: `3ca:20773` (Choudhury et al. 2022, meningioma, 10x; 3CA page
  <https://www.weizmann.ac.il/sites/3CA/brain>, catalog fetched 2026-09-28T07:37:16.700730+00:00).
- Data archive: `Data_Choudhury2022_Brain.tar.gz`, 554,504,664 bytes,
  SHA-256 `2156a73fd5f95a198ef90821f2d734bfa7e0b5aa3686deefd1b5c5d5d1269aa1`.
- Staged raw counts: `inputs/Exp_data_UMIcounts.mtx` (33,538 features x 58,843 cells,
  genes-by-cells; SHA-256 `51bf0452d166511fecca3f32d89f9fd0f631d173143173d82115f49cdaaa6c1d`),
  with `inputs/Cells.csv`, `inputs/Genes.txt`, `inputs/Samples.csv`.
- Immutable user-supplied metabolic gene set: `inputs/metabolic_genes_total.csv`
  (1,988 symbols; SHA-256 `7503180d29693bd1e654ea93281db0e3ec4177ff44842c8b02f6a098402e41a9`).
  It is the only metabolic feature-set source; Reactome was not used.

## Gene matching

Exact-then-unique-case-insensitive matching of the 1,988 supplied symbols against the
expression matrix: 341 exact matches, 1,457 unique case-insensitive matches, 190 unmatched,
0 ambiguous casefold mappings -> 1,798 expression symbols matched before prevalence.
After prevalence filtering: 1,646 metabolic genes in the global analysis, 1,318 in the CD8
subset. Saved in `results/core_analysis/gene_set_mapping.csv`,
`results/core_analysis/matched_metabolic_genes.txt`, and the CD8 counterparts.

## Analysis (native core, workflow_research_quality_metabolic_states_v2)

- Normalization: per-cell library size to 10,000, then log1p
  (x' = log(1 + 10^4 x / library size)); feature scaling Scanpy scale(zero_center=False,
  max_value=10); 30-component PCA; 15-neighbor graph; Leiden (igraph, 2 iterations).
- Seeds `[0, 17, 42, 73, 101]`; resolutions `[0.4, 0.8, 1.2]`.
- Controls: variance-ranked HVG comparator and 19 random size-matched gene sets with a
  matched-K KMeans benchmark. Confounders checked: patient, sample, source, cell type,
  cell subtype, cell cycle phase, complexity, total counts, detected genes, mito percent.
- Within-patient reclustering (replicate field = patient).

## Key results (from the saved core results only)

| Metric | Global | CD8 |
|---|---|---|
| Cells analyzed | 58,843 | 3,624 |
| Metabolic genes analyzed | 1,646 | 1,318 |
| Selected resolution | 0.4 | 0.4 |
| Leiden clusters | 13 | 6 |
| Cluster size range (cells) | 1,051-9,041 | 55-1,872 |
| Silhouette (3,000-cell subsample) | 0.218 | 0.093 |
| Calinski-Harabasz (all cells) | 7,268.856 | 399.641 |
| Davies-Bouldin (all cells) | 1.484 | 2.205 |
| Mean / min pairwise ARI (seeds) | 0.951 / 0.919 | 0.736 / 0.583 |
| HVG comparator silhouette | 0.274 | 0.168 |
| Matched-K metabolic silhouette | 0.228 | 0.095 |
| Random controls >= metabolic value | 5/19 | 17/19 |
| Add-one rank fraction (descriptive) | 0.3 | 0.9 |
| Patient NMI | 0.521 | 0.379 |
| Patient-within ARI range | 0.117-0.942 | 0.486-0.832 |
| Weakest patient (cells) | 3 (3,287) | 6 (2,776) |

Conclusion recorded by both cores: **inconclusive** regarding distinct biological metabolic
states. Candidate partitions are observed computationally; cluster-annotation associations
are descriptive and non-causal; cells are not independent biological replicates; the random
control add-one rank fraction is a descriptive benchmark, not a biological P value.

## Artifacts

- `report/main.tex`, `report/main.pdf` - LaTeX report and compiled PDF.
- `results/summary.json`, `results/cd8_analysis/summary.json` - core summaries.
- `results/core_analysis/core_result.json`, `results/cd8_analysis/core_result.json` -
  authoritative core results (sole numeric source for the report).
- `results/analysis_manifest.json` - evidence manifest (schema version 1).
- `figures/metabolic_umap.pdf`, `figures/clustering_diagnostics.pdf`,
  `figures/cd8_analysis/metabolic_umap.pdf`, `figures/cd8_analysis/clustering_diagnostics.pdf` -
  vector figures saved by the core tool.
- `sources/literature/` - verified Crossref metadata for
  DOI 10.1038/s41588-022-01061-8 (dataset paper) and DOI 10.1186/s13059-017-1382-0 (Scanpy).

## Verification

Dataset DOI `3ca:20773` -> Crossref `10.1038/s41588-022-01061-8` (Nature Genetics 54(5),
649-659, 2022). Scanpy DOI `10.1186/s13059-017-1382-0` (Genome Biology 19(1), 2018).
Both Crossref records are saved under `sources/literature/`.
