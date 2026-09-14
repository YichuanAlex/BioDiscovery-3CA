"""
Q1_R13: Analyze metabolic states using Reactome metabolism genes on 3CA Choudhury 2022 meningioma data.
"""
import scanpy as sc
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.preprocessing import StandardScaler
import hashlib
import json
import os
from pathlib import Path

# Paths
EXP_PATH = "inputs/Exp_data_UMIcounts.mtx"
CELLS_PATH = "inputs/Cells.csv"
GENES_PATH = "inputs/Genes.txt"
METABOLIC_GENES_PATH = "sources/reactome/metabolism_R-HSA-1430728_release_97_genes.txt"
OUTPUT_DIR = "results/core_analysis"
FIGURES_DIR = "figures"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

# Load cells metadata
cells_df = pd.read_csv(CELLS_PATH)
print(f"Loaded {len(cells_df)} cells with columns: {cells_df.columns.tolist()}")

# Check unique cell IDs
print(f"Unique cell names: {cells_df['cell_name'].nunique()}")
print(f"Unique patients: {cells_df['patient'].nunique()}")
print(f"Unique samples: {cells_df['sample'].nunique()}")
print(f"Unique cell types: {cells_df['cell_type'].nunique()}")

# Load genes
genes_list = []
with open(GENES_PATH, 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            genes_list.append(line)
genes_set = set(genes_list)
print(f"Total genes in matrix: {len(genes_list)}")
print(f"Unique gene symbols: {len(genes_set)}")

# Load metabolic genes
with open(METABOLIC_GENES_PATH, 'r') as f:
    metabolic_genes_list = [line.strip() for line in f if line.strip() and not line.startswith('#')]
print(f"Reactome metabolic genes: {len(metabolic_genes_list)}")

# Match metabolic genes to expression matrix
matched_metabolic_genes = [g for g in metabolic_genes_list if g in genes_set]
print(f"Matched metabolic genes: {len(matched_metabolic_genes)}")

# Create gene mapping
gene_to_idx = {gene: i for i, gene in enumerate(genes_list)}
metabolic_gene_indices = [gene_to_idx[g] for g in matched_metabolic_genes]

# Load expression matrix
print(f"Loading expression matrix: {EXP_PATH}")
sc.read_mtx(EXP_PATH, var_names_ignore=[])
adata = sc.get()
print(f"Matrix shape: {adata.shape}")
print(f"Matrix orientation: genes x cells")

# Filter to matched metabolic genes
print(f"Filtering to {len(matched_metabolic_genes)} metabolic genes...")
adata.var = adata.var[matched_metabolic_genes]
print(f"Filtered matrix shape: {adata.shape}")

# Filter cells - keep all QC-passing cells (no explicit QC filtering in this dataset)
print(f"Keeping all {len(adata)} cells")

# Normalize and compute log
print("Normalizing and computing log...")
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)

# Compute HVGs for baseline comparison
print("Computing HVGs for baseline comparison...")
sc.pp.highly_variable_genes(adata, method='mean-variance', n_top_genes=1000)
hvg_indices = adata.var_names.get_values().tolist()
print(f"HVG count: {len(hvg_indices)}")

# Run Leiden clustering with multiple seeds and resolutions
print("\n=== Running Leiden clustering with multiple seeds and resolutions ===")
seeds = [1, 2, 3]
resolutions = [0.2, 0.5, 1.0, 2.0, 4.0]

all_labels = {}
all_metrics = {}

for seed in seeds:
    for res in resolutions:
        print(f"Seed {seed}, Resolution {res}...")
        sc.tl.leiden(adata, resolution=res, seed=seed, key_added=f'cluster_{seed}_{res}')
        labels = adata.obs[f'cluster_{seed}_{res}'].tolist()
        
        # Compute metrics
        sil = silhouette_score(adata.X, labels) if len(set(labels)) > 1 else 0
        ch = calinski_harabasz_score(adata.X, labels) if len(set(labels)) > 1 else 0
        db = davies_bouldin_score(adata.X, labels) if len(set(labels)) > 1 else 0
        
        all_labels[f'{seed}_{res}'] = labels
        all_metrics[f'{seed}_{res}'] = {
            'silhouette': sil,
            'calinski_harabasz': ch,
            'davies_bouldin': db,
            'n_clusters': len(set(labels))
        }

# Save cluster labels for each seed/resolution
for key, labels in all_labels.items():
    labels_df = pd.DataFrame({'cell_name': adata.obs['cell_name'].values, 'cluster': labels})
    labels_df.to_csv(f"{OUTPUT_DIR}/cluster_labels_{key}.csv", index=False)

# Save metrics
metrics_df = pd.DataFrame(all_metrics)
metrics_df.to_csv(f"{OUTPUT_DIR}/cluster_metrics.csv", index=False)

# Run HVG-based clustering for comparison
print("\n=== Running HVG-based clustering ===")
sc.pp.highly_variable_genes(adata, method='mean-variance', n_top_genes=1000)
hvg_mask = adata.var['highly_variable'].values
adata_hvg = adata[:, hvg_mask]
sc.tl.leiden(adata_hvg, resolution=1.0, seed=1, key_added='cluster_hvg')
hvg_labels = adata_hvg.obs['cluster_hvg'].tolist()
hvg_n_clusters = len(set(hvg_labels))

hvg_sil = silhouette_score(adata_hvg.X, hvg_labels)
hvg_ch = calinski_harabasz_score(adata_hvg.X, hvg_labels)
hvg_db = davies_bouldin_score(adata_hvg.X, hvg_labels)

print(f"HVG clustering: {hvg_n_clusters} clusters")
print(f"HVG silhouette: {hvg_sil:.4f}")
print(f"HVG Calinski-Harabasz: {hvg_ch:.4f}")
print(f"HVG Davies-Bouldin: {hvg_db:.4f}")

hvg_labels_df = pd.DataFrame({'cell_name': adata.obs['cell_name'].values, 'cluster': hvg_labels})
hvg_labels_df.to_csv(f"{OUTPUT_DIR}/cluster_labels_hvg.csv", index=False)

# Save summary
summary = {
    'dataset': {
        'study_id': '3ca:20773',
        'title': 'Choudhury et al. 2022',
        'n_cells': len(adata),
        'n_genes': len(adata.var),
        'n_metabolic_genes': len(matched_metabolic_genes),
        'n_hvg': len(hvg_indices),
        'n_hvg_clusters': hvg_n_clusters
    },
    'metabolic_clustering': {
        'seeds': seeds,
        'resolutions': resolutions,
        'metrics': all_metrics
    },
    'hvg_clustering': {
        'n_clusters': hvg_n_clusters,
        'silhouette': hvg_sil,
        'calinski_harabasz': hvg_ch,
        'davies_bouldin': hvg_db
    },
    'methods': {
        'algorithm': 'Scanpy Leiden on Reactome metabolic genes',
        'normalization': 'total_count normalization with log1p',
        'hvg_method': 'mean-variance trend',
        'hvg_n_top': 1000
    }
}

with open(f"{OUTPUT_DIR}/summary.json", 'w') as f:
    json.dump(summary, f, indent=2)

print("\nAnalysis complete. Results saved to", OUTPUT_DIR)
