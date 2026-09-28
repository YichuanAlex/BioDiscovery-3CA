# QA_R14: Metabolic-gene-only clustering of 3CA study 3ca:20773

## Question

Are there distinct clusters of transcriptional metabolic states? In other
words, can we use only a metabolic gene panel to cluster or separate
groups in a single-cell RNA-seq dataset? The same analysis is repeated on
the exact metadata subset `cell_subtype = CD8 T cells`.

## Data and inputs

- Study: `3ca:20773` — Choudhury et al. 2022, meningioma
  (`10.1038/s41588-022-01061-8`), 3CA category page
  `https://www.weizmann.ac.il/sites/3CA/brain` (catalog fetched at
  2026-09-28T07:37:16Z).
- Public raw-count archive (verified cache):
  `Data_Choudhury2022_Brain.tar.gz`, SHA-256
  `2156a73fd5f95a198ef90821f2d734bfa7e0b5aa3686deefd1b5c5d5d1269aa1`.
- Staged raw counts: `inputs/Exp_data_UMIcounts.mtx` (genes-by-cells;
  58,843 cells, 33,538 gene feature rows), SHA-256
  `51bf0452d166511fecca3f32d89f9fd0f631d173143173d82115f49cdaaa6c1d`.
- Cell metadata: `inputs/Cells.csv` (`cell_name` identifier);
  gene names: `inputs/Genes.txt`; samples: `inputs/Samples.csv`.
- Metabolic gene set (immutable user input, the only feature set used):
  `inputs/metabolic_genes_total.csv`, SHA-256
  `7503180d29693bd1e654ea93281db0e3ec4177ff44842c8b02f6a098402e41a9`.
  No Reactome or other substitute gene set was used.

## Gene-set mapping audit (global core)

- 1,988 nonempty source symbol rows; 0 duplicate exact rows.
- 341 exact matches; 1,457 unique case-insensitive matches;
  190 unmatched symbols; 0 ambiguous case-folded symbols;
  0 duplicate expression mappings.
- 1,798 expression symbols matched before prevalence filtering;
  **1,646 metabolic genes analyzed after the min 20-cell prevalence
  filter** (global run). The CD8 subset run analyzed 1,318 metabolic
  genes after the same prevalence filter.
- Exact duplicate symbols were summed on raw counts before QC; the
  symbol-level aggregation leaves gene-ID/locus ambiguity unresolved.
  Saved in `results/core_analysis/gene_set_mapping.csv` and
  `results/core_analysis/source_feature_to_symbol.csv`.

## Analysis (both cores, native engine)

- Engine: `workflow_research_quality_metabolic_states_v2`
  (SHA-256 `51ddbf26c336a932f10d216db6092bc5aa24f402adf9dafee6a0435382592401`).
- Normalization: per-cell library size to 10,000, then
  `log(1+x)`; feature scaling `Scanpy scale(zero_center=False,
  max_value=10)`; PCA (arpack, 30 components); 15-neighbor graph;
  Leiden (igraph, 2 iterations, directed=False).
- Seeds `[0, 17, 42, 73, 101]`; resolutions `[0.4, 0.8, 1.2]`;
  stability filter mean pairwise ARI >= 0.75; primary criterion highest
  median silhouette; tie-breaker highest mean pairwise ARI.
- Controls: HVG (highest variance of library-normalized log1p expression
  among prevalence-passing non-mitochondrial symbols) and 19 size-matched
  random gene controls (KMeans partitions, matched cluster count, seed 0).
- Metrics: silhouette on a 3,000-cell subsample (seed 7321) in PCA space;
  Calinski-Harabasz and Davies-Bouldin on all QC-passing cells.
- QC: min 500 counts, min 200 genes, max 20% mitochondrial; no cells
  excluded in either run.

## Key results (from the saved core results only)

### Global run (`results/core_analysis/core_result.json`, SHA-256 `e20dc9d6bf1d755d2a74259a44ab699735ae2aea6a6d307cf902dbe61496613b`)

- 58,843 cells analyzed; 1,646 metabolic genes; resolution 0.4;
  13 clusters; cluster sizes 1,051–9,041 cells.
