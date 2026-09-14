# Evidence-first report plan

Task: English research report; paper type: research/reanalysis; journal: generic arXiv-compatible preprint; audience: scRNA-seq/cancer researchers. No claim of journal submission or a new biological discovery.

Argument: In one melanoma cohort, KEGG metabolic genes contain strong information for broad cell-group separation, but matched controls and patient/complexity sensitivity analyses do not establish a universal set of malignant transcriptional metabolic states.

| Canonical term | Definition / usage |
|---|---|
| scRNA-seq | single-cell RNA sequencing; transcript measurement, not flux |
| transcriptional metabolic state | metabolic-gene expression pattern; distinguish from measured metabolism |
| ARI | adjusted Rand index, algorithmic seed stability; not biological replication |
| AMI | adjusted mutual information with known cell type or sample |
| balanced accuracy | mean per-class recall over held-out predictions |
| macro-F1 | unweighted mean of class-specific F1 |
| patient-blocked | disjoint sample IDs in GroupKFold; one sample per patient in source cohort |

Drafting order: results from actual summary/tables, methods from actual code, introduction/discussion grounded in verified sources, then main title/abstract. Reading order: abstract, introduction, methods, results, discussion/limitations, availability, conclusion, references.

| Claim | Evidence | Boundary |
|---|---|---|
| Broad separation is possible | all-cell k=2 silhouette 0.377; held-out BA 0.884 | unsupervised fit includes 548 unannotated cells; classification uses 4,097 annotated cells |
| Metabolic specificity is not established by good classification | random BA 0.896, HVG BA 0.892 | no patient-bootstrap CI; no claim of statistically proven inferiority |
| All-cell separation partly tracks complexity | PC1 rho 0.650; adjusted best silhouette 0.224 | residualization removes correlated biology as well as nuisance; not causal |
| Malignant labels largely track patient | AMI 0.742, k=8 best only within k=2..8 | upper-bound-selected k cannot be called a true state count |
| Residual structure remains | adjusted malignant k=2 silhouette 0.228, seed ARI 0.970 | does not prove either universal states or absence of within-patient heterogeneity |
| Within-patient structure is plausible | 9 patients >=30 cells; median max silhouette 0.271 | PCA fitted across malignant patients; clustering within a patient is not external validation |

Important reporting corrections:

- Empirical p=1/21=0.047619 is the minimum possible with 20 random sets. It is an exploratory set-comparison, not decisive evidence of metabolic-specific states or a corrected multi-hypothesis result.
- Random-set SD measures variability across gene sets; pairwise seed ARI SD measures algorithmic variability. Neither is a biological confidence interval.
- Scaling and PCA are training-fold-only in classification, but pooled unsupervised gene eligibility/HVG selection is outside folds. Fully prospective evaluation should repeat feature selection within training folds.
- The pathway heatmap averages standardized expression and rescales means across cell types; it is not scMetabolism activity inference or flux measurement.
- Xiao's processed melanoma subset and this 3CA dataset share the underlying Tirosh source; this is not an independent replication of Xiao.
- Audit-assisted code reuse must be disclosed; figures/statistics rerun here and report prose newly drafted by the local workflow under supervision.
