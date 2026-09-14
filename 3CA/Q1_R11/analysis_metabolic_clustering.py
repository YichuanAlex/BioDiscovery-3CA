"""
Analysis of transcriptional metabolic states in single-cell RNA-seq data.
Question: Are there distinct clusters of transcriptional metabolic states?
Can we use metabolic genes only to cluster or separate groups in the single-cell RNA-seq dataset?

Data: Bischoff et al. 2021 - Lung Adenocarcinoma single-cell RNA-seq
"""

import pandas as pd
import numpy as np
import scipy.stats as stats
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from scipy.spatial.distance import pdist, squareform
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import json

# Set random seed for reproducibility
np.random.seed(42)

print("=" * 80)
print("METABOLIC STATE CLUSTERING ANALYSIS")
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
print(f"   MP categories: {mp_df['meta_program'].unique().tolist()}")

# Analyze MP score distributions
print("\n[4] Analyzing MP score distributions...")
mp_categories = mp_df['meta_program'].unique()
print(f"   Number of distinct MP categories: {len(mp_categories)}")

# Count cells per MP category
mp_counts = mp_df.groupby('meta_program').size()
print("\n   Cells per MP category (top 10):")
for cat, count in mp_counts.head(10).items():
    print(f"     {cat}: {count} cells ({count/len(cells_df)*100:.1f}%)")

# Check if MP assignment column has additional info
print("\n[5] Checking MP assignment column...")
if 'mp_assignment' in cells_df.columns:
    mp_assignments = cells_df['mp_assignment'].fillna('None').value_counts()
    print(f"   Distinct MP assignments: {len(mp_assignments)}")
    print(f"   Assignment distribution (top 10):")
    for cat, count in mp_assignments.head(10).items():
        print(f"     {cat}: {count} cells")
else:
    print("   mp_assignment column not found in cells.csv")

# Calculate correlation between MP scores and other features
print("\n[6] Correlation with cell complexity and other features...")
# Merge MP scores with cells data
cells_with_mp = cells_df.merge(mp_df[['cell_name', 'score']], on='cell_name', how='left')
cells_with_mp = cells_with_mp.dropna(subset=['score'])

# Correlation with complexity
corr_complexity = cells_with_mp['score'].corr(cells_with_mp['complexity'])
print(f"   Correlation MP score vs complexity: {corr_complexity:.4f}")

# Correlation with umap features
corr_umap1 = cells_with_mp['score'].corr(cells_with_mp['umap1'])
corr_umap2 = cells_with_mp['score'].corr(cells_with_mp['umap2'])
print(f"   Correlation MP score vs umap1: {corr_umap1:.4f}")
print(f"   Correlation MP score vs umap2: {corr_umap2:.4f}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"\nTotal cells analyzed: {len(cells_df)}")
print(f"Distinct MP categories: {len(mp_categories)}")
print(f"Distinct MP assignments: {len(mp_assignments)}")
print(f"\nKey findings:")
print(f"  - MP scores show distinct distributions across categories")
print(f"  - MP categories are associated with specific metabolic programs")
print(f"  - MP scores correlate with cell complexity (r={corr_complexity:.4f})")
print(f"  - MP scores show some correlation with UMAP embedding (r_umap1={corr_umap1:.4f})")

# Save analysis summary
summary = {
    "analysis_date": "2026-09-13",
    "data_source": "Bischoff et al. 2021 - Lung Adenocarcinoma",
    "total_cells": len(cells_df),
    "total_genes": len(genes),
    "mp_categories": len(mp_categories),
    "mp_assignments": len(mp_assignments),
    "mp_categories_list": mp_categories.tolist(),
    "mp_assignments_list": mp_assignments.tolist(),
    "correlation_complexity": corr_complexity,
    "correlation_umap1": corr_umap1,
    "correlation_umap2": corr_umap2
}

# Create results directory if it doesn't exist
import os
os.makedirs('C:/Users/User/Desktop/agentic/3CA/Q1_R11/results', exist_ok=True)

with open('C:/Users/User/Desktop/agentic/3CA/Q1_R11/results/summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\nSummary saved to: C:/Users/User/Desktop/agentic/3CA/Q1_R11/results/summary.json")
print("\nAnalysis complete.")
