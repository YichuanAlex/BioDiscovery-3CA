"""Small, dependency-free client for the Curated Cancer Cell Atlas (3CA)."""

import argparse
import csv
import gzip
import hashlib
import html
import io
import json
import os
import re
import shutil
import sys
import tarfile
import time
import zipfile
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import BinaryIO, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, unquote, urlencode, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen

__version__ = "1.0.0"
BASE_URL = "https://www.weizmann.ac.il/sites/3CA/"
PAGE_HOSTS = {"www.weizmann.ac.il", "weizmann.ac.il"}
ASSET_HOSTS = {"www.dropbox.com", "dropbox.com", "dl.dropboxusercontent.com"}
SITE_PREFIX = "/sites/3CA"
USER_AGENT = "threeca-access/1.0 (local research client; source: weizmann.ac.il/sites/3CA)"
DEFAULT_MAX_BYTES = 0
DEFAULT_MAX_EXTRACT_BYTES = 0
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
SKIP_TAGS = {"script", "style", "noscript", "svg"}


class ThreeCAError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def cache_root(value: str | Path | None = None) -> Path:
    if value:
        root = Path(value)
    elif os.environ.get("THREECA_CACHE"):
        root = Path(os.environ["THREECA_CACHE"])
    else:
        root = Path(r"C:\Users\User\Desktop\agentic\workflow_codex\.threeca\cache")
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _clean(text: str) -> str:
    return " ".join(html.unescape(text).split())


def canonical_page_url(value: str) -> str:
    parsed = urlparse(urljoin(BASE_URL, html.unescape(value.strip())))
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host not in PAGE_HOSTS or parsed.username or parsed.password:
        raise ThreeCAError("Page URL must be HTTPS on weizmann.ac.il.")
    if parsed.port not in (None, 443) or not (parsed.path == SITE_PREFIX or parsed.path.startswith(SITE_PREFIX + "/")):
        raise ThreeCAError(f"Page URL must stay under {SITE_PREFIX}/.")
    path = parsed.path + ("/" if parsed.path == SITE_PREFIX else "")
    return urlunparse(("https", "www.weizmann.ac.il", path, "", parsed.query, ""))


def canonical_asset_url(value: str) -> str:
    parsed = urlparse(html.unescape(value.strip()))
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host not in ASSET_HOSTS or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ThreeCAError("Asset URL must be an HTTPS Dropbox link discovered on a 3CA page.")
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["dl"] = "1"
    return urlunparse(("https", host, parsed.path, "", urlencode(query), ""))


def _validate_asset_transport_url(value: str) -> str:
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    allowed = host in ASSET_HOSTS or host.endswith(".dropboxusercontent.com")
    if parsed.scheme != "https" or not allowed or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ThreeCAError("Dropbox redirected the asset request outside the allowed HTTPS hosts.")
    return value


