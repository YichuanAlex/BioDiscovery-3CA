import json
import os

# Read core_result.json
core_path = "results/core_analysis/core_result.json"
with open(core_path, 'r', encoding='utf-8') as f:
    core_result = json.load(f)

print("=== core_result.json ===")
print(json.dumps(core_result, indent=2))