- Leiden silhouette 0.218 (3,000-cell subsample); Calinski-Harabasz
  7,268.856; Davies-Bouldin 1.484.
- Stability: mean pairwise ARI 0.951 (min 0.919); mean pairwise NMI
  0.963 (min 0.942).
- Matched-k KMeans on metabolic genes: silhouette 0.228; HVG control:
  0.274; 19 random controls: 0.194–0.241 (mean 0.217);
  random controls exceeding or equal to metabolic: **5 of 19**;
  add-one rank fraction **0.3** (descriptive add-one rank, not a
  P value).
- Confounder NMI: patient 0.521, sample 0.545, source 0.196,
  cell_type 0.508, cell_subtype 0.656, cell_cycle_phase 0.189.
- Within-patient sensitivity (6 patients): global-vs-within ARI
  0.117–0.942; **weakest patient 3 (3,287 cells)**.
- Conclusion: **inconclusive** (candidate partitions observed; distinct
  biological metabolic states not established).

### CD8 T cell run (`results/cd8_analysis/core_result.json`, SHA-256 `6cad88f3cca927227aa1b0c8c14493eb54e32dbc45bf14bac79b0444f4e8e2d6`)

- Exact subset `cell_subtype = CD8 T cells`: 3,624 cells; 1,318
  metabolic genes; resolution 0.4; 6 clusters; cluster sizes
  55–1,872 cells.
- No resolution passed the stability filter (fallback to all
  resolutions); mean pairwise ARI 0.736 (min 0.583); mean pairwise NMI
  0.761 (min 0.650).
- Leiden silhouette 0.093 (median across seeds 0.103);
  Calinski-Harabasz 399.641; Davies-Bouldin 2.205.
- Matched-k KMeans on metabolic genes: silhouette 0.095; HVG control:
  0.168; 19 random controls: 0.092–0.131 (mean 0.107);
  random controls exceeding or equal to metabolic: **17 of 19**;
  add-one rank fraction **0.9** (descriptive add-one rank, not a
  P value).
- Confounder NMI: patient 0.379, sample 0.430, source 0.340,
  cell_cycle_phase 0.283.
- Within-patient sensitivity (3 patients): global-vs-within ARI
  0.486–0.832; **weakest patient 6 (2,776 cells)**.
- Conclusion: **inconclusive** (CD8 candidate partitions observed;
  distinct biological metabolic states not established).

## Report answers

- Question 1 (global computational grouping): candidate partitions
  observed but distinct metabolic states inconclusive.
- Question 2 (patient/cell-type association): associations are
  descriptive and non-causal.
- Question 3 (CD8 T cells): CD8 candidate partitions observed but
  distinct metabolic states inconclusive.

Cells are nested within patients and samples; all metrics are
descriptive evidence, not independent-replicate significance tests or
causal evidence.

## Artifacts

- `report/main.tex`, `report/main.pdf` — illustrated research report
  (4 vector figures, 1 three-line table, 1 normalization equation,
  Question 1–3 sections with explicit verdicts).
- `results/summary.json` (global), `results/cd8_analysis/summary.json`.
- `results/core_analysis/core_result.json`, `results/cd8_analysis/core_result.json`.
- `results/analysis_manifest.json` — manifest gate for the bundle.
- Figures: `figures/metabolic_umap.pdf`, `figures/clustering_diagnostics.pdf`,
  `figures/cd8_analysis/metabolic_umap.pdf`,
  `figures/cd8_analysis/clustering_diagnostics.pdf`.
- Literature: `sources/literature/crossref_db798362115f799a.json`
  (dataset paper), `sources/literature/crossref_ed78a4eb053ff8b2.json`
  (Scanpy paper).

## Limitations

Clustering is exploratory: it does not test discrete states against a
continuum, and the recorded conclusions are therefore inconclusive on
the existence of distinct biological metabolic states. Seed stability is
conditional on the fixed preprocessing/graph; benchmark exceedance counts
are descriptive; low confounder NMI does not prove independence; and no
causal claim is made.
