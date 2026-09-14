# 3CA metabolic-state analysis (Q1_R18)

This folder contains a fresh analysis of the Choudhury et al. 2022 meningioma single-cell RNA-seq dataset from the Weizmann Curated Cancer Cell Atlas (3CA), using only the genes in `../metabolic genes total.csv` for the primary embeddings and clustering.

## Reproduce

Run from PowerShell:

```powershell
py -3.12 code/analyze_metabolic_states.py
```

Then compile the report from the `report/` directory:

```powershell
latexmk -pdf -interaction=nonstopmode -halt-on-error metabolic_states_report.tex
```

The script reads the verified 3CA cache in place; it does not duplicate the 2.4 GB extracted matrix. Results are written to `results/`, figures to `figures/`, and the LaTeX source and final PDF are in `report/`.

## Analysis boundary

Clusters are unsupervised candidate transcriptional states, not validated metabolic phenotypes. Cell annotations are used only after clustering to describe associations. Cells are nested within ten samples from six patients, so cell-level association metrics are descriptive; patient-stratified summaries are provided separately.

## Headline result

- Global: a size-valid six-cluster partition exists, but its exact labels are initialization-sensitive and all 19 expression-matched random non-metabolic gene sets separated cells at least as well on the common control subsample.
- Cell type: descriptively associated with clusters, but patient, sample, and transcript complexity are comparably important competing explanations.
- CD8 T cells: no tested solution passes the 5% minimum-cluster-size rule; the apparent split is a 54-cell, patient-skewed, high-complexity outlier group.
