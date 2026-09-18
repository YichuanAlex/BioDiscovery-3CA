"""Traceable research sources and deterministic completion checks for this workflow."""

import argparse
import csv
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tool43CA" / "CLI" / "src"))
import threeca

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

USER_AGENT = "workflow-codex-research-quality/1.0"
REACTOME_ROOT = "R-HSA-1430728"
THREECA_CACHE = Path(__file__).resolve().parents[2] / ".threeca" / "cache"
NETWORK_TIMEOUT = float(os.environ.get("WINGPT_NETWORK_TIMEOUT", "120"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _workspace(value: str) -> Path:
    root = Path(value).resolve()
    if not root.is_dir():
        raise ValueError(f"Workspace is not a directory: {root}")
    return root


def _inside(root: Path, value: str, *, exists: bool = True) -> Path:
    candidate = (root / value).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"Path leaves workspace: {value}")
    if exists and not candidate.exists():
        raise ValueError(f"Path does not exist: {value}")
    return candidate


def _request(url: str) -> tuple[bytes, dict[str, str]]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json,*/*"})
    with urllib.request.urlopen(request, timeout=NETWORK_TIMEOUT) as response:
        return response.read(), {key.lower(): value for key, value in response.headers.items()}


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_reactome_metabolic_genes(workspace: str) -> dict:
    root = _workspace(workspace)
    version_url = "https://reactome.org/ContentService/data/database/version"
    events_url = f"https://reactome.org/ContentService/data/pathway/{REACTOME_ROOT}/containedEvents"
    gmt_url = "https://reactome.org/download/current/ReactomePathways.gmt.zip"
    version_raw, _ = _request(version_url)
    release = int(json.loads(version_raw))
    events_raw, _ = _request(events_url)
    events = json.loads(events_raw)
    pathway_ids = {REACTOME_ROOT}
    for event in events:
        if isinstance(event, dict) and re.fullmatch(r"R-HSA-\d+", str(event.get("stId", ""))):
            pathway_ids.add(event["stId"])
    archive, headers = _request(gmt_url)
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        names = [name for name in bundle.namelist() if name.lower().endswith(".gmt")]
        if len(names) != 1:
            raise ValueError(f"Expected one GMT in Reactome archive, found {names}")
        gmt = bundle.read(names[0])
    genes: set[str] = set()
    selected_pathways: set[str] = set()
    for raw_line in gmt.decode("utf-8-sig").splitlines():
        fields = raw_line.split("\t")
        if len(fields) < 3:
            continue
        identifiers = set(re.findall(r"R-HSA-\d+", "\t".join(fields[:2])))
        if identifiers & pathway_ids:
            selected_pathways.update(identifiers & pathway_ids)
            genes.update(gene.strip() for gene in fields[2:] if gene.strip())
    if len(genes) < 100 or not selected_pathways:
        raise ValueError(f"Reactome metabolic extraction is implausible: pathways={len(selected_pathways)}, genes={len(genes)}")
    destination = root / "sources" / "reactome"
    gene_path = destination / f"metabolism_{REACTOME_ROOT}_release_{release}_genes.txt"
    gene_path.parent.mkdir(parents=True, exist_ok=True)
    gene_path.write_text("\n".join(sorted(genes)) + "\n", encoding="utf-8")
    manifest = {
        "source": "Reactome",
        "release": release,
        "root_pathway": REACTOME_ROOT,
        "retrieved_at": _now(),
        "source_urls": {"version": version_url, "contained_events": events_url, "gene_sets": gmt_url},
        "archive_sha256": _sha256_bytes(archive),
        "archive_content_length": headers.get("content-length"),
        "contained_events_sha256": _sha256_bytes(events_raw),
        "contained_event_ids": len(pathway_ids),
        "pathways_with_gene_sets": len(selected_pathways),
        "gene_count": len(genes),
        "genes_path": str(gene_path.relative_to(root)),
        "genes_sha256": _sha256_file(gene_path),
    }
    manifest_path = destination / f"metabolism_{REACTOME_ROOT}_release_{release}_manifest.json"
    manifest["manifest_path"] = str(manifest_path.relative_to(root))
    _write_json(manifest_path, manifest)
    return manifest


def search_pubmed(workspace: str, query: str, max_results: int = 20) -> dict:
    if not query.strip() or max_results < 1:
        raise ValueError("PubMed query must be nonempty and max_results positive")
    root = _workspace(workspace)
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    params = urllib.parse.urlencode({"db": "pubmed", "term": query, "retmode": "json", "retmax": max_results, "tool": "workflow_codex"})
    search_url = base + "esearch.fcgi?" + params
    search_raw, _ = _request(search_url)
    search = json.loads(search_raw)["esearchresult"]
    ids = search.get("idlist", [])
    records = []
    summary_url = None
    summary_raw = b""
    if ids:
        summary_url = base + "esummary.fcgi?" + urllib.parse.urlencode({"db": "pubmed", "id": ",".join(ids), "retmode": "json", "tool": "workflow_codex"})
        summary_raw, _ = _request(summary_url)
        summary = json.loads(summary_raw)["result"]
        for pmid in ids:
            item = summary.get(pmid, {})
            records.append({key: item.get(key) for key in ("uid", "title", "authors", "fulljournalname", "pubdate", "volume", "issue", "pages", "elocationid", "articleids")})
    payload = {
        "source": "NCBI PubMed E-utilities",
        "query": query,
        "retrieved_at": _now(),
        "count": int(search.get("count", 0)),
        "returned": len(records),
        "records": records,
        "source_urls": [search_url, *([summary_url] if summary_url else [])],
        "response_sha256": {"search": _sha256_bytes(search_raw), **({"summary": _sha256_bytes(summary_raw)} if summary_raw else {})},
    }
    cache = root / "sources" / "literature" / f"pubmed_{hashlib.sha256(query.encode()).hexdigest()[:16]}.json"
    payload["metadata_path"] = str(cache.relative_to(root))
    _write_json(cache, payload)
    return payload


def verify_doi(workspace: str, doi: str) -> dict:
    root = _workspace(workspace)
    identifier = doi.strip()
    citation_url = None
    if identifier.startswith("3ca:"):
        study = threeca.get_study(identifier, THREECA_CACHE)
        citation_url = study.get("citation_url")
        identifier = str(citation_url or "")
    normalized = threeca.publication_doi_candidate(identifier)
    if not normalized:
        raise ValueError("No DOI is exposed by this identifier/catalog publication URL. Use structured PubMed evidence to obtain a DOI; do not guess bibliographic fields.")
    if not re.fullmatch(r"10\.\d{4,9}/\S+", normalized, re.I):
        raise ValueError(f"Invalid DOI syntax: {doi}")
    url = "https://api.crossref.org/v1/works/" + urllib.parse.quote(normalized, safe="")
    raw, _ = _request(url)
    message = json.loads(raw)["message"]
    if str(message.get("DOI", "")).lower() != normalized.lower():
        raise ValueError("Crossref response DOI does not match the requested publication")
    payload = {
        "source": "Crossref REST API",
        "requested_identifier": doi,
        "catalog_citation_url": citation_url,
        "source_url": url,
        "retrieved_at": _now(),
        "response_sha256": _sha256_bytes(raw),
        "doi": message.get("DOI"),
        "title": message.get("title", []),
        "container_title": message.get("container-title", []),
        "author": message.get("author", []),
        "published": message.get("published"),
        "volume": message.get("volume"),
        "issue": message.get("issue"),
        "page": message.get("page"),
        "type": message.get("type"),
        "publisher": message.get("publisher"),
        "url": message.get("URL"),
    }
    cache = root / "sources" / "literature" / f"crossref_{hashlib.sha256(normalized.lower().encode()).hexdigest()[:16]}.json"
    payload["metadata_path"] = str(cache.relative_to(root))
    _write_json(cache, payload)
    return payload


def inspect_table(workspace: str, path: str, key_columns: list[str] | None = None) -> dict:
    root = _workspace(workspace)
    target = _inside(root, path)
    keys = key_columns or []
    with target.open("r", encoding="utf-8-sig", newline="") as stream:
        sample = stream.read(65536)
        stream.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
        except csv.Error:
            dialect = csv.excel_tab if target.suffix.lower() in {".tsv", ".txt"} else csv.excel
        reader = csv.DictReader(stream, dialect=dialect)
        columns = reader.fieldnames or []
        missing = [key for key in keys if key not in columns]
        if missing:
            raise ValueError(f"Missing key columns {missing}; actual columns: {columns}")
        rows = 0
        empty_key_rows = 0
        unique: set[tuple[str, ...]] = set()
        for row in reader:
            rows += 1
            if keys:
                value = tuple(row.get(key, "") for key in keys)
                empty_key_rows += any(not item for item in value)
                unique.add(value)
    return {
        "path": str(target.relative_to(root)),
        "bytes": target.stat().st_size,
        "sha256": _sha256_file(target),
        "columns": columns,
        "rows": rows,
        "key_columns": keys,
        "unique_keys": len(unique) if keys else None,
        "duplicate_key_rows": rows - len(unique) if keys else None,
        "empty_key_rows": empty_key_rows if keys else None,
        "grain_valid": bool(keys) and rows == len(unique) and empty_key_rows == 0,
    }


def audit_analysis_code(workspace: str, path: str) -> dict:
    root = _workspace(workspace)
    target = _inside(root, path)
    if target.suffix.lower() != ".py":
        raise ValueError("Analysis-code audit accepts a Python file")
    source = target.read_text(encoding="utf-8-sig")
    command = [sys.executable, "-m", "ruff", "check", str(target), "--select", "F821,F822,F823", "--output-format", "json"]
    completed = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8")
    try:
        ruff_findings = json.loads(completed.stdout or "[]")
    except json.JSONDecodeError:
        ruff_findings = [{"code": "RUFF", "message": (completed.stdout or completed.stderr).strip()}]
    risky_patterns = {
        r"pd\.DataFrame\s*\(\s*\w+\.data": "Sparse matrix data values cannot reconstruct the original cell-by-gene matrix.",
        r"(?:adjusted_rand_score|normalized_mutual_info_score)\s*\([^,]+,\s*np\.arange": "Comparing cluster labels with row numbers is not a stability analysis.",
        r"\[['\"]n_cells['\"]\].*(?:umi|gene_counts)|(?:umi|gene_counts).*\[['\"]n_cells['\"]\]": "A study-level n_cells field must not be used as per-cell UMI or detected-gene QC.",
        r"(?:valid_genes|genes_list)\s*\[:\s*\d+\s*\]": "Substituting the first genes when metabolic matching fails invalidates the feature definition.",
        r"community_leiden": "Use the installed and documented Scanpy/igraph Leiden implementation.",
        r"warnings\.filterwarnings\s*\(\s*['\"]ignore": "Blanket warning suppression can hide numerical or API defects.",
        r"results_df\[['\"]labels['\"]\]\.values": "A vector of per-run label arrays is not one label per cell.",
    }
    scientific_findings = [message for pattern, message in risky_patterns.items() if re.search(pattern, source, re.I | re.S)]
    result = {
        "valid": completed.returncode == 0 and not scientific_findings,
        "path": str(target.relative_to(root)),
        "sha256": _sha256_file(target),
        "ruff_findings": ruff_findings,
        "scientific_findings": scientific_findings,
    }
    return result


def prepare_3ca_dataset(workspace: str, source_path: str, destination: str = "inputs") -> dict:
    """Stage a cached sparse raw-count dataset, avoiding guessed paths and shell-copy semantics."""
    root = _workspace(workspace)
    cache = THREECA_CACHE.resolve()
    source = _inside(cache, source_path)
    candidates = [source] if source.is_file() else list(source.rglob("*.mtx"))
    candidates = [path for path in candidates if re.search(r"counts?", path.name, re.I)]
    if len(candidates) != 1:
        raise ValueError("Select a dataset with exactly one raw-count .mtx (counts/UMIcounts), not TPM or normalized expression. Use the actual extracted_path returned by download_asset.")
    expression = _inside(cache, str(candidates[0]))
    parent = expression.parent
    cells = _inside(cache, str(parent / "Cells.csv"))
    genes = _inside(cache, str(parent / "Genes.txt"))
    with expression.open("r", encoding="ascii") as stream:
        header = stream.readline().lower()
    if "coordinate integer" not in header:
        raise ValueError("Input is not an integer coordinate raw-count matrix; do not renormalize TPM as counts")
    rows, columns, entries = _matrix_market_shape(expression)
    cell_table = inspect_table(str(parent), cells.name, ["cell_name"])
    gene_names = [line.strip() for line in genes.read_text(encoding="utf-8-sig").splitlines()]
    if not cell_table["grain_valid"] or not gene_names or any(not gene for gene in gene_names):
        raise ValueError("Cell ids must be unique and every source gene row must be nonempty")
    if (rows, columns) != (len(gene_names), cell_table["rows"]):
        raise ValueError("Raw-count matrix dimensions do not match the Cells.csv/Genes.txt order contract")
    out = _inside(root, destination, exists=False)
    if out == root or (out.exists() and not out.is_dir()):
        raise ValueError("destination must be a workspace subdirectory, not a file")
    files = [expression, cells, genes]
    if (parent / "Samples.csv").is_file():
        files.append(_inside(cache, str(parent / "Samples.csv")))
    fingerprints = {path.name: _sha256_file(path) for path in files}
    for path in files:
        target = _inside(root, str(out / path.name), exists=False)
        if target.exists() and _sha256_file(target) != fingerprints[path.name]:
            raise ValueError(f"Refusing to overwrite different staged inputs: {target}")
    out.mkdir(parents=True, exist_ok=True)
    for path in files:
        target = out / path.name
        if not target.exists():
            shutil.copy2(path, target)
        if _sha256_file(target) != fingerprints[path.name]:
            raise ValueError(f"Copied input hash mismatch: {target}")
    result = {
        "expression_path": str((out / expression.name).relative_to(root)),
        "cells_path": str((out / cells.name).relative_to(root)),
        "genes_path": str((out / genes.name).relative_to(root)),
        "cell_id_column": "cell_name",
        "matrix_orientation": "genes_by_cells",
        "n_cells": cell_table["rows"], "n_genes": len(gene_names), "matrix_entries": entries,
        "unique_gene_symbols": len(set(gene_names)),
        "duplicate_symbol_rows": len(gene_names) - len(set(gene_names)),
        "input_sha256": fingerprints,
        "source_path": str(source),
        "note": "Copied and hashed public raw inputs only. Count/gene/cell alignment is checked; record the original download URL/archive hash from download_asset separately.",
    }
    _write_json(out / "staging_manifest.json", result)
    return result


def _latex_failure_summary(tex: Path, label: str, returncode: int, output: str) -> str:
    """Keep compiler failures short and include source clues a small model can act on."""
    source = tex.read_text(encoding="utf-8", errors="replace").splitlines()
    matches = list(re.finditer(rf"{re.escape(tex.name)}:(\d+):\s*([^\r\n]+)", output))
    fatal_pattern = re.compile(r"Misplaced|LaTeX Error|Undefined control|Missing \$|Emergency stop|Fatal error|Unable to load (?:picture|PDF)|File `[^']+' not found", re.I)
    selected = next((match for match in matches if fatal_pattern.search(match.group(2))), matches[0] if matches else None)
    line_number = int(selected.group(1)) if selected else None
    reported = f"{tex.name}:{line_number}: {selected.group(2).strip()}" if selected else "No file:line diagnostic was emitted."
    context = []
    if line_number:
        for index in range(max(0, line_number - 4), min(len(source), line_number + 2)):
            context.append(f"{index + 1}: {source[index]}")

    candidates = []
    math_depth = 0
    for index, line in enumerate(source, 1):
        math_depth += len(re.findall(r"\\begin\{(?:equation\*?|align\*?|gather\*?|multline\*?)\}", line))
        safe_reference = re.search(r"\\(?:label|ref|eqref|cite|bibitem|url|href)\{|\\includegraphics(?:\[[^]]*\])?\{", line)
        if math_depth == 0 and not safe_reference and re.search(r"(?<!\\)_", line):
            candidates.append(f"{index}: {line}")
        math_depth = max(0, math_depth - len(re.findall(r"\\end\{(?:equation\*?|align\*?|gather\*?|multline\*?)\}", line)))
    clues = "\n".join(candidates[:12]) or "none found"
    nearby = "\n".join(context) or "unavailable"
    return (
        f"{label} failed with exit code {returncode}.\n"
        f"Reported diagnostic: {reported}\n"
        f"Nearby source:\n{nearby}\n"
        f"Possible unescaped '_' outside math/reference keys (LaTeX may report the later use site):\n{clues}\n"
        f"Full compiler output is saved in {tex.with_suffix('.log').name}."
    )


def build_report(workspace: str, tex_path: str = "report/main.tex", pdf_path: str = "report/main.pdf") -> dict:
    """Compile the declared report in place and propagate every engine failure."""
    root = _workspace(workspace)
    tex = _inside(root, tex_path)
    pdf = _inside(root, pdf_path, exists=False)
    if tex.suffix.lower() != ".tex" or pdf != tex.with_suffix(".pdf"):
        raise ValueError("pdf_path must be the same-directory PDF counterpart of tex_path")
    engine = shutil.which("pdflatex") or shutil.which("tectonic")
    if not engine:
        raise ValueError("pdflatex or tectonic is required")

    def run(command: list[str], label: str) -> None:
        completed = subprocess.run(command, cwd=tex.parent, capture_output=True, text=True, errors="replace")
        if completed.returncode:
            output = (completed.stdout + "\n" + completed.stderr).strip()
            raise ValueError(_latex_failure_summary(tex, label, completed.returncode, output))

    if Path(engine).name == "tectonic":
        latex = [engine, "--keep-logs", "--keep-intermediates", "--reruns", "2", tex.name]
        run(latex, "tectonic")
        passes = 3
    else:
        latex = [engine, "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", tex.name]
        run(latex, "pdflatex pass 1")
        aux = tex.with_suffix(".aux")
        if aux.is_file() and "\\bibdata" in aux.read_text(encoding="utf-8", errors="replace"):
            bibtex = shutil.which("bibtex")
            if not bibtex:
                raise ValueError("The report requests BibTeX but bibtex is unavailable")
            run([bibtex, tex.stem], "bibtex")
        run(latex, "pdflatex pass 2")
        run(latex, "pdflatex pass 3")
        passes = 3
    if not pdf.is_file() or pdf.stat().st_size < 1000 or pdf.read_bytes()[:5] != b"%PDF-":
        raise ValueError(f"Compiler did not produce a valid PDF at {pdf_path}")
    pages = len(PdfReader(pdf).pages)
    if pages < 1:
        raise ValueError("Compiled PDF has no pages")
    return {
        "valid": True,
        "engine": str(engine),
        "passes": passes,
        "tex_path": str(tex.relative_to(root)).replace("\\", "/"),
        "pdf_path": str(pdf.relative_to(root)).replace("\\", "/"),
        "log_path": str(tex.with_suffix(".log").relative_to(root)).replace("\\", "/"),
        "pdf_pages": pages,
        "pdf_bytes": pdf.stat().st_size,
        "pdf_sha256": _sha256_file(pdf),
    }


def _require(mapping: dict, key: str, errors: list[str], label: str = "manifest"):
    value = mapping.get(key)
    if value in (None, "", [], {}):
        errors.append(f"{label}.{key} is required")
    return value


def _matrix_market_shape(path: Path) -> tuple[int, int, int]:
    with path.open("r", encoding="ascii") as stream:
        if not stream.readline().lower().startswith("%%matrixmarket matrix"):
            raise ValueError("not a Matrix Market matrix")
        for line in stream:
            if not line.startswith("%"):
                rows, columns, entries = map(int, line.split()[:3])
                return rows, columns, entries
    raise ValueError("missing Matrix Market dimensions")


def _finite_metrics(value: object) -> bool:
    if not isinstance(value, dict) or not value:
        return False
    return all(isinstance(item, (int, float)) and not isinstance(item, bool) and item == item and abs(item) != float("inf") for item in value.values())


def validate_bundle(workspace: str, manifest_path: str = "results/analysis_manifest.json") -> dict:
    root = _workspace(workspace)
    target = _inside(root, manifest_path)
    manifest = json.loads(target.read_text(encoding="utf-8-sig"))
    errors: list[str] = []
    if manifest.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    dataset = manifest.get("dataset") if isinstance(manifest.get("dataset"), dict) else {}
    feature = manifest.get("feature_set") if isinstance(manifest.get("feature_set"), dict) else {}
    analysis = manifest.get("analysis") if isinstance(manifest.get("analysis"), dict) else {}
    artifacts = manifest.get("artifacts") if isinstance(manifest.get("artifacts"), dict) else {}
    for key in ("study_id", "source_url", "sha256", "expression_path", "cells_path", "gene_names_path", "n_cells", "n_genes", "matrix_orientation", "cell_id_field"):
        _require(dataset, key, errors, "dataset")
    if not re.fullmatch(r"[0-9a-f]{64}", str(dataset.get("sha256", "")), re.I):
        errors.append("dataset.sha256 must be a complete SHA-256")
    if dataset.get("matrix_orientation") not in {"cells_by_genes", "genes_by_cells"}:
        errors.append("dataset.matrix_orientation must be cells_by_genes or genes_by_cells")
    if all(dataset.get(key) not in (None, "") for key in ("expression_path", "cells_path", "gene_names_path", "cell_id_field")):
        try:
            expression_path = _inside(root, str(dataset["expression_path"]))
            cells_path = _inside(root, str(dataset["cells_path"]))
            gene_names_path = _inside(root, str(dataset["gene_names_path"]))
            if _sha256_file(expression_path).lower() != str(dataset.get("sha256", "")).lower():
                errors.append("dataset.sha256 does not match expression_path")
            cell_table = inspect_table(workspace, str(cells_path.relative_to(root)), [str(dataset["cell_id_field"])])
            if cell_table["rows"] != dataset.get("n_cells") or not cell_table["grain_valid"]:
                errors.append("dataset cells_path must contain exactly n_cells unique cell ids")
            actual_gene_names = len([line for line in gene_names_path.read_text(encoding="utf-8-sig").splitlines() if line.strip()])
            if actual_gene_names != dataset.get("n_genes"):
                errors.append(f"dataset gene_names_path contains {actual_gene_names} rows, not n_genes={dataset.get('n_genes')}")
            if expression_path.suffix.lower() == ".mtx" and dataset.get("matrix_orientation") in {"cells_by_genes", "genes_by_cells"}:
                matrix_rows, matrix_columns, _ = _matrix_market_shape(expression_path)
                expected = (dataset.get("n_cells"), dataset.get("n_genes")) if dataset["matrix_orientation"] == "cells_by_genes" else (dataset.get("n_genes"), dataset.get("n_cells"))
                if (matrix_rows, matrix_columns) != expected:
                    errors.append(f"Matrix dimensions {(matrix_rows, matrix_columns)} do not match declared orientation and counts {expected}")
        except (OSError, ValueError, TypeError) as error:
            errors.append(f"dataset file validation failed: {error}")
    for key in ("name", "source_url", "retrieved_at", "sha256", "genes_path", "matched_genes_path", "source_gene_count", "matched_gene_count"):
        _require(feature, key, errors, "feature_set")
    if not re.fullmatch(r"[0-9a-f]{64}", str(feature.get("sha256", "")), re.I):
        errors.append("feature_set.sha256 must be a complete SHA-256")
    if all(feature.get(key) not in (None, "") for key in ("genes_path", "matched_genes_path")):
        try:
            from metabolic_states import _read_gene_set

            genes_path = _inside(root, str(feature.get("genes_path", "")))
            if _sha256_file(genes_path).lower() != str(feature.get("sha256", "")).lower():
                errors.append("feature_set.sha256 does not match genes_path")
            source_gene_symbols, _ = _read_gene_set(genes_path)
            actual_genes = len(source_gene_symbols)
            if int(feature.get("source_gene_count", -1)) != actual_genes:
                errors.append(f"feature_set.source_gene_count={feature.get('source_gene_count')} but genes_path contains {actual_genes} unique genes")
            if not 1 <= int(feature.get("matched_gene_count", 0)) <= actual_genes:
                errors.append("feature_set.matched_gene_count must be positive and no larger than source_gene_count")
            matched_path = _inside(root, str(feature.get("matched_genes_path", "")))
            matched_genes = {line.strip() for line in matched_path.read_text(encoding="utf-8-sig").splitlines() if line.strip()}
            source_genes = set(source_gene_symbols)
            if len(matched_genes) != feature.get("matched_gene_count") or not matched_genes <= source_genes:
                errors.append("feature_set matched_genes_path must contain matched_gene_count unique genes, all from the source set")
        except (OSError, ValueError, TypeError) as error:
            errors.append(f"feature_set file validation failed: {error}")
    for key in ("engine", "core_result_path", "core_result_sha256"):
        _require(analysis, key, errors, "analysis")
    from metabolic_states import ENGINE
    if analysis.get("engine") != ENGINE:
        errors.append(f"analysis.engine must be {ENGINE}")
    if not re.fullmatch(r"[0-9a-f]{64}", str(analysis.get("core_result_sha256", "")), re.I):
        errors.append("analysis.core_result_sha256 must be a complete SHA-256")
    if analysis.get("core_result_path"):
        try:
            core_path = _inside(root, str(analysis["core_result_path"]))
            if _sha256_file(core_path).lower() != str(analysis.get("core_result_sha256", "")).lower():
                errors.append("analysis.core_result_sha256 does not match core_result_path")
            core = json.loads(core_path.read_text(encoding="utf-8-sig"))
            engine_path = Path(__file__).with_name("metabolic_states.py")
            if core.get("engine") != analysis.get("engine") or core.get("engine_sha256") != _sha256_file(engine_path):
                errors.append("Core result was not produced by the current vetted metabolic-states engine")
            core_inputs = core.get("inputs", {})
            if core_inputs.get("expression_sha256", "").lower() != str(dataset.get("sha256", "")).lower():
                errors.append("Core result expression hash does not match manifest dataset")
            for key, manifest_key in (("cells", "cells_path"), ("genes", "gene_names_path")):
                declared_path = _inside(root, str(dataset.get(manifest_key, "")))
                if declared_path != _inside(root, str(core_inputs.get(f"{key}_path", ""))) or _sha256_file(declared_path) != core_inputs.get(f"{key}_sha256"):
                    errors.append(f"Manifest {manifest_key} does not match core input path/hash")
            feature_path = _inside(root, str(feature.get("genes_path", "")))
            if feature_path != _inside(root, str(core_inputs.get("metabolic_genes_path", ""))) or _sha256_file(feature_path) != core_inputs.get("metabolic_genes_sha256"):
                errors.append("Manifest feature_set genes_path does not match core input path/hash")
            core_outputs = core.get("outputs", {})
            for output_key, hash_key in (("summary_path", "summary_sha256"), ("labels_path", "labels_sha256"), ("matched_genes_path", "matched_genes_sha256"), ("matched_expression_genes_path", "matched_expression_genes_sha256"), ("gene_set_mapping_path", "gene_set_mapping_sha256"), ("source_feature_mapping_path", "source_feature_mapping_sha256"), ("baseline_metrics_path", "baseline_metrics_sha256"), ("resolution_seed_metrics_path", "resolution_seed_metrics_sha256"), ("stability_metrics_path", "stability_metrics_sha256"), ("confounder_metrics_path", "confounder_metrics_sha256"), ("stratified_cell_type_associations_path", "stratified_cell_type_associations_sha256"), ("cluster_composition_path", "cluster_composition_sha256"), ("replicate_support_path", "replicate_support_sha256"), ("within_replicate_sensitivity_path", "within_replicate_sensitivity_sha256"), ("umap_coordinates_path", "umap_coordinates_sha256")):
                output_path = _inside(root, str(core_outputs.get(output_key, "")))
                if _sha256_file(output_path).lower() != str(core_outputs.get(hash_key, "")).lower():
                    errors.append(f"Core result {hash_key} does not match {output_key}")
            for figure in core_outputs.get("figures", []):
                if _sha256_file(_inside(root, figure)) != core_outputs.get("figure_sha256", {}).get(figure):
                    errors.append(f"Core figure SHA-256 does not match: {figure}")
            if int(core.get("parameters", {}).get("random_baselines", 0)) < 2:
                errors.append("Core result must include multiple size-matched random-gene baselines")
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
            core = {}
            errors.append(f"Core result validation failed: {error}")
    else:
        core = {}
    subgroup_cores = []
    subgroup_analyses = analysis.get("subgroup_analyses", [])
    if subgroup_analyses and not isinstance(subgroup_analyses, list):
        errors.append("analysis.subgroup_analyses must be a list")
        subgroup_analyses = []
    for index, subgroup in enumerate(subgroup_analyses):
        label = f"analysis.subgroup_analyses[{index}]"
        try:
            scope = subgroup["scope"]
            subgroup_path = _inside(root, subgroup["core_result_path"])
            if _sha256_file(subgroup_path).lower() != str(subgroup.get("core_result_sha256", "")).lower():
                errors.append(f"{label}.core_result_sha256 does not match core_result_path")
            subgroup_core = json.loads(subgroup_path.read_text(encoding="utf-8-sig"))
            if subgroup_core.get("engine") != ENGINE or subgroup_core.get("engine_sha256") != _sha256_file(Path(__file__).with_name("metabolic_states.py")):
                errors.append(f"{label} was not produced by the current vetted engine")
            if subgroup_core.get("facts", {}).get("subset") != {"field": scope.get("field"), "values": scope.get("values"), "source_cells_selected": subgroup_core.get("facts", {}).get("source_cells_selected")}:
                errors.append(f"{label}.scope does not match the core subset")
            for input_hash in ("expression_sha256", "cells_sha256", "genes_sha256", "metabolic_genes_sha256"):
                if subgroup_core.get("inputs", {}).get(input_hash) != core.get("inputs", {}).get(input_hash):
                    errors.append(f"{label} {input_hash} differs from the global core")
            for output_key, hash_key in (("summary_path", "summary_sha256"), ("labels_path", "labels_sha256"), ("gene_set_mapping_path", "gene_set_mapping_sha256"), ("stratified_cell_type_associations_path", "stratified_cell_type_associations_sha256")):
                output = _inside(root, subgroup_core.get("outputs", {}).get(output_key, ""))
                if _sha256_file(output) != subgroup_core.get("outputs", {}).get(hash_key):
                    errors.append(f"{label} {hash_key} does not match {output_key}")
            subgroup_cores.append(subgroup_core)
        except (KeyError, OSError, ValueError, TypeError, json.JSONDecodeError) as error:
            errors.append(f"{label} validation failed: {error}")
    rows = analysis.get("rows_analyzed")
    unique_cells = analysis.get("unique_cells_analyzed")
    if not isinstance(rows, int) or rows < 2 or rows != unique_cells:
        errors.append("analysis rows must be one unique row per analyzed cell")
    if isinstance(dataset.get("n_cells"), int) and isinstance(rows, int) and rows > dataset["n_cells"]:
        errors.append("analysis.rows_analyzed exceeds dataset.n_cells")
    core_facts = core.get("facts", {}) if isinstance(core, dict) else {}
    if dataset.get("n_cells") != core_facts.get("source_cells") or dataset.get("n_genes") != core_facts.get("source_genes"):
        errors.append("Manifest source dimensions do not match core input feature/cell counts")
    if feature.get("matched_gene_count") != core_facts.get("metabolic_genes_analyzed"):
        errors.append("Manifest matched_gene_count does not match core metabolic features")
    if core and analysis.get("random_seeds") != core.get("parameters", {}).get("seeds"):
        errors.append("Manifest random_seeds do not match core parameters")
    if core:
        try:
            if _inside(root, str(artifacts.get("summary", "results/summary.json")), exists=False) != _inside(root, str(core.get("outputs", {}).get("summary_path", "")), exists=False):
                errors.append("Manifest summary artifact does not match core summary")
        except ValueError as error:
            errors.append(str(error))
    if rows != core_facts.get("cells_analyzed") or unique_cells != core_facts.get("unique_cells_analyzed"):
        errors.append("Manifest analyzed-cell counts do not match the vetted core result")
    if analysis.get("input_unit") != "cell":
        errors.append("analysis.input_unit must be cell")
    seeds = analysis.get("random_seeds", [])
    if not isinstance(seeds, list) or len(set(seeds)) < 3:
        errors.append("analysis.random_seeds must contain at least three distinct seeds")
    baselines = analysis.get("baselines", [])
    if not isinstance(baselines, list) or not baselines:
        errors.append("analysis.baselines must record at least one computed comparator")
    for index, baseline in enumerate(baselines if isinstance(baselines, list) else []):
        label = f"analysis.baselines[{index}]"
        if not isinstance(baseline, dict) or not baseline.get("name") or not _finite_metrics(baseline.get("metrics")):
            errors.append(f"{label} must include a name and finite computed metrics")
            continue
        try:
            result_path = _inside(root, baseline["result_path"])
            if not result_path.is_file() or not result_path.stat().st_size:
                errors.append(f"{label}.result_path is empty")
        except (KeyError, OSError, ValueError) as error:
            errors.append(f"{label} result validation failed: {error}")
    confounders = {str(value).lower() for value in analysis.get("confounders_checked", [])}
    if not confounders & {"sample", "patient", "donor"}:
        errors.append("analysis.confounders_checked must include a biological replicate field")
    methods = analysis.get("methods", [])
    core_method_present = False
    if not isinstance(methods, list) or not methods:
        errors.append("analysis.methods must record at least one clustering result")
    for index, method in enumerate(methods if isinstance(methods, list) else []):
        label = f"analysis.methods[{index}]"
        if not isinstance(method, dict):
            errors.append(f"{label} must be an object")
            continue
        for key in ("name", "labels_path", "cell_id_column", "label_column", "n_clusters"):
            _require(method, key, errors, label)
        if not _finite_metrics(method.get("metrics")):
            errors.append(f"{label}.metrics must contain finite computed values")
        try:
            table = inspect_table(workspace, method["labels_path"], [method["cell_id_column"]])
            labels_path = _inside(root, method["labels_path"])
            if core and labels_path == _inside(root, str(core.get("outputs", {}).get("labels_path", ""))):
                core_method_present = True
                if method.get("n_clusters") != core_facts.get("n_clusters") or any(core_facts.get("metrics", {}).get(key) != value for key, value in method.get("metrics", {}).items()):
                    errors.append(f"{label} metrics or cluster count do not match core facts")
            with labels_path.open("r", encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                labels = {row.get(method["label_column"], "") for row in reader}
            labels.discard("")
            if table["rows"] != rows or table["unique_keys"] != rows:
                errors.append(f"{label} labels must contain exactly one row for each analyzed cell")
            if len(labels) != method.get("n_clusters") or len(labels) < 2:
                errors.append(f"{label}.n_clusters does not match distinct labels or is <2")
        except (OSError, ValueError, KeyError, TypeError) as error:
            errors.append(f"{label} validation failed: {error}")
    if not core_method_present:
        errors.append("analysis.methods must include the actual core labels and metrics")
    figures = artifacts.get("figures", [])
    if not isinstance(figures, list) or not figures:
        errors.append("artifacts.figures must list actual generated figures")
    for figure in figures if isinstance(figures, list) else []:
        try:
            item = _inside(root, figure)
            if not item.is_file() or item.stat().st_size < 100:
                errors.append(f"Figure is empty or invalid: {figure}")
        except ValueError as error:
            errors.append(str(error))
    for subgroup_core in subgroup_cores:
        for figure in subgroup_core.get("outputs", {}).get("figures", []):
            if figure not in figures:
                errors.append(f"Subgroup core figure is missing from artifacts.figures: {figure}")
    tex_path = artifacts.get("tex", "report/main.tex")
    pdf_path = artifacts.get("pdf", "report/main.pdf")
    summary_path = artifacts.get("summary", "results/summary.json")
    try:
        tex_file = _inside(root, tex_path)
        pdf_file = _inside(root, pdf_path)
        _inside(root, summary_path)
        tex = tex_file.read_text(encoding="utf-8-sig")
        tex_lower = tex.lower()
        claim_rules = (
            (r"\b(?:not\s+)?significantly\b|\bstatistically\s+significant\b", "Report assigns statistical significance without a valid inferential test"),
            (r"\b(?:better|worse)\s+than\s+random\b", "Report turns the random-control rank into a definitive better/worse claim"),
            (r"\b(?:largely\s+)?driven\s+by\b", "Report makes a causal 'driven by' claim from descriptive association"),
            (r"\b(?:strongly|moderately|weakly)\s+associated\b|\b(?:strong|moderate|weak)\s+association\b", "Report applies an unvalidated qualitative threshold to an association metric"),
            (r"\bno evidence (?:of|for)\b[^.\n]{0,160}\b(?:metabolic|cluster|group|state)", "Report makes a definitive absence claim although the core conclusion is inconclusive"),
            (r"\b(?:leiden|metabolic (?:gene )?clustering)\b[^.\n]{0,160}\b(?:comparable|higher|lower|better|worse)\b[^.\n]{0,80}\bkmeans\b", "Report directly compares Leiden and KMeans silhouette values as if they test the same claim"),
            (r"\b(?:comparable|similar)\s+to\s+(?:the\s+)?random controls?\b|\bvery low\s+silhouette\b", "Report applies an unsupported qualitative threshold to random-control or silhouette results"),
            (r"\bbeyond what could arise from random\b|\brandom controls?\b[^.\n]{0,120}\bindicates?\b", "Report turns descriptive random-control results into a definitive biological conclusion"),
        )
        for pattern, message in claim_rules:
            if re.search(pattern, tex_lower):
                errors.append(message)
        if re.search(r"\\(?:log_?1p|operatorname\{log1p\})\b", tex_lower):
            errors.append("Report must typeset log1p as a standard log(1 + x) expression")
        if core:
            actual_seeds = core.get("parameters", {}).get("seeds", [])
            seed_sentences = [sentence for sentence in re.split(r"[.!?\n]", tex_lower) if "seed" in sentence]
            if actual_seeds and not any(all(re.search(rf"(?<!\d){re.escape(str(seed))}(?!\d)", sentence) for seed in actual_seeds) for sentence in seed_sentences):
                errors.append(f"Report must state the actual core seed grid ({', '.join(map(str, actual_seeds))}) in one seed sentence")
            scaling = str(core.get("methods", {}).get("feature_scaling", "")).lower()
            if "zero_center=false" in scaling and re.search(r"\b(?:with|using)\s+zero[- ]center|\b(?:were|was|are|is)\s+zero[- ]centered\b", tex_lower):
                errors.append("Report contradicts core feature scaling: zero_center=False")
        if subgroup_cores:
            for question in (1, 2, 3):
                next_question = question + 1
                end = rf"(?=question\s*{next_question}\b|\\end\{{document\}})" if question < 3 else r"(?=\\end\{document\})"
                section = re.search(rf"question\s*{question}\b(.*?){end}", tex_lower, re.S)
                if not section:
                    errors.append(f"Report must contain a distinct Question {question} answer section")
                elif not re.search(r"\b(?:inconclusive|descriptive|candidate)\b", section.group(1)):
                    errors.append(f"Question {question} must state an explicit descriptive, candidate, or inconclusive verdict")
        if "\\includegraphics" not in tex:
            errors.append("LaTeX report contains no included figure")
        document_start = tex.find("\\begin{document}")
        document_end = tex.rfind("\\end{document}")
        if document_start < 0 or document_end <= document_start:
            errors.append("LaTeX report must contain a complete document environment")
        elif any(not document_start < match.start() < document_end for match in re.finditer(r"\\includegraphics", tex)):
            errors.append("Every included figure must be inside the LaTeX document environment")
        if core and len(figures) < 2:
            errors.append("The metabolic-state report must contain at least two substantive figures")
        figure_blocks = re.findall(r"\\begin\{figure\}.*?\\end\{figure\}", tex, re.S)
        if core and len(figure_blocks) < len(figures):
            errors.append("Each manifest figure must appear in its own LaTeX figure environment")
        for block in figure_blocks:
            labels = re.findall(r"\\label\{([^}]+)\}", block)
            if "\\includegraphics" not in block or "\\caption{" not in block or len(labels) != 1:
                errors.append("Each figure environment must contain one image, caption and label")
            elif f"\\ref{{{labels[0]}}}" not in tex:
                errors.append(f"Figure label is not referenced in report prose: {labels[0]}")
        table_blocks = re.findall(r"\\begin\{table\}.*?\\end\{table\}", tex, re.S)
        three_line_tables = [block for block in table_blocks if all(token in block for token in ("\\toprule", "\\midrule", "\\bottomrule"))]
        if core and ("\\usepackage{booktabs}" not in tex or not three_line_tables):
            errors.append("Report must include at least one booktabs three-line table")
        for block in three_line_tables:
            labels = re.findall(r"\\label\{([^}]+)\}", block)
            if "\\caption{" not in block or len(labels) != 1:
                errors.append("Each three-line table must contain one caption and label")
            elif f"\\ref{{{labels[0]}}}" not in tex:
                errors.append(f"Table label is not referenced in report prose: {labels[0]}")
            if re.search(r"\\begin\{tabular\}\{[^}]*\|", block):
                errors.append("Three-line tables must not use vertical rules")
        equation_blocks = re.findall(r"\\begin\{(?:equation|align)\*?\}.*?\\end\{(?:equation|align)\*?\}", tex, re.S)
        if core and not equation_blocks:
            errors.append("Report must include at least one displayed mathematical formula")
        for block in equation_blocks:
            labels = re.findall(r"\\label\{([^}]+)\}", block)
            if len(labels) != 1 or f"\\ref{{{labels[0]}}}" not in tex:
                errors.append("Each displayed formula must have one label and a prose reference")
        if core and equation_blocks and "where" not in tex_lower:
            errors.append("Report must define mathematical symbols in prose using a where-clause")
        if re.search(r"\\(?:ref|cite)\{\?+\}", tex) or "??" in tex:
            errors.append("LaTeX report contains unresolved references")
        if core:
            cluster_sizes = core_facts.get("cluster_size_summary", {})
            for field, label in (("minimum_cells", "minimum"), ("maximum_cells", "maximum")):
                value = cluster_sizes.get(field)
                if isinstance(value, int) and str(value) not in tex and f"{value:,}" not in tex:
                    errors.append(f"Report must state the actual {label} cluster size ({value})")
            resolution_selection = core_facts.get("resolution_selection", {})
            if resolution_selection and ("median silhouette" not in tex_lower or "mean pairwise ari" not in tex_lower):
                errors.append("Report must state the actual resolution-selection criterion and ARI stability filter/tie-breaker")
            comparison = core_facts.get("random_control_comparison", {})
            observed = comparison.get("random_controls_exceeding_or_equal")
            total = comparison.get("random_controls_total")
            count_patterns = (f"{observed} of {total}", f"{observed}/{total}", f"{observed} out of {total}")
            if isinstance(observed, int) and isinstance(total, int) and not any(pattern in tex_lower for pattern in count_patterns):
                errors.append(f"Report must state the observed random-control exceedance count ({observed} of {total})")
            if comparison and not re.search(r"add[- ]one", tex_lower):
                errors.append("Report must identify the rank fraction as an add-one correction")
            if re.search(r"\d+(?:\.\d+)?\\?%\s+of\s+(?:the\s+)?random controls?\s+(?:had|were|exceeded)", tex_lower):
                errors.append("Report must not reinterpret the add-one rank fraction as an observed percentage of random controls")
            within = core_facts.get("within_replicate_summary", {})
            if int(within.get("replicates_analyzed", 0)):
                low = within.get("global_vs_within_ari_min")
                high = within.get("global_vs_within_ari_max")
                weakest = str(within.get("weakest_replicate", ""))
                if not all(f"{value:.3f}" in tex for value in (low, high)):
                    errors.append("Report must state the three-decimal within-replicate global-vs-within ARI range")
                if weakest and not any(f"{name} {weakest}" in tex_lower for name in ("patient", "donor", "sample", "replicate")):
                    errors.append(f"Report must identify the weakest within-replicate result ({weakest})")
            if not core_facts.get("random_control_comparison"):
                errors.append("Core result lacks explicit random-control count facts")
            if re.search(r"no (?:single )?cluster (?:was|is) dominated by (?:one |a )?(?:patient|sample)", tex_lower):
                errors.append("Report makes an unsupported no-patient/sample-dominance claim")
        for index, subgroup_core in enumerate(subgroup_cores, 1):
            subgroup_facts = subgroup_core.get("facts", {})
            prefix = f"Subgroup {index} report"
            subgroup_sizes = subgroup_facts.get("cluster_size_summary", {})
            for field, label in (("minimum_cells", "minimum"), ("maximum_cells", "maximum")):
                value = subgroup_sizes.get(field)
                if isinstance(value, int) and str(value) not in tex and f"{value:,}" not in tex:
                    errors.append(f"{prefix} must state the actual {label} cluster size ({value})")
            subgroup_comparison = subgroup_facts.get("random_control_comparison", {})
            observed = subgroup_comparison.get("random_controls_exceeding_or_equal")
            total = subgroup_comparison.get("random_controls_total")
            if isinstance(observed, int) and isinstance(total, int) and not any(pattern in tex_lower for pattern in (f"{observed} of {total}", f"{observed}/{total}", f"{observed} out of {total}")):
                errors.append(f"{prefix} must state the observed random-control exceedance count ({observed} of {total})")
            subgroup_within = subgroup_facts.get("within_replicate_summary", {})
            if int(subgroup_within.get("replicates_analyzed", 0)):
                low = subgroup_within.get("global_vs_within_ari_min")
                high = subgroup_within.get("global_vs_within_ari_max")
                weakest = str(subgroup_within.get("weakest_replicate", ""))
                if not all(f"{value:.3f}" in tex for value in (low, high)):
                    errors.append(f"{prefix} must state the three-decimal within-replicate global-vs-within ARI range")
                if weakest and not any(f"{name} {weakest}" in tex_lower for name in ("patient", "donor", "sample", "replicate")):
                    errors.append(f"{prefix} must identify the weakest within-replicate result ({weakest})")
        if pdf_file.stat().st_mtime_ns < tex_file.stat().st_mtime_ns:
            errors.append("PDF is older than LaTeX source; rebuild it")
        rendered_pages = 0
        pdf_pages = 0
        if pdf_file.stat().st_size < 1000 or pdf_file.read_bytes()[:5] != b"%PDF-":
            errors.append("PDF is invalid or a placeholder")
        else:
            pages = PdfReader(pdf_file).pages
            pdf_pages = len(pages)
            rendered_text = "\n".join(page.extract_text() or "" for page in pages)
            if not rendered_text.strip():
                errors.append("PDF has no extractable report text")
            if "??" in rendered_text:
                errors.append("PDF contains unresolved references")
            log_file = tex_file.with_suffix(".log")
            if not log_file.is_file() or log_file.stat().st_mtime_ns < tex_file.stat().st_mtime_ns:
                errors.append("Current LaTeX compiler log is missing or older than the TeX source")
            else:
                log_text = log_file.read_text(encoding="utf-8-sig", errors="replace")
                if re.search(r"Overfull \\[hv]box|! LaTeX Error|undefined references|Citation .* undefined", log_text, re.I):
                    errors.append("LaTeX log contains overflow, compilation, citation or reference errors")
            renderer = shutil.which("pdftoppm")
            if not renderer:
                errors.append("pdftoppm is required for final all-page PDF rendering QA")
            else:
                with tempfile.TemporaryDirectory() as temporary:
                    prefix = str(Path(temporary) / "page")
                    rendered = subprocess.run([renderer, "-png", "-r", "120", str(pdf_file), prefix], capture_output=True, text=True)
                    page_images = sorted(Path(temporary).glob("page-*.png"))
                    rendered_pages = len(page_images)
                    if rendered.returncode or rendered_pages != pdf_pages:
                        errors.append("All-page PDF rendering failed or produced the wrong page count")
                    for page_image in page_images:
                        with Image.open(page_image) as image:
                            gray = image.convert("L")
                            histogram = gray.histogram()
                            pixels = gray.width * gray.height
                            if sum(histogram[:245]) / pixels < 0.0005:
                                errors.append(f"Rendered PDF contains a blank or nearly blank page: {page_image.name}")
                            border = 2
                            edges = [gray.crop((0, 0, gray.width, border)), gray.crop((0, gray.height - border, gray.width, gray.height)), gray.crop((0, 0, border, gray.height)), gray.crop((gray.width - border, 0, gray.width, gray.height))]
                            if any(sum(edge.histogram()[:235]) for edge in edges):
                                errors.append(f"Rendered PDF content touches the page edge and may be cropped: {page_image.name}")
        for figure in figures if isinstance(figures, list) else []:
            if Path(figure).name not in tex and Path(figure).stem not in tex:
                errors.append(f"Figure is not referenced by LaTeX: {figure}")
    except (OSError, ValueError, TypeError) as error:
        errors.append(f"Report validation failed: {error}")
    references = manifest.get("references", [])
    if not isinstance(references, list) or not references:
        errors.append("references must record verified bibliographic metadata")
    citation_keys = set(re.findall(r"\\cite\w*\{([^}]+)\}", locals().get("tex", "")))
    citation_keys = {key.strip() for group in citation_keys for key in group.split(",") if key.strip()}
    verified_keys = set()
    for reference in references if isinstance(references, list) else []:
        try:
            key = reference["key"]
            doi = reference["doi"].lower()
            metadata = json.loads(_inside(root, reference["metadata_path"]).read_text(encoding="utf-8-sig"))
            if str(metadata.get("doi", "")).lower() != doi or metadata.get("source") != "Crossref REST API":
                errors.append(f"Reference {key} DOI does not match Crossref metadata")
            else:
                verified_keys.add(key)
        except (KeyError, OSError, ValueError, json.JSONDecodeError) as error:
            errors.append(f"Reference validation failed: {error}")
    missing_citations = sorted(citation_keys - verified_keys)
    if missing_citations:
        errors.append(f"Cited keys lack verified metadata: {missing_citations}")
    result = {
        "valid": not errors,
        "checked_at": _now(),
        "manifest_path": str(target.relative_to(root)),
        "manifest_sha256": _sha256_file(target),
        "errors": errors,
        "checks": {"methods": len(methods) if isinstance(methods, list) else 0, "figures": len(figures) if isinstance(figures, list) else 0, "three_line_tables": len(locals().get("three_line_tables", [])), "formulas": len(locals().get("equation_blocks", [])), "pdf_pages": locals().get("pdf_pages", 0), "rendered_pages": locals().get("rendered_pages", 0), "references": len(references) if isinstance(references, list) else 0},
    }
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="research-quality")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--pretty", action="store_true")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("reactome-metabolic-genes")
    pubmed = commands.add_parser("pubmed-search")
    pubmed.add_argument("query")
    pubmed.add_argument("--max-results", type=int, default=20)
    crossref = commands.add_parser("verify-doi")
    crossref.add_argument("doi")
    table = commands.add_parser("inspect-table")
    table.add_argument("path")
    table.add_argument("--key-column", action="append", default=[])
    audit = commands.add_parser("audit-analysis-code")
    audit.add_argument("path")
    stage = commands.add_parser("prepare-3ca-dataset")
    stage.add_argument("source_path")
    stage.add_argument("--destination", default="inputs")
    metabolic = commands.add_parser("analyze-metabolic-states")
    metabolic.add_argument("--expression-path", required=True)
    metabolic.add_argument("--cells-path", required=True)
    metabolic.add_argument("--genes-path", required=True)
    metabolic.add_argument("--metabolic-genes-path", required=True)
    metabolic.add_argument("--cell-id-column", default="cell_name")
    metabolic.add_argument("--output-dir", default="results/core_analysis")
    metabolic.add_argument("--seed", type=int, action="append")
    metabolic.add_argument("--resolution", type=float, action="append")
    metabolic.add_argument("--random-baselines", type=int, default=19)
    metabolic.add_argument("--min-counts", type=int, default=500)
    metabolic.add_argument("--min-genes", type=int, default=200)
    metabolic.add_argument("--max-mito-percent", type=float, default=20.0)
    metabolic.add_argument("--min-feature-cells", type=int, default=20)
    metabolic.add_argument("--min-metabolic-genes", type=int, default=30)
    metabolic.add_argument("--metric-cells", type=int, default=3000)
    metabolic.add_argument("--subset-field")
    metabolic.add_argument("--subset-value", action="append")
    build = commands.add_parser("build-report")
    build.add_argument("--tex-path", default="report/main.tex")
    build.add_argument("--pdf-path", default="report/main.pdf")
    validate = commands.add_parser("validate")
    validate.add_argument("manifest_path", nargs="?", default="results/analysis_manifest.json")
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "reactome-metabolic-genes":
        result = fetch_reactome_metabolic_genes(args.workspace)
    elif args.command == "pubmed-search":
        result = search_pubmed(args.workspace, args.query, args.max_results)
    elif args.command == "verify-doi":
        result = verify_doi(args.workspace, args.doi)
    elif args.command == "inspect-table":
        result = inspect_table(args.workspace, args.path, args.key_column)
    elif args.command == "audit-analysis-code":
        result = audit_analysis_code(args.workspace, args.path)
    elif args.command == "prepare-3ca-dataset":
        result = prepare_3ca_dataset(args.workspace, args.source_path, args.destination)
    elif args.command == "analyze-metabolic-states":
        from metabolic_states import analyze_metabolic_states

        result = analyze_metabolic_states(
            args.workspace,
            args.expression_path,
            args.cells_path,
            args.genes_path,
            args.metabolic_genes_path,
            cell_id_column=args.cell_id_column,
            output_dir=args.output_dir,
            seeds=args.seed,
            resolutions=args.resolution,
            random_baselines=args.random_baselines,
            min_counts=args.min_counts,
            min_genes=args.min_genes,
            max_mito_percent=args.max_mito_percent,
            min_feature_cells=args.min_feature_cells,
            min_metabolic_genes=args.min_metabolic_genes,
            metric_cells=args.metric_cells,
            subset_field=args.subset_field,
            subset_values=args.subset_value,
        )
    elif args.command == "build-report":
        result = build_report(args.workspace, args.tex_path, args.pdf_path)
    else:
        result = validate_bundle(args.workspace, args.manifest_path)
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0 if result.get("valid", True) else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
