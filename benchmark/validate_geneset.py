#!/usr/bin/env python3
"""Validate the frozen metabolic symbols against one checksummed HGNC snapshot."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "metabolic_scRNA_benchmark_v0.1"
GENESET = ROOT / "genesets" / "metabolic_genes_input_v1.csv"
REFERENCE_DIR = ROOT / "genesets" / "reference"
HGNC = REFERENCE_DIR / "hgnc_complete_set.tsv"
HGNC_URL = "https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt"
MGI = REFERENCE_DIR / "MGI_MRK_List2.rpt.gz"
MGI_URL = "https://www.informatics.jax.org/downloads/reports/MRK_List2.rpt.gz"
ORTHOLOGY = REFERENCE_DIR / "MGI_HOM_ProteinCoding.rpt"
ORTHOLOGY_URL = "https://www.informatics.jax.org/downloads/reports/HOM_ProteinCoding.rpt"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> None:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(HGNC_URL, headers={"User-Agent": "metabolic-scRNA-benchmark-curation/0.1"})
    with urllib.request.urlopen(request, timeout=180) as response:
        HGNC.write_bytes(response.read())
        last_modified = response.headers.get("Last-Modified")
    for url, path in ((MGI_URL, MGI), (ORTHOLOGY_URL, ORTHOLOGY)):
        request = urllib.request.Request(url, headers={"User-Agent": "metabolic-scRNA-benchmark-curation/0.1"})
        with urllib.request.urlopen(request, timeout=180) as response:
            path.write_bytes(response.read())

    with HGNC.open(encoding="utf-8", newline="") as stream:
        records = list(csv.DictReader(stream, delimiter="\t"))
    approved = {row["symbol"]: row for row in records if row.get("status") == "Approved"}
    previous, aliases = {}, {}
    for row in records:
        for field, target in (("prev_symbol", previous), ("alias_symbol", aliases)):
            for value in (row.get(field) or "").split("|"):
                if value:
                    target.setdefault(value, set()).add(row["symbol"])

    mouse, mouse_aliases = {}, {}
    with gzip.open(MGI, mode="rt", encoding="utf-8", newline="") as stream:
        for values in csv.reader(stream, delimiter="\t"):
            if len(values) < 12:
                continue
            row = {"mgi_id": values[0], "symbol": values[6], "status": values[7], "locus_type": values[9]}
            mouse[row["symbol"]] = row
            for alias in values[11].split("|"):
                if alias:
                    mouse_aliases.setdefault(alias, set()).add(row["symbol"])
    orthology = {}
    with ORTHOLOGY.open(encoding="utf-8", newline="") as stream:
        for values in csv.reader(stream, delimiter="\t"):
            if len(values) >= 6 and values[1] != "Mouse Gene Symbol":
                orthology.setdefault(values[1], set()).add(values[4])

    with GENESET.open(encoding="utf-8-sig", newline="") as stream:
        symbols = [row["symbol"].strip() for row in csv.DictReader(stream)]
    output_rows, counts, species_counts = [], {}, {}
    for symbol in symbols:
        if symbol in approved:
            status, targets = "approved_exact", [symbol]
        elif symbol in previous:
            targets = sorted(previous[symbol])
            status = "previous_symbol_unique" if len(targets) == 1 else "previous_symbol_ambiguous"
        elif symbol in aliases:
            targets = sorted(aliases[symbol])
            status = "alias_symbol_unique" if len(targets) == 1 else "alias_symbol_ambiguous"
        else:
            status, targets = "unmatched", []
        counts[status] = counts.get(status, 0) + 1
        target = targets[0] if len(targets) == 1 else "|".join(targets)
        row = approved.get(target, {})
        if symbol in mouse:
            mouse_status, mouse_targets = "approved_exact", [symbol]
        elif symbol in mouse_aliases:
            mouse_targets = sorted(mouse_aliases[symbol])
            mouse_status = "alias_unique" if len(mouse_targets) == 1 else "alias_ambiguous"
        else:
            mouse_status, mouse_targets = "unmatched", []
        mouse_target = mouse_targets[0] if len(mouse_targets) == 1 else "|".join(mouse_targets)
        human_match = status in {"approved_exact", "previous_symbol_unique", "alias_symbol_unique"}
        mouse_match = mouse_status in {"approved_exact", "alias_unique"}
        species = "human_and_mouse" if human_match and mouse_match else "human" if human_match else "mouse" if mouse_match else "unresolved"
        species_counts[species] = species_counts.get(species, 0) + 1
        mapped = sorted(orthology.get(mouse_target, set())) if mouse_target else []
        recommended_human = target if human_match else mapped[0] if len(mapped) == 1 else ""
        output_rows.append({
            "input_symbol": symbol,
            "inferred_species": species,
            "human_validation_status": status,
            "human_approved_symbol": target,
            "hgnc_id": row.get("hgnc_id", ""),
            "mouse_validation_status": mouse_status,
            "mouse_approved_symbol": mouse_target,
            "mgi_id": mouse.get(mouse_target, {}).get("mgi_id", ""),
            "recommended_human_symbol": recommended_human,
            "orthology_status": "not_needed" if human_match else "one_to_one" if len(mapped) == 1 else "ambiguous" if len(mapped) > 1 else "not_found",
        })

    report_tsv = ROOT / "genesets" / "metabolic_genes_hgnc_validation.tsv"
    with report_tsv.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=output_rows[0], delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)
    mapped_symbols = list(dict.fromkeys(row["recommended_human_symbol"] for row in output_rows if row["recommended_human_symbol"]))
    mapped_csv = ROOT / "genesets" / "metabolic_genes_human_mapped_candidate_v1.csv"
    with mapped_csv.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["symbol"])
        writer.writerows([[symbol] for symbol in mapped_symbols])
    summary = {
        "schema_version": "1.0",
        "checked_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "references": [
            {"name": "HGNC complete set", "url": HGNC_URL, "last_modified": last_modified, "sha256": digest(HGNC)},
            {"name": "MGI current marker list", "url": MGI_URL, "sha256": digest(MGI)},
            {"name": "MGI one-to-one mouse/human protein-coding orthology", "url": ORTHOLOGY_URL, "sha256": digest(ORTHOLOGY)},
        ],
        "input_sha256": digest(GENESET),
        "n_symbols": len(symbols),
        "human_symbol_counts": counts,
        "inferred_species_counts": species_counts,
        "recommended_human_symbols": sum(bool(row["recommended_human_symbol"]) for row in output_rows),
        "recommended_human_unique_symbols": len(mapped_symbols),
        "all_resolved_unambiguously": all(row["inferred_species"] != "unresolved" and bool(row["recommended_human_symbol"]) for row in output_rows),
        "validation_tsv": {"path": report_tsv.relative_to(ROOT).as_posix(), "sha256": digest(report_tsv)},
        "mapped_human_candidate_csv": {"path": mapped_csv.relative_to(ROOT).as_posix(), "sha256": digest(mapped_csv)},
        "note": "Symbol validity does not establish that the list is biologically complete or specifically metabolic.",
    }
    summary_path = ROOT / "genesets" / "hgnc_validation_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
