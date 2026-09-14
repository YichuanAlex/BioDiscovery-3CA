#!/usr/bin/env python3
"""Build the metabolic scRNA-seq benchmark curation release with stdlib only."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import mimetypes
import re
import shutil
import subprocess
import tarfile
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
SEED_FILE = HERE / "curation_seed.json"
SOURCE_GENESET = HERE.parent / "data" / "metabolic genes total.csv"
OUT = HERE / "metabolic_scRNA_benchmark_v0.1"
PRIVATE_OUT = HERE / "metabolic_scRNA_benchmark_v0.1_private"
LOCAL_ARTICLES = {
    "10.1038/s41586-023-06130-4": HERE.parent / "material" / "2023-Nature-Hallmarks of transcriptional intratumour.pdf"
}
USER_AGENT = "metabolic-scRNA-benchmark-curation/0.1 (academic OA retrieval)"
NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

ACCESSION_RE = re.compile(
    r"\b(?:GSE\d+|GSM\d+|PRJNA\d+|PRJEB\d+|PRJCA\d+|OEP\d+|SRP\d{5,}|SRA\d{5,}|"
    r"EGAS\d+|EGAD\d+|E-MTAB-\d+|SCP\d+|HRA\d+|CRA\d+)\b",
    re.I,
)
URL_RE = re.compile(r"https?://[^\s<>\"']+", re.I)
REPOSITORY_HOSTS = (
    "ncbi.nlm.nih.gov/geo",
    "ncbi.nlm.nih.gov/sra",
    "ebi.ac.uk/ega",
    "ebi.ac.uk/biostudies",
    "zenodo.org",
    "figshare.com",
    "github.com",
    "cellxgene.cziscience.com",
    "singlecell.broadinstitute.org",
    "portals.broadinstitute.org",
    "biosino.org",
    "cancerdiversity.asia",
    "weizmann.ac.il/sites/3ca",
)
SUPPLEMENT_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".tsv", ".txt",
    ".zip", ".gz", ".tgz", ".tar", ".mp4", ".mov", ".avi", ".rds", ".h5", ".h5ad",
}

# Exact Nature assets verified from the publisher DOM on 2026-09-11.
NATURE_ASSET_SPECS = {
    "10.1038/s41586-023-06130-4": ((1, 4, "pdf"), (5, 19, "xlsx")),
    "10.1038/s41467-019-11738-0": ((1, 1, "pdf"), (2, 3, "xlsx"), (4, 6, "pdf")),
    "10.1038/s41591-023-02371-y": ((1, 2, "pdf"), (3, 3, "xlsx")),
    "10.1038/s41591-018-0057-z": ((1, 2, "pdf"), (3, 6, "xlsx")),
    "10.1038/s42255-025-01233-w": ((1, 2, "pdf"), (3, 8, "xls"), (9, 9, "pdf"), (10, 10, "xls"), (11, 11, "pdf"), (12, 12, "xls"), (13, 13, "pdf"), (14, 20, "xls")),
    "10.1038/s41422-020-0355-0": ((1, 14, "pdf"), (15, 22, "xlsx")),
    "10.1038/s41586-023-06733-x": ((1, 2, "pdf"), (3, 3, "zip"), (4, 17, "xlsx")),
    "10.1038/s41590-022-01231-0": ((1, 2, "pdf"), (3, 16, "xlsx")),
    "10.1038/s41467-023-40457-w": ((1, 3, "pdf"), (4, 5, "xls"), (6, 6, "pdf")),
    "10.1038/s42003-020-1027-9": ((1, 2, "pdf"), (3, 3, "xlsx"), (4, 5, "pdf")),
    "10.1038/s41467-019-12235-0": ((1, 3, "pdf"),),
    "10.1038/s41592-021-01336-8": ((1, 2, "pdf"), (3, 9, "xlsx")),
    "10.1038/s41467-021-25960-2": ((1, 1, "pdf"), (2, 2, "docx"), (3, 3, "zip"), (4, 4, "pdf"), (5, 5, "xlsx")),
    "10.1038/s41467-021-21038-1": ((1, 3, "pdf"),),
}


def request(url: str, *, timeout: int = 60) -> tuple[bytes, dict[str, str], str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json, application/xml, text/html, application/pdf, */*",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read(), {key.lower(): value for key, value in response.headers.items()}, response.geturl()


def request_json(url: str, *, timeout: int = 60) -> dict:
    body, _, _ = request(url, timeout=timeout)
    return json.loads(body.decode("utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path: Path, base: Path, source_url: str = "", role: str = "source_material") -> dict:
    return {
        "relative_path": path.relative_to(base).as_posix(),
        "role": role,
        "media_type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
        "source_url": source_url,
    }


def safe_name(value: str, limit: int = 100) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", "", value or ""))
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_.")
    return (value or "file")[:limit]


def payload_matches_extension(payload: bytes, extension: str) -> bool:
    extension = extension.lower()
    if extension == ".pdf":
        return payload.startswith(b"%PDF")
    if extension in {".xlsx", ".docx", ".zip"}:
        return payload.startswith(b"PK\x03\x04")
    if extension == ".xls":
        return payload.startswith(b"\xd0\xcf\x11\xe0") or payload.startswith(b"PK\x03\x04")
    return bool(payload) and b"preparing to download" not in payload[:5000].lower()


def verified_nature_assets(doi: str) -> list[str]:
    specs = NATURE_ASSET_SPECS.get(doi, ())
    match = re.fullmatch(r"10\.1038/s(\d+)-(\d{3})-(\d+)-[a-z0-9]+", doi, re.I)
    if not specs or not match:
        return []
    journal, short_year, article = match.groups()
    year = str(2000 + int(short_year))
    stem = f"{journal}_{year}_{int(article)}"
    base = f"https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2F{doi.split('/', 1)[1]}/MediaObjects"
    return [f"{base}/{stem}_MOESM{number}_ESM.{ext}" for start, end, ext in specs for number in range(start, end + 1)]


def strip_jats(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def first_date(message: dict) -> str:
    for key in ("published-print", "published-online", "published", "issued", "created"):
        parts = (message.get(key) or {}).get("date-parts") or []
        if parts and parts[0]:
            values = list(parts[0]) + [1, 1]
            return f"{values[0]:04d}-{values[1]:02d}-{values[2]:02d}"
    return ""


def crossref_metadata(seed: dict) -> tuple[dict, str]:
    paper_root = OUT / "papers" / f"{seed['paper_id']}_{seed['slug']}"
    cached_paper = paper_root / "metadata" / "paper.json"
    if cached_paper.exists():
        try:
            record = json.loads(cached_paper.read_text(encoding="utf-8"))
            publication = record.get("publication", {})
            bib = paper_root / "metadata" / "bibliography.bib"
            bib_text = bib.read_text(encoding="utf-8", errors="ignore") if bib.exists() else ""
            author_match = re.search(r"\bauthor\s*=\s*\{([^}]*)\}", bib_text, re.I)
            return {
                "title": record.get("title") or seed["title"],
                "authors": [name.strip() for name in (author_match.group(1).split(" and ") if author_match else []) if name.strip()],
                "venue": publication.get("venue", ""),
                "publisher": publication.get("publisher", ""),
                "published_at": publication.get("published_at", ""),
                "type": "journal-article",
                "url": (seed.get("source_urls") or [f"https://doi.org/{seed['doi']}"])[0],
                "abstract": "",
                "licenses": [],
                "links": [],
                "relation": {},
                "crossref_prefix": seed["doi"].split("/", 1)[0],
            }, "cached"
        except Exception:
            pass
    doi = seed["doi"]
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
    try:
        message = request_json(url)["message"]
        authors = []
        for author in message.get("author", []):
            name = " ".join(part for part in [author.get("given", ""), author.get("family", "")] if part).strip()
            authors.append(name)
        metadata = {
            "title": (message.get("title") or [seed["title"]])[0],
            "authors": authors,
            "venue": (message.get("container-title") or [""])[0],
            "publisher": message.get("publisher", ""),
            "published_at": first_date(message),
            "type": message.get("type", "journal-article"),
            "url": message.get("URL", f"https://doi.org/{doi}"),
            "abstract": strip_jats(message.get("abstract", "")),
            "licenses": [entry.get("URL", "") for entry in message.get("license", []) if entry.get("URL")],
            "links": message.get("link", []),
            "relation": message.get("relation", {}),
            "crossref_prefix": message.get("prefix", ""),
        }
        return metadata, "ok"
    except Exception as exc:  # network/provider failures remain typed in provenance
        return {
            "title": seed["title"],
            "authors": [],
            "venue": "",
            "publisher": "",
            "published_at": "",
            "type": "journal-article",
            "url": f"https://doi.org/{doi}",
            "abstract": "",
            "licenses": [],
            "links": [],
            "relation": {},
            "crossref_prefix": "",
        }, f"failed:{type(exc).__name__}:{str(exc)[:120]}"


def batched_id_conversion(dois: list[str]) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for path in (OUT / "papers").glob("P*/metadata/paper.json"):
        try:
            identifiers = json.loads(path.read_text(encoding="utf-8")).get("identifiers", {})
            doi = str(identifiers.get("doi") or "").lower()
            if doi:
                found[doi] = {"requested-id": doi, "pmid": identifiers.get("pmid"), "pmcid": identifiers.get("pmcid")}
        except Exception:
            continue
    if all(doi.lower() in found for doi in dois):
        return found
    for start in range(0, len(dois), 20):
        batch = [doi for doi in dois[start : start + 20] if doi.lower() not in found]
        if not batch:
            continue
        url = (
            "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?format=json&ids="
            + urllib.parse.quote(",".join(batch), safe=",")
        )
        try:
            response = request_json(url)
            for record in response.get("records", []):
                found[record.get("requested-id", "").lower()] = record
        except Exception:
            pass
        time.sleep(0.4)
    return found


def pubmed_lookup_missing(doi: str) -> str:
    term = urllib.parse.quote(f'"{doi}"[AID]')
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&term={term}"
    try:
        ids = request_json(url).get("esearchresult", {}).get("idlist", [])
        return ids[0] if ids else ""
    except Exception:
        return ""


def pubmed_integrity(pmids: list[str]) -> dict[str, dict]:
    if not pmids:
        return {}
    cached = {}
    for path in (OUT / "papers").glob("P*/metadata/paper.json"):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            pmid = str(record.get("identifiers", {}).get("pmid") or "")
            if pmid:
                integrity = record.get("integrity", {})
                cached[pmid] = {key: integrity.get(key, default) for key, default in (
                    ("publication_types", []), ("retracted", False),
                    ("expression_of_concern", False), ("corrections", []),
                )}
        except Exception:
            continue
    missing_pmids = [pmid for pmid in pmids if not cached.get(pmid, {}).get("publication_types")]
    if not missing_pmids:
        return cached
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=xml&id="
        + urllib.parse.quote(",".join(missing_pmids), safe=",")
    )
    try:
        body, _, _ = request(url)
        root = ET.fromstring(body)
    except Exception:
        return {}
    results: dict[str, dict] = dict(cached)
    for article in root.findall(".//PubmedArticle"):
        pmid_node = article.find(".//MedlineCitation/PMID")
        if pmid_node is None or not pmid_node.text:
            continue
        publication_types = ["".join(node.itertext()).strip() for node in article.findall(".//PublicationType")]
        corrections = []
        for node in article.findall(".//CommentsCorrections"):
            corrections.append({
                "ref_type": node.attrib.get("RefType", ""),
                "ref_source": " ".join("".join(node.itertext()).split()),
            })
        results[pmid_node.text] = {
            "publication_types": publication_types,
            "retracted": any(value.lower() == "retracted publication" for value in publication_types),
            "expression_of_concern": any(value.lower() == "expression of concern" for value in publication_types),
            "corrections": corrections,
        }
    return results


def safe_extract(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as bundle:
        bundle.extractall(destination, filter="data")


def copy_unique(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    candidate = destination
    counter = 2
    while candidate.exists():
        if sha256(candidate) == sha256(source):
            return candidate
        candidate = destination.with_name(f"{destination.stem}_{counter}{destination.suffix}")
        counter += 1
    shutil.copy2(source, candidate)
    return candidate


def classify_pmc_files(extracted: Path, origin: Path, source_url: str) -> list[dict]:
    files = [path for path in extracted.rglob("*") if path.is_file()]
    nxmls = sorted((path for path in files if path.suffix.lower() in {".nxml", ".xml"}), key=lambda p: p.stat().st_size, reverse=True)
    pdfs = sorted((path for path in files if path.suffix.lower() == ".pdf"), key=lambda p: p.stat().st_size, reverse=True)
    copied: list[Path] = []
    main_xml = copy_unique(nxmls[0], origin / "main_article.xml") if nxmls else None
    if main_xml:
        copied.append(main_xml)
    main_pdf = copy_unique(pdfs[0], origin / "main_article.pdf") if pdfs else None
    if main_pdf:
        copied.append(main_pdf)

    supplement_names: set[str] = set()
    if nxmls:
        text = nxmls[0].read_text(encoding="utf-8", errors="ignore")
        for match in re.finditer(r"(?:xlink:href|href)=[\"']([^\"']+)[\"']", text, re.I):
            supplement_names.add(Path(urllib.parse.unquote(match.group(1))).name.lower())
    supplement_dir = origin / "supplementary"
    for path in files:
        if path in nxmls[:1] or path in pdfs[:1]:
            continue
        name = path.name.lower()
        suffix = path.suffix.lower()
        looks_supplementary = (
            name in supplement_names
            or suffix in SUPPLEMENT_EXTENSIONS
            or bool(re.search(r"supp|moesm|mmc\d|additional", name, re.I))
        )
        if not looks_supplementary:
            continue
        copied.append(copy_unique(path, supplement_dir / safe_name(path.name, 140)))
    return [file_record(path, origin, source_url, "supporting_information" if "supplementary" in path.parts else "main_article") for path in copied]


def download_pmc(pmcid: str, origin: Path) -> tuple[list[dict], dict]:
    audit = {"provider": "PMC OA package", "pmcid": pmcid, "status": "not_attempted", "source_url": ""}
    files: list[dict] = []
    endpoint = f"https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id={pmcid}"
    try:
        body, _, _ = request(endpoint)
        root = ET.fromstring(body)
        links = [node.attrib for node in root.findall(".//link")]
        tgz = next((item.get("href", "") for item in links if item.get("format", "").lower() == "tgz"), "")
        pdf = next((item.get("href", "") for item in links if "pdf" in item.get("format", "").lower()), "")
        source = tgz or pdf
        audit["source_url"] = source
        if tgz:
            source = re.sub(r"^ftp://ftp\.ncbi\.nlm\.nih\.gov/", "https://ftp.ncbi.nlm.nih.gov/", tgz)
            with tempfile.TemporaryDirectory(prefix="pmc_benchmark_") as tmp:
                tmpdir = Path(tmp)
                archive = tmpdir / f"{pmcid}.tar.gz"
                payload, _, final_url = request(source, timeout=180)
                archive.write_bytes(payload)
                safe_extract(archive, tmpdir / "extracted")
                files = classify_pmc_files(tmpdir / "extracted", origin, final_url)
            audit["status"] = "downloaded_with_si" if any(row["role"] == "supporting_information" for row in files) else "open_access_downloaded"
        if pdf:
            source = re.sub(r"^ftp://ftp\.ncbi\.nlm\.nih\.gov/", "https://ftp.ncbi.nlm.nih.gov/", pdf)
            payload, _, final_url = request(source, timeout=180)
            if payload.startswith(b"%PDF"):
                target = origin / "main_article.pdf"
                target.write_bytes(payload)
                files.append(file_record(target, origin, final_url, "main_article"))
                audit["status"] = "open_access_downloaded"
        audit["status"] = "oa_package_not_available"
    except Exception as exc:
        audit["status"] = f"oa_package_failed:{type(exc).__name__}:{str(exc)[:120]}"

    if not any(row["role"] == "main_article" for row in files):
        # Europe PMC is a lawful fallback for PMC author manuscripts outside the OA package subset.
        for kind, url in (
            ("xml", f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"),
            ("pdf", f"https://europepmc.org/articles/{pmcid}?pdf=render"),
        ):
            try:
                payload, _, final_url = request(url, timeout=120)
                if kind == "pdf" and not payload.startswith(b"%PDF"):
                    continue
                if kind == "xml" and b"<article" not in payload[:5000]:
                    continue
                target = origin / f"main_article.{kind}"
                target.write_bytes(payload)
                files.append(file_record(target, origin, final_url, "main_article"))
            except Exception:
                continue
        if files:
            audit["status"] = "open_access_downloaded"
            audit["provider"] = "Europe PMC"

    # PMC article pages expose author-manuscript full text and SI even when oa.fcgi has no package.
    page_url = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"
    try:
        payload, headers, final_url = request(page_url, timeout=120)
        page = payload.decode("utf-8", errors="ignore")
        is_pmc_article = "pmc.ncbi.nlm.nih.gov/articles/" in final_url and "citation_title" in page.lower()
        if "html" in headers.get("content-type", "").lower() and is_pmc_article:
            if not any(row["role"] == "main_article" for row in files):
                target = origin / "main_article.html"
                target.write_text(page, encoding="utf-8")
                files.append(file_record(target, origin, final_url, "main_article"))
            supplement_dir = origin / "supplementary"
            supplement_dir.mkdir(exist_ok=True)
            for url in hrefs_from_html(page, final_url):
                name = urllib.parse.unquote(Path(urllib.parse.urlparse(url).path).name)
                if not re.search(r"supp|suppl|media|mmc\d|moesm|reporting|source.?data|table.?s\d", name, re.I):
                    continue
                if not re.search(r"\.(pdf|xlsx?|csv|tsv|zip|docx?|txt)(?:$|\?)", url, re.I):
                    continue
                try:
                    item, _, item_url = request(url, timeout=180)
                    extension = Path(name).suffix.lower()
                    if not item or not payload_matches_extension(item, extension):
                        continue
                    target = supplement_dir / safe_name(name, 140)
                    target.write_bytes(item)
                    files.append(file_record(target, origin, item_url, "supporting_information"))
                except Exception:
                    continue
    except Exception as exc:
        audit["pmc_article_page_status"] = f"failed:{type(exc).__name__}:{str(exc)[:120]}"

    files = list({row["relative_path"]: row for row in files}.values())
    if any(row["role"] == "supporting_information" for row in files):
        audit["status"] = "downloaded_with_si"
    elif files:
        audit["status"] = "open_access_downloaded"
    return files, audit


def hrefs_from_html(text: str, base_url: str) -> list[str]:
    hrefs = []
    for match in re.finditer(r"href\s*=\s*[\"']([^\"']+)[\"']", text, re.I):
        href = html.unescape(match.group(1))
        hrefs.append(urllib.parse.urljoin(base_url, href))
    return list(dict.fromkeys(hrefs))


def is_challenge_page(text: str) -> bool:
    sample = text[:20000].lower()
    return any(marker in sample for marker in ("captcha", "checking your browser", "access denied", "sign in to access"))


def is_full_article_html(text: str, url: str) -> bool:
    host_path = urllib.parse.urlparse(url).netloc.lower() + urllib.parse.urlparse(url).path.lower()
    if any(host in host_path for host in REPOSITORY_HOSTS):
        return False
    return bool(re.search(r"<article\b|article[-_ ]body|class=[\"'][^\"']*full[-_ ]text", text, re.I))


def download_official_fallback(seed: dict, metadata: dict, origin: Path, existing: list[dict]) -> tuple[list[dict], dict]:
    audit = {"provider": "official_publisher_or_repository", "status": "no_authorized_pdf_found", "attempts": []}
    files = list(existing)
    main_present = any(row["role"] == "main_article" for row in files)
    if main_present and any(row["role"] == "supporting_information" for row in files):
        audit["status"] = "downloaded_with_si"
        audit["attempts"].append({"status": "skipped_publisher_fallback_complete_pmc_package"})
        return files, audit

    local = LOCAL_ARTICLES.get(seed["doi"])
    if local and local.exists() and not main_present:
        target = origin / "main_article.pdf"
        shutil.copy2(local, target)
        files.append(file_record(target, origin, str(local), "main_article"))
        main_present = True
        audit["attempts"].append({"url": str(local), "status": "local_user_supplied_copy"})

    landing_text = ""
    landing_url = ""
    for url in [*seed.get("source_urls", []), metadata.get("url", "")]:
        if not url:
            continue
        try:
            payload, headers, final_url = request(url, timeout=60)
            content_type = headers.get("content-type", "").lower()
            if payload.startswith(b"%PDF"):
                if not main_present:
                    target = origin / "main_article.pdf"
                    target.write_bytes(payload)
                    files.append(file_record(target, origin, final_url, "main_article"))
                    main_present = True
                audit["attempts"].append({"url": final_url, "status": "pdf_downloaded"})
                continue
            text = payload.decode("utf-8", errors="ignore")
            is_full_article = is_full_article_html(text, final_url)
            if "html" in content_type and len(text) > 3000 and not is_challenge_page(text) and is_full_article:
                landing_text, landing_url = text, final_url
                if not main_present:
                    target = origin / "main_article.html"
                    target.write_text(text, encoding="utf-8")
                    files.append(file_record(target, origin, final_url, "main_article"))
                    main_present = True
                audit["attempts"].append({"url": final_url, "status": "full_text_html_available"})
                break
            audit["attempts"].append({"url": final_url, "status": "not_full_text"})
        except Exception as exc:
            audit["attempts"].append({"url": url, "status": f"failed:{type(exc).__name__}:{str(exc)[:80]}"})

    candidate_links = []
    for link in metadata.get("links", []):
        url = link.get("URL", "")
        if url and ("pdf" in link.get("content-type", "").lower() or url.lower().endswith(".pdf")):
            candidate_links.append(url)
    for url in seed.get("source_urls", []):
        if "nature.com/articles/" in url and not url.endswith(".pdf"):
            candidate_links.append(url.rstrip("/") + ".pdf")
    if landing_text:
        candidate_links.extend(url for url in hrefs_from_html(landing_text, landing_url) if re.search(r"\.pdf(?:\?|$)|download.*pdf", url, re.I))
    for url in list(dict.fromkeys(candidate_links))[:12]:
        if main_present:
            break
        try:
            payload, _, final_url = request(url, timeout=120)
            if payload.startswith(b"%PDF") and len(payload) > 10000:
                target = origin / "main_article.pdf"
                target.write_bytes(payload)
                files.append(file_record(target, origin, final_url, "main_article"))
                main_present = True
                audit["attempts"].append({"url": final_url, "status": "pdf_downloaded"})
        except Exception as exc:
            audit["attempts"].append({"url": url, "status": f"failed:{type(exc).__name__}"})

    supplement_links = verified_nature_assets(seed["doi"])
    if landing_text and not supplement_links:
        supplement_links += [
            url for url in hrefs_from_html(landing_text, landing_url)
            if re.search(r"supp|additional[_-]?file|moesm|mmc\d|downloadSupplement", url, re.I)
        ]
    if supplement_links:
        for index, url in enumerate(list(dict.fromkeys(supplement_links))[:30], 1):
            try:
                payload, headers, final_url = request(url, timeout=120)
                content_type = headers.get("content-type", "").split(";")[0].lower()
                ext = Path(urllib.parse.urlparse(final_url).path).suffix.lower()
                if payload.startswith(b"%PDF"):
                    ext = ".pdf"
                elif content_type in {"application/zip", "application/x-zip-compressed"}:
                    ext = ".zip"
                elif content_type in {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}:
                    ext = ".xlsx"
                elif content_type in {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"}:
                    ext = ".docx"
                if ext not in SUPPLEMENT_EXTENSIONS or len(payload) < 100 or not payload_matches_extension(payload, ext):
                    continue
                basename = safe_name(Path(urllib.parse.urlparse(final_url).path).name or f"supplement_{index}{ext}", 140)
                if not Path(basename).suffix:
                    basename += ext
                target = copy_unique_bytes(payload, origin / "supplementary" / basename)
                files.append(file_record(target, origin, final_url, "supporting_information"))
            except Exception:
                continue

    has_si = any(row["role"] == "supporting_information" for row in files)
    if main_present:
        audit["status"] = "downloaded_with_si" if has_si else "full_text_available_si_not_found"
    return files, audit


def copy_unique_bytes(payload: bytes, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    candidate = destination
    digest = hashlib.sha256(payload).hexdigest()
    counter = 2
    while candidate.exists():
        if sha256(candidate) == digest:
            return candidate
        candidate = destination.with_name(f"{destination.stem}_{counter}{destination.suffix}")
        counter += 1
    candidate.write_bytes(payload)
    return candidate


def text_from_origin(origin: Path) -> str:
    chunks = []
    pdftotext = shutil.which("pdftotext")
    for path in sorted(origin.glob("main_article.*")):
        suffix = path.suffix.lower()
        if suffix in {".xml", ".html", ".txt"}:
            chunks.append(strip_jats(path.read_text(encoding="utf-8", errors="ignore")))
        elif suffix == ".pdf" and pdftotext:
            try:
                result = subprocess.run(
                    [pdftotext, "-q", "-enc", "UTF-8", str(path), "-"],
                    capture_output=True,
                    check=False,
                    timeout=180,
                )
                if result.returncode == 0:
                    chunks.append(result.stdout.decode("utf-8", errors="ignore"))
            except (OSError, subprocess.SubprocessError):
                pass
    return "\n".join(chunks)


def discover_data_sources(text: str, seed: dict) -> tuple[list[dict], list[str]]:
    verified = {value.upper(): value for value in seed.get("verified_accessions", [])}
    roles = {key.upper(): value for key, value in seed.get("accession_roles", {}).items()}
    accessions: list[dict] = []
    for value in seed.get("verified_accessions", []):
        upper = value.upper()
        access = "controlled" if upper.startswith(("EGAS", "EGAD", "DUOS-", "PHS")) else "public"
        accessions.append({"accession": value, "access": access, "role": roles.get(upper, "unspecified"), "verification": "manually_seeded_from_primary_source"})
    for match in ACCESSION_RE.findall(text):
        canonical = match.upper()
        if canonical in verified or any(row["accession"].upper() == canonical for row in accessions):
            continue
        access = "controlled" if canonical.startswith(("EGAS", "EGAD", "DUOS-", "PHS")) else "public"
        accessions.append({"accession": canonical, "access": access, "role": roles.get(canonical, "unspecified_candidate"), "verification": "automatically_extracted_candidate"})
    urls = []
    for match in URL_RE.findall(text):
        cleaned = match.rstrip(".,);]}")
        if any(host in cleaned.lower() for host in REPOSITORY_HOSTS):
            urls.append(cleaned)
    urls.extend(seed.get("code_urls", []))
    urls.extend(seed.get("data_urls", []))
    return accessions, list(dict.fromkeys(urls))[:200]


def year_from_metadata(metadata: dict) -> str:
    return (metadata.get("published_at") or "")[:4] or "unknown"


def bibtex(seed: dict, metadata: dict) -> str:
    first_family = "Paper"
    if metadata.get("authors"):
        first_family = metadata["authors"][0].split()[-1]
    key = safe_name(f"{first_family}{year_from_metadata(metadata)}{seed['paper_id']}", 60)
    authors = " and ".join(metadata.get("authors") or ["Unknown"])
    fields = {
        "title": metadata.get("title") or seed["title"],
        "author": authors,
        "journal": metadata.get("venue", ""),
        "year": year_from_metadata(metadata),
        "doi": seed["doi"],
        "url": metadata.get("url") or f"https://doi.org/{seed['doi']}",
    }
    lines = [f"@article{{{key},"]
    for name, value in fields.items():
        value = str(value).replace("{", "").replace("}", "")
        lines.append(f"  {name} = {{{value}}},")
    lines.append("}\n")
    return "\n".join(lines)


def question_template(axis: str) -> str:
    if axis == "Q1":
        return (
            "Using only the provided fixed metabolic-gene set as expression features after documented symbol and coverage QC, "
            "determine whether the cells contain distinct, reproducible transcriptional metabolic states. Compare against "
            "expression-matched random gene sets and a full-transcriptome representation; quantify stability across seeds and "
            "biological-replicate bootstraps, and test transfer to held-out patients or samples."
        )
    if axis == "Q2":
        return (
            "Derive metabolic states without using cell-type labels, then determine whether those states are associated with "
            "annotated cell types. Use patient/sample-aware effect sizes and blocked permutations, and distinguish cell-type "
            "association from study, batch, tissue, library-size, and mitochondrial-quality effects."
        )
    if axis == "Q3":
        return (
            "Within the pre-annotated CD8+ T-cell compartment, determine whether more than one reproducible transcriptional "
            "metabolic state exists. Require support across donors/samples, cross-patient transfer, and sensitivity analyses "
            "across reasonable scoring and clustering choices; do not describe RNA-derived scores as measured metabolic flux."
        )
    return "Use this paper record as a benchmark-governance reference; it is not an agent-visible scored discovery task."


def required_artifacts(axis: str) -> list[dict]:
    common = [
        {"path": "submission/metrics.json", "format": "JSON", "required": True},
        {"path": "submission/claims.jsonl", "format": "JSONL", "required": True},
        {"path": "submission/provenance.json", "format": "JSON", "required": True},
        {"path": "submission/report.md", "format": "Markdown", "required": True},
    ]
    if axis in {"Q1", "Q3"}:
        common.insert(0, {"path": "submission/cluster_assignments.tsv", "format": "TSV", "required": True, "columns": ["cell_id", "metabolic_state", "confidence"]})
        common.insert(1, {"path": "submission/state_summary.tsv", "format": "TSV", "required": True, "columns": ["metabolic_state", "n_cells", "n_samples", "n_patients", "top_features"]})
    if axis == "Q2":
        common.insert(0, {"path": "submission/associations.tsv", "format": "TSV", "required": True, "columns": ["metabolic_state", "cell_type", "effect_size", "p_value", "q_value", "inference_unit"]})
    return common


def output_schema(task_id: str, axis: str) -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://example.org/metabolic-scrna/{task_id}/metrics.schema.json",
        "title": f"Metrics contract for {task_id}",
        "type": "object",
        "additionalProperties": True,
        "required": ["task_id", "primary_question", "conclusion", "inference_unit", "sensitivity", "uncertainty", "evidence_level"],
        "properties": {
            "task_id": {"const": task_id},
            "primary_question": {"const": axis},
            "conclusion": {"type": "string", "minLength": 20},
            "inference_unit": {"enum": ["patient", "donor", "sample", "tumour"]},
            "state_count": {"type": ["integer", "null"], "minimum": 0},
            "cluster_stability_ari": {"type": ["number", "null"], "minimum": -1, "maximum": 1},
            "heldout_macro_f1": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
            "blocked_permutation_p": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
            "sensitivity": {"type": "array", "minItems": 1, "items": {"type": "object"}},
            "uncertainty": {"type": "object"},
            "evidence_level": {"enum": ["transcriptional_program", "model_inferred_metabolic_potential", "orthogonally_supported", "inconclusive"]},
            "flux_claim_made": {"type": "boolean"}
        }
    }


def generic_schemas() -> dict[str, dict]:
    draft = "https://json-schema.org/draft/2020-12/schema"
    return {
        "paper.schema.json": {
            "$schema": draft,
            "type": "object",
            "required": ["schema_version", "paper_id", "title", "identifiers", "publication", "integrity", "curation"],
            "properties": {"paper_id": {"type": "string"}, "title": {"type": "string"}, "identifiers": {"type": "object"}}
        },
        "data-manifest.schema.json": {
            "$schema": draft,
            "type": "object",
            "required": ["schema_version", "dataset_id", "version", "source_accessions", "biological_scope", "files", "materialization_status"]
        },
        "task.schema.json": {
            "$schema": draft,
            "type": "object",
            "required": ["schema_version", "task_id", "task_version", "paper_id", "dataset_id", "question", "inference_unit", "required_artifacts"]
        },
        "run.schema.json": {
            "$schema": draft,
            "type": "object",
            "required": ["schema_version", "run_id", "task_id", "task_version", "system_id", "started_at", "status"],
            "properties": {"status": {"enum": ["running", "completed", "failed", "invalid"]}}
        },
        "event.schema.json": {
            "$schema": draft,
            "type": "object",
            "required": ["schema_version", "run_id", "sequence", "timestamp", "event_type"],
            "properties": {"sequence": {"type": "integer", "minimum": 0}, "event_type": {"type": "string"}}
        },
        "score.schema.json": {
            "$schema": draft,
            "type": "object",
            "required": ["score_schema_version", "run_id", "task_id", "total_score", "hard_gate_pass"],
            "properties": {"total_score": {"type": "number", "minimum": 0, "maximum": 100}, "hard_gate_pass": {"type": "boolean"}}
        }
    }


def build_geneset() -> dict:
    rows = list(csv.DictReader(SOURCE_GENESET.open(encoding="utf-8-sig", newline="")))
    genes = [row.get("symbol", "").strip() for row in rows if row.get("symbol", "").strip()]
    unique = list(dict.fromkeys(genes))
    geneset_dir = OUT / "genesets"
    geneset_dir.mkdir(parents=True, exist_ok=True)
    target_csv = geneset_dir / "metabolic_genes_input_v1.csv"
    with target_csv.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["symbol"])
        writer.writerows([[gene] for gene in unique])
    gmt = geneset_dir / "metabolic_genes_input_v1.gmt"
    gmt.write_text("METABOLIC_GENES_INPUT_V1\tuser_supplied_unweighted_gene_set\t" + "\t".join(unique) + "\n", encoding="utf-8")
    audit_path = geneset_dir / "hgnc_validation_summary.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8")) if audit_path.exists() else {}
    manifest = {
        "schema_version": "1.0",
        "geneset_id": "metabolic-genes-input-v1",
        "species": "mixed human/mouse symbols; human ortholog mapping is a candidate and requires curation" if audit else "unresolved",
        "id_space": "mixed HGNC/MGI symbol candidates",
        "source": str(SOURCE_GENESET),
        "source_sha256": sha256(SOURCE_GENESET),
        "direction": "unsigned",
        "weights": "absent",
        "provenance": "user_supplied; upstream biological source not present in the CSV",
        "n_input_rows": len(genes),
        "n_unique_symbols": len(unique),
        "n_blank": len(rows) - len(genes),
        "n_duplicate": len(genes) - len(unique),
        "files": [file_record(target_csv, OUT), file_record(gmt, OUT)],
        "symbol_validation": {
            "status": "completed_with_unresolved_symbols" if audit else "not_run",
            "reference_summary": "genesets/hgnc_validation_summary.json" if audit else None,
            "inferred_species_counts": audit.get("inferred_species_counts"),
            "recommended_human_symbols": audit.get("recommended_human_symbols"),
            "recommended_human_unique_symbols": audit.get("recommended_human_unique_symbols"),
            "all_resolved_unambiguously": audit.get("all_resolved_unambiguously"),
        },
        "blocking_fields_before_biological_gold": ["upstream_source", "species_confirmation", "HGNC_release", "inclusion_rule"]
    }
    for name in ("hgnc_validation_summary.json", "metabolic_genes_hgnc_validation.tsv", "metabolic_genes_human_mapped_candidate_v1.csv"):
        path = geneset_dir / name
        if path.exists():
            manifest["files"].append(file_record(path, OUT))
    write_json(geneset_dir / "genesets.json", manifest)
    return manifest


def task_payload(seed: dict, dataset_id: str) -> dict:
    axis = seed["primary_axis"]
    task_id = f"metabolic-scrna-{seed['paper_id'].lower()}-{axis.lower()}"
    return {
        "schema_version": "1.0",
        "benchmark_version": "0.1.0-curation",
        "task_id": task_id,
        "task_version": "0.1.0",
        "paper_id": seed["paper_id"],
        "dataset_id": dataset_id,
        "dataset_version": "0.1.0",
        "task_family_id": f"metabolic-scrna-{axis.lower()}",
        "leakage_group_id": f"paper-and-source-data-{seed['paper_id'].lower()}",
        "track": "blind_rediscovery" if not seed["task_status"].startswith("reference_only") else "reference_only",
        "curation_status": seed["task_status"],
        "domain": {
            "disease": "cancer or immune-state method validation",
            "modality": "scRNA-seq",
            "analysis_types": [axis, "metabolic_gene_set", "robustness", "evidence_reporting"]
        },
        "scientific_context": "Determine what can be learned from a fixed metabolic-gene set without confusing transcriptional programs with measured metabolic flux.",
        "question": question_template(axis),
        "inference_unit": "patient",
        "visible_inputs": [
            {"path": "benchmark://genesets/metabolic_genes_input_v1.csv", "description": "Frozen unsigned metabolic-gene list supplied by the user."},
            {"path": "data_manifest.public.json", "description": "Versioned pointers and metadata for the paper-associated dataset; materialize only licensed public objects."}
        ],
        "external_resources": {"literature": "prohibited during scored blind rediscovery", "network": "disabled after input materialization"},
        "resource_budget": {"wall_time_hours": 8, "cpu_cores": 8, "memory_gb": 64, "gpu": "optional"},
        "required_artifacts": required_artifacts(axis),
        "hard_gates": [
            "gene-symbol and overlap coverage reported",
            "biological replicate is the inferential unit",
            "negative-control gene sets included",
            "batch, library-size, and mitochondrial-quality confounding assessed",
            "RNA-derived activity is not reported as measured flux",
            "all required files conform to the output contract"
        ]
    }


def render_prompt(task: dict) -> str:
    artifacts = "\n".join(f"- `{item['path']}` ({item['format']})" for item in task["required_artifacts"])
    gates = "\n".join(f"- {item}" for item in task["hard_gates"])
    return f"""# {task['task_id']}\n\n## Scientific question\n\n{task['question']}\n\n## Inputs\n\n- `metabolic_genes_input_v1.csv`: fixed, unsigned user-supplied gene symbols.\n- `data_manifest.public.json`: paper-associated public data objects and acquisition routes.\n\nThe paper, supplementary figures, author results, and candidate claims are curator-only and must not be mounted in the agent workspace.\n\n## Required submission\n\n{artifacts}\n\n## Hard gates\n\n{gates}\n\nReport negative or inconclusive results when warranted. Cluster labels are arbitrary; evidence must be based on label-invariant comparisons and replicate-aware statistics.\n"""


