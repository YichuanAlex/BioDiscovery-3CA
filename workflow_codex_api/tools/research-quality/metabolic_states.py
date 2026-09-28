"""Reproducible single-cell clustering restricted to a supplied metabolic gene set."""

import hashlib
import json
import math
from itertools import combinations
from pathlib import Path

import anndata as ad
import matplotlib
import numpy as np
import pandas as pd
import scanpy as sc
import scipy.sparse as sp
from scipy.io import mmread
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    normalized_mutual_info_score,
    silhouette_score,
)
from sklearn.cluster import KMeans

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

matplotlib.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"], "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7, "svg.fonttype": "none", "pdf.fonttype": 42})

ENGINE = "workflow_research_quality_metabolic_states_v2"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative(root: Path, path: Path) -> str:
    return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_gene_set(path: Path) -> tuple[list[str], dict]:
    """Read a one-column symbol CSV/TSV or a one-symbol-per-line text file."""
    if path.suffix.lower() in {".csv", ".tsv"}:
        table = pd.read_csv(path, sep="\t" if path.suffix.lower() == ".tsv" else ",", dtype=str)
        columns = {str(column).strip().casefold(): column for column in table.columns}
        if "symbol" not in columns:
            raise ValueError("Gene-set CSV/TSV must contain a symbol column")
        raw = table[columns["symbol"]].dropna().astype(str).tolist()
        source_format = path.suffix.lower().lstrip(".")
    else:
        raw = path.read_text(encoding="utf-8-sig").splitlines()
        source_format = "one_symbol_per_line"
    cleaned = [value.strip() for value in raw if value.strip()]
    unique = list(dict.fromkeys(cleaned))
    folded = {}
    for symbol in unique:
        folded.setdefault(symbol.casefold(), []).append(symbol)
    return unique, {
        "format": source_format,
        "nonempty_rows": len(cleaned),
        "unique_exact_symbols": len(unique),
        "duplicate_exact_rows": len(cleaned) - len(unique),
        "casefold_collision_groups": sum(len(values) > 1 for values in folded.values()),
    }


def _match_gene_set(source_symbols: list[str], expression_symbols: list[str]) -> tuple[pd.DataFrame, np.ndarray]:
    exact = {symbol: index for index, symbol in enumerate(expression_symbols)}
    folded: dict[str, list[int]] = {}
    for index, symbol in enumerate(expression_symbols):
        folded.setdefault(symbol.casefold(), []).append(index)
    records = []
    used = set()
    matched = []
    for source in source_symbols:
        candidates = [exact[source]] if source in exact else folded.get(source.casefold(), [])
        if not candidates:
            index, mode = None, "unmatched"
        elif len(candidates) > 1:
            index, mode = None, "ambiguous_casefold"
        elif candidates[0] in used:
            index, mode = candidates[0], "duplicate_expression_mapping"
        else:
            index = candidates[0]
            mode = "exact" if source in exact else "case_insensitive_unique"
            used.add(index)
            matched.append(index)
        records.append({
            "input_symbol": source,
            "expression_symbol": expression_symbols[index] if index is not None else "",
            "match_mode": mode,
            "expression_row_1based": index + 1 if index is not None else None,
        })
    return pd.DataFrame(records), np.asarray(matched, dtype=int)


def _finite(value: float) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"Non-finite metric: {value}")
    return value


def _normalized(raw_cells_by_genes: sp.spmatrix, totals: np.ndarray) -> sp.csr_matrix:
    matrix = raw_cells_by_genes.astype(np.float32).tocsr(copy=True)
    matrix = matrix.multiply((10_000.0 / totals)[:, None]).tocsr()
    matrix.data = np.log1p(matrix.data)
    return matrix


def _collapse_gene_symbols(matrix: sp.csr_matrix, symbols: list[str]) -> tuple[sp.csr_matrix, list[str], np.ndarray]:
    codes, unique = pd.factorize(np.asarray(symbols, dtype=object), sort=False)
    if len(unique) == len(symbols):
        return matrix, list(unique), codes
    # Symbol aggregation is not stable gene-ID disambiguation; preserve the source-row mapping.
    grouping = sp.csr_matrix((np.ones(len(symbols), dtype=np.int64), (codes, np.arange(len(symbols)))), shape=(len(unique), len(symbols)))
    collapsed = (grouping @ matrix).tocsr()
    collapsed.eliminate_zeros()
    return collapsed, list(unique), codes


def _embedding(raw_cells_by_genes: sp.spmatrix, totals: np.ndarray, seed: int, *, build_graph: bool = True) -> tuple[ad.AnnData, np.ndarray]:
    matrix = _normalized(raw_cells_by_genes, totals)
    data = ad.AnnData(X=matrix)
    sc.pp.scale(data, zero_center=False, max_value=10)
    components = min(30, data.n_obs - 1, data.n_vars - 1)
    if components < 2:
        raise ValueError(f"Need at least three cells and genes after QC, got {data.shape}")
    sc.pp.pca(data, n_comps=components, zero_center=True, svd_solver="arpack", random_state=seed)
    if build_graph:
        sc.pp.neighbors(data, n_neighbors=min(15, data.n_obs - 1), n_pcs=components, random_state=seed)
    return data, np.asarray(data.obsm["X_pca"], dtype=np.float32)


def _partition(data: ad.AnnData, resolution: float, seed: int, key: str, *, allow_single_cluster: bool = False) -> np.ndarray:
    sc.tl.leiden(
        data,
        resolution=resolution,
        random_state=seed,
        key_added=key,
        flavor="igraph",
        n_iterations=2,
        directed=False,
    )
    labels = data.obs[key].astype(str).to_numpy()
    if np.unique(labels).size < 2 and not allow_single_cluster:
        raise ValueError(f"Leiden produced fewer than two clusters at resolution={resolution}, seed={seed}")
    return labels


