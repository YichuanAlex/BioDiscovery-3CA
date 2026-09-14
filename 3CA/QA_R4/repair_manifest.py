import json
import os

# Read current manifest
manifest_path = "results/analysis_manifest.json"
with open(manifest_path, 'r', encoding='utf-8') as f:
    manifest = json.load(f)

print("=== CURRENT MANIFEST ===")
print(json.dumps(manifest, indent=2))

# Read core results
core_path = "results/core_analysis/core_result.json"
with open(core_path, 'r', encoding='utf-8') as f:
    core = json.load(f)

print("\n=== CORE RESULT ===")
print(json.dumps(core, indent=2))

# Read summary
summary_path = "results/summary.json"
with open(summary_path, 'r', encoding='utf-8') as f:
    summary = json.load(f)

print("\n=== SUMMARY ===")
print(json.dumps(summary, indent=2))

# Check cells.csv for cell_id_field
cells_path = "inputs/Cells.csv"
if os.path.exists(cells_path):
    with open(cells_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        if len(lines) > 0:
            header = lines[0].strip()
            print(f"\n=== CELLS.CSV HEADER ===")
            print(header)
            # Find cell_id field
            for i, col in enumerate(header.split(',')):
                if 'cell' in col.lower():
                    print(f"Cell-related column {i}: {col}")