def build_paper(seed: dict, metadata: dict, crossref_status: str, id_record: dict, integrity_map: dict) -> tuple[dict, dict, dict]:
    folder_name = f"{seed['paper_id']}_{seed['slug']}"
    paper_root = OUT / "papers" / folder_name
    origin = paper_root / "origin"
    for subdir in ("metadata", "data", "task/public", "curation", "provenance"):
        (paper_root / subdir).mkdir(parents=True, exist_ok=True)
    origin.mkdir(parents=True, exist_ok=True)

    pmcid = id_record.get("pmcid", "") or ""
    pmid = str(id_record.get("pmid", "") or "")
    if not pmid:
        pmid = pubmed_lookup_missing(seed["doi"])
    prior_manifest_path = origin / "download_manifest.json"
    prior_manifest = {}
    if prior_manifest_path.exists():
        try:
            prior_manifest = json.loads(prior_manifest_path.read_text(encoding="utf-8"))
        except Exception:
            prior_manifest = {}
    prior_files = []
    for row in prior_manifest.get("files", []):
        path = origin / row.get("relative_path", "")
        if (row.get("role") == "main_article" and path.suffix.lower() == ".html" and path.exists()
                and not is_full_article_html(path.read_text(encoding="utf-8", errors="ignore"), row.get("source_url", ""))):
            continue
        prior_files.append(row)
    # An empty, completed manifest is also a valid cached result: it records that
    # lawful retrieval was attempted and no authorized local file was obtained.
    prior_files_valid = prior_manifest_path.exists() and all((origin / row["relative_path"]).exists() for row in prior_files)
    if prior_files_valid:
        files = prior_files
        pmc_audit = prior_manifest.get("pmc_attempt", {"status": "resumed"})
        fallback_audit = prior_manifest.get("official_fallback_attempt", {"status": "resumed"})
        # Resume only deterministic, publisher-verified SI downloads. Repeating failed
        # PMC/publisher discovery attempts adds minutes per paper without new evidence.
        if (not any(row["role"] == "supporting_information" for row in files)
                and seed["doi"] in NATURE_ASSET_SPECS):
            files, fallback_audit = download_official_fallback(seed, metadata, origin, files)
    else:
        pmc_files: list[dict] = []
        pmc_audit = {"status": "pmcid_not_available", "pmcid": pmcid}
        if pmcid:
            pmc_files, pmc_audit = download_pmc(pmcid, origin)
        files, fallback_audit = download_official_fallback(seed, metadata, origin, pmc_files)
    source_text = text_from_origin(origin)
    accessions, repository_urls = discover_data_sources(source_text, seed)

    integrity = integrity_map.get(pmid, {})
    paper_json = {
        "schema_version": "1.0",
        "paper_id": seed["paper_id"],
        "folder_id": folder_name,
        "title": metadata.get("title") or seed["title"],
        "identifiers": {"doi": seed["doi"], "pmid": pmid or None, "pmcid": pmcid or None},
        "publication": {
            "venue": metadata.get("venue", ""),
            "publisher": metadata.get("publisher", ""),
            "type": "peer_reviewed" if seed["tier"] in {"A", "B", "C"} else "unknown",
            "published_at": metadata.get("published_at", ""),
            "version": "version_of_record"
        },
        "integrity": {
            "checked_at": NOW,
            "sources": ["Crossref metadata", "PubMed publication types/comments when PMID resolved"],
            "screening_completeness": "Crossref+PubMed" if pmid and integrity else "Crossref_only_or_unresolved",
            "retracted": integrity.get("retracted", False),
            "expression_of_concern": integrity.get("expression_of_concern", False),
            "corrections": integrity.get("corrections", []),
            "publication_types": integrity.get("publication_types", [])
        },
        "selection": {key: seed[key] for key in ("tier", "role", "primary_axis", "secondary_axes", "rationale")},
        "code_sources": [{"url": url, "commit": None, "license": "to_verify"} for url in seed.get("code_urls", [])],
        "data_sources": accessions,
        "verified_data_urls": seed.get("data_urls", []),
        "repository_urls_extracted": repository_urls,
        "curation": {
            "status": seed["task_status"],
            "completed_stages": ["S0_candidate_registration", "S1_source_inventory", "S2_candidate_insight", "S3_paper_data_task_mapping"],
            "pending_stages": ["S4_independent_reproduction", "S5_final_prompt_approval", "S6_answerability_and_leakage_tests", "S7_grader_adversarial_tests", "S8_dual_signoff"],
            "domain_curator": None,
            "computational_curator": None,
            "reviewed_at": None
        }
    }
    write_json(paper_root / "metadata" / "paper.json", paper_json)
    bibliography = paper_root / "metadata" / "bibliography.bib"
    if metadata.get("authors") or not bibliography.exists():
        bibliography.write_text(bibtex(seed, metadata), encoding="utf-8")

    main_present = any(row.get("role") == "main_article" for row in files)
    si_present = any(row.get("role") == "supporting_information" for row in files)
    fallback_audit["status"] = (
        "downloaded_with_si" if main_present and si_present
        else "full_text_available_si_not_found" if main_present
        else "supporting_information_only" if si_present
        else "no_authorized_pdf_found"
    )
    origin_manifest = {
        "schema_version": "1.0",
        "paper_id": seed["paper_id"],
        "si_requested": True,
        "downloaded_at": NOW,
        "pmc_attempt": pmc_audit,
        "official_fallback_attempt": fallback_audit,
        "files": files,
        "verification": {
            "checks": ["nonzero size", "PDF magic when applicable", "SHA-256", "source URL recorded"],
            "pdf_text_or_title_check": "external acceptance check; see top-level 构建与验收报告.md"
        }
    }
    if prior_manifest.get("browser_verification"):
        origin_manifest["browser_verification"] = prior_manifest["browser_verification"]
    write_json(origin / "download_manifest.json", origin_manifest)
    (origin / "README.md").write_text(
        "# Origin materials\n\nCurator-only copies obtained from PMC/Europe PMC, an official publisher page, or a user-supplied local paper. "
        "This folder is never mounted into a scored agent run because the paper and supplements can reveal the target conclusion. "
        "See `download_manifest.json` for file-level source, size, and SHA-256. Absence of a file means no lawful automated copy was found; it is not replaced by a placeholder PDF.\n",
        encoding="utf-8",
    )

    dataset_id = f"metabolic-scrna-{seed['paper_id'].lower()}"
    data_manifest = {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "version": "0.1.0",
        "created_at": NOW,
        "source_accessions": accessions,
        "verified_data_urls": seed.get("data_urls", []),
        "repository_urls": repository_urls,
        "license": {"identifier": "per-upstream-object", "redistribution_allowed": False, "reason": "Pointers are registered; each upstream object requires an object-level licence check before redistribution."},
        "biological_scope": {
            "species": "Homo sapiens unless the paper-specific manifest states otherwise",
            "disease": "cancer or immune-state method validation",
            "assay": "scRNA-seq or orthogonal single-cell assay",
            "unit_of_observation": "cell",
            "unit_of_inference": "patient/donor/sample",
            "reference_genome": "paper-specific; unresolved until materialization",
            "gene_id_space": "paper-specific input mapped to HGNC symbols"
        },
        "processing_level": "registered_source",
        "materialization_status": "registered_not_materialized",
        "files": [
            {
                "relative_path": "benchmark://genesets/metabolic_genes_input_v1.csv",
                "role": "shared_gene_set",
                "media_type": "text/csv",
                "agent_visible": True,
                "sha256": sha256(OUT / "genesets" / "metabolic_genes_input_v1.csv")
            }
        ],
        "transformations": [],
        "required_before_release": [
            "resolve exact raw/processed file list",
            "record file sizes and SHA-256 after lawful materialization",
            "record counts/log-normalized/scaled matrix location",
            "map patient, sample, tumour, batch, cell_type, and CD8 annotations",
            "confirm object-level licences and access conditions"
        ]
    }
    write_json(paper_root / "data" / "data_manifest.json", data_manifest)
    (paper_root / "data" / "README.md").write_text(
        "# Data snapshot status\n\nThis curation release registers stable accessions and repository routes. Large or licence-unclear omics objects are not duplicated. "
        "Before scoring, materialize an immutable snapshot, add object-level licences, file sizes and SHA-256, and convert the selected matrix to a documented h5ad/Zarr layout without overwriting the upstream object.\n",
        encoding="utf-8",
    )

    task = task_payload(seed, dataset_id)
    public = paper_root / "task" / "public"
    write_json(public / "task.yaml", task)  # JSON is valid YAML 1.2 and preserves exact types.
    (public / "prompt.md").write_text(render_prompt(task), encoding="utf-8")
    write_json(public / "data_manifest.public.json", data_manifest)
    write_json(public / "output_contract.schema.json", output_schema(task["task_id"], seed["primary_axis"]))
    (public / "README.md").write_text(
        "# Agent-visible task package\n\nOnly this directory, the frozen shared gene set, and a materialized data snapshot may be mounted for a scored run. "
        "Do not mount `origin`, `curation`, or the separate private benchmark root.\n",
        encoding="utf-8",
    )

    paper_card = f"""# Paper Card: {seed['paper_id']}\n\n## Citation\n\n{paper_json['title']}  \nDOI: {seed['doi']}\n\n## Benchmark role\n\n- Tier: {seed['tier']}\n- Role: {seed['role']}\n- Primary axis: {seed['primary_axis']}\n- Secondary axes: {', '.join(seed['secondary_axes']) or 'None'}\n- Current status: {seed['task_status']}\n\n## Why it was selected\n\n{seed['rationale']}\n\n## Candidate paper-supported claim\n\n{seed['candidate_claim']}\n\nThis sentence is a curation candidate, not a verified gold claim. It remains excluded from official scoring until independent reproduction and sensitivity testing are complete.\n\n## Data and code inventory\n\n- Seeded stable identifiers: {', '.join(seed.get('verified_accessions', [])) or 'None; inspect full text and supplement.'}\n- Automatically extracted candidate identifiers: {', '.join(row['accession'] for row in accessions if row['verification'].startswith('automatically')) or 'None'}\n- Code URLs: {', '.join(seed.get('code_urls', [])) or 'None recorded'}\n- Origin status: {fallback_audit['status'] if fallback_audit else pmc_audit.get('status')}\n\n## Evidence boundary\n\nRNA expression can support a transcriptional metabolic program or model-inferred metabolic potential. It does not by itself establish enzyme activity, metabolite abundance, exchange flux, or causal metabolic mechanism.\n\n## Next curation actions\n\n1. Materialize the exact permitted input files and freeze checksums.\n2. Map the target claim to figures, supplementary tables, code, and data objects.\n3. Reproduce the claim in a clean environment with patient/sample-aware statistics.\n4. Run at least one reasonable method/threshold sensitivity analysis and an expression-matched random-gene-set control.\n5. Complete answerability, leakage, adversarial grader tests, and dual sign-off.\n"""
    (paper_root / "curation" / "paper_card.md").write_text(paper_card, encoding="utf-8")
    claim = {
        "schema_version": "1.0",
        "claim_id": f"{seed['paper_id']}-C001",
        "paper_id": seed["paper_id"],
        "text": seed["candidate_claim"],
        "subject": "paper-specific cell or metabolic state",
        "relation": "paper-reported association or separation",
        "object": "paper-specific phenotype",
        "direction": "paper-specific",
        "context": "see paper card and source",
        "estimand": "unresolved until independent reproduction",
        "expected": None,
        "uncertainty": None,
        "evidence_level": "candidate",
        "source_anchors": [],
        "reproduction_anchors": [],
        "acceptable_alternatives": [],
        "overclaim_boundary": "Do not infer measured flux or causality from RNA-derived scores alone.",
        "status": "candidate_unverified",
        "included_in_score": False
    }
    write_jsonl(paper_root / "curation" / "claim_map.jsonl", [claim])
    provenance = {
        "schema_version": "1.0",
        "paper_id": seed["paper_id"],
        "created_at": NOW,
        "selection_source": "curation_seed.json",
        "crossref_status": crossref_status,
        "id_converter_record": id_record,
        "origin_manifest": "origin/download_manifest.json",
        "data_manifest": "data/data_manifest.json",
        "task_source": "task/public/task.yaml",
        "network_sources": ["Crossref REST", "NCBI ID Converter", "PubMed E-utilities", "PMC OA API", "Europe PMC", *seed.get("source_urls", [])]
    }
    write_json(paper_root / "provenance" / "provenance.json", provenance)

    private = PRIVATE_OUT / "papers" / folder_name / "private"
    private.mkdir(parents=True, exist_ok=True)
    write_jsonl(private / "gold_claims.jsonl", [claim])
    rubric = {
        "schema_version": "1.0",
        "task_id": task["task_id"],
        "status": "draft_not_scoreable",
        "release_eligible": False,
        "hard_gates": task["hard_gates"],
        "weights": {
            "data_and_gene_set_integrity": 15,
            "replicate_aware_statistics": 20,
            "primary_artifact_agreement": 30,
            "robustness_and_negative_controls": 20,
            "claim_evidence_and_uncertainty": 15
        },
        "deterministic_metrics_to_finalize": ["schema validity", "ARI/NMI or label-invariant set agreement", "held-out-patient transfer", "blocked-permutation association", "effect-size direction", "required artifact completeness"],
        "blocking_reason": "Gold artifacts, tolerances, and independent reproduction anchors are not yet available."
    }
    write_json(private / "rubric.json", rubric)
    (private / "adjudication.md").write_text(
        "# Adjudication status\n\nNot ready for leaderboard scoring. Independent reproduction, sensitivity analysis, adversarial grader tests, and domain/computational sign-off are required.\n",
        encoding="utf-8",
    )

    paper_registry = {
        "paper_id": seed["paper_id"],
        "folder": f"papers/{folder_name}",
        "title": paper_json["title"],
        "doi": seed["doi"],
        "pmid": pmid or None,
        "pmcid": pmcid or None,
        "tier": seed["tier"],
        "role": seed["role"],
        "primary_axis": seed["primary_axis"],
        "curation_status": seed["task_status"],
        "origin_status": fallback_audit["status"],
        "n_origin_files": len(files),
        "n_accessions": len(accessions)
    }
    task_registry = {
        "task_id": task["task_id"],
        "paper_id": seed["paper_id"],
        "path": f"papers/{folder_name}/task/public/task.yaml",
        "primary_axis": seed["primary_axis"],
        "status": seed["task_status"],
        "release_split": "curation_pool",
        "scoreable": False
    }
    dataset_registry = {
        "dataset_id": dataset_id,
        "paper_id": seed["paper_id"],
        "path": f"papers/{folder_name}/data/data_manifest.json",
        "version": "0.1.0",
        "materialization_status": "registered_not_materialized",
        "source_accessions": accessions
    }
    return paper_registry, task_registry, dataset_registry


