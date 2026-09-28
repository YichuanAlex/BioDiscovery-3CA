#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
RUNTIME="$ROOT/.runtime/macos/life-sciences"
SKILLS="$ROOT/skills/anthropic-life-sciences"
SCVERSE="$RUNTIME/scverse/bin/python"
ALLOTROPE="$RUNTIME/allotrope/bin/python"
NEXTFLOW_BIN="$RUNTIME/nextflow/bin"

export PYTHONNOUSERSITE=1
unset PYTHONHOME PYTHONPATH
export JAVA_HOME="$RUNTIME/nextflow/lib/jvm"
export PATH="$JAVA_HOME/bin:$NEXTFLOW_BIN:$PATH"

"$SCVERSE" -I -c '
import anndata, mudata, scanpy, scipy, scvelo, scvi, torch, yaml
print("scverse imports: OK")
print({
    "anndata": anndata.__version__,
    "mudata": mudata.__version__,
    "scanpy": scanpy.__version__,
    "scvelo": scvelo.__version__,
    "scvi-tools": scvi.__version__,
    "torch": torch.__version__,
})
assert hasattr(scvi.model.SCVI, "setup_anndata")
'
"$SCVERSE" "$SKILLS/single-cell-rna-qc/scripts/qc_analysis.py" --help >/dev/null
"$SCVERSE" "$SKILLS/scvi-tools/scripts/train_model.py" --help >/dev/null
"$SCVERSE" "$SKILLS/nextflow-development/scripts/check_environment.py" --help >/dev/null

"$ALLOTROPE" -I -c '
import importlib.metadata as metadata
import allotropy, openpyxl, pandas, pdfplumber
expected = {
    "allotropy": "0.1.55",
    "pandas": "2.3.3",
    "openpyxl": "3.1.2",
    "pdfplumber": "0.9.0",
}
actual = {name: metadata.version(name) for name in expected}
assert actual == expected, (actual, expected)
print("Allotrope exact pins: OK", actual)
'
"$ALLOTROPE" "$SKILLS/instrument-data-to-allotrope/scripts/convert_to_asm.py" --help >/dev/null
"$SCVERSE" "$SKILLS/clinical-trial-protocol-skill/scripts/sample_size_calculator.py" --help >/dev/null

java -version
nextflow -version
mkdir -p "$RUNTIME/smoke/work"
(
  cd "$RUNTIME/smoke"
  nextflow run "$ROOT/scripts/nextflow-smoke.nf" -ansi-log false -work-dir "$RUNTIME/smoke/work"
)

echo "Life-sciences macOS smoke tests: PASS"
