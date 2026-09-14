#!/usr/bin/env python
"""Test whether metabolic genes alone define separable scRNA-seq cell states."""

from __future__ import annotations

import hashlib
import json
import math
import os
import urllib.request
from pathlib import Path

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "4")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.io import mmread
from scipy.stats import spearmanr
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    adjusted_mutual_info_score,
    adjusted_rand_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    silhouette_score,
)
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "Data_Tirosh2016_Skin"
OUT = ROOT / "results"
FIG = OUT / "figures"
TABLE = OUT / "tables"
GENESET_URL = "https://raw.githubusercontent.com/wu-yc/scMetabolism/main/data/KEGG_metabolism_nc.gmt"
SEED = 20260912

PALETTE = [
    "#3B6FB6", "#D9822B", "#2A9D8F", "#B75D69", "#7A6FAC",
    "#6B8E23", "#C44E52", "#4C4C4C", "#76B7B2", "#EDC948",
]

mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 7,
        "axes.titlesize": 8,
        "axes.labelsize": 7,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "legend.frameon": False,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    }
)


def save_figure(fig: plt.Figure, stem: str) -> None:
    # Keep small labels readable after insertion into a 6.5-inch preprint column.
    for text_artist in fig.findobj(match=mpl.text.Text):
        if text_artist.get_fontsize() < 6:
            text_artist.set_fontsize(6)
    fig.savefig(FIG / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(FIG / f"{stem}.svg", bbox_inches="tight")
    fig.savefig(FIG / f"{stem}.png", dpi=400, bbox_inches="tight")
    fig.savefig(
        FIG / f"{stem}.tiff",
        dpi=600,
        bbox_inches="tight",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(fig)


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(-0.12, 1.07, label, transform=ax.transAxes, fontsize=10, fontweight="bold", va="top")


def download_genesets() -> Path:
    path = ROOT / "data" / "reference" / "KEGG_metabolism_nc.gmt"
    provenance_path = path.parent / "geneset_provenance.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        request = urllib.request.Request(GENESET_URL, headers={"User-Agent": "3CA-Q1-analysis"})
        with urllib.request.urlopen(request, timeout=60) as response:
            path.write_bytes(response.read())
        record = {
            "source_url": GENESET_URL,
            "retrieved_at": pd.Timestamp.now(tz="UTC").isoformat(),
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        provenance_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    elif not provenance_path.exists():
        raise FileNotFoundError(f"Missing provenance record for cached gene set: {provenance_path}")
    else:
        record = json.loads(provenance_path.read_text(encoding="utf-8"))
        actual = {"bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        if record.get("source_url") != GENESET_URL or any(record.get(key) != value for key, value in actual.items()):
            raise ValueError(f"Cached gene set does not match its provenance record: {path}")
    return path


def parse_gmt(path: Path) -> dict[str, list[str]]:
    pathways = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.rstrip().split("\t")
        if len(fields) >= 3:
            pathways[fields[0]] = list(dict.fromkeys(fields[2:]))
    return pathways


def load_data() -> tuple[np.ndarray, pd.DataFrame, np.ndarray]:
    cells = pd.read_csv(RAW / "Cells.csv")
    genes = pd.read_csv(RAW / "Genes.txt", sep="\t", header=None)[0].astype(str).to_numpy()
    matrix = mmread(RAW / "Exp_data_TPM.mtx").tocsr().T.astype(np.float32)
    if matrix.shape != (len(cells), len(genes)):
        raise ValueError(f"Matrix/cell/gene mismatch: {matrix.shape}, {len(cells)}, {len(genes)}")
    # The +1 pseudocount is the positivity guard specified by the 3CA transformation.
    matrix.data = np.log2(matrix.data / 10.0 + 1.0)
    return matrix, cells, genes


def feature_matrix(matrix, indices: np.ndarray) -> tuple[np.ndarray, np.ndarray, PCA]:
    dense = matrix[:, indices].toarray()
    keep = dense.var(axis=0) > 1e-8
    dense = dense[:, keep]
    scaled = StandardScaler().fit_transform(dense)
    n_components = min(50, scaled.shape[1] - 1, scaled.shape[0] - 1)
    pca = PCA(n_components=n_components, svd_solver="randomized", random_state=SEED)
    scores = pca.fit_transform(scaled)
    return scaled, scores, pca


def residualized_scores(scaled: np.ndarray, covariates: np.ndarray) -> tuple[np.ndarray, PCA]:
    covariates = np.asarray(covariates, dtype=np.float64)
    if covariates.ndim == 1:
        covariates = covariates[:, None]
    design = np.column_stack([np.ones(len(scaled)), covariates])
    residuals = scaled - design @ np.linalg.lstsq(design, scaled, rcond=None)[0]
    n_components = min(50, residuals.shape[1] - 1, residuals.shape[0] - 1)
    pca = PCA(n_components=n_components, svd_solver="randomized", random_state=SEED)
    return pca.fit_transform(residuals), pca


def silhouette_curve(scores: np.ndarray, ks=range(2, 11)) -> tuple[pd.DataFrame, np.ndarray]:
    rows = []
    best_labels = None
    best_score = -np.inf
    sample_size = min(2000, len(scores))
    for k in ks:
        labels = KMeans(n_clusters=k, n_init=20, random_state=SEED).fit_predict(scores[:, :30])
        score = silhouette_score(scores[:, :30], labels, sample_size=sample_size, random_state=SEED)
        rows.append({"k": k, "silhouette": score})
        if score > best_score:
            best_score, best_labels = score, labels
    return pd.DataFrame(rows), best_labels


def seed_stability(scores: np.ndarray, k: int) -> tuple[float, float]:
    assignments = [
        KMeans(n_clusters=k, n_init=10, random_state=SEED + i).fit_predict(scores[:, :30])
        for i in range(10)
    ]
    values = [adjusted_rand_score(assignments[i], assignments[j]) for i in range(10) for j in range(i)]
    return float(np.mean(values)), float(np.std(values, ddof=1))


def detection_matched_indices(matrix, metabolic: np.ndarray, eligible: np.ndarray, random_generator) -> np.ndarray:
    detection = np.asarray((matrix > 0).mean(axis=0)).ravel()
    edges = np.unique(np.quantile(detection[eligible], np.linspace(0, 1, 11)))
    if len(edges) < 3:
        return random_generator.choice(eligible, size=len(metabolic), replace=False)
    bins = np.digitize(detection, edges[1:-1], right=True)
    chosen = []
    available = set(eligible.tolist())
    for b in range(len(edges) - 1):
        need = int(np.sum(bins[metabolic] == b))
        candidates = np.array(sorted(i for i in available if bins[i] == b), dtype=int)
        take = min(need, len(candidates))
        if take:
            picks = random_generator.choice(candidates, size=take, replace=False).tolist()
            chosen.extend(picks)
            available.difference_update(picks)
    if len(chosen) < len(metabolic):
        extra = random_generator.choice(np.array(sorted(available)), size=len(metabolic) - len(chosen), replace=False)
        chosen.extend(extra.tolist())
    return np.array(chosen, dtype=int)


def patient_blocked_classifier(matrix, feature_idx, cells, mask) -> tuple[dict, np.ndarray, list[str]]:
    X = matrix[mask][:, feature_idx].toarray()
    y = cells.loc[mask, "cell_type"].astype(str).to_numpy()
    groups = cells.loc[mask, "sample"].astype(str).to_numpy()
    labels = sorted(np.unique(y))
    predictions = np.empty(len(y), dtype=object)
    for train, test in GroupKFold(n_splits=5).split(X, y, groups):
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X[train])
        X_test = scaler.transform(X[test])
        n_components = min(40, X_train.shape[1] - 1, X_train.shape[0] - 1)
        pca = PCA(n_components=n_components, svd_solver="randomized", random_state=SEED)
        X_train = pca.fit_transform(X_train)
        X_test = pca.transform(X_test)
        model = LogisticRegression(max_iter=2000, class_weight="balanced", C=1.0)
        model.fit(X_train, y[train])
        predictions[test] = model.predict(X_test)
    metrics = {
        "balanced_accuracy": balanced_accuracy_score(y, predictions),
        "macro_f1": f1_score(y, predictions, labels=labels, average="macro", zero_division=0),
    }
    cm = confusion_matrix(y, predictions, labels=labels, normalize="true")
    return metrics, cm, labels


def pathway_scores(scaled: np.ndarray, selected_genes: np.ndarray, pathways: dict[str, list[str]], cells) -> pd.DataFrame:
    lookup = {g: i for i, g in enumerate(selected_genes)}
    scores = {}
    for name, members in pathways.items():
        idx = [lookup[g] for g in members if g in lookup]
        if len(idx) >= 5:
            scores[name] = scaled[:, idx].mean(axis=1)
    frame = pd.DataFrame(scores)
    frame["cell_type"] = cells["cell_type"].fillna("Unannotated").to_numpy()
    return frame.groupby("cell_type").mean()


def scatter_categories(ax, x, y, categories, title, point_size=4):
    categories = pd.Series(categories).fillna("Unannotated").astype(str)
    order = categories.value_counts().index.tolist()
    for i, label in enumerate(order):
        mask = categories.eq(label).to_numpy()
        ax.scatter(x[mask], y[mask], s=point_size, alpha=0.62, color=PALETTE[i % len(PALETTE)], label=label, rasterized=True)
    ax.set_title(title, loc="left", fontweight="bold")
    ax.set_xlabel("Component 1")
    ax.set_ylabel("Component 2")
    ax.legend(markerscale=2.5, fontsize=5.8, ncol=2, handletextpad=0.3, columnspacing=0.6)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    TABLE.mkdir(parents=True, exist_ok=True)
    pathways = parse_gmt(download_genesets())
    matrix, cells, genes = load_data()
    gene_to_idx = {g: i for i, g in enumerate(genes)}
    metabolic_names = sorted(set().union(*map(set, pathways.values())) & set(genes))
    metabolic_idx = np.array([gene_to_idx[g] for g in metabolic_names], dtype=int)
    detection = np.asarray((matrix > 0).mean(axis=0)).ravel()
    metabolic_idx = metabolic_idx[detection[metabolic_idx] >= 0.01]
    metabolic_names = genes[metabolic_idx]

    scaled, scores, pca = feature_matrix(matrix, metabolic_idx)
    curve, clusters = silhouette_curve(scores)
    best_row = curve.loc[curve["silhouette"].idxmax()]
    best_k = int(best_row["k"])
    best_silhouette = float(best_row["silhouette"])
    stability_mean, stability_sd = seed_stability(scores, best_k)
    cells["metabolic_cluster"] = clusters + 1
    annotated = cells["cell_type"].notna().to_numpy()

    eligible = np.flatnonzero((detection >= 0.01) & ~np.isin(np.arange(len(genes)), metabolic_idx))
    random_generator = np.random.Generator(np.random.PCG64(SEED))
    random_rows = []
    random_sets = []
    for replicate in range(20):
        idx = detection_matched_indices(matrix, metabolic_idx, eligible, random_generator)
        random_sets.append(idx)
        _, random_scores, _ = feature_matrix(matrix, idx)
        random_curve, _ = silhouette_curve(random_scores)
        random_rows.append({"replicate": replicate + 1, "max_silhouette": random_curve["silhouette"].max()})
    random_results = pd.DataFrame(random_rows)
    random_p = (1 + np.sum(random_results["max_silhouette"] >= best_silhouette)) / (len(random_results) + 1)

    classifier_metrics, cm, cm_labels = patient_blocked_classifier(matrix, metabolic_idx, cells, annotated)
    random_classifier_rows = []
    for replicate, idx in enumerate(random_sets, start=1):
        metrics, _, _ = patient_blocked_classifier(matrix, idx, cells, annotated)
        random_classifier_rows.append({"replicate": replicate, **metrics})
    random_classifier_results = pd.DataFrame(random_classifier_rows)

    variances = np.asarray(matrix.power(2).mean(axis=0)).ravel() - np.asarray(matrix.mean(axis=0)).ravel() ** 2
    hvg_idx = np.argsort(variances)[-len(metabolic_idx):]
    hvg_classifier, _, _ = patient_blocked_classifier(matrix, hvg_idx, cells, annotated)

    ami_cell_type = adjusted_mutual_info_score(cells.loc[annotated, "cell_type"], clusters[annotated])
    ami_sample = adjusted_mutual_info_score(cells["sample"].astype(str), clusters)
    rho_complexity, p_complexity = spearmanr(scores[:, 0], np.log1p(cells["complexity"].to_numpy()))
    complexity = StandardScaler().fit_transform(np.log1p(cells[["complexity"]].to_numpy()))
    adjusted_scores, _ = residualized_scores(scaled, complexity)
    adjusted_curve, _ = silhouette_curve(adjusted_scores)
    adjusted_best = adjusted_curve.loc[adjusted_curve["silhouette"].idxmax()]
    adjusted_stability_mean, adjusted_stability_sd = seed_stability(adjusted_scores, int(adjusted_best["k"]))

    malignant = cells["cell_type"].eq("Malignant").to_numpy()
    mal_scaled, mal_scores, _ = feature_matrix(matrix[malignant], metabolic_idx)
    mal_curve, mal_clusters = silhouette_curve(mal_scores, range(2, 9))
    mal_best = mal_curve.loc[mal_curve["silhouette"].idxmax()]
    mal_stability_mean, mal_stability_sd = seed_stability(mal_scores, int(mal_best["k"]))
    mal_samples = cells.loc[malignant, "sample"].astype(str).to_numpy()
    mal_ami_sample = adjusted_mutual_info_score(mal_samples, mal_clusters)
    sample_dummies = pd.get_dummies(pd.Series(mal_samples), drop_first=True, dtype=float).to_numpy()
    mal_complexity = StandardScaler().fit_transform(
        np.log1p(cells.loc[malignant, ["complexity"]].to_numpy())
    )
    mal_adjusted_scores, _ = residualized_scores(
        mal_scaled, np.column_stack([sample_dummies, mal_complexity])
    )
    mal_adjusted_curve, _ = silhouette_curve(mal_adjusted_scores, range(2, 9))
    mal_adjusted_best = mal_adjusted_curve.loc[mal_adjusted_curve["silhouette"].idxmax()]
    mal_adjusted_stability_mean, mal_adjusted_stability_sd = seed_stability(
        mal_adjusted_scores, int(mal_adjusted_best["k"])
    )
    per_patient = []
    for sample, count in pd.Series(mal_samples).value_counts().items():
        if count >= 30:
            mask = mal_samples == sample
            patient_curve, _ = silhouette_curve(mal_scores[mask], range(2, min(7, count - 1)))
            per_patient.append({"sample": sample, "n_malignant_cells": int(count), "max_silhouette": patient_curve["silhouette"].max()})
    per_patient = pd.DataFrame(per_patient)

    pathway_by_type = pathway_scores(scaled, metabolic_names, pathways, cells)
    pathway_z = pathway_by_type.sub(pathway_by_type.mean()).div(pathway_by_type.std(ddof=0).replace(0, np.nan))
    top_pathways = pathway_z.var(axis=0).nlargest(18).index
    pathway_z = pathway_z[top_pathways]

    summary = {
        "dataset": {
            "cells": int(matrix.shape[0]),
            "genes": int(matrix.shape[1]),
            "nonzero_entries": int(matrix.nnz),
            "samples": int(cells["sample"].nunique()),
            "annotated_cells": int(annotated.sum()),
            "malignant_cells": int(malignant.sum()),
        },
        "metabolic_features": {
            "kegg_pathways": len(pathways),
            "unique_genes_in_dataset_after_detection_filter": len(metabolic_idx),
            "pca_variance_30_components": float(pca.explained_variance_ratio_[:30].sum()),
        },
        "all_cells_clustering": {
            "selected_k": best_k,
            "silhouette": best_silhouette,
            "seed_stability_ari_mean": stability_mean,
            "seed_stability_ari_sd": stability_sd,
            "matched_random_mean": float(random_results["max_silhouette"].mean()),
            "matched_random_sd": float(random_results["max_silhouette"].std(ddof=1)),
            "empirical_p": float(random_p),
            "ami_cell_type": float(ami_cell_type),
            "ami_sample": float(ami_sample),
            "pc1_complexity_spearman_rho": float(rho_complexity),
            "pc1_complexity_p": float(p_complexity),
            "complexity_adjusted_selected_k": int(adjusted_best["k"]),
            "complexity_adjusted_silhouette": float(adjusted_best["silhouette"]),
            "complexity_adjusted_seed_stability_ari_mean": adjusted_stability_mean,
            "complexity_adjusted_seed_stability_ari_sd": adjusted_stability_sd,
        },
        "patient_blocked_cell_type_classification": {
            "metabolic_balanced_accuracy": float(classifier_metrics["balanced_accuracy"]),
            "metabolic_macro_f1": float(classifier_metrics["macro_f1"]),
            "matched_random_balanced_accuracy_mean": float(random_classifier_results["balanced_accuracy"].mean()),
            "matched_random_balanced_accuracy_sd": float(random_classifier_results["balanced_accuracy"].std(ddof=1)),
            "matched_random_macro_f1_mean": float(random_classifier_results["macro_f1"].mean()),
            "matched_random_macro_f1_sd": float(random_classifier_results["macro_f1"].std(ddof=1)),
            "hvg_balanced_accuracy": float(hvg_classifier["balanced_accuracy"]),
            "hvg_macro_f1": float(hvg_classifier["macro_f1"]),
        },
        "malignant_cells_clustering": {
            "cells": int(malignant.sum()),
            "samples": int(pd.Series(mal_samples).nunique()),
            "selected_k": int(mal_best["k"]),
            "silhouette": float(mal_best["silhouette"]),
            "seed_stability_ari_mean": mal_stability_mean,
            "seed_stability_ari_sd": mal_stability_sd,
            "ami_sample": float(mal_ami_sample),
            "patient_and_complexity_adjusted_selected_k": int(mal_adjusted_best["k"]),
            "patient_and_complexity_adjusted_silhouette": float(mal_adjusted_best["silhouette"]),
            "patient_and_complexity_adjusted_seed_stability_ari_mean": mal_adjusted_stability_mean,
            "patient_and_complexity_adjusted_seed_stability_ari_sd": mal_adjusted_stability_sd,
            "within_patient_median_max_silhouette": float(per_patient["max_silhouette"].median()),
            "within_patient_iqr": [
                float(per_patient["max_silhouette"].quantile(0.25)),
                float(per_patient["max_silhouette"].quantile(0.75)),
            ],
            "patients_with_at_least_30_cells": int(len(per_patient)),
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    curve.to_csv(TABLE / "silhouette_all_cells.csv", index=False)
    mal_curve.to_csv(TABLE / "silhouette_malignant_cells.csv", index=False)
    adjusted_curve.to_csv(TABLE / "silhouette_complexity_adjusted_all_cells.csv", index=False)
    mal_adjusted_curve.to_csv(TABLE / "silhouette_patient_complexity_adjusted_malignant.csv", index=False)
    random_results.to_csv(TABLE / "matched_random_gene_sets.csv", index=False)
    random_classifier_results.to_csv(TABLE / "matched_random_classification.csv", index=False)
    per_patient.to_csv(TABLE / "within_patient_malignant_clustering.csv", index=False)
    cells.to_csv(TABLE / "cell_assignments.csv", index=False)
    pathway_by_type.to_csv(TABLE / "pathway_scores_by_cell_type.csv")

    assert matrix.shape == (4645, 23686)
    assert len(metabolic_idx) == 1360
    assert np.isfinite([best_silhouette, classifier_metrics["balanced_accuracy"], float(mal_best["silhouette"])]).all()

    counts = cells["cell_type"].fillna("Unannotated").value_counts().sort_values()
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 6.4), constrained_layout=True)
    ax = axes[0, 0]
    boxes = [(0.02, "3CA matrix\n23,686 genes"), (0.27, "1,360 KEGG\ngenes"), (0.52, "PCA + K-means"), (0.77, "Patient-held-out\nvalidation")]
    for x, label in boxes:
        ax.add_patch(plt.Rectangle((x, 0.36), 0.19, 0.28, facecolor="#E9F0F8", edgecolor="#3B6FB6", lw=0.8))
        ax.text(x + 0.095, 0.50, label, ha="center", va="center", fontsize=5.6)
    for x in (0.22, 0.47, 0.72):
        ax.annotate("", xy=(x + 0.04, 0.50), xytext=(x, 0.50), arrowprops={"arrowstyle": "->", "lw": 1, "color": "#4C4C4C"})
    ax.set_axis_off(); ax.set_title("Analysis design", loc="left", fontweight="bold"); panel_label(ax, "a")
    ax = axes[0, 1]
    ax.barh(counts.index, counts.values, color="#6A8EAE")
    for y, value in enumerate(counts.values): ax.text(value + 20, y, f"{value:,}", va="center", fontsize=6)
    ax.set_xlabel("Cells"); ax.set_title("Cell annotations", loc="left", fontweight="bold"); panel_label(ax, "b")
    ax = axes[1, 0]
    scatter_categories(ax, cells["umap1"], cells["umap2"], cells["cell_type"], "3CA whole-transcriptome UMAP")
    ax.set_xlabel("UMAP 1"); ax.set_ylabel("UMAP 2"); panel_label(ax, "c")
    ax = axes[1, 1]; ax.set_axis_off(); panel_label(ax, "d")
    facts = [
        ("Study", "Tirosh et al. 2016"), ("Technology", "Smart-seq2"),
        ("Samples", f"{cells['sample'].nunique()} patients"), ("Cells", f"{len(cells):,}"),
        ("Annotated", f"{annotated.sum():,}"), ("Metabolic genes", f"{len(metabolic_idx):,}"),
        ("KEGG pathways", f"{len(pathways)}"), ("Primary unit", "patient for generalization"),
    ]
    ax.set_title("Study and analysis scope", loc="left", fontweight="bold")
    for i, (key, value) in enumerate(facts):
        y = 0.91 - i * 0.105
        ax.text(0.02, y, key, color="#555555", fontsize=6.5)
        ax.text(0.47, y, value, color="#111111", fontsize=6.8, fontweight="bold")
    save_figure(fig, "figure1_dataset_and_design")

    fig, axes = plt.subplots(2, 2, figsize=(7.2, 6.4), constrained_layout=True)
    scatter_categories(axes[0, 0], scores[:, 0], scores[:, 1], cells["cell_type"], "Metabolic-gene PCA by cell type")
    panel_label(axes[0, 0], "a")
    scatter_categories(axes[0, 1], scores[:, 0], scores[:, 1], cells["metabolic_cluster"].map(lambda x: f"Cluster {x}"), f"K-means solution (k = {best_k})")
    panel_label(axes[0, 1], "b")
    ax = axes[1, 0]
    ax.plot(curve["k"], curve["silhouette"], marker="o", color="#3B6FB6", label="Metabolic genes")
    ax.plot(adjusted_curve["k"], adjusted_curve["silhouette"], marker="s", color="#2A9D8F", label="After complexity adjustment")
    ax.fill_between(
        curve["k"],
        random_results["max_silhouette"].quantile(0.025),
        random_results["max_silhouette"].quantile(0.975),
        color="#B7B7B7",
        alpha=0.35,
        label="Random-set max, 95% range",
    )
    ax.axhline(random_results["max_silhouette"].mean(), color="#666666", ls="--", lw=1)
    ax.set_xlabel("Number of clusters, k"); ax.set_ylabel("Mean silhouette")
    ax.set_title("Cluster separation and matched-gene baseline", loc="left", fontweight="bold")
    ax.legend(fontsize=6); panel_label(ax, "c")
    ax = axes[1, 1]
    image = ax.imshow(cm, vmin=0, vmax=1, cmap="Blues")
    ax.set_xticks(range(len(cm_labels)), cm_labels, rotation=45, ha="right", rotation_mode="anchor", fontsize=5.5)
    ax.set_yticks(range(len(cm_labels)), cm_labels, fontsize=5.5)
    ax.set_xlabel("Predicted"); ax.set_ylabel("Observed")
    ax.set_title("Held-out-patient cell-type classification", loc="left", fontweight="bold")
    for i in range(len(cm_labels)):
        for j in range(len(cm_labels)):
            ax.text(j, i, f"{cm[i,j]:.2f}", ha="center", va="center", fontsize=5.2, color="white" if cm[i,j] > 0.55 else "#222222")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="Row proportion")
    panel_label(ax, "d")
    save_figure(fig, "figure2_metabolic_separation")

    fig = plt.figure(figsize=(7.2, 8.4), constrained_layout=True)
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 0.85, 1.25])
    ax = fig.add_subplot(gs[0, 0])
    ax.scatter(np.ones(len(random_results)), random_results["max_silhouette"], s=18, color="#A7A7A7", alpha=0.8, label="Matched random")
    ax.scatter([1], [best_silhouette], s=55, color="#C44E52", marker="D", label="Metabolic")
    ax.set_xlim(0.75, 1.25); ax.set_xticks([1], ["Gene sets"]); ax.set_ylabel("Maximum silhouette")
    ax.set_title(f"Specificity (empirical p = {random_p:.3f})", loc="left", fontweight="bold"); ax.legend(fontsize=5.8); panel_label(ax, "a")
    ax = fig.add_subplot(gs[0, 1])
    scatter_categories(ax, mal_scores[:, 0], mal_scores[:, 1], mal_samples, "Malignant cells by patient", point_size=6)
    ax.legend(fontsize=5.2, ncol=3, markerscale=1.8); panel_label(ax, "b")
    ax = fig.add_subplot(gs[1, 0])
    ax.plot(mal_curve["k"], mal_curve["silhouette"], marker="o", color="#B75D69", label="Observed")
    ax.plot(mal_adjusted_curve["k"], mal_adjusted_curve["silhouette"], marker="s", color="#2A9D8F", label="Patient + complexity adjusted")
    ax.set_xlabel("Number of clusters, k"); ax.set_ylabel("Mean silhouette")
    ax.set_title("Malignant-cell separation", loc="left", fontweight="bold"); ax.legend(fontsize=5.5); panel_label(ax, "c")
    ax = fig.add_subplot(gs[2, :])
    heat = ax.imshow(pathway_z.T, aspect="auto", cmap="RdBu_r", vmin=-2, vmax=2)
    ax.set_xticks(range(len(pathway_z.index)), pathway_z.index, rotation=45, ha="right", rotation_mode="anchor", fontsize=5.5)
    clean_names = [name.replace("KEGG_", "").replace("_", " ").title() for name in pathway_z.columns]
    ax.set_yticks(range(len(clean_names)), clean_names, fontsize=5.3)
    ax.set_title("Cell-type mean metabolic pathway scores", loc="left", fontweight="bold")
    fig.colorbar(heat, ax=ax, fraction=0.03, pad=0.02, label="Across-type z-score"); panel_label(ax, "d")
    ax = fig.add_subplot(gs[1, 1])
    names = ["Cell type", "Patient", "Malignant:\npatient"]
    values = [ami_cell_type, ami_sample, mal_ami_sample]
    ax.barh(names, values, color=["#3B6FB6", "#D9822B", "#B75D69"])
    for i, value in enumerate(values): ax.text(value + 0.01, i, f"{value:.2f}", va="center", fontsize=6)
    ax.set_xlim(0, max(0.55, max(values) + 0.1)); ax.set_xlabel("Adjusted mutual information")
    ax.set_title("What the clusters track", loc="left", fontweight="bold"); panel_label(ax, "e")
    save_figure(fig, "figure3_robustness_and_interpretation")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
