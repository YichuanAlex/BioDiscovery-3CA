import hashlib
import json

# Compute SHA-256 of core_result.json
with open("results/core_analysis/core_result.json", "rb") as f:
    core_sha = hashlib.sha256(f.read()).hexdigest()
print(f"core_result.json SHA-256: {core_sha}")

# Compute SHA-256 of each figure
figures = [
    "figures/metabolic_umap.pdf",
    "figures/clustering_diagnostics.pdf",
    "figures/cd8_analysis/metabolic_umap.pdf",
    "figures/cd8_analysis/clustering_diagnostics.pdf"
]

for fig in figures:
    try:
        with open(fig, "rb") as f:
            sha = hashlib.sha256(f.read()).hexdigest()
        print(f"{fig} SHA-256: {sha}")
    except FileNotFoundError:
        print(f"{fig} NOT FOUND")

# Compute SHA-256 of analysis_manifest.json
with open("results/analysis_manifest.json", "rb") as f:
    manifest_sha = hashlib.sha256(f.read()).hexdigest()
print(f"analysis_manifest.json SHA-256: {manifest_sha}")

# Read core_result.json to get parameters
with open("results/core_analysis/core_result.json", "r") as f:
    core = json.load(f)
print(f"\nCore parameters.seeds: {core.get('parameters', {}).get('seeds', 'N/A')}")
print(f"Core random_seeds in methods: {core.get('methods', {}).get('control_partition', {}).get('seed', 'N/A')}")