def write_top_level(seed: dict, paper_rows: list[dict], task_rows: list[dict], dataset_rows: list[dict], gene_manifest: dict) -> None:
    (OUT / "VERSION").write_text(seed["benchmark_version"] + "\n", encoding="utf-8")
    (OUT / "CHANGELOG.md").write_text(
        "# Changelog\n\n## 0.1.0-curation - 2026-09-11\n\n- Registered 30 peer-reviewed paper records.\n- Added curator-only lawful full-text/SI retrieval with file-level manifests.\n- Added one structured candidate task per paper and a separate private draft-gold root.\n- Froze the user-supplied 1,988-gene metabolic input as CSV and GMT.\n- Marked all tasks non-scoreable until data materialization, independent reproduction, and dual sign-off.\n",
        encoding="utf-8",
    )
    write_jsonl(OUT / "registry" / "papers.jsonl", paper_rows)
    write_jsonl(OUT / "registry" / "tasks_public.jsonl", task_rows)
    write_jsonl(OUT / "registry" / "datasets.jsonl", dataset_rows)
    write_json(OUT / "registry" / "splits.json", {
        "benchmark_version": seed["benchmark_version"],
        "status": "provisional",
        "groups": {"curation_pool": [row["task_id"] for row in task_rows]},
        "note": "No train/validation/sealed split is released before leakage groups and independent gold are finalized."
    })
    for name, schema in generic_schemas().items():
        write_json(OUT / "schemas" / name, schema)

    table = "\n".join(
        f"| {row['paper_id']} | {row['tier']} | {row['primary_axis']} | {row['role']} | {row['title'].replace('|', '/')} | {row['origin_status']} |"
        for row in paper_rows
    )
    audit = gene_manifest.get("symbol_validation", {})
    downloaded = sum(row["origin_status"] != "no_authorized_pdf_found" for row in paper_rows)
    readme = f"""# Metabolic scRNA-seq Benchmark v0.1 - curation release\n\nThis repository instantiates the first-stage rules for the question: can a fixed metabolic-gene list reveal reproducible transcriptional metabolic states across all cells, across cell types, and within CD8+ T cells?\n\n## What is complete\n\n- 30 deduplicated, DOI-identified paper records selected for direct biology, metabolic inference, gene-set scoring, single-cell integration, statistics, and benchmark governance.\n- One clean paper folder per record with `origin`, `metadata`, `data`, `task/public`, `curation`, and `provenance`.\n- Lawful PMC/Europe PMC/official-publisher/local-user retrieval attempts with SI enabled and typed failures; {downloaded}/30 papers have local main text and {sum(row['origin_status'] == 'downloaded_with_si' for row in paper_rows)}/30 have supporting information.\n- Frozen user input gene set: {gene_manifest['n_unique_symbols']} unique symbols. Current HGNC/MGI audit infers {audit.get('inferred_species_counts', {}).get('mouse', 'unknown')} mouse-only candidates and leaves {audit.get('inferred_species_counts', {}).get('unresolved', 'unknown')} unresolved; the {audit.get('recommended_human_unique_symbols', 'unavailable')}-symbol human-mapped file is a candidate, not a silent replacement.\n- Separate private root at `{PRIVATE_OUT}` containing only draft, non-scoreable claim/rubric records.\n\n## What is deliberately not claimed\n\nThis is a curation release, not a leaderboard release. No task is scoreable until public omics inputs are materialized and checksummed, candidate claims are independently reproduced, sensitivities and negative controls are run, graders are adversarially tested, and a domain plus computational curator sign off. The build does not invent missing PDFs, supplement files, licences, accessions, or gold numbers.\n\n## Runtime boundary\n\nFor an agent run, mount only `papers/<paper>/task/public`, the chosen immutable data snapshot, and an explicitly curator-approved gene-set version. Never mount `origin`, `curation`, or the separate private root.\n\n## Paper inventory\n\n| ID | Tier | Axis | Role | Paper | Origin status |\n|---|---:|---|---|---|---|\n{table}\n\n## Next release gate\n\nPromote the smallest executable pilot first: P001/P002 for metabolic-state clustering, P003/P004 for within-CD8 states, P014/P015 for alternative metabolic inference, and P028/P029 as statistical hard-gate tasks. Resolve the 82 unmapped gene symbols and materialize exact public matrices before any task is labelled scoreable.\n"""
    readme = readme.replace("## Paper inventory", "## Acceptance report\n\nSee `构建与验收报告.md` for file-level QA, gene-species validation, release boundaries, and the next promotion gate.\n\n## Paper inventory")
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    (OUT / "DATASET_CARD.md").write_text(readme + "\n## Licence and access\n\nEach paper and upstream dataset retains its own licence. Local copies are for user-authorized research curation. Redistribution is false by default until an object-level licence audit records otherwise. Controlled EGA objects remain pointers and must never enter the public release.\n", encoding="utf-8")
    (OUT / "runs").mkdir(parents=True, exist_ok=True)
    (OUT / "runs" / "README.md").write_text(
        "# Run bundles\n\nNo model trajectories exist in the first curation release. Future runs must store `run.json`, append-only `events.jsonl`, `human.log`, `workspace_manifest.json`, `submission/`, and `grading/`. Observable actions and artifacts are recorded; hidden chain-of-thought is neither required nor stored.\n",
        encoding="utf-8",
    )
    PRIVATE_OUT.mkdir(parents=True, exist_ok=True)
    (PRIVATE_OUT / "README.md").write_text(
        "# Private draft-gold root\n\nThis directory is intentionally outside the public benchmark root. All claim and rubric files are draft and non-scoreable. Deploy sealed evaluation from a separate repository or storage bucket; do not expose this root to agents.\n",
        encoding="utf-8",
    )


