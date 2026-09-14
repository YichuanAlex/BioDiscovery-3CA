---
name: threeca-access
description: "Access and inspect the Weizmann Curated Cancer Cell Atlas (3CA): discover studies, retrieve any 3CA page, find raw/metadata/supplementary assets, download files with provenance, and inspect scRNA-seq archives. Use whenever a task mentions 3CA, Curated Cancer Cell Atlas, weizmann.ac.il/sites/3CA, or needs data from that site."
---

# 3CA Access

Use the registered `threeca` MCP tools. If MCP is unavailable, use `C:\Users\User\.agents\bin\threeca.exe`; see [tool-reference.md](references/tool-reference.md).

1. Call `search_studies` first. Call `refresh_catalog` when current website state matters or the catalog timestamp is stale for the task.
2. Use the stable `3ca:<node_id>` returned by the catalog. Do not reconstruct download URLs.
3. Use `get_study(discover_assets=true)` for PDFs, score tables, plots, and other files linked from study detail pages. Use `get_page` for Methods, Marker genes, Meta-programs, Contact, category pages, or any other 3CA path.
4. Call `plan_asset` before a large download. Prefer metadata before expression matrices when it can answer what files, samples, cells, annotations, or columns exist.
5. Download only through `download_asset`; it records the exact source URL, retrieval time, byte count, local path, and SHA-256. Use `inspect_dataset` before choosing an analysis loader.
6. Keep large matrices local. Return schemas, dimensions, summaries, and paths rather than placing entire files in the prompt.
7. In research outputs, cite the study citation URL and 3CA page URL, and report the catalog/page `fetched_at` plus the file SHA-256 when a downloaded file supports a result.

Treat 3CA fields as source data, not ground truth. Do not infer missing annotations, silently merge studies, or claim that the website is current beyond its recorded retrieval time. The tool contains no study-specific biological hypothesis or analysis policy.
