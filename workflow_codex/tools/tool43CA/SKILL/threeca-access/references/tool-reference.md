# Tool reference

The MCP server exposes: `refresh_catalog`, `search_studies`, `get_study`, `get_page`, `search_cached_pages`, `crawl_site`, `plan_asset`, `download_asset`, `inspect_dataset`, and `verify_dataset`.

CLI equivalents return JSON on stdout and errors on stderr:

```powershell
$threeca = 'C:\Users\User\Desktop\agentic\workflow_codex\tools\tool43CA\.venv\Scripts\threeca.exe'
& $threeca --pretty refresh
& $threeca --pretty search 'author or disease' --category lung --technology 10x
& $threeca --pretty show 20764 --discover-assets
& $threeca --pretty page methods
& $threeca --pretty page-search 'normalization'
& $threeca --pretty crawl --max-pages 1500
& $threeca --pretty plan 20764 --kind metadata
& $threeca --pretty download 20764 --kind metadata --extract
& $threeca --pretty inspect 'C:\Users\User\Desktop\agentic\workflow_codex\.threeca\cache\downloads\FILE.tar.gz'
& $threeca --pretty verify 'C:\Users\User\Desktop\agentic\workflow_codex\.threeca\cache\downloads\FILE.tar.gz'
```

For a supplementary URL, first fetch its 3CA detail page (or use `show --discover-assets`), then pass the exact returned Dropbox URL to `plan` or `download`. Direct arbitrary URLs are rejected. Download and safe-extraction sizes have no workflow ceiling; source validation, archive traversal guards, available disk, and operating-system limits still apply.

`get_page` caches both normalized content and the unmodified response HTML. MCP text is capped by default, but `raw_html_path` identifies the complete local copy. `crawl_site` starts from all catalog categories and every cataloged study-detail page; `search_cached_pages` searches that local corpus.
