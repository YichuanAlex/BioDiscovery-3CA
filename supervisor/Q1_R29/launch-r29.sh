#!/bin/bash
set -euo pipefail
PROJECT_ROOT="/Users/bytedance/Downloads/BioDiscovery-3CA"
WORKFLOW_ROOT="$PROJECT_ROOT/workflow_codex"
TASK_ROOT="$PROJECT_ROOT/3CA/Q1_R29"
SUPERVISOR_ROOT="$PROJECT_ROOT/supervisor/Q1_R29"
PROMPT="$SUPERVISOR_ROOT/prompt.txt"
shopt -s nullglob dotglob
task_entries=("$TASK_ROOT"/*)
if (( ${#task_entries[@]} != 0 )); then echo "R29 must start empty." >&2; exit 64; fi
source "$WORKFLOW_ROOT/macos-env.sh"
TASK_HASH="$("$WINGPT_PYTHON" -c 'import hashlib,pathlib,sys; print(hashlib.sha256(str(pathlib.Path(sys.argv[1]).resolve()).lower().encode()).hexdigest()[:24])' "$TASK_ROOT")"
if [[ -e "$CODEX_HOME/tasks/$TASK_HASH.json" ]]; then echo "R29 checkpoint already exists." >&2; exit 65; fi
export TASK_ROOT SUPERVISOR_ROOT PROMPT
"$WINGPT_PYTHON" - <<'PY'
import hashlib,json,os,platform
from datetime import datetime,timezone
from pathlib import Path
s=Path(os.environ["SUPERVISOR_ROOT"]); p=Path(os.environ["PROMPT"]); m=Path(os.environ["WINGPT_MODEL"])
d={"round":"Q1_R29","started_at":datetime.now(timezone.utc).isoformat(),"platform":platform.platform(),"task":os.environ["TASK_ROOT"],"model":str(m),"model_config_sha256":hashlib.sha256((m/"config.json").read_bytes()).hexdigest(),"prompt_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"context_tokens":int(os.environ["WINGPT_CONTEXT_TOKENS"]),"max_tokens":int(os.environ["WINGPT_MAX_TOKENS"]),"research_workspace_initially_empty":True,"source_policy":"fresh task state; verified public raw cache only"}
(s/"run-manifest.json").write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
PY
echo "$$" > "$SUPERVISOR_ROOT/runner.pid"
exec "$WORKFLOW_ROOT/run-wingpt.sh" --workspace "$TASK_ROOT" --allow-write --allow-shell --autonomous --max-rounds 0 --prompt-file "$PROMPT" \
  --require-artifact "results/core_analysis/core_result.json" --require-artifact "report/main.tex" --require-artifact "report/main.pdf" \
  --require-artifact "results/summary.json" --require-artifact "results/analysis_manifest.json" --require-artifact "README.md"
