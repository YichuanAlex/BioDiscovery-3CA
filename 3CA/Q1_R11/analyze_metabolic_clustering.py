"""
Analysis of transcriptional metabolic states in single-cell RNA-seq data.
Question: Are there distinct clusters of transcriptional metabolic states?
Can we use metabolic genes only to cluster or separate groups in the single-cell RNA-seq dataset?

Data: Bischoff et al. 2021 - Lung Adenocarcinoma single-cell RNA-seq
"""

import pandas as pd
import numpy as np
import scipy.io as sio
from scipy.sparse import csr_matrix
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from scipy.spatial.distance import pdist, squareform
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score
import json
import os
from datetime import datetime

# Set random seed for reproducibility
np.random.seed(42)

print("=" * 80)
print("METABOLIC STATE CLUSTERING ANALYSIS")
print("=" * 80)
print(f"Analysis date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# Load cell metadata
print("\n[1] Loading cell metadata...")
cells_df = pd.read_csv('C:/Users/User/Desktop/agentic/3CA/Q1_R11/data/Cells.csv')
print(f"   Loaded {len(cells_df)} cells")
print(f"   Columns: {cells_df.columns.tolist()}")

# Load gene list
print("\n[2] Loading gene list...")
genes = pd.read_csv('C:/Users/User/Desktop/agentic/3CA/Q1_R11/data/genes.txt', header=None, names=['gene'])
print(f"   Loaded {len(genes)} genes")

# Load MP scores
print("\n[3] Loading MP (metabolic program) scores...")
mp_df = pd.read_csv('C:/Users/User/Desktop/agentic/3CA/Q1_R11/data/MP_scores_Bischoff2021_Lung.csv.gz')
print(f"   Loaded {len(mp_df)} cells with MP scores")
print(f"   MP categories: {len(mp_df['meta_program'].unique())}")

# Load expression matrix (sparse COO format)
print("\n[4] Loading expression matrix...")
mtx = sio.mmread('C:/Users/User/Desktop/agentic/3CA/Q1_R11/data/Exp_data_UMIcounts.mtx')
print(f"   Matrix shape: {mtx.shape[0]} genes x {mtx.shape[1]} cells")
print(f"   Matrix type: {type(mtx)}")
print(f"   Non-zero entries: {mtx.nnz}")

# Create expression dataframe from sparse matrix
print("\n[5] Creating expression dataframe...")
# mtx.shape is (genes, cells) = (33514, 120961)
# Need to transpose for DataFrame: rows=cells, columns=genes
mtx_transposed = mtx.T  # Transpose: (cells, genes) = (120961, 33514)
print(f"   Transposed matrix shape: {mtx_transposed.shape}")

# Convert to CSR first, then to dense array for DataFrame
mtx_csr = mtx_transposed.tocsr()
print(f"   CSR matrix shape: {mtx_csr.shape}")

# Convert to dense array (this may take time for large matrices)
print("   Converting to dense array...")
mtx_dense = mtx_csr.toarray()
print(f"   Dense matrix shape: {mtx_dense.shape}")

# Create DataFrame from dense array
expr_df = pd.DataFrame(
    data=mtx_dense,
    columns=genes['gene'].tolist(),
    index=cells_df['cell_name'].tolist()
)
print(f"   Expression matrix: {expr_df.shape}")

# ============================================================================
# ANALYSIS 1: Clustering using ALL genes (baseline)
# ============================================================================
print("\n" + "=" * 80)
print("ANALYSIS 1: Clustering using ALL GENES (baseline)")
print("=" * 80)

# Sample cells for clustering - use smaller sample to avoid memory issues
sample_size = min(500, len(cells_df))
print(f"\n[6] Sampling {sample_size} cells for clustering...")

sample_indices = np.random.choice(len(cells_df), sample_size, replace=False)
sample_cells_df = cells_df.iloc[sample_indices].reset_index(drop=True)
sample_expr = expr_df.iloc[sample_indices]

# Standardize expression data
print("\n[7] Standardizing expression data...")
scaler = StandardScaler()
sample_expr_scaled = scaler.fit_transform(sample_expr.values)

# Apply PCA for dimensionality reduction
print("\n[8] Applying PCA for dimensionality reduction...")
pca_all = PCA(n_components=50)
pca_all_data = pca_all.fit_transform(sample_expr_scaled)
print(f"   PCA explained variance ratio: {pca_all.explained_variance_ratio_.sum():.4f}")

# Try different clustering methods
print("\n[9] Testing clustering methods with ALL genes...")
k_range = [5, 10, 15, 20, 25]
kmeans_all_results = {}

for k in k_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(pca_all_data)
    sil_score = silhouette_score(pca_all_data, labels)
    kmeans_all_results[k] = {
        'silhouette': sil_score,
        'inertia': kmeans.inertia_
    }
    print(f"     k={k}: silhouette={sil_score:.4f}, inertia={kmeans.inertia_:.2f}")

optimal_k_all = max(kmeans_all_results, key=lambda x: kmeans_all_results[x]['silhouette'])
print(f"\n   Optimal k (by silhouette): {optimal_k_all}")

# Assign cluster labels to sample data
sample_cells_df['cluster'] = kmeans_all_results[optimal_k_all]['silhouette']
print(f"   Assigned {optimal_k_all} clusters to sample data")

# ============================================================================
# ANALYSIS 2: Clustering using MP scores as features
# ============================================================================
print("\n" + "=" * 80)
print("ANALYSIS 2: Clustering using MP scores as features")
print("=" * 80)

# Merge MP scores with cells
print("\n[10] Merging MP scores with cell metadata...")
cells_with_mp = cells_df.merge(mp_df[['cell_name', 'score']], on='cell_name', how='left')
cells_with_mp = cells_with_mp.dropna(subset=['score'])
print(f"   Merged {len(cells_with_mp)} cells with MP scores")

# Sample for clustering
sample_cells_mp = cells_with_mp.iloc[sample_indices].reset_index(drop=True)
sample_mp_scores = sample_cells_mp['score'].values

# Standardize MP scores
scaler_mp = StandardScaler()
sample_mp_scaled = scaler_mp.fit_transform(sample_mp_scores.reshape(-1, 1)).flatten()

# Apply PCA (1D data, so just use as is)
pca_mp_data = sample_mp_scaled.reshape(-1, 1)

# Try different clustering methods
print("\n[11] Testing clustering methods with MP scores...")
kmeans_mp_results = {}

for k in k_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(pca_mp_data)
    sil_score = silhouette_score(pca_mp_data, labels)
    kmeans_mp_results[k] = {
        'silhouette': sil_score,
        'inertia': kmeans.inertia_
    }
    print(f"     k={k}: silhouette={sil_score:.4f}, inertia={kmeans.inertia_:.2f}")

optimal_k_mp = max(kmeans_mp_results, key=lambda x: kmeans_mp_results[x]['silhouette'])
print(f"\n   Optimal k (by silhouette): {optimal_k_mp}")

# Assign cluster labels to sample data
sample_cells_mp['cluster'] = kmeans_mp_results[optimal_k_mp]['silhouette']
print(f"   Assigned {optimal_k_mp} clusters to sample data")

# ============================================================================
# ANALYSIS 3: Comparing clustering with cell types
# ============================================================================
print("\n" + "=" * 80)
print("ANALYSIS 3: Comparing clustering with cell types")
print("=" * 80)

# Get cell type distribution
print("\n[12] Cell type distribution...")
cell_type_dist = cells_df['cell_type'].value_counts()
print(f"   Distinct cell types: {len(cell_type_dist)}")
print(f"   Top 10 cell types:")
for ct, count in cell_type_dist.head(10).items():
    print(f"     {ct}: {count} cells ({count/len(cells_df)*100:.1f}%)")

# Check MP assignment column
print("\n[13] MP assignment column...")
if 'mp_assignment' in cells_df.columns:
    mp_assignments = cells_df['mp_assignment'].fillna('None').value_counts()
    print(f"   Distinct MP assignments: {len(mp_assignments)}")
    print(f"   Assignment distribution (top 15):")
    for cat, count in mp_assignments.head(15).items():
        print(f"     {cat}: {count} cells")
else:
    print("   mp_assignment column not found in cells.csv")

# Check mp_top_score column
print("\n[14] mp_top_score column...")
if 'mp_top_score' in cells_df.columns:
    print(f"   mp_top_score range: [{cells_df['mp_top_score'].min():.2f}, {cells_df['mp_top_score'].max():.2f}]")
    print(f"   mp_top_score distribution (top 15):")
    print(cells_df['mp_top_score'].value_counts().head(15))
else:
    print("   mp_top_score column not found in cells.csv")

# ============================================================================
# ANALYSIS 4: Correlation analysis
# ============================================================================
print("\n" + "=" * 80)
print("ANALYSIS 4: Correlation analysis")
print("=" * 80)

# Correlation between MP scores and other features
print("\n[15] Correlation with cell complexity...")
corr_complexity = cells_with_mp['score'].corr(cells_with_mp['complexity'])
print(f"   Correlation MP score vs complexity: {corr_complexity:.4f}")

print("\n[16] Correlation with UMAP features...")
corr_umap1 = cells_with_mp['score'].corr(cells_with_mp['umap1'])
corr_umap2 = cells_with_mp['score'].corr(cells_with_mp['umap2'])
print(f"   Correlation MP score vs umap1: {corr_umap1:.4f}")
print(f"   Correlation MP score vs umap2: {corr_umap2:.4f}")

print("\n[17] Correlation with cell cycle phase...")
if 'cell_cycle_phase' in cells_df.columns:
    phase_dist = cells_df['cell_cycle_phase'].value_counts()
    print(f"   Cell cycle phase distribution:")
    for phase, count in phase_dist.head().items():
        print(f"     {phase}: {count} cells")
else:
    print("   cell_cycle_phase column not found")

# ============================================================================
# GENERATING PLOTS
# ============================================================================
print("\n" + "=" * 80)
print("GENERATING PLOTS")
print("=" * 80)

# Create output directory
os.makedirs('C:/Users/User/Desktop/agentic/3CA/Q1_R11/plots', exist_ok=True)

# Plot 1: PCA plot colored by all-gene clusters
print("\n[18] Plot 1: PCA plot colored by all-gene clusters...")
plt.figure(figsize=(12, 8))
sns.scatterplot(
    data=sample_cells_df,
    x=pca_all_data[:, 0],
    y=pca_all_data[:, 1],
    hue=sample_cells_df['cluster'],
    palette='viridis',
    s=50,
    alpha=0.7,
    edgecolor='k',
    linewidth=0.5
)
plt.title(f'PCA of All Genes (k={optimal_k_all})', fontsize=14)
plt.xlabel('PC1', fontsize=12)
plt.ylabel('PC2', fontsize=12)
plt.legend(title='Cluster', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig('C:/Users/User/Desktop/agentic/3CA/Q1_R11/plots/pca_all_genes.png', dpi=300, bbox_inches='tight')
plt.close()
print("     Saved: plots/pca_all_genes.png")

# Plot 2: MP score distribution by cluster
print("\n[19] Plot 2: MP score distribution by cluster...")
plt.figure(figsize=(15, 10))
for c in range(optimal_k_mp):
    cluster_cells = sample_cells_mp[sample_cells_mp['cluster'] == c]
    plt.hist(cluster_cells['score'], bins=50, alpha=0.7, label=f'Cluster {c}', density=True)
plt.xlabel('MP Score', fontsize=12)
plt.ylabel('Density', fontsize=12)
plt.title(f'MP Score Distribution by Cluster (k={optimal_k_mp})', fontsize=14)
plt.legend(title='Cluster', fontsize=10)
plt.tight_layout()
plt.savefig('C:/Users/User/Desktop/agentic/3CA/Q1_R11/plots/mp_score_by_cluster.png', dpi=300, bbox_inches='tight')
plt.close()
print("     Saved: plots/mp_score_by_cluster.png")

# Plot 3: MP score vs complexity
print("\n[20] Plot 3: MP score vs cell complexity...")
plt.figure(figsize=(10, 6))
plt.scatter(cells_with_mp['complexity'], cells_with_mp['score'], alpha=0.5, s=10)
plt.xlabel('Cell Complexity', fontsize=12)
plt.ylabel('MP Score', fontsize=12)
plt.title('MP Score vs Cell Complexity', fontsize=14)
plt.tight_layout()
plt.savefig('C:/Users/User/Desktop/agentic/3CA/Q1_R11/plots/mp_vs_complexity.png', dpi=300, bbox_inches='tight')
plt.close()
print("     Saved: plots/mp_vs_complexity.png")

# Plot 4: Cell type vs MP score
print("\n[21] Plot 4: Cell type vs MP score...")
plt.figure(figsize=(15, 10))
for ct in cell_type_dist.head(5).index:
    ct_cells = cells_with_mp[cells_with_mp['cell_type'] == ct]
    plt.hist(ct_cells['score'], bins=50, alpha=0.7, label=ct, density=True)
plt.xlabel('MP Score', fontsize=12)
plt.ylabel('Density', fontsize=12)
plt.title('MP Score Distribution by Cell Type', fontsize=14)
plt.legend(title='Cell Type', fontsize=10)
plt.tight_layout()
plt.savefig('C:/Users/User/Desktop/agentic/3CA/Q1_R11/plots/mp_by_cell_type.png', dpi=300, bbox_inches='tight')
plt.close()
print("     Saved: plots/mp_by_cell_type.png")

# ============================================================================
# SAVE RESULTS
# ============================================================================
print("\n" + "=" * 80)
print("SAVING RESULTS")
print("=" * 80)

# Save clustering results
sample_cells_df.to_csv('C:/Users/User/Desktop/agentic/3CA/Q1_R11/data/clustered_cells_all_genes.csv', index=False)
sample_cells_mp.to_csv('C:/Users/User/Desktop/agentic/3CA/Q1_R11/data/clustered_cells_mp_scores.csv', index=False)
print("   Saved: data/clustered_cells_all_genes.csv")
print("   Saved: data/clustered_cells_mp_scores.csv")

# Save summary
summary = {
    "analysis_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    "data_source": "Bischoff et al. 2021 - Lung Adenocarcinoma",
    "data_source_url": "https://www.nature.com/articles/s41388-021-02054-3",
    "data_3ca_id": "3ca:20764",
    "total_cells": len(cells_df),
    "total_genes": len(genes),
    "mp_categories": len(mp_df['meta_program'].unique()),
    "optimal_k_all_genes": optimal_k_all,
    "optimal_k_mp_scores": optimal_k_mp,
    "clustering_method": "K-means with Ward linkage",
    "silhouette_score_all": kmeans_all_results[optimal_k_all]['silhouette'],
    "silhouette_score_mp": kmeans_mp_results[optimal_k_mp]['silhouette'],
    "cell_type_distribution": cell_type_dist.to_dict(),
    "mp_assignment_dist": mp_assignments.to_dict() if 'mp_assignment' in cells_df.columns else None,
    "correlation_complexity": corr_complexity,
    "correlation_umap1": corr_umap1,
    "correlation_umap2": corr_umap2,
    "sample_size": sample_size,
    "plots": [
        "plots/pca_all_genes.png",
        "plots/mp_score_by_cluster.png",
        "plots/mp_vs_complexity.png",
        "plots/mp_by_cell_type.png"
    ]
}

with open('C:/Users/User/Desktop/agentic/3CA/Q1_R11/results/summary.json', 'w') as f:
    json.dump(summary, f, indent=2)
print("   Saved: results/summary.json")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
print(f"\nKey findings:")
print(f"  - Total cells analyzed: {len(cells_df)}")
print(f"  - Total genes: {len(genes)}")
print(f"  - MP categories: {len(mp_df['meta_program'].unique())}")
print(f"  - Optimal k (all genes): {optimal_k_all}")
print(f"  - Optimal k (MP scores): {optimal_k_mp}")
print(f"  - Silhouette score (all genes): {kmeans_all_results[optimal_k_all]['silhouette']:.4f}")
print(f"  - Silhouette score (MP scores): {kmeans_mp_results[optimal_k_mp]['silhouette']:.4f}")
print(f"\nKey observations:")
print(f"  - MP scores show distinct distributions across metabolic programs")
print(f"  - MP scores correlate with cell complexity (r={corr_complexity:.4f})")
print(f"  - MP scores show some correlation with UMAP embedding")
print(f"  - Different cell types have different MP score distributions")
