# Q1 Metabolic State Analysis — README

## Delivered Files

### Scripts
- `download_data.py` — downloads 3CA study 3ca:20111 expression and metadata archives, records SHA-256 hashes and retrieval timestamps.
- `analyze_metabolic_states.py` — full analysis pipeline: feature matrix construction, PCA, k-means clustering, silhouette curves, matched random controls, patient-blocked classification, complexity residualization, and AMI computation.

### Data
- `data/source_manifest.json` — SHA-256 hashes and retrieval timestamps for expression and metadata archives.
- `results/summary.json` — all numeric results (silhouettes, AMI, balanced accuracy, etc.).
- `results/tables/` — per-panel result tables (silhouette curves, classification metrics, within-patient summaries).

### Figures
- `results/figures/figure1_dataset_and_design.pdf` (and .png, .svg, .tiff)
- `results/figures/figure2_metabolic_separation.pdf` (and .png, .svg, .tiff)
- `results/figures/figure3_robustness_and_interpretation.pdf` (and .png, .svg, .tiff)

### Report
- `report/main.tex` — arXiv-compatible LaTeX document with six sections (Introduction, Methods, Results, Figures, Discussion, Data and Code Availability).
- `report/references.bib` — 7 entries (Tirosh2016, Gavish2023, Xiao2019, Kanehisa2023, Rousseeuw1987, Hubert1985, Wu2022).
- `report/source-ledger.md` — URL, timestamp, and claim-supported entries for 3CA study detail, 3CA methods, Xiao2019, Gavish2023, Tirosh2016 PubMed.

## Dependencies

**Python** (local only, no global Codex CLI/MCP/skills):
- numpy==1.21.5
- pandas==2.0.3
- scipy==1.10.1
- scikit-learn==1.3.2
- matplotlib==3.7.5

**LaTeX** (local MiKTeX):
- `C:\Program Files\MiKTeX\miktex\bin\x64\latexmk.exe`
- `pdflatex` with `plainnat` bibliography style

## Rerun Commands

```powershell
# Download data
cd C:\Users\User\Desktop\agentic\3CA\Q1
python download_data.py

# Run analysis
python analyze_metabolic_states.py

# Compile report
cd report
"C:\Program Files\MiKTeX\miktex\bin\x64\latexmk.exe" -pdf -interaction=nonstopmode -halt-on-error main.tex
```

## Prerequisites

- Source archives (expression matrix, metadata, KEGG metabolic gene set) must be downloaded via `download_data.py` or cached locally.
- Python 3.8+ and MiKTeX installed locally.
- No global Codex CLI, MCP server, or workflow-local skills are required; all tools are local Python and LaTeX.

## Analysis Scope and Limitations

- Single-cohort reanalysis of Tirosh et al. melanoma Smart-seq2 data (19 samples, 4,645 cells).
- Metabolic genes defined by KEGG pathway membership (85 pathways, 1,360 genes after detection filtering).
- Clustering evaluated on all cells and malignant cells separately; complexity residualization and patient adjustment performed.
- Patient-blocked cross-validation uses GroupKFold5; no patient appears in both training and test folds.
- Results are exploratory; no independent validation cohort is available.
- The analysis does not measure metabolic flux; it uses transcriptional proxies.
- K-means performs forced partitioning; the choice of k does not prove discrete biological states.

## Code Reuse and Historical Edits

This analysis reuses the user-authorized standard Codex analysis script with only the raw data path adjusted. All statistics and figures were regenerated from independently downloaded raw matrices. The `methods.tex` and `results.tex` files were directly revised by the supervisor based on prior feedback. The `main.tex` structure was corrected to remove duplicate section headings and replace the manual bibliography with `plainnat` style and `references.bib`. The `figures.tex` captions were corrected to remove fabricated cell counts, remove malignant-cell k=2..8 from Figure 2c, and fix the Figure 3a caption.

## Current Status

- PDF compiled successfully (9 pages, exit code 0).
- Supervisor scientific/text/visual acceptance is still pending.
- README exists only after actual successful write.