def _metrics(embedding: np.ndarray, labels: np.ndarray, metric_cells: int, seed: int) -> dict[str, float]:
    if np.unique(labels).size < 2:
        raise ValueError("Cluster metrics require at least two labels")
    sample_size = min(metric_cells, len(labels))
    silhouette = silhouette_score(
        embedding,
        labels,
        sample_size=sample_size if sample_size < len(labels) else None,
        random_state=7321,
    )
    return {
        "silhouette": _finite(silhouette),
        "calinski_harabasz": _finite(calinski_harabasz_score(embedding, labels)),
        "davies_bouldin": _finite(davies_bouldin_score(embedding, labels)),
        "metric_cells": int(sample_size),
    }


def _pairwise_stability(partitions: list[np.ndarray]) -> tuple[float, float, float, float]:
    pairs = list(combinations(partitions, 2))
    ari = [adjusted_rand_score(left, right) for left, right in pairs]
    nmi = [normalized_mutual_info_score(left, right) for left, right in pairs]
    return _finite(np.mean(ari)), _finite(np.min(ari)), _finite(np.mean(nmi)), _finite(np.min(nmi))


def _top_variable_genes(
    genes_by_cells: sp.csr_matrix,
    qc_indices: np.ndarray,
    scale: np.ndarray,
    eligible: np.ndarray,
    count: int,
) -> np.ndarray:
    scores = np.full(genes_by_cells.shape[0], -np.inf, dtype=np.float64)
    for start in range(0, genes_by_cells.shape[0], 512):
        stop = min(start + 512, genes_by_cells.shape[0])
        block = genes_by_cells[start:stop, qc_indices].astype(np.float32).multiply(scale[None, :]).tocsr()
        block.data = np.log1p(block.data)
        mean = np.asarray(block.sum(axis=1)).ravel() / len(qc_indices)
        square_mean = np.asarray(block.power(2).sum(axis=1)).ravel() / len(qc_indices)
        scores[start:stop] = square_mean - mean * mean
    scores[~eligible] = -np.inf
    chosen = np.argpartition(scores, -count)[-count:]
    return chosen[np.argsort(scores[chosen])[::-1]]


def _categorical_associations(metadata: pd.DataFrame, labels: np.ndarray, columns: list[str]) -> pd.DataFrame:
    records = []
    for column in columns:
        if column not in metadata:
            continue
        values = metadata[column].fillna("missing").astype(str).to_numpy()
        if np.unique(values).size < 2:
            continue
        records.append(
            {
                "field": column,
                "kind": "categorical",
                "levels": int(np.unique(values).size),
                "nmi_with_cluster": _finite(normalized_mutual_info_score(labels, values)),
                "ari_with_cluster": _finite(adjusted_rand_score(labels, values)),
                "eta_squared": None,
            }
        )
    return pd.DataFrame(records)


def _numeric_associations(metadata: pd.DataFrame, labels: np.ndarray, columns: list[str]) -> pd.DataFrame:
    records = []
    for column in columns:
        if column not in metadata:
            continue
        values = pd.to_numeric(metadata[column], errors="coerce").to_numpy(dtype=float)
        valid = np.isfinite(values)
        if valid.sum() < 3 or np.nanvar(values[valid]) == 0:
            continue
        grand = np.nanmean(values[valid])
        total = np.nansum((values[valid] - grand) ** 2)
        between = 0.0
        for label in np.unique(labels[valid]):
            group = values[valid & (labels == label)]
            between += len(group) * (np.nanmean(group) - grand) ** 2
        records.append(
            {
                "field": column,
                "kind": "numeric",
                "levels": None,
                "nmi_with_cluster": None,
                "ari_with_cluster": None,
                "eta_squared": _finite(between / total),
            }
        )
    return pd.DataFrame(records)


def _stratified_categorical_associations(
    metadata: pd.DataFrame,
    labels: np.ndarray,
    columns: list[str],
    replicate_field: str | None,
) -> pd.DataFrame:
    records = []
    if not replicate_field:
        return pd.DataFrame(columns=["replicate_field", "replicate", "field", "cells", "levels", "clusters", "nmi_with_cluster", "ari_with_cluster"])
    replicates = metadata[replicate_field].fillna("missing").astype(str).to_numpy()
    for replicate in np.unique(replicates):
        indices = np.flatnonzero(replicates == replicate)
        if replicate == "missing" or len(indices) < 50 or np.unique(labels[indices]).size < 2:
            continue
        for column in columns:
            if column not in metadata:
                continue
            values = metadata.iloc[indices][column].fillna("missing").astype(str).to_numpy()
            if np.unique(values).size < 2:
                continue
            records.append({
                "replicate_field": replicate_field,
                "replicate": replicate,
                "field": column,
                "cells": len(indices),
                "levels": int(np.unique(values).size),
                "clusters": int(np.unique(labels[indices]).size),
                "nmi_with_cluster": _finite(normalized_mutual_info_score(labels[indices], values)),
                "ari_with_cluster": _finite(adjusted_rand_score(labels[indices], values)),
            })
    return pd.DataFrame(records)


def _replicate_sensitivity(
    raw: sp.csr_matrix,
    totals: np.ndarray,
    labels: np.ndarray,
    metadata: pd.DataFrame,
    replicate_field: str | None,
    resolution: float,
    seeds: list[int],
    metric_cells: int,
) -> pd.DataFrame:
    records = []
    if not replicate_field:
        return pd.DataFrame(columns=["replicate", "cells", "status"])
    values = metadata[replicate_field].fillna("missing").astype(str).to_numpy()
    for replicate in np.unique(values):
        indices = np.flatnonzero(values == replicate)
        record = {"replicate": replicate, "cells": len(indices), "status": "not_assessable"}
        if len(indices) < 100 or replicate == "missing":
            record["reason"] = "Fewer than 100 cells or unknown replicate; no per-replicate inference"
            records.append(record)
            continue
        data, embedding = _embedding(raw[indices], totals[indices], seeds[0])
        partitions = [_partition(data, resolution, seed, f"within_{seed}", allow_single_cluster=True) for seed in seeds]
        if np.unique(partitions[0]).size < 2:
            record.update({"status": "single_cluster", "reason": "Within-replicate Leiden produced one cluster; separation metrics are undefined"})
            records.append(record)
            continue
        ari_mean, ari_min, nmi_mean, nmi_min = _pairwise_stability(partitions)
        record.update({
            "status": "descriptive_only",
            "n_clusters_reclustered": int(np.unique(partitions[0]).size),
            "mean_pairwise_ari": ari_mean,
            "min_pairwise_ari": ari_min,
            "mean_pairwise_nmi": nmi_mean,
            "min_pairwise_nmi": nmi_min,
            "ari_global_vs_within_replicate": _finite(adjusted_rand_score(labels[indices], partitions[0])),
            **_metrics(embedding, partitions[0], metric_cells, seeds[0]),
        })
        records.append(record)
    return pd.DataFrame(records)


