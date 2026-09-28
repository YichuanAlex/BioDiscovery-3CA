#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
NODE="${WINGPT_NODE:-$ROOT/.runtime/macos/tools/bin/node}"
PYTHON="$ROOT/.runtime/macos/tooluniverse/bin/python"

[[ -x "$NODE" ]] || { echo "Missing project Node.js: $NODE" >&2; exit 2; }
[[ -x "$PYTHON" ]] || { echo "Missing ToolUniverse Python: $PYTHON" >&2; exit 2; }
"$PYTHON" -I -c 'import sys, tooluniverse; assert sys.version_info[:2] == (3, 12); print("ToolUniverse Python 3.12 import: OK")'
"$NODE" --check "$ROOT/codex-cli/bin/wingpt-tooluniverse-mcp.js"
"$NODE" "$ROOT/codex-cli/bin/test-tooluniverse-mcp.mjs" --all
echo "ToolUniverse local compact MCP smoke tests: PASS"
