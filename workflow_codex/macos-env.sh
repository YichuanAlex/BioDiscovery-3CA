#!/bin/bash
# Source from Bash launchers; environment changes stay in the launched process.
WORKFLOW_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_RUNTIME="$WORKFLOW_ROOT/.runtime/macos"
unset PYTHONHOME
unset PYTHONPATH
export WINGPT_PYTHON="${WINGPT_PYTHON:-$WORKFLOW_RUNTIME/python/bin/python}"
export WINGPT_MODEL="${WINGPT_MODEL:-$(cd "$WORKFLOW_ROOT/.." && pwd)/model/Qwen3.5-4B-MLX-4bit}"
export WINGPT_API_URL="${WINGPT_API_URL:-http://127.0.0.1:8000/v1}"
export WINGPT_PROVIDER=local-mlx
export WINGPT_CONTEXT_TOKENS="${WINGPT_CONTEXT_TOKENS:-32768}"
export WINGPT_MAX_TOKENS="${WINGPT_MAX_TOKENS:-4096}"
if [[ ! -x "$WINGPT_PYTHON" ]]; then
  echo "Missing project Python runtime: $WINGPT_PYTHON. Run setup-macos.sh first." >&2
  return 1 2>/dev/null || exit 1
fi
PYTHON_BASE_BIN="$("$WINGPT_PYTHON" -I -c 'import sys; print(sys.base_prefix)')/bin"
export PATH="$WORKFLOW_RUNTIME/tools/bin:$WORKFLOW_RUNTIME/python/bin:$PYTHON_BASE_BIN:$PATH"
export PYTHONNOUSERSITE=1
export PYTHONUNBUFFERED=1
export PYTHONPATH="$WORKFLOW_ROOT/tools/research-quality:$WORKFLOW_ROOT/tools/tool43CA/CLI/src${PYTHONPATH:+:$PYTHONPATH}"
export CODEX_HOME="$WORKFLOW_ROOT/.runtime/codex-home"
export THREECA_CACHE="$WORKFLOW_ROOT/.threeca/cache"
export MPLCONFIGDIR="$WORKFLOW_RUNTIME/matplotlib"
export NUMBA_CACHE_DIR="$WORKFLOW_RUNTIME/numba"
export XDG_CACHE_HOME="$WORKFLOW_RUNTIME/cache"
export HF_HOME="$WORKFLOW_RUNTIME/huggingface"
export HF_HUB_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-4}"
export NUMBA_NUM_THREADS="${NUMBA_NUM_THREADS:-4}"
mkdir -p "$MPLCONFIGDIR" "$NUMBA_CACHE_DIR" "$XDG_CACHE_HOME" "$HF_HOME/hub" "$WORKFLOW_RUNTIME/logs"