class _PageParser(HTMLParser):
    """Extract the main page text, links, and Drupal study tables."""

    def __init__(self, base_url: str):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.main_depth = 0
        self.skip_depth = 0
        self.hidden_depth = 0
        self.in_title = False
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self.links: list[dict[str, str]] = []
        self.anchor_href: str | None = None
        self.anchor_parts: list[str] = []
        self.in_table = False
        self.tables: list[list[list[dict[str, object]]]] = []
        self.table_rows: list[list[dict[str, object]]] = []
        self.row: list[dict[str, object]] | None = None
        self.cell: dict[str, object] | None = None

    @property
    def active(self) -> bool:
        return self.main_depth > 0 and self.skip_depth == 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        nonvoid = tag not in VOID_TAGS
        if self.main_depth:
            if nonvoid:
                self.main_depth += 1
        elif values.get("id") == "block-wis-theme-content":
            self.main_depth = 1

        if self.main_depth:
            if self.skip_depth:
                if nonvoid:
                    self.skip_depth += 1
            elif tag in SKIP_TAGS:
                self.skip_depth = 1
            if self.hidden_depth:
                if nonvoid:
                    self.hidden_depth += 1
            elif "visually-hidden" in values.get("class", "").split():
                self.hidden_depth = 1

        if tag == "title":
            self.in_title = True
        if not self.active:
            return
        if tag == "a" and self.anchor_href is None:
            self.anchor_href = values.get("href")
            self.anchor_parts = []
        if tag == "table" and "views-table" in values.get("class", "").split():
            self.in_table = True
            self.table_rows = []
        elif self.in_table and tag == "tr":
            self.row = []
        elif self.in_table and tag in {"th", "td"}:
            header = values.get("headers") or values.get("id") or ""
            self.cell = {"header": header, "text_parts": [], "links": []}

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if not self.active or self.hidden_depth:
            return
        self.text_parts.append(data)
        if self.anchor_href is not None:
            self.anchor_parts.append(data)
        if self.cell is not None:
            self.cell["text_parts"].append(data)  # type: ignore[index]

    def handle_endtag(self, tag: str) -> None:
        was_active = self.active
        if tag == "title":
            self.in_title = False
        if was_active:
            if tag == "a" and self.anchor_href is not None:
                link = {"url": urljoin(self.base_url, self.anchor_href), "text": _clean(" ".join(self.anchor_parts))}
                self.links.append(link)
                if self.cell is not None:
                    self.cell["links"].append(link)  # type: ignore[index]
                self.anchor_href = None
                self.anchor_parts = []
            elif self.in_table and tag in {"th", "td"} and self.cell is not None:
                self.cell["text"] = _clean(" ".join(self.cell.pop("text_parts")))  # type: ignore[arg-type]
                if self.row is not None:
                    self.row.append(self.cell)
                self.cell = None
            elif self.in_table and tag == "tr" and self.row is not None:
                if self.row:
                    self.table_rows.append(self.row)
                self.row = None
            elif self.in_table and tag == "table":
                self.tables.append(self.table_rows)
                self.table_rows = []
                self.in_table = False

        if self.main_depth:
            if self.hidden_depth:
                self.hidden_depth -= 1
            if self.skip_depth:
                self.skip_depth -= 1
            self.main_depth -= 1

    def result(self) -> dict[str, object]:
        unique_links: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for link in self.links:
            key = (link["url"], link["text"])
            if key not in seen:
                seen.add(key)
                unique_links.append(link)
        return {
            "title": _clean(" ".join(self.title_parts)),
            "text": _clean(" ".join(self.text_parts)),
            "links": unique_links,
            "tables": self.tables,
        }


