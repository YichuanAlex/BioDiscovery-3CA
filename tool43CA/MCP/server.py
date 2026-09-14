"""stdio MCP facade for the threeca-access package."""

from pathlib import Path

from mcp.server.fastmcp import FastMCP

import threeca

mcp = FastMCP("threeca")


def _cache_path(path: str) -> str:
    candidate = Path(path).resolve()
    root = threeca.cache_root()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"MCP file access is limited to the 3CA cache: {root}")
    return str(candidate)


@mcp.tool()
def refresh_catalog() -> dict:
    """Refresh all 3CA cancer-category tables and return counts, data-quality warnings, and the catalog path."""
    return threeca.catalog_summary(threeca.refresh_catalog())


@mcp.tool()
def search_studies(query: str = "", category: str = "", disease: str = "", technology: str = "", min_samples: int = 0, min_cells: int = 0, asset: str = "") -> dict:
    """Search the cached 3CA catalog; asset may be data or metadata."""
    return threeca.search_studies(query, category, disease, technology, min_samples, min_cells, asset)


@mcp.tool()
def get_study(study_id: str, discover_assets: bool = False) -> dict:
    """Get one study by stable 3CA id; optionally visit its detail pages to discover supplementary files."""
    return threeca.get_study(study_id, discover_assets=discover_assets)


@mcp.tool()
def get_page(url_or_path: str, force: bool = False, max_chars: int = 30000) -> dict:
    """Fetch any HTTPS page under weizmann.ac.il/sites/3CA, preserving raw HTML in the local cache."""
    result = threeca.fetch_page(url_or_path, force=force)
    if max_chars > 0 and len(result["text"]) > max_chars:
        result = {**result, "text": result["text"][:max_chars], "text_truncated": True}
    return result


@mcp.tool()
def search_cached_pages(query: str, limit: int = 20) -> dict:
    """Full-text search normalized content from 3CA pages already fetched or crawled."""
    return threeca.search_pages(query, limit=limit)


@mcp.tool()
def crawl_site(max_pages: int = 1500, force: bool = False) -> dict:
    """Cache discoverable 3CA content pages and raw HTML; use force only to refresh every page."""
    return threeca.crawl_site(max_pages=max_pages, force=force)


@mcp.tool()
def plan_asset(target: str, kind: str = "") -> dict:
    """Resolve a study asset or discovered Dropbox URL and report its name, type, and remote size without downloading it."""
    return threeca.plan_asset(target, kind)


@mcp.tool()
def download_asset(target: str, kind: str = "", extract: bool = False, max_bytes: int = threeca.DEFAULT_MAX_BYTES, max_extract_bytes: int = threeca.DEFAULT_MAX_EXTRACT_BYTES) -> dict:
    """Download a cataloged 3CA file into the fixed local cache with SHA-256 provenance and optional safe extraction."""
    return threeca.download_asset(target, kind, max_bytes=max_bytes, extract=extract, max_extract_bytes=max_extract_bytes)


@mcp.tool()
def inspect_dataset(path: str, sample_rows: int = 3) -> dict:
    """Inspect an archive or table in the 3CA cache without loading a full expression matrix into the model context."""
    return threeca.inspect_dataset(_cache_path(path), sample_rows)


@mcp.tool()
def verify_dataset(path: str) -> dict:
    """Compute SHA-256, check archive integrity, and compare the download manifest for a cached 3CA file."""
    return threeca.verify_dataset(_cache_path(path))


if __name__ == "__main__":
    mcp.run(transport="stdio")
