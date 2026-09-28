#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
NODE="${WINGPT_NODE:-$ROOT/.runtime/macos/tools/bin/node}"
test -x "$NODE" || { echo "Project-local Node runtime is missing: $NODE" >&2; exit 1; }
exec "$NODE" "$ROOT/scripts/uninstall-anonymous-http-mcp.mjs"