def analyze_metabolic_states(
    workspace: str,
    expression_path: str,
    cells_path: str,
    genes_path: str,
    metabolic_genes_path: str,
    *,
    cell_id_column: str = "cell_name",
    output_dir: str = "results/core_analysis",
    seeds: list[int] | None = None,
    resolutions: list[float] | None = None,
    random_baselines: int = 19,
    min_counts: int = 500,
    min_genes: int = 200,
    max_mito_percent: float = 20.0,
    min_feature_cells: int = 20,
    min_metabolic_genes: int = 30,
    metric_cells: int = 3000,
    subset_field: str | None = None,
    subset_values: list[str] | None = None,
) -> dict:
    root = Path(workspace).resolve()
    if not root.is_dir():
        raise ValueError(f"Workspace is not a directory: {root}")
    paths = {}
    for name, value in {
        "expression": expression_path,
        "cells": cells_path,
        "genes": genes_path,
        "metabolic_genes": metabolic_genes_path,
    }.items():
        path = (root / value).resolve()
        if root not in path.parents or not path.is_file():
            raise ValueError(f"{name} path is missing or leaves workspace: {value}")
        paths[name] = path
    seeds = seeds or [0, 17, 42, 73, 101]
    resolutions = resolutions or [0.4, 0.8, 1.2]
    if len(set(seeds)) < 3 or random_baselines < 2:
        raise ValueError("Require at least three seeds and two random baselines")
    if metric_cells < 100:
        raise ValueError("metric_cells must be at least 100")
    if bool(subset_field) != bool(subset_values):
        raise ValueError("subset_field and at least one subset_values entry must be supplied together")

    cells = pd.read_csv(paths["cells"])
    if cell_id_column not in cells or cells[cell_id_column].isna().any() or cells[cell_id_column].duplicated().any():
        raise ValueError(f"{cell_id_column} must exist and uniquely identify every cells row")
    source_cell_rows = len(cells)
    source_genes = [line.strip() for line in paths["genes"].read_text(encoding="utf-8-sig").splitlines()]
    if not source_genes or any(not gene for gene in source_genes):
        raise ValueError("Gene-name file must contain one nonempty symbol per source matrix feature")
    genes = source_genes
    source_metabolic, gene_set_audit = _read_gene_set(paths["metabolic_genes"])
    if not source_metabolic:
        raise ValueError("Gene set contains no symbols")

    loaded = mmread(paths["expression"])
    if not sp.issparse(loaded):
        raise ValueError("Expression Matrix Market input must be sparse")
    raw = loaded.tocsr()
    del loaded
    source_shape = raw.shape
    raw.sum_duplicates()
    raw.eliminate_zeros()
    if raw.shape == (len(genes), len(cells)):
        genes_by_cells = raw
        orientation = "genes_by_cells"
    elif raw.shape == (len(cells), len(genes)):
        genes_by_cells = raw.T.tocsr()
        orientation = "cells_by_genes"
    else:
        raise ValueError(f"Matrix shape {raw.shape} does not align with {len(genes)} genes and {len(cells)} cells")
    if raw.data.size and (not np.isfinite(raw.data).all() or np.min(raw.data) < 0 or not np.equal(raw.data, np.floor(raw.data)).all()):
        raise ValueError("Raw count matrix must contain finite non-negative integer counts")
    genes_by_cells, genes, gene_codes = _collapse_gene_symbols(genes_by_cells, genes)
    del raw

    subset = {"field": None, "values": [], "source_cells_selected": source_cell_rows}
    if subset_field:
        if subset_field not in cells:
            raise ValueError(f"Subset field is missing from cell metadata: {subset_field}")
        requested = [str(value) for value in subset_values if str(value)]
        available = set(cells[subset_field].dropna().astype(str))
        missing = sorted(set(requested) - available)
        if missing:
            raise ValueError(f"Subset values are absent from {subset_field}: {missing}")
        selected_source_cells = cells[subset_field].astype(str).isin(requested).to_numpy()
        if selected_source_cells.sum() < 100:
            raise ValueError(f"Only {int(selected_source_cells.sum())} source cells match the requested subset")
        genes_by_cells = genes_by_cells[:, selected_source_cells].tocsr()
        cells = cells.loc[selected_source_cells].reset_index(drop=True)
        subset = {"field": subset_field, "values": requested, "source_cells_selected": len(cells)}

    totals = np.asarray(genes_by_cells.sum(axis=0)).ravel().astype(float)
    detected = np.asarray((genes_by_cells > 0).sum(axis=0)).ravel().astype(int)
    mito_indices = np.array([index for index, gene in enumerate(genes) if gene.upper().startswith("MT-")], dtype=int)
    mito = np.asarray(genes_by_cells[mito_indices].sum(axis=0)).ravel() if len(mito_indices) else np.zeros(len(cells))
    mito_percent = np.divide(100 * mito, totals, out=np.zeros_like(totals), where=totals > 0)
    qc = (totals > 0) & (totals >= min_counts) & (detected >= min_genes) & (mito_percent <= max_mito_percent)
    qc_indices = np.flatnonzero(qc)
    if len(qc_indices) < 100:
        raise ValueError(f"Only {len(qc_indices)} cells pass prespecified QC")

    prevalence = np.diff(genes_by_cells[:, qc_indices].tocsr().indptr)
    gene_set_mapping, matched_before_prevalence = _match_gene_set(source_metabolic, genes)
    metabolic_indices = matched_before_prevalence[prevalence[matched_before_prevalence] >= min_feature_cells]
    included_indices = set(metabolic_indices.tolist())
    gene_set_mapping["prevalence_cells"] = [
        int(prevalence[int(index) - 1]) if pd.notna(index) else None
        for index in gene_set_mapping["expression_row_1based"]
    ]
    gene_set_mapping["included_after_prevalence"] = [
        pd.notna(index) and int(index) - 1 in included_indices
        for index in gene_set_mapping["expression_row_1based"]
    ]
    gene_set_audit.update({
        "exact_matches": int((gene_set_mapping["match_mode"] == "exact").sum()),
        "case_insensitive_unique_matches": int((gene_set_mapping["match_mode"] == "case_insensitive_unique").sum()),
        "unmatched_symbols": int((gene_set_mapping["match_mode"] == "unmatched").sum()),
        "ambiguous_casefold_symbols": int((gene_set_mapping["match_mode"] == "ambiguous_casefold").sum()),
        "duplicate_expression_mappings": int((gene_set_mapping["match_mode"] == "duplicate_expression_mapping").sum()),
        "matched_expression_symbols_before_prevalence": int(len(matched_before_prevalence)),
        "included_expression_symbols_after_prevalence": int(len(metabolic_indices)),
    })
    if len(metabolic_indices) < min_metabolic_genes:
        raise ValueError(f"Only {len(metabolic_indices)} supplied metabolic genes are present after prevalence filtering")
    out = (root / output_dir).resolve()
    if root not in out.parents:
        raise ValueError("output_dir leaves workspace")
    out.mkdir(parents=True, exist_ok=True)
    figures = root / "figures" if output_dir == "results/core_analysis" else root / "figures" / Path(output_dir).name
    figures.mkdir(parents=True, exist_ok=True)
    mapping_path = out / "source_feature_to_symbol.csv"
    pd.DataFrame({"source_row_1based": np.arange(1, len(source_genes) + 1), "gene_symbol": source_genes, "aggregated_row_1based": gene_codes + 1}).to_csv(mapping_path, index=False)
    gene_set_mapping_path = out / "gene_set_mapping.csv"
    gene_set_mapping.to_csv(gene_set_mapping_path, index=False)
    source_symbol_by_expression = {
        int(row["expression_row_1based"]) - 1: str(row["input_symbol"])
        for _, row in gene_set_mapping.iterrows()
        if pd.notna(row["expression_row_1based"]) and row["match_mode"] in {"exact", "case_insensitive_unique"}
    }
    matched_path = out / "matched_metabolic_genes.txt"
    matched_path.write_text("\n".join(source_symbol_by_expression[index] for index in metabolic_indices) + "\n", encoding="utf-8")
    matched_expression_path = out / "matched_expression_genes.txt"
    matched_expression_path.write_text("\n".join(genes[index] for index in metabolic_indices) + "\n", encoding="utf-8")

    qc_metadata = cells.iloc[qc_indices].reset_index(drop=True).copy()
    qc_metadata["computed_total_counts"] = totals[qc]
    qc_metadata["computed_detected_genes"] = detected[qc]
    qc_metadata["computed_mito_percent"] = mito_percent[qc]
    qc_metadata.to_csv(out / "qc_cell_metadata.csv", index=False)
    qc_totals = totals[qc]
    metabolic_raw = genes_by_cells[metabolic_indices][:, qc_indices].T.tocsr()
    primary, primary_embedding = _embedding(metabolic_raw, qc_totals, seeds[0])

    sensitivity_records = []
    partitions_by_resolution: dict[float, list[np.ndarray]] = {}
    for resolution in resolutions:
        partitions = []
        for seed in seeds:
            key = f"leiden_{str(resolution).replace('.', '_')}_{seed}"
            labels = _partition(primary, resolution, seed, key)
            partitions.append(labels)
            metrics = _metrics(primary_embedding, labels, metric_cells, seed)
            sensitivity_records.append(
                {"resolution": resolution, "seed": seed, "n_clusters": int(np.unique(labels).size), **metrics}
            )
        partitions_by_resolution[resolution] = partitions
    sensitivity = pd.DataFrame(sensitivity_records)
    stability_records = []
    for resolution, partitions in partitions_by_resolution.items():
        mean_ari, min_ari, mean_nmi, min_nmi = _pairwise_stability(partitions)
        resolution_metrics = sensitivity[sensitivity["resolution"] == resolution]
        stability_records.append(
            {
                "resolution": resolution,
                "mean_pairwise_ari": mean_ari,
                "min_pairwise_ari": min_ari,
                "mean_pairwise_nmi": mean_nmi,
                "min_pairwise_nmi": min_nmi,
                "median_silhouette": _finite(resolution_metrics["silhouette"].median()),
            }
        )
    stability = pd.DataFrame(stability_records)
    stable = stability[stability["mean_pairwise_ari"] >= 0.75]
    selection_pool = stable if not stable.empty else stability
    selected_resolution = float(selection_pool.sort_values(["median_silhouette", "mean_pairwise_ari"], ascending=False).iloc[0]["resolution"])
    resolution_selection = {
        "stability_filter": "mean_pairwise_ari >= 0.75",
        "stable_candidates": [float(value) for value in stable["resolution"].tolist()],
        "fallback_to_all_resolutions": bool(stable.empty),
        "primary_criterion": "highest median silhouette across seeds",
        "tie_breaker": "highest mean_pairwise_ari",
        "selected_resolution": selected_resolution,
    }
    selected_labels = partitions_by_resolution[selected_resolution][0]
    selected_metrics = _metrics(primary_embedding, selected_labels, metric_cells, seeds[0])
    comparison_clusters = int(np.unique(selected_labels).size)
    metabolic_comparison_labels = KMeans(n_clusters=comparison_clusters, n_init=20, random_state=seeds[0]).fit_predict(primary_embedding)
    metabolic_comparison_metrics = _metrics(primary_embedding, metabolic_comparison_labels, metric_cells, seeds[0])
    selected_stability = stability[stability["resolution"] == selected_resolution].iloc[0].to_dict()
    sensitivity.to_csv(out / "resolution_seed_metrics.csv", index=False)
    stability.to_csv(out / "stability_metrics.csv", index=False)
    labels_path = out / "cluster_labels.csv"
    pd.DataFrame({cell_id_column: qc_metadata[cell_id_column], "cluster": selected_labels}).to_csv(labels_path, index=False)

    eligible = (prevalence >= min_feature_cells) & np.array([not gene.upper().startswith("MT-") for gene in genes])
    matched_expression_mask = np.zeros(len(genes), dtype=bool)
    matched_expression_mask[matched_before_prevalence] = True
    candidates_mask = eligible & ~matched_expression_mask
    if candidates_mask.sum() < len(metabolic_indices):
        raise ValueError("Not enough expressed non-metabolic genes for a size-matched random baseline")
    scale = 10_000.0 / qc_totals
    hvg_indices = _top_variable_genes(genes_by_cells, qc_indices, scale, eligible, len(metabolic_indices))
    (out / "hvg_baseline_genes.txt").write_text("\n".join(genes[index] for index in hvg_indices) + "\n", encoding="utf-8")

    baseline_records = []
    baseline_sets: list[tuple[str, int | None, np.ndarray]] = [("HVG_size_matched", None, hvg_indices)]
    candidates = np.flatnonzero(candidates_mask)
    for index in range(random_baselines):
        seed = 10_000 + index
        chosen = np.random.default_rng(seed).choice(candidates, size=len(metabolic_indices), replace=False)
        baseline_sets.append((f"random_size_matched_{index + 1:02d}", seed, chosen))
    for name, seed, indices in baseline_sets:
        feature_path = out / f"{name}_genes.txt"
        feature_path.write_text("\n".join(genes[index] for index in indices) + "\n", encoding="utf-8")
        baseline_raw = genes_by_cells[indices][:, qc_indices].T.tocsr()
        _, baseline_embedding = _embedding(baseline_raw, qc_totals, seeds[0], build_graph=False)
        baseline_labels = KMeans(n_clusters=comparison_clusters, n_init=20, random_state=seeds[0]).fit_predict(baseline_embedding)
        baseline_records.append(
            {
                "name": name,
                "method": "KMeans matched to primary Leiden cluster count",
                "feature_selection_seed": seed,
                "embedding_and_kmeans_seed": seeds[0],
                "silhouette_subsample_seed": 7321,
                "gene_count": len(indices),
                "n_clusters": int(np.unique(baseline_labels).size),
                **_metrics(baseline_embedding, baseline_labels, metric_cells, seed),
                "genes_path": _relative(root, feature_path),
            }
        )
    baselines = pd.DataFrame(baseline_records)
    baselines_path = out / "baseline_metrics.csv"
    baselines.to_csv(baselines_path, index=False)
    random_silhouettes = baselines[baselines["name"].str.startswith("random_")]["silhouette"].to_numpy()
    random_exceedance_count = int(np.sum(random_silhouettes >= metabolic_comparison_metrics["silhouette"]))
    baseline_exceedance = (1 + random_exceedance_count) / (1 + len(random_silhouettes))
    random_control_comparison = {
        "metabolic_matched_kmeans_silhouette": _finite(metabolic_comparison_metrics["silhouette"]),
        "random_controls_exceeding_or_equal": random_exceedance_count,
        "random_controls_total": int(len(random_silhouettes)),
        "add_one_rank_fraction": _finite(baseline_exceedance),
        "interpretation": "descriptive add-one rank, not the observed exceedance proportion and not a biological P value",
    }

    categorical = _categorical_associations(
        qc_metadata,
        selected_labels,
        ["patient", "donor", "sample", "source", "cell_type", "cell_subtype", "cell_cycle_phase"],
    )
    numeric = _numeric_associations(qc_metadata, selected_labels, ["complexity", "computed_total_counts", "computed_detected_genes", "computed_mito_percent"])
    confounders = pd.concat([categorical, numeric], ignore_index=True)
    confounders_path = out / "confounder_metrics.csv"
    confounders.to_csv(confounders_path, index=False)
    composition_records = []
    for field in ["patient", "donor", "sample", "source", "cell_type", "cell_subtype", "cell_cycle_phase"]:
        if field not in qc_metadata:
            continue
        table = pd.crosstab(selected_labels, qc_metadata[field].fillna("missing").astype(str))
        for cluster in table.index:
            total = int(table.loc[cluster].sum())
            for value, count in table.loc[cluster].items():
                composition_records.append(
                    {"field": field, "cluster": str(cluster), "value": str(value), "cells": int(count), "within_cluster_fraction": _finite(count / total)}
                )
    pd.DataFrame(composition_records).to_csv(out / "cluster_composition.csv", index=False)
    cluster_counts = pd.Series(selected_labels).value_counts()
    cluster_size_summary = {
        "minimum_cells": int(cluster_counts.min()),
        "minimum_cluster": str(cluster_counts.idxmin()),
        "maximum_cells": int(cluster_counts.max()),
        "maximum_cluster": str(cluster_counts.idxmax()),
    }
    categorical_nmi_summary = {
        str(row["field"]): _finite(row["nmi_with_cluster"])
        for _, row in categorical.dropna(subset=["nmi_with_cluster"]).iterrows()
    }

    replicate_field = next((field for field in ["patient", "donor", "sample"] if field in qc_metadata), None)
    stratified_associations = _stratified_categorical_associations(
        qc_metadata,
        selected_labels,
        ["cell_type", "cell_subtype"],
        replicate_field,
    )
    stratified_associations_path = out / "stratified_cell_type_associations.csv"
    stratified_associations.to_csv(stratified_associations_path, index=False)
    cell_type_association_summary = {}
    for field in ["cell_type", "cell_subtype"]:
        global_rows = categorical[categorical["field"] == field]
        per_replicate = stratified_associations[stratified_associations["field"] == field] if not stratified_associations.empty else pd.DataFrame()
        if global_rows.empty:
            continue
        summary_row = {"global_nmi": _finite(global_rows.iloc[0]["nmi_with_cluster"]), "replicates_assessable": int(len(per_replicate))}
        if not per_replicate.empty:
            summary_row.update({
                "within_replicate_nmi_min": _finite(per_replicate["nmi_with_cluster"].min()),
                "within_replicate_nmi_max": _finite(per_replicate["nmi_with_cluster"].max()),
                "within_replicate_nmi_median": _finite(per_replicate["nmi_with_cluster"].median()),
            })
        cell_type_association_summary[field] = summary_row
    support_records = []
    if replicate_field:
        table = pd.crosstab(qc_metadata[replicate_field].fillna("missing").astype(str), selected_labels)
        for cluster in table.columns:
            support_records.append(
                {
                    "cluster": str(cluster),
                    "replicate_field": replicate_field,
                    "replicates_with_at_least_5_cells": int((table[cluster] >= 5).sum()),
                    "total_replicates": int(len(table)),
                }
            )
    support = pd.DataFrame(support_records)
    support.to_csv(out / "replicate_support.csv", index=False)
    replicate_sensitivity = _replicate_sensitivity(metabolic_raw, qc_totals, selected_labels, qc_metadata, replicate_field, selected_resolution, seeds, metric_cells)
    replicate_sensitivity.to_csv(out / "within_replicate_sensitivity.csv", index=False)
    valid_replicates = replicate_sensitivity[replicate_sensitivity["status"] == "descriptive_only"]
    if valid_replicates.empty:
        within_replicate_summary = {"replicate_field": replicate_field, "replicates_analyzed": 0}
    else:
        weakest = valid_replicates.loc[valid_replicates["ari_global_vs_within_replicate"].idxmin()]
        within_replicate_summary = {
            "replicate_field": replicate_field,
            "replicates_analyzed": int(len(valid_replicates)),
            "global_vs_within_ari_min": _finite(valid_replicates["ari_global_vs_within_replicate"].min()),
            "global_vs_within_ari_max": _finite(valid_replicates["ari_global_vs_within_replicate"].max()),
            "weakest_replicate": str(weakest["replicate"]),
            "weakest_replicate_cells": int(weakest["cells"]),
        }

    sc.tl.umap(primary, random_state=seeds[0])
    umap = np.asarray(primary.obsm["X_umap"])
    umap_path = out / "umap_coordinates.csv"
    pd.DataFrame({cell_id_column: qc_metadata[cell_id_column], "UMAP1": umap[:, 0], "UMAP2": umap[:, 1]}).to_csv(umap_path, index=False)
    figure_paths = []
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 4.1))
    color_specs = [("cluster", selected_labels), ("cell_type", qc_metadata.get("cell_type", pd.Series("unavailable", index=qc_metadata.index))), (replicate_field or "replicate", qc_metadata.get(replicate_field, pd.Series("unavailable", index=qc_metadata.index)) if replicate_field else pd.Series("unavailable", index=qc_metadata.index))]
    for axis, (title, values) in zip(axes, color_specs):
        codes, uniques = pd.factorize(pd.Series(values).fillna("missing").astype(str), sort=True)
        colors = plt.get_cmap("tab20")(np.arange(len(uniques)) % 20)
        axis.scatter(umap[:, 0], umap[:, 1], c=colors[codes], s=0.5, alpha=0.55, linewidths=0, rasterized=True)
        axis.set_title(f"{title.replace('_', ' ')} ({len(uniques)} labels)")
        axis.set_xlabel("UMAP1")
        axis.set_ylabel("UMAP2")
        handles = [Line2D([], [], marker="o", linestyle="", color=color, markersize=3, label=str(label)) for color, label in zip(colors, uniques)]
        axis.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.21), ncol=3 if title == "cluster" else 1, frameon=False)
        if title == "cluster":
            for code, label in enumerate(uniques):
                position = np.median(umap[codes == code], axis=0)
                axis.text(*position, str(label), fontsize=7, ha="center", va="center")
    fig.suptitle("Metabolic-only UMAP", fontsize=10)
    fig.subplots_adjust(left=0.07, right=0.99, bottom=0.37, top=0.87, wspace=0.45)
    fig.savefig(figures / "metabolic_umap.png", dpi=300)
    fig.savefig(figures / "metabolic_umap.svg", bbox_inches="tight")
    fig.savefig(figures / "metabolic_umap.pdf", bbox_inches="tight")
    plt.close(fig)
    figure_paths.append(_relative(root, figures / "metabolic_umap.pdf"))

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.8))
    for seed, part in sensitivity.groupby("seed"):
        axes[0].plot(part["resolution"], part["silhouette"], marker="o", label=str(seed))
    axes[0].set(xlabel="Leiden resolution", ylabel="Silhouette", title="Resolution and seed sensitivity")
    axes[0].legend(title="seed", fontsize=7)
    axes[1].bar(np.arange(len(baselines)), baselines["silhouette"], color=["#4477AA", *(["#7f8c8d"] * (len(baselines) - 1))])
    axes[1].set_xticks(np.arange(len(baselines)), ["HVG", *[f"R{i:02d}" for i in range(1, len(baselines))]], rotation=60, ha="right", rotation_mode="anchor")
    axes[1].axhline(metabolic_comparison_metrics["silhouette"], color="#c0392b", label="Metabolic matched-k KMeans")
    axes[1].set(xlabel="Matched baseline", ylabel="Silhouette", title="Metabolic vs gene-set controls")
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(figures / "clustering_diagnostics.png", dpi=300)
    fig.savefig(figures / "clustering_diagnostics.svg", bbox_inches="tight")
    fig.savefig(figures / "clustering_diagnostics.pdf", bbox_inches="tight")
    plt.close(fig)
    figure_paths.append(_relative(root, figures / "clustering_diagnostics.pdf"))

    categorical_nmi = categorical[categorical["field"].isin(["patient", "donor", "sample", "cell_type"])]["nmi_with_cluster"] if not categorical.empty else pd.Series(dtype=float)
    confounded = bool(not categorical_nmi.empty and categorical_nmi.max() >= 0.5)
    replicated = bool(not support.empty and (support["replicates_with_at_least_5_cells"] >= 2).all())
    stable_result = bool(float(selected_stability["mean_pairwise_ari"]) >= 0.75)
    separated = bool(selected_metrics["silhouette"] > 0)
    superior = bool(metabolic_comparison_metrics["silhouette"] > np.max(random_silhouettes))
    # ponytail: exploratory one-study pipeline, independent-donor validation and
    # a continuum-vs-discrete null model are needed before asserting discrete biological states.
    conclusion = "inconclusive"

    summary_path = root / "results" / "summary.json" if output_dir == "results/core_analysis" else out / "summary.json"
    scope_text = "all QC-passing cells" if not subset_field else f"{subset_field} in {subset['values']}"
    summary = {
        "question": "Are there distinct clusters of transcriptional metabolic states?" if not subset_field else f"Are there distinct metabolic states within {scope_text}?",
        "analysis_scope": subset,
        "conclusion": conclusion,
        "interpretation": "Metabolic-only cell-group separation is described by actual labels, seed stability, gene-set controls and within-replicate sensitivity. These exploratory results do not by themselves establish discrete biological metabolic states or their absence.",
        "cells_analyzed": int(len(qc_indices)),
        "source_cells": int(source_cell_rows),
        "source_cells_selected": int(len(cells)),
        "source_feature_rows": len(source_genes),
        "unique_gene_symbols": len(genes),
        "duplicate_symbol_rows_aggregated": len(source_genes) - len(genes),
        "metabolic_genes_analyzed": int(len(metabolic_indices)),
        "selected_resolution": selected_resolution,
        "resolution_selection": resolution_selection,
        "n_clusters": int(np.unique(selected_labels).size),
        "cluster_size_summary": cluster_size_summary,
        "metrics": {**selected_metrics, **{key: _finite(value) for key, value in selected_stability.items() if key != "resolution"}},
        "matched_kmeans_control_metrics": metabolic_comparison_metrics,
        "baseline_silhouette_summary": {"HVG": _finite(baselines.iloc[0]["silhouette"]), "random_min": _finite(random_silhouettes.min()), "random_max": _finite(random_silhouettes.max()), "random_mean": _finite(random_silhouettes.mean())},
        "random_control_comparison": random_control_comparison,
        "categorical_confounder_nmi": categorical_nmi_summary,
        "cell_type_association_summary": cell_type_association_summary,
        "within_replicate_summary": within_replicate_summary,
        "evidence_checks": {
            "stable_mean_ari_at_least_0_75": stable_result,
            "positive_descriptive_silhouette": separated,
            "higher_matched_k_silhouette_than_all_random_gene_controls": superior,
            "all_clusters_supported_by_at_least_two_replicates": replicated,
            "not_dominated_by_patient_sample_or_cell_type_nmi_at_least_0_5": not confounded,
            "random_baseline_exceedance_fraction_not_a_biological_p_value": _finite(baseline_exceedance),
        },
        "limitations": [
            "Silhouette is estimated on a fixed random subset; all QC-passing cells are retained for PCA, graph construction, and clustering.",
            "The unsupervised question has no predefined condition contrast; no cell-level differential-expression P values are reported.",
            "No significance test is performed on data-derived cluster labels; within-replicate reclustering is descriptive and not held-out donor validation.",
            "Random gene controls are matched in size, not expression mean or dispersion; their exceedance fraction is a descriptive benchmark, not a biological P value.",
            "Resolution was selected using the same dataset. ARI/NMI assess Leiden randomization conditional on the fixed PCA/neighbor graph, not all preprocessing uncertainty.",
            "A threshold on confounder NMI does not establish independence; independent validation, QC/batch sensitivity and a continuum-versus-discrete comparison remain necessary.",
            "Identical source gene symbols are summed before QC/normalization. Symbol-level aggregation preserves library counts but does not disambiguate stable gene IDs or distinct loci.",
            "Gene symbols are matched exactly first and then by unique case-insensitive equivalence. The saved mapping, unmatched symbols and ambiguities must be reviewed before biological interpretation.",
        ],
    }
    _json(summary_path, summary)
    core_path = out / "core_result.json"
    core = {
        "engine": ENGINE,
        "engine_path": _relative(root, Path(__file__)) if root in Path(__file__).resolve().parents else str(Path(__file__).resolve()),
        "engine_sha256": _sha256(Path(__file__)),
        "methods": {
            "unit": "Exact-symbol aggregated raw counts; all source features form each cell library-size denominator",
            "normalization": "Per-cell library size to 10000, then log1p",
            "feature_scaling": "Scanpy scale(zero_center=False, max_value=10)",
            "pca": {"solver": "arpack", "zero_center": True, "components": int(primary_embedding.shape[1]), "seed": seeds[0]},
            "neighbors": {"n_neighbors": min(15, len(qc_indices) - 1), "seed": seeds[0]},
            "leiden": {"flavor": "igraph", "n_iterations": 2, "directed": False},
            "HVG_control": "Highest variance of library-normalized log1p expression among prevalence-passing non-mitochondrial symbols; no dispersion/mean bin normalization",
            "random_controls": "Size-matched sampling without replacement from prevalence-passing non-metabolic, non-mitochondrial symbols",
            "control_partition": {"method": "KMeans", "n_init": 20, "clusters": comparison_clusters, "seed": seeds[0]},
            "metrics": {"space": "PCA", "silhouette_subsample_seed": 7321, "silhouette_cells": min(metric_cells, len(qc_indices)), "CH_DBI_population": "All QC-passing cells"},
            "stability": "Leiden randomization on a fixed PCA/neighbor graph; resolution chosen on the same dataset",
            "resolution_selection": resolution_selection,
        },
        "inputs": {
            "expression_path": _relative(root, paths["expression"]),
            "expression_sha256": _sha256(paths["expression"]),
            "cells_path": _relative(root, paths["cells"]),
            "cells_sha256": _sha256(paths["cells"]),
            "genes_path": _relative(root, paths["genes"]),
            "genes_sha256": _sha256(paths["genes"]),
            "matrix_orientation": orientation,
            "matrix_shape": list(source_shape),
            "metabolic_genes_path": _relative(root, paths["metabolic_genes"]),
            "metabolic_genes_sha256": _sha256(paths["metabolic_genes"]),
            "gene_set_audit": gene_set_audit,
            "subset": subset,
        },
        "parameters": {
            "seeds": seeds,
            "resolutions": resolutions,
            "random_baselines": random_baselines,
            "min_counts": min_counts,
            "min_genes": min_genes,
            "max_mito_percent": max_mito_percent,
            "min_feature_cells": min_feature_cells,
            "min_metabolic_genes": min_metabolic_genes,
            "metric_cells": metric_cells,
            "duplicate_gene_symbols": "sum_raw_counts_by_exact_symbol_before_qc",
        },
        "outputs": {
            "summary_path": _relative(root, summary_path),
            "summary_sha256": _sha256(summary_path),
            "labels_path": _relative(root, labels_path),
            "labels_sha256": _sha256(labels_path),
            "matched_genes_path": _relative(root, matched_path),
            "matched_genes_sha256": _sha256(matched_path),
            "matched_expression_genes_path": _relative(root, matched_expression_path),
            "matched_expression_genes_sha256": _sha256(matched_expression_path),
            "gene_set_mapping_path": _relative(root, gene_set_mapping_path),
            "gene_set_mapping_sha256": _sha256(gene_set_mapping_path),
            "baseline_metrics_path": _relative(root, baselines_path),
            "baseline_metrics_sha256": _sha256(baselines_path),
            "resolution_seed_metrics_path": _relative(root, out / "resolution_seed_metrics.csv"),
            "resolution_seed_metrics_sha256": _sha256(out / "resolution_seed_metrics.csv"),
            "stability_metrics_path": _relative(root, out / "stability_metrics.csv"),
            "stability_metrics_sha256": _sha256(out / "stability_metrics.csv"),
            "confounder_metrics_path": _relative(root, confounders_path),
            "confounder_metrics_sha256": _sha256(confounders_path),
            "stratified_cell_type_associations_path": _relative(root, stratified_associations_path),
            "stratified_cell_type_associations_sha256": _sha256(stratified_associations_path),
            "cluster_composition_path": _relative(root, out / "cluster_composition.csv"),
            "cluster_composition_sha256": _sha256(out / "cluster_composition.csv"),
            "replicate_support_path": _relative(root, out / "replicate_support.csv"),
            "replicate_support_sha256": _sha256(out / "replicate_support.csv"),
            "within_replicate_sensitivity_path": _relative(root, out / "within_replicate_sensitivity.csv"),
            "within_replicate_sensitivity_sha256": _sha256(out / "within_replicate_sensitivity.csv"),
            "source_feature_mapping_path": _relative(root, mapping_path),
            "source_feature_mapping_sha256": _sha256(mapping_path),
            "umap_coordinates_path": _relative(root, umap_path),
            "umap_coordinates_sha256": _sha256(umap_path),
            "figures": figure_paths,
            "figure_sha256": {path: _sha256(root / path) for path in figure_paths},
        },
        "facts": {
            "source_cells": int(source_cell_rows),
            "source_cells_selected": int(len(cells)),
            "source_genes": len(source_genes),
            "unique_gene_symbols": len(genes),
            "duplicate_symbol_rows_aggregated": len(source_genes) - len(genes),
            "cells_analyzed": int(len(qc_indices)),
            "unique_cells_analyzed": int(qc_metadata[cell_id_column].nunique()),
            "metabolic_source_genes": int(len(source_metabolic)),
            "gene_set_audit": gene_set_audit,
            "subset": subset,
            "metabolic_genes_analyzed": int(len(metabolic_indices)),
            "n_clusters": int(np.unique(selected_labels).size),
            "conclusion": conclusion,
            "selected_resolution": selected_resolution,
            "selected_seed": seeds[0],
            "resolution_selection": resolution_selection,
            "cluster_size_summary": cluster_size_summary,
            "metrics": summary["metrics"],
            "confounders_checked": confounders["field"].tolist(),
            "categorical_confounder_nmi": categorical_nmi_summary,
            "cell_type_association_summary": cell_type_association_summary,
            "replicate_field": replicate_field,
            "within_replicate_summary": within_replicate_summary,
            "baseline_exceedance_fraction": _finite(baseline_exceedance),
            "random_control_comparison": random_control_comparison,
            "baseline_silhouette_summary": summary["baseline_silhouette_summary"],
        },
    }
    _json(core_path, core)
    result = {
        "engine": ENGINE,
        "conclusion": conclusion,
        "core_result_path": _relative(root, core_path),
        "core_result_sha256": _sha256(core_path),
        "summary_path": _relative(root, summary_path),
        "labels_path": _relative(root, labels_path),
        "figures": figure_paths,
        "analysis_scope": subset,
        "cells_analyzed": int(len(qc_indices)),
        "metabolic_genes_analyzed": int(len(metabolic_indices)),
        "n_clusters": int(np.unique(selected_labels).size),
    }
    return result