def verify() -> dict:
    seed = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    expected = len(seed["papers"])
    problems = []
    papers = OUT / "papers"
    paper_dirs = sorted(path for path in papers.glob("P*_") if path.is_dir()) if papers.exists() else []
    # glob above does not match full names portably; use an explicit prefix check.
    paper_dirs = sorted(path for path in papers.iterdir() if path.is_dir() and re.match(r"P\d{3}_", path.name)) if papers.exists() else []
    if len(paper_dirs) != expected:
        problems.append(f"paper folder count {len(paper_dirs)} != {expected}")
    origin_files = main_files = supplement_files = papers_with_main = papers_with_si = 0
    origin_bytes = 0
    for paper_dir in paper_dirs:
        required = [
            paper_dir / "origin" / "download_manifest.json",
            paper_dir / "metadata" / "paper.json",
            paper_dir / "data" / "data_manifest.json",
            paper_dir / "task" / "public" / "task.yaml",
            paper_dir / "task" / "public" / "prompt.md",
            paper_dir / "task" / "public" / "output_contract.schema.json",
            paper_dir / "curation" / "paper_card.md",
            paper_dir / "provenance" / "provenance.json",
        ]
        for path in required:
            if not path.exists():
                problems.append(f"missing {path}")
        manifest_path = paper_dir / "origin" / "download_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"files": []}
        listed_paths = [row.get("relative_path", "") for row in manifest.get("files", [])]
        if len(listed_paths) != len(set(listed_paths)):
            problems.append(f"duplicate origin manifest path: {paper_dir.name}")
        has_main = has_si = False
        for row in manifest.get("files", []):
            path = paper_dir / "origin" / row.get("relative_path", "")
            if not path.is_file():
                problems.append(f"manifest target missing: {path}")
                continue
            size = path.stat().st_size
            origin_files += 1
            origin_bytes += size
            if size != row.get("size_bytes"):
                problems.append(f"size mismatch: {path}")
            if sha256(path) != row.get("sha256"):
                problems.append(f"checksum mismatch: {path}")
            if not row.get("source_url"):
                problems.append(f"source URL missing: {path}")
            role = row.get("role")
            has_main |= role == "main_article"
            has_si |= role == "supporting_information"
            main_files += role == "main_article"
            supplement_files += role == "supporting_information"
            head = path.read_bytes()[:20000]
            if path.suffix.lower() in {".pdf", ".xlsx", ".docx", ".zip", ".xls"} and not payload_matches_extension(head, path.suffix):
                problems.append(f"file signature mismatch: {path}")
            if is_challenge_page(head.decode("utf-8", errors="ignore")):
                problems.append(f"challenge page stored as source material: {path}")
        for path in (paper_dir / "origin").rglob("*"):
            if path.is_file() and path.name not in {"README.md", "download_manifest.json"}:
                relative = path.relative_to(paper_dir / "origin").as_posix()
                if relative not in listed_paths:
                    problems.append(f"unmanifested origin file: {path}")
        papers_with_main += has_main
        papers_with_si += has_si
        task = json.loads((paper_dir / "task" / "public" / "task.yaml").read_text(encoding="utf-8"))
        if "candidate_claim" in json.dumps(task).lower() or "gold" in json.dumps(task).lower():
            problems.append(f"possible answer leakage in {paper_dir.name}/task/public/task.yaml")
    genes = list(csv.DictReader((OUT / "genesets" / "metabolic_genes_input_v1.csv").open(encoding="utf-8"))) if (OUT / "genesets" / "metabolic_genes_input_v1.csv").exists() else []
    symbols = [row.get("symbol", "") for row in genes]
    if len(symbols) != 1988 or len(set(symbols)) != 1988:
        problems.append(f"gene set expected 1988 unique symbols, got rows={len(symbols)} unique={len(set(symbols))}")
    for schema in (OUT / "schemas").glob("*.json") if (OUT / "schemas").exists() else []:
        json.loads(schema.read_text(encoding="utf-8"))
    for name, id_key in (("papers.jsonl", "paper_id"), ("tasks_public.jsonl", "task_id"), ("datasets.jsonl", "dataset_id")):
        path = OUT / "registry" / name
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()] if path.exists() else []
        ids = [row.get(id_key) for row in rows]
        if len(rows) != expected or len(set(ids)) != expected:
            problems.append(f"registry {name} expected {expected} unique rows, got rows={len(rows)} unique={len(set(ids))}")
    gene_audit_path = OUT / "genesets" / "hgnc_validation_summary.json"
    gene_audit = json.loads(gene_audit_path.read_text(encoding="utf-8")) if gene_audit_path.exists() else {}
    if gene_audit.get("n_symbols") != len(symbols):
        problems.append("gene symbol audit missing or does not match frozen input")
    result = {
        "checked_at": NOW,
        "expected_papers": expected,
        "paper_folders": len(paper_dirs),
        "gene_symbols": len(symbols),
        "origin_files": origin_files,
        "origin_bytes": origin_bytes,
        "main_article_files": main_files,
        "supporting_information_files": supplement_files,
        "papers_with_main_article": papers_with_main,
        "papers_with_supporting_information": papers_with_si,
        "gene_symbols_with_recommended_human_mapping": gene_audit.get("recommended_human_symbols"),
        "gene_symbols_unresolved": gene_audit.get("inferred_species_counts", {}).get("unresolved"),
        "problems": problems,
        "pass": not problems,
    }
    if OUT.exists():
        write_json(OUT / "verification_report.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--no-download", action="store_true", help="Build structure and metadata without remote full-text retrieval")
    args = parser.parse_args()
    if args.verify_only:
        report = verify()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["pass"] else 1

    seed = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    papers = seed["papers"]
    dois = [paper["doi"] for paper in papers]
    assert len(papers) == 30 and len(set(dois)) == 30 and len({p["paper_id"] for p in papers}) == 30
    OUT.mkdir(parents=True, exist_ok=True)
    PRIVATE_OUT.mkdir(parents=True, exist_ok=True)
    gene_manifest = build_geneset()
    id_records = batched_id_conversion(dois)

    crossref: dict[str, tuple[dict, str]] = {}
    resolved_pmids = []
    for index, paper in enumerate(papers, 1):
        print(f"[metadata {index:02d}/30] {paper['doi']}", flush=True)
        crossref[paper["doi"]] = crossref_metadata(paper)
        record = id_records.get(paper["doi"].lower(), {})
        if record.get("pmid"):
            resolved_pmids.append(str(record["pmid"]))
        time.sleep(0.25)
    integrity_map = pubmed_integrity(resolved_pmids)

    paper_rows, task_rows, dataset_rows = [], [], []
    for index, paper in enumerate(papers, 1):
        print(f"[paper {index:02d}/30] {paper['paper_id']} {paper['title']}", flush=True)
        metadata, status = crossref[paper["doi"]]
        id_record = id_records.get(paper["doi"].lower(), {})
        if args.no_download:
            original_download_pmc = globals()["download_pmc"]
            original_fallback = globals()["download_official_fallback"]
            globals()["download_pmc"] = lambda pmcid, origin: ([], {"provider": "skipped", "pmcid": pmcid, "status": "skipped_by_flag"})
            globals()["download_official_fallback"] = lambda s, m, o, e: ([], {"provider": "skipped", "status": "skipped_by_flag", "attempts": []})
        try:
            paper_row, task_row, dataset_row = build_paper(paper, metadata, status, id_record, integrity_map)
        finally:
            if args.no_download:
                globals()["download_pmc"] = original_download_pmc
                globals()["download_official_fallback"] = original_fallback
        paper_rows.append(paper_row)
        task_rows.append(task_row)
        dataset_rows.append(dataset_row)
    write_top_level(seed, paper_rows, task_rows, dataset_rows, gene_manifest)
    report = verify()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
