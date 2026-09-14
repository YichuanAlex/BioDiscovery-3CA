# Source Ledger — Q1 Metabolic State Analysis

## 1. 3CA Study 3ca:20111 (Tirosh et al. 2016)

| Field | Value |
|-------|-------|
| **3CA ID** | 3ca:20111 |
| **Title** | Tirosh et al. 2016 |
| **Citation URL** | https://science.sciencemag.org/content/352/6282/189 |
| **3CA Detail Page** | https://www.weizmann.ac.il/sites/3CA/study-data/comments/20111 |
| **fetched_at** | 2026-09-12T01:45:17.510099+00:00 |
| **Disease** | Melanoma |
| **Technology** | SmartSeq2 |
| **Samples** | 19 |
| **Cells** | 4,645 |
| **Assets** | Data archive (expression), Metadata archive, Cell types PDF, Summary PDF, Meta-programs PDF, MP scores CSV, CNAs PNG, CNA matrix CSV, UMAP PDF, Cell cycle PDF |

**Claim supported:** 3CA provides the Tirosh 2016 melanoma SmartSeq2 dataset (19 samples, 4,645 cells) as the primary scRNA-seq resource for this project. The 3CA website hosts both expression data and metadata archives.

---

## 2. 3CA Methods Page

| Field | Value |
|-------|-------|
| **URL** | https://www.weizmann.ac.il/sites/3CA/methods |
| **fetched_at** | 2026-09-12T01:46:08.970137+00:00 |
| **Source** | 3CA Curated Cancer Cell Atlas |

**Preprocessing pipeline (3CA):**
- **Cell filtering:** Exclude cells with low #genes. For SmartSeq2: #genes < 2000. For 10X: #genes < 1000.
- **Sample filtering:** Exclude samples with < 10 malignant cells; exclude samples with unclear CNA patterns.
- **Gene filtering:** Keep top ~7000 genes with highest mean across all cells.
- **Normalization:** UMI counts → CPM; then `log2(x/10 + 1)` (division by 10 assumes complexity ~100,000). Centering per gene, separately per study.
- **Meta-program definition:** NMF with K=4–9, robust NMF programs (recur across K and tumors), Jaccard clustering → 67 MPs → 41 MPs after filtering → grouped into 11 hallmarks.
- **UMAP generation:** Filter genes with mean log2(TPM/CPM) < 4, center by gene, 50 PCs via IRLBA, UMAP with n_neighbors scaled to cell count.

**Claim supported:** 3CA uses `log2(x/10 + 1)` normalization and a specific NMF-based meta-program pipeline. This differs from the Xiao/Dai/Locasale 2019 pipeline (see below).

---

## 3. Xiao/Dai/Locasale 2019 (Nature Communications)

| Field | Value |
|-------|-------|
| **URL** | https://www.nature.com/articles/s41467-019-11738-0 |
| **DOI** | 10.1038/s41467-019-11738-0 |
| **fetched_at** | 2026-09-12 (live web) |
| **Title** | Metabolic landscape of the tumor microenvironment at single cell resolution |
| **Authors** | Zhengtao Xiao, Ziwei Dai, Jason W. Locasale |
| **Journal** | Nature Communications |
| **Year** | 2019 |

**Key methods & claims (Xiao et al. 2019):**
- **Datasets:** 4,054 melanoma cells + 5,502 HNSCC cells from scRNA-seq (a differently processed subset of the same underlying Tirosh melanoma study, GSE72056; not an independent melanoma cohort).
- **Imputation:** Zero-value imputation before t-SNE to reduce dropout effects.
- **Clustering:** t-SNE on 1,566 metabolic genes.
- **Pathway activity score:** Average expression across all genes in a pathway, all cells of a type.
- **Normalization:** Deconvolution method (not `log2(x/10+1)`).
- **Cell-type grouping:** 11 KEGG categories.
- **Key findings:** Malignant cells show global upregulation of metabolic pathways; mitochondrial activity is the major contributor to metabolic heterogeneity; glycolysis and OXPHOS correlate with hypoxia; bulk RNA-seq poorly captures single-cell metabolic heterogeneity.

