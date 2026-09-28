#!/bin/bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/macos-env_api.sh"
exec "$WINGPT_PYTHON" "$WORKFLOW_ROOT/scripts/macos_runtime_api.py" run "$@"
