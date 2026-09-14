"""Read-only report/provenance checks; save derived acceptance evidence in supervisor."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

SUP = Path(__file__).resolve().parent
TASK = Path(r"C:\Users\User\Desktop\agentic\3CA\Q1")
REPORT = TASK / "report"
entries = re.findall(r"@article\{([^,]+),(.*?)\n\}", (REPORT / "references.bib").read_text(), re.S)
keys = ["Tirosh2016", "Gavish2023", "Xiao2019", "Kanehisa2023", "Rousseeuw1987", "Hubert1985", "Wu2022"]
years = [2016, 2023, 2019, 2023, 1987, 1985, 2022]
assert [k for k, _ in entries] == keys
normalize = lambda s: re.sub(r"\s+", " ", s).strip().lower()
bibliography = []
for i, (key, body) in enumerate(entries, 1):
    fields = dict(re.findall(r"(\w+)\s*=\s*\{([^}]*)\}", body))
    metadata = json.loads((REPORT / ("metadata-%d.json" % i)).read_text(encoding="utf-8-sig"))["message"]
    for field, value in [("doi", metadata["DOI"]), ("title", metadata["title"][0]),
                         ("journal", metadata["container-title"][0])]:
        assert normalize(fields[field]) == normalize(value), (key, field)
    assert int(fields["year"]) == years[i - 1]
    assert "and and" not in normalize(fields["author"])
    assert metadata["author"][0]["family"] in fields["author"]
    bibliography.append({"key": key, "doi": fields["doi"], "verified_against": "saved Crossref response"})

manifest = json.loads((TASK / "data/source_manifest.json").read_text())
# Hash the saved source artifacts independently; exact field structure stays in original manifests.
provenance = []
for file in [TASK / "data/Data_Tirosh2016_Skin.tar.gz", TASK / "data/Meta-data_Tirosh2016_Skin.tar.gz",
             TASK / "data/KEGG_metabolism_nc.gmt"]:
    assert file.is_file(), str(file)
    digest = hashlib.sha256()
    with file.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    provenance.append({"file": str(file.relative_to(TASK)), "bytes": file.stat().st_size, "sha256": digest.hexdigest()})
assert provenance[0]["sha256"] == "9e157aceb5a39add6e04c4d92db7f970bf19413a14a8c87a1262f9424f0818f6"
assert provenance[1]["sha256"] == "741107ef4ad09cb19b9a22c8af40ce7440e24f18cf1012c2ebb4c03600fede17"
assert provenance[2]["sha256"] == "754f60c535516449f601a34351f8be0846abe8d86fd0080c77c4d6ceac069262"

sources = "\n".join(f.read_text(encoding="utf-8") for f in REPORT.glob("*.tex"))
main_source = (REPORT / "main.tex").read_text(encoding="utf-8")
for stem in ["introduction", "methods", "results", "figures", "discussion", "availability"]:
    assert main_source.count("\\input{" + stem + ".tex}") == 1, "Missing/duplicate content input: " + stem
assert "\\begin{thebibliography}" not in main_source
assert main_source.count("\\bibliography{references}") == 1
assert main_source.count("\\bibliographystyle{plainnat}") == 1
readme = (TASK / "README.md").read_text(encoding="utf-8")
for block in re.findall(r"```powershell\s*\n(.*?)```", readme, re.S):
    # Parse only: never execute the README's research/build commands in supervision.
    subprocess.run([r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe", "-NoProfile", "-Command",
                    "try { [void][scriptblock]::Create([Console]::In.ReadToEnd()) } catch { Write-Error $_; exit 1 }"],
                   input=block, text=True, encoding="utf-8", check=True, capture_output=True)
for incorrect in ["does not guarantee that no patient", "not a formal statistical test",
                  "not nested within each patient or cluster", "snapshot of metabolic gene expression",
                  "groups do not correspond to established, universal malignant metabolic states",
                  "the clustering predicts known cell-type labels"]:
    assert incorrect not in sources, "Rejected scientific wording remains: " + incorrect
assert "\\subsection{Limitations}" in sources
for key in keys:
    assert re.search(r"\\cite\w*\{[^}]*\b" + key + r"\b[^}]*\}", sources), "Uncited reference: " + key
assert sources.count("\\toprule") >= 2 and sources.count("\\bottomrule") >= 2
assert sources.count("\\begin{equation}") >= 3
for stem in ["figure1_dataset_and_design", "figure2_metabolic_separation", "figure3_robustness_and_interpretation"]:
    assert stem in sources
log = (REPORT / "main.log").read_text(errors="replace")
for marker in ["Undefined control sequence", "LaTeX Error", "undefined references", "Citation", "Overfull"]:
    assert marker not in log, "Review compilation diagnostic: " + marker
pdf_reader = Path(r"C:\Program Files\MiKTeX\miktex\bin\x64\pdftotext.exe")
pdf_text = subprocess.check_output([str(pdf_reader), "-layout", str(REPORT / "main.pdf"), "-"], text=True, encoding="utf-8")
pages = [p for p in pdf_text.split("\f") if p.strip()]
assert len(pages) >= 5
assert all(len(page.strip()) > 80 for page in pages), "Suspicious empty page"
assert "??" not in pdf_text and "[?]" not in pdf_text
assert not re.search(r"\b(TODO|TBD|PLACEHOLDER)\b", pdf_text)
for number in ["0.377", "0.224", "0.884", "0.896", "0.892", "0.856", "0.875", "0.897", "0.742", "0.228"]:
    assert number in pdf_text, "Expected rounded result missing: " + number
record = {"status": "PASS", "scope": "bibliography metadata, source artifact hashes, required figures/tables/equations, LaTeX diagnostics, PDF text and key numerical values",
          "visual_qa": "separate manual page inspection required; not certified by this script",
          "pages": len(pages), "page_text_lengths": [len(p.strip()) for p in pages],
          "bibliography": bibliography, "source_artifacts": provenance,
          "pdf_sha256": hashlib.sha256((REPORT / "main.pdf").read_bytes()).hexdigest()}
(SUP / "report-audit.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
print("PASS: 7 verified references, source hashes, report structures/values, clean compilation, %d PDF pages." % len(pages))
