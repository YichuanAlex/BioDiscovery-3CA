#!/bin/bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/macos-env.sh"
exec "$WINGPT_PYTHON" "$WORKFLOW_ROOT/scripts/macos_runtime.py" run "$@"
