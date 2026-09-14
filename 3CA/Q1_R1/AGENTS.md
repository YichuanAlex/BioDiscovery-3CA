# Q1 execution contract

Complete the user's research task in this directory. Work autonomously and keep all generated code, downloaded data, results, figures, LaTeX, and the final PDF here.

## Runtime and isolation

- Use only the tools exposed by the current `workflow_codex` session. The paths under `C:\Users\User\.agents` in the user's prompt describe the intended 3CA capability, but they are not authorization to use the globally installed CLI, skill, MCP server, Codex home, or sessions.
- Use the registered project-local 3CA function tools. Do not invoke a global `threeca.exe` from PowerShell.
- The user-authorized reference implementation under `C:\Users\User\Desktop\3ca\Q1` may be reused as an audited code baseline when an independently written implementation fails review. Do not copy its downloaded data, precomputed results, figures, PDF, or prose. Adapt a copied script so this workspace remains self-contained, rerun every computation here, and document the reuse in `README.md` and `TASK_STATE.md`.
- Do not use Computer Use for this task.

## Persistence

- Create `TASK_STATE.md` immediately. Record each phase as `pending`, `running`, or `complete`, the exact next action, commands that failed, and outputs already verified.
- Update `TASK_STATE.md` at every phase boundary and before any progress response. On continuation, read it and resume the first incomplete phase.
- A progress summary is not completion. Continue using tools until every acceptance check below passes. Print `TASK_COMPLETE` only at the true end.
- Never invent a result. If a computation fails, record the failure, fix the smallest root cause, rerun it, and distinguish unavailable evidence from a negative result.

## Required data workflow

1. Use `search_studies` first, then `get_study` with asset discovery and `plan_asset` before downloads. Use `download_asset`, `inspect_asset`, and `verify_asset` where applicable.
2. Use 3CA study `3ca:20111` (Tirosh et al., melanoma, Smart-seq2): 19 samples and 4,645 cells. Download both expression data and metadata through the local 3CA tools. Record canonical URLs, retrieval timestamps, sizes, and SHA-256 hashes in a manifest.
3. Expected source-file regression checks are:
   - expression archive: 234,187,869 bytes; SHA-256 `9e157aceb5a39add6e04c4d92db7f970bf19413a14a8c87a1262f9424f0818f6`
   - metadata archive: 127,155 bytes; SHA-256 `741107ef4ad09cb19b9a22c8af40ce7440e24f18cf1012c2ebb4c03600fede17`
   Investigate a mismatch; do not overwrite observed values with these expected values.
4. Research the official 3CA pages and the primary dataset/pathway sources. Save a source ledger with URL, access date, claim supported, and bibliographic identifier. Prefer primary sources.

## Required analysis

- Build reproducible scripts, not notebook-only or hand-calculated results. Pin or record dependencies.
- Use the study's TPM matrix with the documented `log2(TPM/10 + 1)` transform. Define the metabolic feature set from KEGG metabolic pathways and record the mapping/filtering logic.
- Report data dimensions, detected metabolic genes, sparsity/detection summaries, and analysis populations.
- Analyze all curated cells (including unannotated cells) and malignant cells separately. Evaluate cell-type classification on annotated cells only.
- For metabolic genes only: scale features, reduce with PCA, evaluate K-means by silhouette (`k=2..10` for all cells, `k=2..8` for malignant cells, `k=2..6` within sufficiently sized patients), and quantify seed stability by adjusted Rand index. Report an optimum at a scan boundary as a boundary, not a biological state count.
- Quantify alignment with cell type and patient/sample using adjusted mutual information.
- Test whether library complexity drives the result and repeat clustering after complexity residualization.
- For malignant cells, also adjust for patient plus complexity and calculate within-patient silhouette summaries for adequately sized patients.
- Compare metabolic genes against at least 20 detection-matched random gene sets and a highly-variable-gene baseline.
- Evaluate cell-type separation with patient-blocked cross-validation; report balanced accuracy and macro-F1. Do not use cells from one patient in both train and test folds.
- Keep random seeds explicit. Avoid pseudoreplication and describe the observational limits of this single dataset.
- The conclusion must answer both questions directly and distinguish broad cell-identity separation from universal transcriptional metabolic states.

## Deliverables and checks

Create at least:

- `README.md`
- `TASK_STATE.md`
- `requirements.txt`
- `download_data.py`
- `analyze_metabolic_states.py`
- `data/source_manifest.json`
- `results/summary.json`
- machine-readable result tables under `results/tables/`
- at least three publication-ready figures under `results/figures/` in PDF and PNG; also provide SVG or TIFF when practical
- `report/main.tex`
- `report/references.bib`
- `report/main.pdf`

The English report must use an arXiv-compatible article layout, contain a concise abstract, introduction, methods, results, discussion, limitations, data/code availability, and references. Include numbered mathematical equations, `booktabs` three-line tables, figure captions, and source-grounded citations. Compile it and check the PDF text, page count, missing references, LaTeX errors, figure readability, and that every table value can be traced to generated result files.

For long files, create the first part with `write_file` and continue with `append_file`. Use PowerShell only for reproducible commands in the current workspace.