**Difference from 3CA pipeline:**
- Xiao et al. use deconvolution normalization, not the `log2(x/10+1)` transform.
- They use t-SNE for dimensionality reduction, not NMF-based meta-programs.
- They focus on metabolic pathway activity scores, not meta-program clustering.
- They analyze two tumor types (melanoma + HNSCC), whereas 3CA's 3ca:20111 is melanoma-only.

**Claim supported:** Xiao et al. demonstrate that single-cell metabolic profiling reveals global upregulation of metabolic pathways in malignant cells and that mitochondrial activity drives metabolic heterogeneity. Their methods differ substantially from 3CA's NMF-based meta-program approach.

---

## 4. Gavish et al. 2023 (Nature)

| Field | Value |
|-------|-------|
| **URL** | https://www.nature.com/articles/s41586-023-06130-4 |
| **DOI** | 10.1038/s41586-023-06130-4 |
| **fetched_at** | 2026-09-12 (live web) |
| **Title** | Hallmarks of transcriptional intratumour heterogeneity across a thousand tumours |
| **Authors** | Avishai Gavish, Michael Tyler, Alissa C. Greenwald, et al. |
| **Journal** | Nature |
| **Year** | 2023 |

**Key methods & claims (Gavish et al. 2023):**
- **Dataset:** 77 studies, 1,163 tumour samples, 24 cancer types.
- **Meta-program definition:** NMF with K=4–9, robust NMF programs (recur across K and tumors), Jaccard clustering → 67 MPs → 41 MPs after filtering → grouped into 11 hallmarks.
- **Normalization:** Not explicitly detailed in the abstract; likely similar to 3CA pipeline.
- **Key findings:** 41 consensus meta-programs across malignant cells; most malignant ITH programs are similar to non-malignant epithelial programs, suggesting heterogeneity exists before oncogenesis.

**Claim supported:** Gavish et al. establish the 3CA meta-program framework and show that transcriptional ITH is largely shared across cancer types, with many malignant programs mirroring non-malignant epithelial programs.

---

## 5. Tirosh et al. 2016 (PubMed)

| Field | Value |
|-------|-------|
| **URL** | https://pubmed.ncbi.nlm.nih.gov/27124452/ |
| **DOI** | 10.1126/science.aad0501 |
| **fetched_at** | 2026-09-12 (live web — page returned empty, likely cookie-blocked) |
| **Title** | Dissecting the multicellular ecosystem of metastatic melanoma by single-cell RNA-seq |
| **Authors** | Itay Tirosh, et al. |
| **Journal** | Science |
| **Year** | 2016 |

**Note:** The PubMed page returned an empty/untrusted response (likely due to cookie requirements). The study is the original source of the 3ca:20111 dataset.

**Claim supported:** Tirosh et al. 2016 established the melanoma single-cell RNA-seq dataset (19 samples, 4,645 cells) that forms the basis of 3CA study 3ca:20111. The original paper describes the multicellular ecosystem of metastatic melanoma.

---

## Summary of Methodological Differences

| Aspect | 3CA (Gavish 2023) | Xiao/Dai/Locasale 2019 |
|--------|-------------------|------------------------|
| **Normalization** | `log2(x/10 + 1)` | Deconvolution |
| **Dimensionality reduction** | NMF → robust MPs → Jaccard clustering | t-SNE |
| **Meta-program definition** | NMF with K=4–9, Jaccard clustering | Not used |
| **Datasets** | 77 studies, 1,163 tumours | 2 studies (melanoma + HNSCC) |
| **Focus** | Transcriptional ITH hallmarks | Metabolic landscape at single-cell resolution |
