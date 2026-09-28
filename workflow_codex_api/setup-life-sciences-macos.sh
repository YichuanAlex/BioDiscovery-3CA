#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
CONDA="${WINGPT_CONDA:-/Users/Shared/miniforge3/bin/conda}"
NODE="${WINGPT_NODE:-$ROOT/.runtime/macos/tools/bin/node}"
RUNTIME="$ROOT/.runtime/macos/life-sciences"
SKILLS="$ROOT/skills/anthropic-life-sciences"
SCVERSE="$RUNTIME/scverse"
ALLOTROPE="$RUNTIME/allotrope"
NEXTFLOW="$RUNTIME/nextflow"
LOCKS="$RUNTIME/locks"

[[ "$(uname -s)" == "Darwin" ]] || { echo "This installer is for macOS." >&2; exit 2; }
[[ -x "$CONDA" ]] || { echo "Missing conda: $CONDA" >&2; exit 2; }
[[ -x "$NODE" ]] || { echo "Missing project Node.js: $NODE. Run setup-macos.sh first." >&2; exit 2; }
"$NODE" "$ROOT/scripts/install-anthropic-life-sciences.mjs"

mkdir -p "$RUNTIME/conda-pkgs" "$RUNTIME/pip-cache" "$LOCKS"
export CONDA_PKGS_DIRS="$RUNTIME/conda-pkgs"
export PIP_CACHE_DIR="$RUNTIME/pip-cache"
export PYTHONNOUSERSITE=1
unset PYTHONHOME PYTHONPATH

ensure_python_env() {
  local prefix="$1"
  local python_version="$2"
  if [[ ! -x "$prefix/bin/python" ]]; then
    "$CONDA" create --yes --prefix "$prefix" --override-channels --channel conda-forge \
      "python=$python_version" pip
  fi
}

ensure_python_env "$SCVERSE" 3.12
"$SCVERSE/bin/python" -m pip install --disable-pip-version-check \
  -r "$ROOT/scripts/life-sciences-scverse-requirements.txt"
"$SCVERSE/bin/python" -m pip check
/usr/bin/python3 -c 'import pathlib,subprocess,sys; pathlib.Path(sys.argv[1]).write_bytes(subprocess.check_output(sys.argv[2:]))' \
  "$LOCKS/scverse-pip-freeze.txt" "$SCVERSE/bin/python" -m pip freeze --all
/usr/bin/python3 -c 'import pathlib,subprocess,sys; pathlib.Path(sys.argv[1]).write_bytes(subprocess.check_output(sys.argv[2:]))' \
  "$LOCKS/scverse-conda-explicit.txt" "$CONDA" list --prefix "$SCVERSE" --explicit

ensure_python_env "$ALLOTROPE" 3.11
"$ALLOTROPE/bin/python" -m pip install --disable-pip-version-check \
  -r "$ROOT/scripts/life-sciences-allotrope-requirements.txt"
"$ALLOTROPE/bin/python" -m pip check
/usr/bin/python3 -c 'import pathlib,subprocess,sys; pathlib.Path(sys.argv[1]).write_bytes(subprocess.check_output(sys.argv[2:]))' \
  "$LOCKS/allotrope-pip-freeze.txt" "$ALLOTROPE/bin/python" -m pip freeze --all
/usr/bin/python3 -c 'import pathlib,subprocess,sys; pathlib.Path(sys.argv[1]).write_bytes(subprocess.check_output(sys.argv[2:]))' \
  "$LOCKS/allotrope-conda-explicit.txt" "$CONDA" list --prefix "$ALLOTROPE" --explicit

"$CONDA" create --yes --prefix "$NEXTFLOW" --override-channels \
  --channel conda-forge --channel bioconda openjdk=17.0.18 nextflow=25.04.8
/usr/bin/python3 -c 'import pathlib,subprocess,sys; pathlib.Path(sys.argv[1]).write_bytes(subprocess.check_output(sys.argv[2:]))' \
  "$LOCKS/nextflow-conda-explicit.txt" "$CONDA" list --prefix "$NEXTFLOW" --explicit

echo "Installed isolated life-sciences runtimes under $RUNTIME"
echo "Run ./test-life-sciences-macos.sh for import and CLI smoke tests."
