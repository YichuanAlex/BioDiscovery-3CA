"""Reproducible metabolic-gene-only clustering of one verified 3CA dataset."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import scipy.sparse as sp
import seaborn as sns
import sklearn
from scipy.io import mmread
from sklearn.cluster import KMeans, MiniBatchKMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (
    adjusted_mutual_info_score,
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    normalized_mutual_info_score,
    silhouette_score,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = Path(
    r"C:\Users\User\.agents\cache\threeca\downloads\b4d828443422"
    r"\Data_Choudhury2022_Brain.extracted\Data_Choudhury2022_Brain"
)
DEFAULT_GENES = ROOT.parent / "metabolic genes total.csv"
SEEDS = (0, 17, 42, 73, 101)
METRIC_SEED = 7321
CONTROL_REPLICATES = 19
MIN_CLUSTER_FRACTION = 0.05


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_symbols(values: pd.Series) -> pd.Series:
    return values.astype(str).str.strip().str.upper()


def normalize_and_scale(
    counts_gxc: sp.csr_matrix,
    gene_indices: np.ndarray,
    cell_indices: np.ndarray,
    library_sizes: np.ndarray,
) -> tuple[sp.csr_matrix, np.ndarray]:
    counts = counts_gxc[gene_indices][:, cell_indices].T.tocsr().astype(np.float32)
    factors = np.divide(
        10_000.0,
        library_sizes[cell_indices],
        out=np.zeros(len(cell_indices), dtype=np.float32),
        where=library_sizes[cell_indices] > 0,
    )
    logged = sp.diags(factors).dot(counts).tocsr()
    logged.data = np.log1p(logged.data)
    scaled = logged.toarray()
    means = scaled.mean(axis=0, dtype=np.float64).astype(np.float32)
    sds = scaled.std(axis=0, dtype=np.float64).astype(np.float32)
    sds[sds == 0] = 1.0
    scaled -= means
    scaled /= sds
    np.clip(scaled, -10.0, 10.0, out=scaled)
    return logged, scaled


def cluster_model(n_cells: int, k: int, seed: int):
    if n_cells >= 10_000:
        return MiniBatchKMeans(
            n_clusters=k,
            random_state=seed,
            n_init=20,
            batch_size=4096,
            max_iter=300,
        )
    return KMeans(n_clusters=k, random_state=seed, n_init=20, max_iter=500)


def pca_embedding(scaled: np.ndarray, seed: int, n_components: int = 30):
    n_components = max(2, min(n_components, scaled.shape[0] - 1, scaled.shape[1] - 1))
    model = PCA(n_components=n_components, svd_solver="randomized", random_state=seed)
    return model.fit_transform(scaled).astype(np.float32), model


def metric_subset(n_cells: int, limit: int, seed: int = METRIC_SEED) -> np.ndarray:
    if n_cells <= limit:
        return np.arange(n_cells)
    return np.sort(np.random.default_rng(seed).choice(n_cells, size=limit, replace=False))


def k_sweep(pcs: np.ndarray, ks: range, metric_limit: int) -> tuple[pd.DataFrame, int, bool, int]:
    idx = metric_subset(len(pcs), metric_limit)
    rows = []
    for k in ks:
        labels = cluster_model(len(pcs), k, SEEDS[0]).fit_predict(pcs)
        local_labels = labels[idx]
        sizes = np.bincount(labels, minlength=k)
        rows.append(
            {
                "k": k,
                "silhouette": float(silhouette_score(pcs[idx], local_labels)),
                "calinski_harabasz": float(calinski_harabasz_score(pcs[idx], local_labels)),
                "davies_bouldin": float(davies_bouldin_score(pcs[idx], local_labels)),
                "min_cluster_cells": int(sizes.min()),
                "min_cluster_fraction": float(sizes.min() / len(labels)),
            }
        )
    frame = pd.DataFrame(rows)
    unconstrained_k = int(frame.loc[frame["silhouette"].idxmax(), "k"])
    eligible = frame[frame["min_cluster_fraction"] >= MIN_CLUSTER_FRACTION]
    passes = not eligible.empty
    selected_k = int(
        (eligible if passes else frame).loc[
            (eligible if passes else frame)["silhouette"].idxmax(), "k"
        ]
    )
    return frame, selected_k, passes, unconstrained_k


def cluster_stability(pcs: np.ndarray, k: int) -> tuple[np.ndarray, pd.DataFrame]:
    reference = cluster_model(len(pcs), k, SEEDS[0]).fit_predict(pcs)
    rows = [{"seed": SEEDS[0], "ari_vs_seed_0": 1.0}]
    for seed in SEEDS[1:]:
        labels = cluster_model(len(pcs), k, seed).fit_predict(pcs)
        rows.append({"seed": seed, "ari_vs_seed_0": adjusted_rand_score(reference, labels)})
    return reference, pd.DataFrame(rows)


def matched_random_set(
    target: np.ndarray,
    eligible: np.ndarray,
    prevalence: np.ndarray,
    mean_counts: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    basis = eligible
    prev_edges = np.unique(np.quantile(np.log1p(prevalence[basis]), np.linspace(0, 1, 5)))
    mean_edges = np.unique(np.quantile(np.log1p(mean_counts[basis]), np.linspace(0, 1, 5)))

    def bins(indices: np.ndarray) -> np.ndarray:
        p = np.digitize(np.log1p(prevalence[indices]), prev_edges[1:-1], right=True)
        m = np.digitize(np.log1p(mean_counts[indices]), mean_edges[1:-1], right=True)
        return p * 4 + m

    target_bins = bins(target)
    eligible_bins = bins(eligible)
    chosen: list[int] = []
    used: set[int] = set()
    for bin_id, required in zip(*np.unique(target_bins, return_counts=True)):
        candidates = eligible[eligible_bins == bin_id]
        candidates = np.array([value for value in candidates if int(value) not in used])
        take = min(int(required), len(candidates))
        if take:
            selected = rng.choice(candidates, size=take, replace=False)
            chosen.extend(int(value) for value in selected)
            used.update(int(value) for value in selected)
    remaining = len(target) - len(chosen)
    if remaining:
        pool = np.array([value for value in eligible if int(value) not in used])
        chosen.extend(int(value) for value in rng.choice(pool, size=remaining, replace=False))
    return np.asarray(chosen, dtype=int)


def control_score(
    counts_gxc: sp.csr_matrix,
    genes: np.ndarray,
    cells: np.ndarray,
    library_sizes: np.ndarray,
    k: int,
    seed: int,
) -> float:
    _, scaled = normalize_and_scale(counts_gxc, genes, cells, library_sizes)
    pcs, _ = pca_embedding(scaled, seed, n_components=20)
    labels = cluster_model(len(pcs), k, seed).fit_predict(pcs)
    return float(silhouette_score(pcs, labels))


def random_controls(
    counts_gxc: sp.csr_matrix,
    target_genes: np.ndarray,
    cells: np.ndarray,
    library_sizes: np.ndarray,
    prevalence: np.ndarray,
    mean_counts: np.ndarray,
    all_gene_names: np.ndarray,
    k: int,
    sample_limit: int,
) -> tuple[float, pd.DataFrame, float]:
    local = metric_subset(len(cells), sample_limit)
    metric_cells = cells[local]
    observed = control_score(
        counts_gxc, target_genes, metric_cells, library_sizes, k, METRIC_SEED
    )
    target_set = set(int(value) for value in target_genes)
    names = np.char.upper(all_gene_names.astype(str))
    technical = np.char.startswith(names, "MT-") | np.char.startswith(names, "RPL") | np.char.startswith(names, "RPS")
    eligible = np.array(
        [
            idx
            for idx in np.flatnonzero(prevalence >= max(10, int(np.ceil(0.01 * len(cells)))))
            if int(idx) not in target_set and not technical[idx]
        ],
        dtype=int,
    )
    rng = np.random.default_rng(METRIC_SEED)
    rows = []
    for replicate in range(CONTROL_REPLICATES):
        random_genes = matched_random_set(
            target_genes, eligible, prevalence, mean_counts, rng
        )
        score = control_score(
            counts_gxc,
            random_genes,
            metric_cells,
            library_sizes,
            k,
            10_000 + replicate,
        )
        rows.append({"replicate": replicate + 1, "silhouette": score})
    frame = pd.DataFrame(rows)
    exceed = int((frame["silhouette"] >= observed).sum())
    empirical_p = (exceed + 1) / (CONTROL_REPLICATES + 1)
    return observed, frame, empirical_p


def top_genes(logged: sp.csr_matrix, labels: np.ndarray, names: np.ndarray, n: int = 12):
    rows = []
    for cluster in sorted(np.unique(labels)):
        inside = labels == cluster
        outside = ~inside
        mean_in = np.asarray(logged[inside].mean(axis=0)).ravel()
        mean_out = np.asarray(logged[outside].mean(axis=0)).ravel()
        delta = mean_in - mean_out
        for idx in np.argsort(delta)[::-1][:n]:
            rows.append(
                {
                    "cluster": int(cluster),
                    "gene": str(names[idx]),
                    "mean_log1p_in": float(mean_in[idx]),
                    "mean_log1p_out": float(mean_out[idx]),
                    "mean_log1p_difference": float(delta[idx]),
                }
            )
    return pd.DataFrame(rows)


def annotation_metrics(labels: np.ndarray, metadata: pd.DataFrame) -> dict:
    metrics = {}
    for column in ("cell_type", "cell_subtype", "patient", "sample", "source"):
        values = metadata[column].fillna("Missing").astype(str).to_numpy()
        metrics[column] = {
            "nmi": float(normalized_mutual_info_score(labels, values)),
            "ami": float(adjusted_mutual_info_score(labels, values)),
        }
    per_patient = []
    for patient, index in metadata.groupby("patient", sort=True).groups.items():
        positions = metadata.index.get_indexer(index)
        local_types = metadata.loc[index, "cell_type"].fillna("Missing").astype(str)
        local_labels = labels[positions]
        if len(np.unique(local_labels)) > 1 and local_types.nunique() > 1:
            per_patient.append(
                {
                    "patient": str(patient),
                    "n_cells": len(index),
                    "cluster_cell_type_nmi": float(
                        normalized_mutual_info_score(local_labels, local_types)
                    ),
                }
            )
    metrics["per_patient_cell_type"] = per_patient
    return metrics


def save_embedding(path: Path, pcs: np.ndarray, labels: np.ndarray, metadata: pd.DataFrame, title: str):
    display = metric_subset(len(pcs), 25_000)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    scatter = axes[0].scatter(
        pcs[display, 0], pcs[display, 1], c=labels[display], s=4, alpha=0.55, cmap="tab20"
    )
    axes[0].set_title(f"{title}: metabolic clusters")
    axes[0].set_xlabel("Metabolic PC1")
    axes[0].set_ylabel("Metabolic PC2")
    legend = axes[0].legend(*scatter.legend_elements(), title="Cluster", loc="best", fontsize=7)
    axes[0].add_artist(legend)
    categories = metadata["cell_type"].fillna("Missing").astype("category")
    category_colors = plt.cm.tab10(np.arange(len(categories.cat.categories)) % 10)
    axes[1].scatter(
        pcs[display, 0],
        pcs[display, 1],
        c=category_colors[categories.cat.codes.to_numpy()[display]],
        s=4,
        alpha=0.55,
    )
    handles = [
        plt.Line2D([0], [0], marker="o", linestyle="", color=category_colors[i], label=value)
        for i, value in enumerate(categories.cat.categories)
    ]
    axes[1].legend(handles=handles, title="3CA cell type", fontsize=7, loc="best")
    axes[1].set_title(f"{title}: post hoc cell types")
    axes[1].set_xlabel("Metabolic PC1")
    axes[1].set_ylabel("Metabolic PC2")
    fig.savefig(path, dpi=220)
    plt.close(fig)


def save_evidence_figure(
    path: Path,
    sweep: pd.DataFrame,
    selected_k: int,
    observed_control: float,
    controls: pd.DataFrame,
    composition: pd.DataFrame,
    composition_group: str,
    title: str,
):
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5), constrained_layout=True)
    valid = sweep["min_cluster_fraction"] >= MIN_CLUSTER_FRACTION
    axes[0].plot(sweep["k"], sweep["silhouette"], color="0.75", linewidth=1)
    axes[0].scatter(sweep.loc[valid, "k"], sweep.loc[valid, "silhouette"], label=r"all clusters $\geq$5%")
    axes[0].scatter(sweep.loc[~valid, "k"], sweep.loc[~valid, "silhouette"], marker="x", color="0.45", label="fails 5% rule")
    axes[0].axvline(selected_k, color="tab:red", linestyle="--", label=f"selected k={selected_k}")
    axes[0].set(xlabel="k", ylabel="Silhouette score", title="Prespecified k sweep")
    axes[0].legend(fontsize=8)
    axes[1].scatter(controls["replicate"], controls["silhouette"], color="0.45", s=28)
    axes[1].axhline(observed_control, color="tab:red", label="metabolic genes")
    axes[1].set(xlabel="Matched random-gene replicate", ylabel="Silhouette score", title="Gene-set specificity control")
    axes[1].legend(fontsize=8)
    sns.heatmap(composition, cmap="viridis", vmin=0, vmax=1, ax=axes[2], cbar_kws={"label": "Within-cluster fraction"})
    axes[2].set_title(f"Post hoc {composition_group} composition")
    axes[2].set_xlabel(composition_group.capitalize())
    axes[2].set_ylabel("Metabolic cluster")
    fig.suptitle(title)
    fig.savefig(path, dpi=220)
    plt.close(fig)


def save_signature_heatmap(path: Path, logged: sp.csr_matrix, labels: np.ndarray, genes: np.ndarray, markers: pd.DataFrame, title: str):
    selected = markers.groupby("cluster", sort=True).head(4)["gene"].drop_duplicates().tolist()
    lookup = {gene: idx for idx, gene in enumerate(genes)}
    indices = [lookup[gene] for gene in selected]
    cluster_means = []
    for cluster in sorted(np.unique(labels)):
        cluster_means.append(np.asarray(logged[labels == cluster][:, indices].mean(axis=0)).ravel())
    matrix = np.asarray(cluster_means).T
    matrix = (matrix - matrix.mean(axis=1, keepdims=True)) / np.where(
        matrix.std(axis=1, keepdims=True) == 0, 1, matrix.std(axis=1, keepdims=True)
    )
    fig_height = max(5, 0.22 * len(selected))
    fig, ax = plt.subplots(figsize=(8, fig_height), constrained_layout=True)
    sns.heatmap(
        matrix,
        cmap="vlag",
        center=0,
        yticklabels=selected,
        xticklabels=[f"C{value}" for value in sorted(np.unique(labels))],
        ax=ax,
        cbar_kws={"label": "Row z-score of mean log1p expression"},
    )
    ax.set_title(title)
    ax.set_xlabel("Metabolic cluster")
    ax.set_ylabel("Descriptive top metabolic genes")
    fig.savefig(path, dpi=220)
    plt.close(fig)


def analyse_scope(
    scope: str,
    counts: sp.csr_matrix,
    all_genes: np.ndarray,
    user_gene_indices: np.ndarray,
    cell_indices: np.ndarray,
    metadata: pd.DataFrame,
    library_sizes: np.ndarray,
    prevalence_all: np.ndarray,
    mean_all: np.ndarray,
    ks: range,
    metric_limit: int,
    control_limit: int,
    results_dir: Path,
    figures_dir: Path,
) -> dict:
    min_cells = max(20, int(np.ceil(0.01 * len(cell_indices))))
    if len(cell_indices) == counts.shape[1]:
        local_prevalence = prevalence_all
        local_mean = mean_all
    else:
        subset = counts[:, cell_indices]
        local_prevalence = np.asarray(subset.getnnz(axis=1)).ravel()
        local_mean = np.asarray(subset.sum(axis=1)).ravel() / len(cell_indices)
        del subset
    retained = user_gene_indices[local_prevalence[user_gene_indices] >= min_cells]
    logged, scaled = normalize_and_scale(counts, retained, cell_indices, library_sizes)
    pcs, pca = pca_embedding(scaled, SEEDS[0])
    del scaled
    gc.collect()
    sweep, selected_k, passes_size_floor, unconstrained_k = k_sweep(pcs, ks, metric_limit)
    labels, stability = cluster_stability(pcs, selected_k)
    markers = top_genes(logged, labels, all_genes[retained])
    scope_metadata = metadata.iloc[cell_indices].copy().reset_index(drop=True)
    composition_counts = pd.crosstab(labels, scope_metadata["cell_type"], dropna=False)
    composition = composition_counts.div(composition_counts.sum(axis=1), axis=0)
    evidence_group = "patient" if scope == "cd8" else "cell type"
    evidence_values = scope_metadata["patient"].astype(str) if scope == "cd8" else scope_metadata["cell_type"]
    evidence_counts = pd.crosstab(labels, evidence_values, dropna=False)
    evidence_composition = evidence_counts.div(evidence_counts.sum(axis=1), axis=0)
    annotations = annotation_metrics(labels, scope_metadata)
    observed_control, controls, empirical_p = random_controls(
        counts,
        retained,
        cell_indices,
        library_sizes,
        local_prevalence,
        local_mean,
        all_genes,
        selected_k,
        control_limit,
    )
    cluster_sizes = pd.Series(labels).value_counts().sort_index().rename_axis("cluster").rename("n_cells").reset_index()
    diagnostic_frame = scope_metadata.assign(cluster=labels).groupby("cluster", sort=True).agg(
        n_cells=("cell_name", "size"),
        median_complexity=("complexity", "median"),
        mean_complexity=("complexity", "mean"),
        n_patients=("patient", "nunique"),
        n_samples=("sample", "nunique"),
    ).reset_index()
    sweep.to_csv(results_dir / f"{scope}_k_sweep.csv", index=False)
    stability.to_csv(results_dir / f"{scope}_stability.csv", index=False)
    controls.to_csv(results_dir / f"{scope}_matched_random_controls.csv", index=False)
    markers.to_csv(results_dir / f"{scope}_top_genes.csv", index=False)
    composition_counts.to_csv(results_dir / f"{scope}_cluster_cell_type_counts.csv")
    composition.to_csv(results_dir / f"{scope}_cluster_cell_type_fractions.csv")
    cluster_sizes.to_csv(results_dir / f"{scope}_cluster_sizes.csv", index=False)
    diagnostic_frame.to_csv(results_dir / f"{scope}_cluster_diagnostics.csv", index=False)
    pd.DataFrame({"cell_name": scope_metadata["cell_name"], "cluster": labels}).to_csv(
        results_dir / f"{scope}_cell_clusters.csv", index=False
    )
    save_embedding(figures_dir / f"{scope}_embedding.png", pcs, labels, scope_metadata, scope.upper())
    save_evidence_figure(
        figures_dir / f"{scope}_evidence.png",
        sweep,
        selected_k,
        observed_control,
        controls,
        evidence_composition,
        evidence_group,
        scope.upper(),
    )
    save_signature_heatmap(
        figures_dir / f"{scope}_signatures.png",
        logged,
        labels,
        all_genes[retained],
        markers,
        f"{scope.upper()} candidate metabolic-state signatures",
    )
    cluster_patient = pd.crosstab(scope_metadata["patient"], labels)
    cluster_patient.to_csv(results_dir / f"{scope}_patient_cluster_counts.csv")
    cluster_patient_fractions = cluster_patient.div(cluster_patient.sum(axis=1), axis=0)
    cluster_patient_fractions.to_csv(results_dir / f"{scope}_patient_cluster_fractions.csv")
    patient_multistate = int(((cluster_patient_fractions >= 0.05).sum(axis=1) >= 2).sum())
    return {
        "scope": scope,
        "n_cells": int(len(cell_indices)),
        "n_patients": int(scope_metadata["patient"].nunique()),
        "n_samples": int(scope_metadata["sample"].nunique()),
        "min_expression_cells": int(min_cells),
        "n_metabolic_genes_retained": int(len(retained)),
        "selected_k": int(selected_k),
        "unconstrained_best_k": int(unconstrained_k),
        "selected_solution_meets_min_cluster_fraction": bool(passes_size_floor),
        "minimum_cluster_fraction_rule": MIN_CLUSTER_FRACTION,
        "silhouette_selected_k": float(sweep.loc[sweep["k"] == selected_k, "silhouette"].iloc[0]),
        "pca_variance_first_10": float(pca.explained_variance_ratio_[:10].sum()),
        "stability_mean_ari_vs_seed_0": float(stability.loc[stability["seed"] != 0, "ari_vs_seed_0"].mean()),
        "stability_min_ari_vs_seed_0": float(stability.loc[stability["seed"] != 0, "ari_vs_seed_0"].min()),
        "matched_random_observed_silhouette": float(observed_control),
        "matched_random_exceed_count": int((controls["silhouette"] >= observed_control).sum()),
        "matched_random_replicates": CONTROL_REPLICATES,
        "matched_random_add_one_p": float(empirical_p),
        "annotation_associations": annotations,
        "patients_with_at_least_two_clusters_ge_5pct": patient_multistate,
        "cluster_sizes": cluster_sizes.to_dict(orient="records"),
        "cluster_diagnostics": diagnostic_frame.to_dict(orient="records"),
    }


def self_test() -> None:
    counts = sp.csr_matrix(np.array([[1, 0, 2, 0], [0, 3, 0, 1], [1, 1, 1, 1]], dtype=int))
    library = np.asarray(counts.sum(axis=0)).ravel()
    logged, scaled = normalize_and_scale(counts, np.array([0, 1]), np.arange(4), library)
    assert logged.shape == (4, 2)
    assert scaled.shape == (4, 2)
    assert np.all(np.isfinite(scaled))
    assert clean_symbols(pd.Series([" a ", "B"])).tolist() == ["A", "B"]
    print("self-test passed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--gene-list", type=Path, default=DEFAULT_GENES)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return

    started = time.time()
    results_dir = ROOT / "results"
    figures_dir = ROOT / "figures"
    results_dir.mkdir(exist_ok=True)
    figures_dir.mkdir(exist_ok=True)
    cells_path = args.data_dir / "Cells.csv"
    samples_path = args.data_dir / "Samples.csv"
    genes_path = args.data_dir / "Genes.txt"
    matrix_path = args.data_dir / "Exp_data_UMIcounts.mtx"
    metadata = pd.read_csv(cells_path)
    samples = pd.read_csv(samples_path)
    all_genes = pd.read_csv(genes_path, header=None, names=["symbol"])["symbol"].astype(str).to_numpy()
    user = pd.read_csv(args.gene_list)
    if "symbol" not in user.columns:
        raise ValueError("The metabolic gene table must contain a 'symbol' column.")
    user_symbols = clean_symbols(user["symbol"]).drop_duplicates()
    lookup = {symbol.upper(): idx for idx, symbol in enumerate(all_genes)}
    matched_symbols = [symbol for symbol in user_symbols if symbol in lookup]
    unmatched_symbols = [symbol for symbol in user_symbols if symbol not in lookup]
    user_gene_indices = np.asarray([lookup[symbol] for symbol in matched_symbols], dtype=int)
    pd.DataFrame({"symbol": matched_symbols}).to_csv(results_dir / "metabolic_genes_matched.csv", index=False)
    pd.DataFrame({"symbol": unmatched_symbols}).to_csv(results_dir / "metabolic_genes_unmatched.csv", index=False)

    print(f"Loading {matrix_path} ...", flush=True)
    counts = mmread(matrix_path).tocsr()
    if counts.shape != (len(all_genes), len(metadata)):
        raise ValueError(f"Matrix shape {counts.shape} does not match genes/cells.")
    prevalence_all = np.diff(counts.indptr)
    mean_all = np.asarray(counts.sum(axis=1)).ravel() / counts.shape[1]
    library_sizes = np.asarray(counts.sum(axis=0)).ravel().astype(np.float32)

    all_indices = np.arange(len(metadata))
    global_result = analyse_scope(
        "global",
        counts,
        all_genes,
        user_gene_indices,
        all_indices,
        metadata,
        library_sizes,
        prevalence_all,
        mean_all,
        range(2, 13),
        5_000,
        2_500,
        results_dir,
        figures_dir,
    )
    cd8_mask = metadata["cell_subtype"].fillna("").astype(str).str.strip().eq("CD8 T cells").to_numpy()
    cd8_indices = np.flatnonzero(cd8_mask)
    if len(cd8_indices) < 100:
        raise ValueError(f"Only {len(cd8_indices)} exact CD8 T cells were found.")
    cd8_result = analyse_scope(
        "cd8",
        counts,
        all_genes,
        user_gene_indices,
        cd8_indices,
        metadata,
        library_sizes,
        prevalence_all,
        mean_all,
        range(2, 9),
        3_000,
        2_000,
        results_dir,
        figures_dir,
    )
    summary = {
        "study": {
            "id": "3ca:20773",
            "title": "Choudhury et al. 2022",
            "disease": "Meningioma",
            "technology": "10x",
            "n_cells": int(len(metadata)),
            "n_samples": int(len(samples)),
            "n_patients": int(metadata["patient"].nunique()),
        },
        "gene_list": {
            "path": str(args.gene_list.resolve()),
            "sha256": sha256(args.gene_list),
            "rows": int(len(user)),
            "unique_symbols": int(len(user_symbols)),
            "matched_symbols": int(len(matched_symbols)),
            "unmatched_symbols": int(len(unmatched_symbols)),
        },
        "global": global_result,
        "cd8": cd8_result,
        "methods": {
            "normalization": "per-cell library-size normalization to 10,000 counts followed by log1p",
            "feature_prevalence": "matched metabolic genes expressed in at least 1% of cells in each scope, with a floor of 20 cells",
            "feature_scaling": "gene-wise mean centering and standard-deviation scaling; values clipped to [-10, 10]",
            "embedding": "randomized PCA using metabolic genes only",
            "cluster_selection": "maximum silhouette score in prespecified k sweep",
            "cluster_size_guardrail": "primary selection restricted to solutions whose smallest cluster contains at least 5% of the scope; an unconstrained diagnostic solution is retained only if none pass",
            "stability_seeds": list(SEEDS),
            "metric_subsample_seed": METRIC_SEED,
            "control": "19 non-metabolic random gene sets approximately matched on expression prevalence and mean count; same cells, gene count, PCA and k",
        },
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
            "matplotlib": matplotlib.__version__,
            "seaborn": sns.__version__,
        },
        "provenance": {
            "catalog_fetched_at": "2026-09-14T07:28:19.364731+00:00",
            "homepage_fetched_at": "2026-09-14T07:29:04.027738+00:00",
            "methods_fetched_at": "2026-09-14T07:29:14.861872+00:00",
            "data_archive_sha256": "2156a73fd5f95a198ef90821f2d734bfa7e0b5aa3686deefd1b5c5d5d1269aa1",
            "metadata_archive_sha256": "0614f546a56916066ed8f7fca1a24dbdfc9e7b28af1bd1c9e982a59a25ea3828",
            "data_archive_verified_at": "2026-09-14T07:32:23.523276+00:00",
            "metadata_archive_verified_at": "2026-09-14T07:32:15.071142+00:00",
            "study_page": "https://www.weizmann.ac.il/sites/3CA/brain",
            "homepage": "https://www.weizmann.ac.il/sites/3CA/",
            "methods_page": "https://www.weizmann.ac.il/sites/3CA/methods",
            "citation_url": "https://www.nature.com/articles/s41588-022-01061-8",
        },
        "elapsed_seconds": time.time() - started,
    }
    (results_dir / "results_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
