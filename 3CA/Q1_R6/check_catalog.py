import json
import os

cache_dir = r"C:\Users\User\Desktop\agentic\workflow_codex\.threeca\cache"
catalog_path = os.path.join(cache_dir, "catalog.json")

if not os.path.exists(catalog_path):
    print("Catalog not found at", catalog_path)
    exit(1)

with open(catalog_path) as f:
    data = json.load(f)

print("Categories:", len(data["categories"]))
for c in data["categories"]:
    print(f"  {c['name']}: {len(c.get('studies',[]))} studies")
