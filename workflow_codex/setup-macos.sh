#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
BASE_PYTHON="${WINGPT_BASE_PYTHON:-/Users/Shared/miniforge3/envs/py312/bin/python}"
CONDA="${WINGPT_CONDA:-/Users/Shared/miniforge3/bin/conda}"
RUNTIME="$ROOT/.runtime/macos"
mkdir -p "$RUNTIME"
export CONDA_PKGS_DIRS="$RUNTIME/conda-pkgs"
export PIP_CACHE_DIR="$RUNTIME/pip-cache"
unset PYTHONHOME
unset PYTHONPATH
export PYTHONNOUSERSITE=1
echo "Install plan: reuse py312 MLX packages; add project-local science/MCP packages and Node/TeX/PDF tools."
"$BASE_PYTHON" -I -c 'import sys; assert sys.version_info >= (3, 10); print(f"Base Python: {sys.executable} ({sys.version.split()[0]})")'
"$BASE_PYTHON" -m venv --system-site-packages "$RUNTIME/python"
"$RUNTIME/python/bin/python" -m pip install -r "$ROOT/tools/research-quality/science-requirements.txt" -r "$ROOT/tools/tool43CA/MCP/requirements.txt" "$ROOT/tools/tool43CA/CLI"
"$CONDA" create --yes --prefix "$RUNTIME/tools" --override-channels --channel conda-forge 'nodejs>=24,<25' tectonic poppler
"$RUNTIME/python/bin/python" -m pip freeze > "$RUNTIME/python-packages.txt"
"$CONDA" list --prefix "$RUNTIME/tools" --explicit > "$RUNTIME/conda-explicit.txt"
echo "Project-local macOS dependencies installed: $RUNTIME"