def _open(request: Request, timeout: float | None = None):
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            return urlopen(request, timeout=timeout)
        except (HTTPError, URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(1 + attempt)
    raise ThreeCAError(f"Network request failed: {last_error}") from last_error


def fetch_page(value: str, cache: str | Path | None = None, force: bool = False) -> dict[str, object]:
    root = cache_root(cache)
    url = canonical_page_url(value)
    key = hashlib.sha256(url.encode()).hexdigest()
    record_path = root / "pages" / f"{key}.json"
    raw_path = root / "pages" / f"{key}.html"
    if record_path.exists() and raw_path.exists() and not force:
        record = json.loads(record_path.read_text(encoding="utf-8"))
        record["cache_hit"] = True
        return record

    response = _open(Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"}))
    with response:
        raw = response.read()
        final_url = response.geturl()
        canonical_page_url(final_url)
        charset = response.headers.get_content_charset() or "utf-8"
    text = raw.decode(charset, "replace")
    parser = _PageParser(final_url)
    parser.feed(text)
    record = {
        "url": url,
        "final_url": final_url,
        "fetched_at": _now(),
        "raw_html_path": str(raw_path),
        **parser.result(),
    }
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(raw)
    _write_json(record_path, record)
    record["cache_hit"] = False
    return record


def _field_name(header: str) -> str:
    name = header.removeprefix("view-").removesuffix("-table-column").removeprefix("field-")
    return {"meta-data": "metadata", "comments": "summary"}.get(name, name)


def _number(value: str) -> int | None:
    digits = re.sub(r"[^0-9]", "", value)
    return int(digits) if digits else None


def _category_links(home: dict[str, object]) -> list[dict[str, object]]:
    categories: list[dict[str, object]] = []
    seen: set[str] = set()
    pattern = re.compile(r"^(.*?)\s+#studies\s+(\d+)\s+#samples\s+(\d+)\s+#cells\s+(\d+)", re.I)
    for link in home["links"]:  # type: ignore[index]
        match = pattern.search(link["text"])  # type: ignore[index]
        if not match:
            continue
        try:
            url = canonical_page_url(link["url"])  # type: ignore[index]
        except ThreeCAError:
            # The homepage's "All cancers" card currently links to a Dropbox PDF.
            continue
        if url in seen:
            continue
        seen.add(url)
        categories.append({
            "name": match.group(1).strip(),
            "url": url,
            "reported_studies": int(match.group(2)),
            "reported_samples": int(match.group(3)),
            "reported_cells": int(match.group(4)),
        })
    if not categories:
        raise ThreeCAError("No cancer category links were found; the 3CA page structure may have changed.")
    return categories


def _homepage_totals(home: dict[str, object]) -> dict[str, int] | None:
    pattern = re.compile(r"^All cancers\s+#studies\s+(\d+)\s+#samples\s+(\d+)\s+#cells\s+(\d+)", re.I)
    for link in home["links"]:  # type: ignore[index]
        if match := pattern.search(link["text"]):  # type: ignore[index]
            return {"studies": int(match.group(1)), "samples": int(match.group(2)), "cells": int(match.group(3))}
    return None


def _study_rows(page: dict[str, object], category: dict[str, object]) -> list[dict[str, object]]:
    studies: list[dict[str, object]] = []
    for table in page["tables"]:  # type: ignore[index]
        for row in table:
            fields = {_field_name(cell["header"]): cell for cell in row if cell["header"]}  # type: ignore[index]
            if "title" not in fields or "data" not in fields:
                continue
            title = fields["title"]["text"]
            if title.casefold() == "title" and not fields["title"]["links"]:
                continue
            links = [link for cell in fields.values() for link in cell["links"]]
            node_ids = [match.group(1) for link in links if (match := re.search(r"/study-data/[^/]+/(\d+)(?:$|[?#])", link["url"]))]
            fallback = hashlib.sha1(f"{category['name']}|{title}".encode()).hexdigest()[:12]
            study_id = f"3ca:{node_ids[0] if node_ids else fallback}"
            assets: dict[str, str] = {}
            for kind in ("data", "metadata"):
                if kind in fields and fields[kind]["links"]:
                    assets[kind] = canonical_asset_url(fields[kind]["links"][0]["url"])
            detail_pages: dict[str, str] = {}
            for kind in ("cell-types", "summary", "meta-programs", "cnas", "umap", "cell-cycle"):
                if kind in fields and fields[kind]["links"]:
                    detail_pages[kind.replace("-", "_")] = canonical_page_url(fields[kind]["links"][0]["url"])
            citation_url = fields["title"]["links"][0]["url"] if fields["title"]["links"] else None
            studies.append({
                "id": study_id,
                "node_id": node_ids[0] if node_ids else None,
                "title": title,
                "category": category["name"],
                "category_url": category["url"],
                "citation_url": citation_url,
                "citation_doi_candidate": publication_doi_candidate(citation_url or ""),
                "disease": fields.get("disease", {}).get("text"),
                "technology": fields.get("technology", {}).get("text"),
                "samples": _number(fields.get("samples", {}).get("text", "")),
                "cells": _number(fields.get("cells", {}).get("text", "")),
                "assets": assets,
                "detail_pages": detail_pages,
            })
    return studies


def refresh_catalog(cache: str | Path | None = None, workers: int = 4) -> dict[str, object]:
    root = cache_root(cache)
    home = fetch_page(BASE_URL, root, force=True)
    categories = _category_links(home)
    pages: dict[str, dict[str, object]] = {}
    with ThreadPoolExecutor(max_workers=max(1, min(workers, 8))) as pool:
        futures = {pool.submit(fetch_page, category["url"], root, True): category for category in categories}
        for future in as_completed(futures):
            category = futures[future]
            pages[str(category["url"])] = future.result()
    studies = [study for category in categories for study in _study_rows(pages[str(category["url"])], category)]
    unique = {study["id"]: study for study in studies}
    if len(unique) != len(studies):
        raise ThreeCAError("Duplicate study identifiers found; refusing to write an ambiguous catalog.")
    studies.sort(key=lambda item: (str(item["category"]), str(item["title"])))
    parsed_totals = {
        "records": len(studies),
        "unique_citations": len({study["citation_url"] for study in studies if study["citation_url"]}),
        "samples": sum(study["samples"] or 0 for study in studies),
        "cells": sum(study["cells"] or 0 for study in studies),
    }
    homepage_totals = _homepage_totals(home)
    category_card_totals = {
        "records": sum(int(category["reported_studies"]) for category in categories),
        "samples": sum(int(category["reported_samples"]) for category in categories),
        "cells": sum(int(category["reported_cells"]) for category in categories),
    }
    warnings = []
    if homepage_totals and any(parsed_totals[key] != homepage_totals[key] for key in ("samples", "cells")):
        warnings.append("Parsed category rows do not equal the homepage totals; both values are preserved.")
    if any(parsed_totals[key] != category_card_totals[key] for key in ("records", "samples", "cells")):
        warnings.append("Parsed category rows do not equal the category-card totals; both values are preserved.")
    catalog = {
        "schema_version": 1,
        "source_url": BASE_URL,
        "fetched_at": _now(),
        "categories": categories,
        "studies": studies,
        "totals": {"categories": len(categories), "parsed": parsed_totals, "homepage_reported": homepage_totals, "category_cards_reported": category_card_totals},
        "data_quality_warnings": warnings,
    }
    _write_json(root / "catalog.json", catalog)
    return {**catalog, "catalog_path": str(root / "catalog.json")}


def catalog_summary(catalog: dict[str, object], cache: str | Path | None = None) -> dict[str, object]:
    return {
        "source_url": catalog["source_url"],
        "fetched_at": catalog["fetched_at"],
        "totals": catalog["totals"],
        "data_quality_warnings": catalog.get("data_quality_warnings", []),
        "catalog_path": str(cache_root(cache) / "catalog.json"),
    }


def load_catalog(cache: str | Path | None = None) -> dict[str, object]:
    path = cache_root(cache) / "catalog.json"
    if not path.exists():
        return refresh_catalog(cache)
    return json.loads(path.read_text(encoding="utf-8"))


def search_studies(
    query: str = "",
    category: str = "",
    disease: str = "",
    technology: str = "",
    min_samples: int = 0,
    min_cells: int = 0,
    asset: str = "",
    cache: str | Path | None = None,
) -> dict[str, object]:
    catalog = load_catalog(cache)
    needles = [value.casefold() for value in (query, category, disease, technology)]
    matches = []
    for study in catalog["studies"]:  # type: ignore[index]
        haystack = " ".join(str(study.get(key) or "") for key in ("title", "category", "disease", "technology")).casefold()
        if needles[0] and needles[0] not in haystack:
            continue
        if needles[1] and needles[1] not in str(study.get("category") or "").casefold():
            continue
        if needles[2] and needles[2] not in str(study.get("disease") or "").casefold():
            continue
        if needles[3] and needles[3] not in str(study.get("technology") or "").casefold():
            continue
        if (study.get("samples") or 0) < min_samples or (study.get("cells") or 0) < min_cells:
            continue
        if asset and asset not in study.get("assets", {}):
            continue
        matches.append(study)
    return {"catalog_fetched_at": catalog["fetched_at"], "count": len(matches), "studies": matches}


def publication_doi_candidate(value: str) -> str | None:
    """Extract a DOI candidate from a DOI or publisher URL; Crossref must still verify it."""
    value = unquote(value.strip())
    match = re.search(r"10\.\d{4,9}/[^?#\s]+", value, re.I)
    if match:
        return match.group(0)
    parsed = urlparse(value)
    article = re.fullmatch(r"/articles/([A-Za-z0-9.-]+)", parsed.path)
    if parsed.hostname in {"nature.com", "www.nature.com"} and article:
        return "10.1038/" + article.group(1)
    return None


def get_study(study_id: str, cache: str | Path | None = None, discover_assets: bool = False) -> dict[str, object]:
    catalog = load_catalog(cache)
    normalized = study_id if study_id.startswith("3ca:") else f"3ca:{study_id}"
    study = next((dict(item) for item in catalog["studies"] if item["id"] == normalized), None)  # type: ignore[index]
    if study is None:
        raise ThreeCAError(f"Unknown study id: {study_id}")
    study["catalog_fetched_at"] = catalog["fetched_at"]
    study["citation_doi_candidate"] = publication_doi_candidate(str(study.get("citation_url") or ""))
    study["publication_verification_call"] = {"tool": "verify_doi", "arguments": {"doi": normalized}, "note": "Resolve the original catalog publication via Crossref; do not guess its title or journal using generic web search."}
    if discover_assets:
        study["discovered_assets"] = discover_study_assets(study, cache)
    return study


def _is_asset_url(value: str) -> bool:
    return (urlparse(value).hostname or "").lower() in ASSET_HOSTS


def discover_study_assets(study: dict[str, object] | str, cache: str | Path | None = None) -> list[dict[str, str]]:
    if isinstance(study, str):
        study = get_study(study, cache)
    assets = [
        {"kind": kind, "url": url, "source_page": str(study["category_url"]), "label": kind}
        for kind, url in study["assets"].items()  # type: ignore[union-attr]
    ]
    for kind, url in study["detail_pages"].items():  # type: ignore[union-attr]
        page = fetch_page(url, cache)
        for link in page["links"]:  # type: ignore[index]
            if _is_asset_url(link["url"]):
                assets.append({"kind": str(kind), "url": canonical_asset_url(link["url"]), "source_page": str(url), "label": link["text"]})
    unique: dict[str, dict[str, str]] = {}
    for asset in assets:
        unique[asset["url"]] = asset
    return list(unique.values())


def search_pages(query: str, cache: str | Path | None = None, limit: int = 20) -> dict[str, object]:
    root = cache_root(cache)
    needle = query.casefold().strip()
    if not needle:
        raise ThreeCAError("Page search query cannot be empty.")
    matches = []
    for path in (root / "pages").glob("*.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        text = str(record.get("text") or "")
        position = text.casefold().find(needle)
        if position >= 0 or needle in str(record.get("title") or "").casefold():
            start = max(0, position - 180) if position >= 0 else 0
            matches.append({"url": record["url"], "title": record.get("title"), "fetched_at": record.get("fetched_at"), "snippet": text[start : start + 500]})
            if len(matches) >= limit:
                break
    return {"query": query, "count": len(matches), "matches": matches}


def crawl_site(cache: str | Path | None = None, max_pages: int = 0, workers: int = 4, force: bool = False) -> dict[str, object]:
    if max_pages < 0:
        raise ThreeCAError("max_pages must be non-negative; zero means unlimited.")
    root = cache_root(cache)
    catalog = load_catalog(root)
    seeds = [BASE_URL, urljoin(BASE_URL, "methods"), urljoin(BASE_URL, "contact-us"), urljoin(BASE_URL, "search-genes"), urljoin(BASE_URL, "marker-genes")]
    seeds += [str(item["url"]) for item in catalog["categories"]]  # type: ignore[index]
    for study in catalog["studies"]:  # type: ignore[index]
        seeds.extend(study["detail_pages"].values())
    queue = deque(dict.fromkeys(canonical_page_url(url) for url in seeds))
    queued = set(queue)
    seen: set[str] = set()
    errors: list[dict[str, str]] = []
    cache_hits = 0
    while queue and (not max_pages or len(seen) < max_pages):
        remaining = max_pages - len(seen) if max_pages else len(queue)
        batch = [queue.popleft() for _ in range(min(max(1, workers), remaining, len(queue)))]
        with ThreadPoolExecutor(max_workers=max(1, min(workers, 8))) as pool:
            futures = {pool.submit(fetch_page, url, root, force): url for url in batch}
            for future in as_completed(futures):
                url = futures[future]
                seen.add(url)
                try:
                    page = future.result()
                    cache_hits += int(bool(page.get("cache_hit")))
                    for link in page["links"]:  # type: ignore[index]
                        try:
                            child = canonical_page_url(link["url"])
                        except ThreeCAError:
                            continue
                        if child not in seen and child not in queued and (not max_pages or len(queued) < max_pages * 2):
                            queued.add(child)
                            queue.append(child)
                except Exception as exc:
                    errors.append({"url": url, "error": str(exc)})
    return {"catalog_fetched_at": catalog["fetched_at"], "pages_processed": len(seen), "cache_hits": cache_hits, "errors": errors, "cache_root": str(root)}


def _known_asset_urls(cache: str | Path | None = None) -> set[str]:
    root = cache_root(cache)
    known: set[str] = set()
    catalog = load_catalog(root)
    for study in catalog["studies"]:  # type: ignore[index]
        known.update(study["assets"].values())
    for path in (root / "pages").glob("*.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        for link in record.get("links", []):
            if _is_asset_url(link["url"]):
                known.add(canonical_asset_url(link["url"]))
    return known


def resolve_asset(target: str, kind: str = "", cache: str | Path | None = None) -> str:
    if target.startswith("https://"):
        url = canonical_asset_url(target)
        if url not in _known_asset_urls(cache):
            raise ThreeCAError("Asset URL was not found in the catalog or a cached 3CA page. Fetch its 3CA page first.")
        return url
    if not kind:
        raise ThreeCAError("A study target requires --kind (data, metadata, or a discovered detail kind).")
    study = get_study(target, cache)
    if kind in study["assets"]:
        return study["assets"][kind]  # type: ignore[index]
    matches = [asset for asset in discover_study_assets(study, cache) if asset["kind"] == kind]
    if len(matches) == 1:
        return matches[0]["url"]
    if not matches:
        raise ThreeCAError(f"Study has no asset kind '{kind}'.")
    raise ThreeCAError(f"Asset kind '{kind}' has multiple files; use the exact URL returned by show --discover-assets.")


def _filename(headers, url: str) -> str:
    disposition = headers.get("Content-Disposition", "")
    extended = re.search(r"filename\*=UTF-8''([^;]+)", disposition, re.I)
    regular = re.search(r'filename="?([^";]+)', disposition, re.I)
    name = unquote((extended or regular).group(1)) if (extended or regular) else unquote(Path(urlparse(url).path).name)
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
    return name or hashlib.sha256(url.encode()).hexdigest()[:16]


def plan_asset(target: str, kind: str = "", cache: str | Path | None = None) -> dict[str, object]:
    url = resolve_asset(target, kind, cache)
    try:
        response = _open(Request(url, method="HEAD", headers={"User-Agent": USER_AGENT}))
    except ThreeCAError:
        response = _open(Request(url, headers={"User-Agent": USER_AGENT, "Range": "bytes=0-0"}))
    with response:
        headers = response.headers
        final_url = _validate_asset_transport_url(response.geturl())
        length = headers.get("Content-Length")
        content_range = headers.get("Content-Range", "")
        if match := re.search(r"/(\d+)$", content_range):
            length = match.group(1)
        return {
            "source_url": url,
            "final_url": final_url,
            "filename": _filename(headers, final_url),
            "content_length": int(length) if length and length.isdigit() else None,
            "content_type": headers.get_content_type(),
            "planned_at": _now(),
        }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_asset(
    target: str,
    kind: str = "",
    cache: str | Path | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
    extract: bool = False,
    max_extract_bytes: int = DEFAULT_MAX_EXTRACT_BYTES,
) -> dict[str, object]:
    root = cache_root(cache)
    plan = plan_asset(target, kind, root)
    if max_bytes and plan["content_length"] and plan["content_length"] > max_bytes:
        raise ThreeCAError(f"Remote asset is {plan['content_length']} bytes, above max_bytes={max_bytes}.")
    asset_key = hashlib.sha256(str(plan["source_url"]).encode()).hexdigest()[:12]
    destination = root / "downloads" / asset_key / str(plan["filename"])
    manifest_path = destination.with_suffix(destination.suffix + ".manifest.json")
    if destination.exists() and manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("bytes") == destination.stat().st_size:
            result = {**manifest, "cache_hit": True}
            if extract:
                result["extraction"] = extract_archive(destination, max_extract_bytes)
            return result

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + f".{os.getpid()}.part")
    digest = hashlib.sha256()
    total = 0
    try:
        response = _open(Request(str(plan["source_url"]), headers={"User-Agent": USER_AGENT}))
        with response, temporary.open("wb") as output:
            _validate_asset_transport_url(response.geturl())
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if max_bytes and total > max_bytes:
                    raise ThreeCAError(f"Download exceeded max_bytes={max_bytes}.")
                output.write(chunk)
                digest.update(chunk)
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    manifest = {
        **plan,
        "path": str(destination),
        "bytes": total,
        "sha256": digest.hexdigest(),
        "downloaded_at": _now(),
        "cache_hit": False,
    }
    _write_json(manifest_path, manifest)
    if extract:
        manifest["extraction"] = extract_archive(destination, max_extract_bytes)
    return manifest


def _safe_member(name: str) -> None:
    normalized = name.replace("\\", "/")
    if normalized.startswith("/") or re.match(r"^[A-Za-z]:", normalized) or ".." in Path(normalized).parts:
        raise ThreeCAError(f"Unsafe archive member path: {name}")


def _archive_stem(path: Path) -> str:
    name = path.name
    for suffix in (".tar.gz", ".tar.bz2", ".tar.xz", ".tgz", ".zip", ".gz"):
        if name.lower().endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


def extract_archive(path: str | Path, max_extract_bytes: int = DEFAULT_MAX_EXTRACT_BYTES) -> dict[str, object]:
    source = Path(path).resolve()
    destination = source.parent / (_archive_stem(source) + ".extracted")
    if destination.exists():
        return {"path": str(destination), "cache_hit": True}
    temporary = source.parent / (destination.name + f".{os.getpid()}.part")
    temporary.mkdir(parents=True, exist_ok=False)
    try:
        if tarfile.is_tarfile(source):
            with tarfile.open(source) as archive:
                members = archive.getmembers()
                for member in members:
                    _safe_member(member.name)
                total = sum(member.size for member in members if member.isfile())
                if max_extract_bytes and total > max_extract_bytes:
                    raise ThreeCAError(f"Expanded archive is {total} bytes, above max_extract_bytes={max_extract_bytes}.")
                archive.extractall(temporary, filter="data")
        elif zipfile.is_zipfile(source):
            with zipfile.ZipFile(source) as archive:
                infos = archive.infolist()
                for info in infos:
                    _safe_member(info.filename)
                    if (info.external_attr >> 16) & 0o170000 == 0o120000:
                        raise ThreeCAError(f"Archive symlink is not allowed: {info.filename}")
                total = sum(info.file_size for info in infos)
                if max_extract_bytes and total > max_extract_bytes:
                    raise ThreeCAError(f"Expanded archive is {total} bytes, above max_extract_bytes={max_extract_bytes}.")
                archive.extractall(temporary)
        elif source.suffix.lower() == ".gz":
            total = 0
            output = temporary / source.stem
            with gzip.open(source, "rb") as compressed, output.open("wb") as uncompressed:
                while chunk := compressed.read(1024 * 1024):
                    total += len(chunk)
                    if max_extract_bytes and total > max_extract_bytes:
                        raise ThreeCAError(f"Expanded file exceeded max_extract_bytes={max_extract_bytes}.")
                    uncompressed.write(chunk)
        else:
            raise ThreeCAError("Supported extraction formats: tar.*, zip, and gzip.")
        temporary.replace(destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return {"path": str(destination), "cache_hit": False}


def _preview_text(stream: BinaryIO, name: str, sample_rows: int) -> dict[str, object] | None:
    lower = name.lower()
    with io.TextIOWrapper(stream, encoding="utf-8-sig", errors="replace", newline="") as wrapper:
        if lower.endswith(".mtx"):
            for line in wrapper:
                if not line.startswith("%") and line.strip():
                    parts = line.split()
                    return {"name": name, "format": "matrix-market", "dimensions": [int(value) for value in parts[:3]] if len(parts) >= 3 and all(value.isdigit() for value in parts[:3]) else parts[:3]}
            return None
        if not lower.endswith((".csv", ".tsv", ".txt")):
            return None
        delimiter = "\t" if lower.endswith((".tsv", ".txt")) else ","
        reader = csv.reader(wrapper, delimiter=delimiter)
        rows = []
        for _, row in zip(range(sample_rows + 1), reader):
            rows.append(row)
        return {"name": name, "format": "delimited-text", "delimiter": delimiter, "columns": rows[0] if rows else [], "sample_rows": rows[1:]}


def inspect_dataset(path: str | Path, sample_rows: int = 3, max_members: int = 5000) -> dict[str, object]:
    source = Path(path).resolve()
    if source.is_dir():
        entries = []
        truncated = False
        # ponytail: shallow listing capped at 100; inspect a returned file for content, not the whole tree.
        with os.scandir(source) as items:
            for entry in items:
                if len(entries) >= min(max_members, 100):
                    truncated = True
                    break
                entries.append({"name": entry.name, "type": "symlink" if entry.is_symlink() else "directory" if entry.is_dir(follow_symlinks=False) else "file"})
        return {"path": str(source), "format": "directory", "inspected_at": _now(), "entries": entries, "entries_truncated": truncated, "previews": [], "instruction": "This existing directory is only a file listing, not a table or matrix preview. Inspect an actual returned file name; do not invent paths."}
    if not source.is_file():
        raise ThreeCAError(f"Dataset file not found: {source}")
    result: dict[str, object] = {"path": str(source), "bytes": source.stat().st_size, "inspected_at": _now()}
    members: list[dict[str, object]] = []
    previews: list[dict[str, object]] = []
    if tarfile.is_tarfile(source):
        result["format"] = "tar"
        with tarfile.open(source) as archive:
            infos = archive.getmembers()
            for info in infos[:max_members]:
                _safe_member(info.name)
                members.append({"name": info.name, "bytes": info.size, "type": "file" if info.isfile() else "directory"})
                if info.isfile() and len(previews) < 20 and (stream := archive.extractfile(info)):
                    with stream:
                        if preview := _preview_text(stream, info.name, sample_rows):
                            previews.append(preview)
            result["member_count"] = len(infos)
    elif zipfile.is_zipfile(source):
        result["format"] = "zip"
        with zipfile.ZipFile(source) as archive:
            infos = archive.infolist()
            for info in infos[:max_members]:
                _safe_member(info.filename)
                members.append({"name": info.filename, "bytes": info.file_size, "type": "directory" if info.is_dir() else "file"})
                if not info.is_dir() and len(previews) < 20:
                    with archive.open(info) as stream:
                        if preview := _preview_text(stream, info.filename, sample_rows):
                            previews.append(preview)
            result["member_count"] = len(infos)
    elif source.suffix.lower() == ".gz":
        result["format"] = "gzip"
        with gzip.open(source, "rb") as stream:
            if preview := _preview_text(stream, source.stem, sample_rows):
                previews.append(preview)
    else:
        result["format"] = "file"
        with source.open("rb") as stream:
            if preview := _preview_text(stream, source.name, sample_rows):
                previews.append(preview)
    result["members"] = members
    result["members_truncated"] = bool(result.get("member_count", 0) > len(members))
    result["previews"] = previews
    return result


def verify_dataset(path: str | Path) -> dict[str, object]:
    source = Path(path).resolve()
    if not source.is_file():
        raise ThreeCAError(f"Dataset file not found: {source}")
    archive_ok = None
    if tarfile.is_tarfile(source):
        with tarfile.open(source) as archive:
            for info in archive.getmembers():
                _safe_member(info.name)
        archive_ok = True
    elif zipfile.is_zipfile(source):
        with zipfile.ZipFile(source) as archive:
            bad = archive.testzip()
        archive_ok = bad is None
    elif source.suffix.lower() == ".gz":
        with gzip.open(source, "rb") as stream:
            for _ in iter(lambda: stream.read(1024 * 1024), b""):
                pass
        archive_ok = True
    manifest_path = source.with_suffix(source.suffix + ".manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
    digest = _sha256(source)
    return {
        "path": str(source),
        "bytes": source.stat().st_size,
        "sha256": digest,
        "archive_ok": archive_ok,
        "manifest_match": None if not manifest else manifest.get("sha256") == digest and manifest.get("bytes") == source.stat().st_size,
        "verified_at": _now(),
    }


def _output(value: object, pretty: bool) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2 if pretty else None))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="threeca", description="Traceable access to the Curated Cancer Cell Atlas")
    parser.add_argument("--cache", help="Cache directory (default: workflow-local .threeca/cache)")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    refresh = commands.add_parser("refresh", help="Refresh the complete study catalog")
    refresh.add_argument("--workers", type=int, default=4)
    search = commands.add_parser("search", help="Search studies")
    search.add_argument("query", nargs="?", default="")
    search.add_argument("--category", default="")
    search.add_argument("--disease", default="")
    search.add_argument("--technology", default="")
    search.add_argument("--min-samples", type=int, default=0)
    search.add_argument("--min-cells", type=int, default=0)
    search.add_argument("--asset", choices=("", "data", "metadata"), default="")
    show = commands.add_parser("show", help="Show one study by 3CA id")
    show.add_argument("study_id")
    show.add_argument("--discover-assets", action="store_true")
    page = commands.add_parser("page", help="Fetch any page under the 3CA site")
    page.add_argument("url_or_path")
    page.add_argument("--force", action="store_true")
    page.add_argument("--max-chars", type=int, default=0, help="Limit returned normalized text; raw HTML is always cached")
    page_search = commands.add_parser("page-search", help="Search cached 3CA page text")
    page_search.add_argument("query")
    page_search.add_argument("--limit", type=int, default=20)
    crawl = commands.add_parser("crawl", help="Cache all discoverable 3CA content pages")
    crawl.add_argument("--max-pages", type=int, default=0, help="Optional page ceiling; zero crawls all discoverable pages")
    crawl.add_argument("--workers", type=int, default=4)
    crawl.add_argument("--force", action="store_true")
    plan = commands.add_parser("plan", help="Inspect an asset before downloading")
    plan.add_argument("target", help="Study id or discovered Dropbox URL")
    plan.add_argument("--kind", default="")
    download = commands.add_parser("download", help="Download a cataloged or discovered asset")
    download.add_argument("target")
    download.add_argument("--kind", default="")
    download.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    download.add_argument("--extract", action="store_true")
    download.add_argument("--max-extract-bytes", type=int, default=DEFAULT_MAX_EXTRACT_BYTES)
    inspect = commands.add_parser("inspect", help="List archive members and preview tabular schemas")
    inspect.add_argument("path")
    inspect.add_argument("--sample-rows", type=int, default=3)
    verify = commands.add_parser("verify", help="Hash and validate a downloaded file")
    verify.add_argument("path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "refresh":
            result = catalog_summary(refresh_catalog(args.cache, args.workers), args.cache)
        elif args.command == "search":
            result = search_studies(args.query, args.category, args.disease, args.technology, args.min_samples, args.min_cells, args.asset, args.cache)
        elif args.command == "show":
            result = get_study(args.study_id, args.cache, args.discover_assets)
        elif args.command == "page":
            result = fetch_page(args.url_or_path, args.cache, args.force)
            if args.max_chars and len(result["text"]) > args.max_chars:
                result = {**result, "text": result["text"][: args.max_chars], "text_truncated": True}
        elif args.command == "page-search":
            result = search_pages(args.query, args.cache, args.limit)
        elif args.command == "crawl":
            result = crawl_site(args.cache, args.max_pages, args.workers, args.force)
        elif args.command == "plan":
            result = plan_asset(args.target, args.kind, args.cache)
        elif args.command == "download":
            result = download_asset(args.target, args.kind, args.cache, args.max_bytes, args.extract, args.max_extract_bytes)
        elif args.command == "inspect":
            result = inspect_dataset(args.path, args.sample_rows)
        else:
            result = verify_dataset(args.path)
        _output(result, args.pretty)
        return 0
    except (ThreeCAError, OSError, ValueError, tarfile.TarError, zipfile.BadZipFile) as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
