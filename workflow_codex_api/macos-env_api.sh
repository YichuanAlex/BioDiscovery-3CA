#!/bin/bash
# DeepSeek API workflow environment. Source from Bash launchers only.
WORKFLOW_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_WORKFLOW_ROOT="$(cd "$WORKFLOW_ROOT/../workflow_codex" && pwd)"
SOURCE_WORKFLOW_RUNTIME="$SOURCE_WORKFLOW_ROOT/.runtime/macos"
WORKFLOW_RUNTIME="$WORKFLOW_ROOT/.runtime_api"
DEEPSEEK_KEY_FILE="${DEEPSEEK_KEY_FILE:-$WORKFLOW_ROOT/.secrets/deepseek_api_key}"
unset PYTHONHOME
unset PYTHONPATH
if [[ -z "${DEEPSEEK_API_KEY:-}" ]]; then
  if [[ ! -f "$DEEPSEEK_KEY_FILE" ]]; then
    echo "Missing DeepSeek API credential file: $DEEPSEEK_KEY_FILE" >&2
    return 1 2>/dev/null || exit 1
  fi
  export DEEPSEEK_API_KEY="$(<"$DEEPSEEK_KEY_FILE")"
fi
if [[ ! "$DEEPSEEK_API_KEY" =~ ^sk-[A-Za-z0-9_-]{16,}$ ]]; then
  echo "DeepSeek API credential format is invalid." >&2
  return 1 2>/dev/null || exit 1
fi
export WINGPT_PYTHON="${WINGPT_PYTHON:-$SOURCE_WORKFLOW_RUNTIME/python/bin/python}"
export WINGPT_SCV_PYTHON="${WINGPT_SCV_PYTHON:-$SOURCE_WORKFLOW_RUNTIME/life-sciences/scverse/bin/python}"
export WINGPT_ALLOTROPE_PYTHON="${WINGPT_ALLOTROPE_PYTHON:-$SOURCE_WORKFLOW_RUNTIME/life-sciences/allotrope/bin/python}"
export WINGPT_NEXTFLOW_HOME="${WINGPT_NEXTFLOW_HOME:-$SOURCE_WORKFLOW_RUNTIME/life-sciences/nextflow}"
export WINGPT_JAVA_HOME="${WINGPT_JAVA_HOME:-$WINGPT_NEXTFLOW_HOME/lib/jvm}"
export WINGPT_MODEL="${WINGPT_MODEL:-deepseek-v4-pro}"
export WINGPT_API_URL="${WINGPT_API_URL:-https://api.deepseek.com}"
export WINGPT_PROVIDER=deepseek-api
export WINGPT_MODEL_CONTEXT_TOKENS="${WINGPT_MODEL_CONTEXT_TOKENS:-1000000}"
export WINGPT_CONTEXT_TOKENS="${WINGPT_CONTEXT_TOKENS:-1000000}"
export WINGPT_MAX_TOKENS="${WINGPT_MAX_TOKENS:-65536}"
export WINGPT_REASONING_EFFORT="${WINGPT_REASONING_EFFORT:-max}"
export WINGPT_API_TIMEOUT_MS="${WINGPT_API_TIMEOUT_MS:-900000}"
export WINGPT_API_USER_ID="${WINGPT_API_USER_ID:-biodiscovery_api}"
if [[ ! -x "$WINGPT_PYTHON" ]]; then
  echo "Missing shared project Python runtime: $WINGPT_PYTHON. Run workflow_codex/setup-macos.sh first." >&2
  return 1 2>/dev/null || exit 1
fi
PYTHON_BASE_BIN="$("$WINGPT_PYTHON" -I -c 'import sys; print(sys.base_prefix)')/bin"
export PATH="$WINGPT_JAVA_HOME/bin:$WINGPT_NEXTFLOW_HOME/bin:$SOURCE_WORKFLOW_RUNTIME/tools/bin:$SOURCE_WORKFLOW_RUNTIME/python/bin:$PYTHON_BASE_BIN:$PATH"
export PYTHONNOUSERSITE=1
export PYTHONUNBUFFERED=1
export PYTHONPATH="$WORKFLOW_ROOT/tools/research-quality:$WORKFLOW_ROOT/tools/tool43CA/CLI/src${PYTHONPATH:+:$PYTHONPATH}"
export CODEX_HOME="${CODEX_HOME:-$WORKFLOW_ROOT/.runtime_api/codex-home}"
export THREECA_CACHE="$SOURCE_WORKFLOW_ROOT/.threeca/cache"
export WINGPT_TOOLUNIVERSE_PYTHON="${WINGPT_TOOLUNIVERSE_PYTHON:-$SOURCE_WORKFLOW_RUNTIME/tooluniverse/bin/python}"
export WINGPT_TOOLUNIVERSE_ENTRY="${WINGPT_TOOLUNIVERSE_ENTRY:-$WORKFLOW_ROOT/components/tooluniverse/src/run_stdio.py}"
export WINGPT_TOOLUNIVERSE_CACHE="${WINGPT_TOOLUNIVERSE_CACHE:-$WORKFLOW_ROOT/components/tooluniverse/workflow-tool-schema.json}"
export MPLCONFIGDIR="$WORKFLOW_RUNTIME/matplotlib"
export NUMBA_CACHE_DIR="$WORKFLOW_RUNTIME/numba"
export XDG_CACHE_HOME="$WORKFLOW_RUNTIME/cache"
export HF_HOME="$SOURCE_WORKFLOW_RUNTIME/huggingface"
export HF_HUB_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-4}"
export NUMBA_NUM_THREADS="${NUMBA_NUM_THREADS:-4}"
mkdir -p "$MPLCONFIGDIR" "$NUMBA_CACHE_DIR" "$XDG_CACHE_HOME" "$CODEX_HOME/tasks" "$CODEX_HOME/sessions" "$WORKFLOW_RUNTIME/logs"
