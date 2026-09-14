# Figure audit

Backend: Python/matplotlib, as established by the existing input script. This task's preference is recorded here only; global skill preferences were not changed.

Reuse level: exact scientific reuse of the user-authorized plotting implementation with the independently downloaded raw-input path adapted. Figures themselves were recomputed, not copied.

| Figure/panel | Evidence role and population | Spread / unit | Visual audit |
|---|---|---|---|
| 1a | Pipeline, 23,686 genes to 1,360 retained metabolic genes | Schematic, not a measurement | Labels readable, no collisions |
| 1b | Annotation counts, all 4,645 cells including 548 unannotated | Counts, no sampling interval | All categories included; values trace to cells.csv |
| 1c | Whole-transcriptome UMAP supplied in the 3CA cell metadata | Individual cells; not a newly fitted metabolic embedding | Axes/legend clear; caption must identify source coordinates |
| 1d | Scope and sample counts | Descriptive | Distinguish all-cell clustering from 4,097 annotated-cell classification |
| 2a/2b | Metabolic PCA and k=2 assignments, 4,645 cells | Individual cells | Clear shared geometry; overlap reflects data, not hidden categories |
| 2c | k scan, complexity adjustment, matched-random maxima | One fitted clustering per k; random band is empirical 95% range across 20 sets, NOT confidence interval | Series and band clear; caption must define range |
| 2d | Patient-blocked classification confusion matrix, 4,097 annotated cells | Row-normalized predictions over held-out patients, not fold SD | Values legible; rare NK-cell recall must not be obscured by aggregate score |
| 3a | Metabolic vs 20 matched-random maxima | Gene-set unit; empirical p resolution 1/21 | Points and primary marker clear; exploratory, no universal-state claim |
| 3b | Malignant metabolic PCA by sample, 1,257 cells/15 samples | Individual cells | Legend clear; patient-associated separation apparent |
| 3c | Raw and patient+complexity-adjusted malignant k scans | One fit per k, seed ARI reported in text/table separately | No overlap/collision; exploratory residualization, not causal adjustment |
| 3d | Cell-type mean pathway scores for 18 selected pathways | Cell-type mean, descriptive across-type z-score, no inferential interval | Long labels and color bar readable; transcript score is not metabolic flux |
| 3e | AMI with labels/sample | Descriptive alignment statistic | Bars labeled; all-cell and malignant populations must be stated |

Static preflight: 20 PASS, 0 WARN, 0 FAIL. Exported PDF font audits: figure1 minimum 5.6 pt; figures2/3 minimum 5.2 pt; no sub-floor text runs. Actual PNG exports inspected panel by panel. Final report must preserve figure aspect ratio and the glyph floor after scaling.

No data were filtered for aesthetics. Feature detection filtering and annotation/malignant population restrictions belong to the analysis and are recorded in the report. The silhouette sample of 2,000 is a declared computational estimate, not reduction of the fitted clustering population. No submitted-journal production compliance is claimed: this is an arXiv-style research report, not a Nature submission.

Typography continuation: all text artists now have a 6 pt floor in the common export helper; figures were rerun and re-inspected. Figure3 PDF minimum is 6 pt with no sub-floor runs. Its expanded long pathway labels still fit without collisions. A standard 6.5-inch report column may scale the figure; require at least 5 pt effective text after that scaling and check actual report pages.
