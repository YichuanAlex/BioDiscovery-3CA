---
name: threeca-access
description: "Access and inspect the Weizmann Curated Cancer Cell Atlas (3CA): discover studies, retrieve any 3CA page, find raw/metadata/supplementary assets, download files with provenance, and inspect scRNA-seq archives. Use whenever a task mentions 3CA, Curated Cancer Cell Atlas, weizmann.ac.il/sites/3CA, or needs data from that site."
---

# 3CA Access

Use the project-registered `threeca` MCP tools. If MCP is unavailable, use `C:\Users\User\Desktop\agentic\workflow_codex\tools\tool43CA\.venv\Scripts\threeca.exe`; see [tool-reference.md](references/tool-reference.md).

1. Call `search_studies` first. Call `refresh_catalog` when current website state matters or the catalog timestamp is stale for the task. Once a viable result exists, select by recorded criteria and continue with stable study ids; do not enumerate every category or repeat an identical catalog/CLI search. If a result says it was truncated, narrow filters instead of requesting the same broad result. Prefer the registered tools while they work; use the CLI only as a fallback.
2. Use the stable `3ca:<node_id>` returned by the catalog. Do not reconstruct download URLs.
   The catalog JSON stores studies in the top-level `studies` array. `categories` contains category summaries, not nested study arrays. Use the exact returned study `id`, never its list position or a category number.
3. Use `get_study(discover_assets=true)` for PDFs, score tables, plots, and other files linked from study detail pages. Use `get_page` for Methods, Marker genes, Meta-programs, Contact, category pages, or any other 3CA path.
4. Call `plan_asset` before a large download. Prefer metadata before expression matrices when it can answer what files, samples, cells, annotations, or columns exist.
5. Download only through `download_asset`; it records the exact source URL, retrieval time, byte count, local path, and SHA-256. Use `inspect_dataset` before choosing an analysis loader. For a directory it returns only actual shallow file names, not matrix validation; inspect a returned file name rather than inventing paths.
6. Keep large matrices local. Return schemas, dimensions, summaries, and paths rather than placing entire files in the prompt.
7. In research outputs, cite the study citation URL and 3CA page URL, and report the catalog/page `fetched_at` plus the file SHA-256 when a downloaded file supports a result.

Treat 3CA fields as source data, not ground truth. Do not infer missing annotations, silently merge studies, or claim that the website is current beyond its recorded retrieval time. The tool contains no study-specific biological hypothesis or analysis policy.

For long research tasks, save the selected study id, source/metadata schemas, downloaded file paths and hashes, executed commands, and the next action using `task_checkpoint` when available. Work on one verified phase at a time. A successful download is not a validated analysis; inspect actual headers and matrix orientation before writing a loader, test it on a small slice, then validate the full dimensions and sample/cell alignment. Never copy prior reports or computed results as new evidence.

For citations, save the retrieved primary article/DOI metadata before drafting BibTeX. Treat cookie challenges and missing fields as missing evidence, not permission to guess. Report only statistics that the executed code actually computed. Write UTF-8 source files with the file tools, use unique local edits for repairs, rerun validation after changes, and check that earlier outputs still pass. Persist visible evidence and pending actions, not invented reasoning. Submit `complete_task` only after real artifacts and successful verification exist; its acceptance is structural, not scientific.
