#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
CONDA="${WINGPT_CONDA:-/Users/Shared/miniforge3/bin/conda}"
NODE="${WINGPT_NODE:-$ROOT/.runtime/macos/tools/bin/node}"
COMPONENT="$ROOT/components/tooluniverse"
RUNTIME="$ROOT/.runtime/macos/tooluniverse"
PYTHON="$RUNTIME/bin/python"

[[ "$(uname -s)" == "Darwin" ]] || { echo "This installer is for macOS." >&2; exit 2; }
[[ -x "$CONDA" ]] || { echo "Missing conda: $CONDA" >&2; exit 2; }
[[ -x "$NODE" ]] || { echo "Missing project Node.js: $NODE. Run setup-macos.sh first." >&2; exit 2; }

/usr/bin/python3 "$ROOT/scripts/install-tooluniverse.py"
mkdir -p "$ROOT/.runtime/macos/conda-pkgs" "$ROOT/.runtime/macos/pip-cache"
export CONDA_PKGS_DIRS="$ROOT/.runtime/macos/conda-pkgs"
export PIP_CACHE_DIR="$ROOT/.runtime/macos/pip-cache"
export PYTHONNOUSERSITE=1
unset PYTHONHOME PYTHONPATH

if [[ ! -x "$PYTHON" ]]; then
  "$CONDA" create --yes --prefix "$RUNTIME" --override-channels --channel conda-forge python=3.12 pip
fi
"$PYTHON" -I -c 'import sys; assert sys.version_info[:2] == (3, 12), sys.version'
"$PYTHON" -m pip install --disable-pip-version-check --no-input \
  -r "$ROOT/scripts/tooluniverse-requirements.txt"
"$PYTHON" -m pip install --disable-pip-version-check --no-input --no-deps --force-reinstall "$COMPONENT"
"$PYTHON" -m pip check
"$PYTHON" -m pip freeze --all > "$ROOT/.runtime/macos/tooluniverse-pip-freeze.txt"
WINGPT_TOOLUNIVERSE_PYTHON="$PYTHON" \
WINGPT_TOOLUNIVERSE_ENTRY="$COMPONENT/src/run_stdio.py" \
  "$NODE" "$ROOT/codex-cli/bin/wingpt-tooluniverse-mcp.js" \
  --cache-schema "$COMPONENT/workflow-tool-schema.json"

echo "Installed local ToolUniverse compact MCP in isolated Python 3.12: $RUNTIME"
echo "No API key, account, remote MCP, or subscription service was configured."
