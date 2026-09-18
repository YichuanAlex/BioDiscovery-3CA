#!/bin/bash
set -euo pipefail

PROJECT_ROOT="/Users/bytedance/Downloads/BioDiscovery-3CA"
WORKFLOW_ROOT="$PROJECT_ROOT/workflow_codex"
TASK_ROOT="$PROJECT_ROOT/3CA/Q1_R19"
SUPERVISOR_ROOT="$PROJECT_ROOT/supervisor/Q1_R19"
PROMPT="$PROJECT_ROOT/supervisor/Q1_R19/prompt.txt"

shopt -s nullglob dotglob
task_entries=("$TASK_ROOT"/*)
if (( ${#task_entries[@]} != 0 )); then
  echo "R19 must start from an empty research workspace." >&2
  exit 64
fi

source "$WORKFLOW_ROOT/macos-env.sh"
TASK_HASH="$("$WINGPT_PYTHON" -c 'import hashlib, pathlib, sys; print(hashlib.sha256(str(pathlib.Path(sys.argv[1]).resolve()).lower().encode()).hexdigest()[:24])' "$TASK_ROOT")"
CHECKPOINT="$CODEX_HOME/tasks/$TASK_HASH.json"
if [[ -e "$CHECKPOINT" ]]; then
  echo "A task checkpoint already exists for R19; do not delete or reuse it." >&2
  exit 65
fi

export PROJECT_ROOT WORKFLOW_ROOT TASK_ROOT SUPERVISOR_ROOT PROMPT
"$WINGPT_PYTHON" - <<'PY'
import hashlib
import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path

supervisor = Path(os.environ["SUPERVISOR_ROOT"])
prompt = Path(os.environ["PROMPT"])
model = Path(os.environ["WINGPT_MODEL"])
payload = {
    "round": "Q1_R19",
    "started_at": datetime.now(timezone.utc).isoformat(),
    "platform": platform.platform(),
    "workflow": os.environ["WORKFLOW_ROOT"],
    "task": os.environ["TASK_ROOT"],
    "model": str(model),
    "model_config_sha256": hashlib.sha256((model / "config.json").read_bytes()).hexdigest(),
    "prompt_sha256": hashlib.sha256(prompt.read_bytes()).hexdigest(),
    "python": os.environ["WINGPT_PYTHON"],
    "api_url": os.environ["WINGPT_API_URL"],
    "context_tokens": int(os.environ["WINGPT_CONTEXT_TOKENS"]),
    "max_tokens": int(os.environ["WINGPT_MAX_TOKENS"]),
    "required_artifacts": [
        "results/core_analysis/core_result.json",
        "report/main.tex",
        "report/main.pdf",
        "results/summary.json",
        "results/analysis_manifest.json",
        "README.md",
    ],
    "research_workspace_initially_empty": True,
    "source_policy": "fresh task state; verified public raw cache only",
}
(supervisor / "run-manifest.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
PY

echo "$$" > "$SUPERVISOR_ROOT/runner.pid"
exec "$WORKFLOW_ROOT/run-wingpt.sh" \
  --workspace "$TASK_ROOT" \
  --allow-write \
  --allow-shell \
  --autonomous \
  --max-rounds 0 \
  --prompt-file "$PROMPT" \
  --require-artifact "results/core_analysis/core_result.json" \
  --require-artifact "report/main.tex" \
  --require-artifact "report/main.pdf" \
  --require-artifact "results/summary.json" \
  --require-artifact "results/analysis_manifest.json" \
  --require-artifact "README.md"
