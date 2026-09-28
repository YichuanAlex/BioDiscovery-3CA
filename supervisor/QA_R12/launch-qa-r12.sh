#!/bin/bash
set -euo pipefail

PROJECT_ROOT="/Users/bytedance/Downloads/BioDiscovery-3CA"
WORKFLOW_ROOT="$PROJECT_ROOT/workflow_codex"
TASK_ROOT="$PROJECT_ROOT/3CA/QA_R12"
SUPERVISOR_ROOT="$PROJECT_ROOT/supervisor/QA_R12"
PROMPT="$SUPERVISOR_ROOT/prompt.txt"
CONTRACT="$SUPERVISOR_ROOT/workspace-AGENTS.md"
INPUT_SOURCE="$PROJECT_ROOT/3CA/QA_R10/inputs/metabolic_genes_total.csv"
EXPECTED_INPUT_SHA256="7503180d29693bd1e654ea93281db0e3ec4177ff44842c8b02f6a098402e41a9"

shopt -s nullglob dotglob
task_entries=("$TASK_ROOT"/*)
if (( ${#task_entries[@]} != 0 )); then
  echo "QA_R12 must be empty before immutable input staging." >&2
  exit 64
fi

source "$WORKFLOW_ROOT/macos-env.sh"
TASK_HASH="$("$WINGPT_PYTHON" -c 'import hashlib,pathlib,sys; print(hashlib.sha256(str(pathlib.Path(sys.argv[1]).resolve()).lower().encode()).hexdigest()[:24])' "$TASK_ROOT")"
if [[ -e "$CODEX_HOME/tasks/$TASK_HASH.json" ]]; then
  echo "QA_R12 checkpoint already exists." >&2
  exit 65
fi

actual_input_hash="$("$WINGPT_PYTHON" -c 'import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' "$INPUT_SOURCE")"
if [[ "$actual_input_hash" != "$EXPECTED_INPUT_SHA256" ]]; then
  echo "Immutable user input hash mismatch." >&2
  exit 66
fi

mkdir -p "$TASK_ROOT/inputs"
cp "$INPUT_SOURCE" "$TASK_ROOT/inputs/metabolic_genes_total.csv"
cp "$CONTRACT" "$TASK_ROOT/AGENTS.md"
staged_hash="$("$WINGPT_PYTHON" -c 'import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' "$TASK_ROOT/inputs/metabolic_genes_total.csv")"
[[ "$staged_hash" == "$EXPECTED_INPUT_SHA256" ]] || { echo "Staged input hash mismatch." >&2; exit 67; }

export PROJECT_ROOT WORKFLOW_ROOT TASK_ROOT SUPERVISOR_ROOT PROMPT CONTRACT INPUT_SOURCE EXPECTED_INPUT_SHA256
export RUNNER_PID="$$"
"$WINGPT_PYTHON" - <<'PY'
import hashlib
import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path

workflow = Path(os.environ["WORKFLOW_ROOT"])
task = Path(os.environ["TASK_ROOT"])
supervisor = Path(os.environ["SUPERVISOR_ROOT"])
model = Path(os.environ["WINGPT_MODEL"])
staged = task / "inputs" / "metabolic_genes_total.csv"
contract = task / "AGENTS.md"
now = datetime.now(timezone.utc).isoformat()

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

provenance = {
    "source_path": "3CA/QA_R10/inputs/metabolic_genes_total.csv",
    "source_role": "immutable_user_supplied_input_only; no prior analysis artifact reused",
    "staged_path": "inputs/metabolic_genes_total.csv",
    "staged_at": now,
    "sha256": sha(staged),
    "bytes": staged.stat().st_size,
    "role": "immutable_user_supplied_gene_set",
}
(task / "inputs" / "input-provenance.json").write_text(
    json.dumps(provenance, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

critical = [
    "codex-cli/bin/wingpt.js",
    "codex-cli/bin/wingpt-http-mcp.js",
    "codex-cli/bin/wingpt-tooluniverse-mcp.js",
    "codex-cli/bin/wingpt-research.js",
    "codex-cli/bin/wingpt-threeca.js",
    "scripts/macos_runtime.py",
    "skills/anthropic-life-sciences/manifest.json",
    ".runtime/anonymous-http-mcp/manifest.json",
    "components/tooluniverse/workflow-install.json",
    "components/tooluniverse/workflow-tool-schema.json",
    "macos-context-profile.json",
]
manifest = {
    "round": "QA_R12",
    "started_at": now,
    "platform": platform.platform(),
    "workflow": str(workflow),
    "task": str(task),
    "supervisor": str(supervisor),
    "runner_pid": int(os.environ["RUNNER_PID"]),
    "model": str(model),
    "model_config_sha256": sha(model / "config.json"),
    "context": {
        "model_native": 262144,
        "production_context": int(os.environ["WINGPT_CONTEXT_TOKENS"]),
        "maximum_prompt": int(os.environ["WINGPT_CONTEXT_TOKENS"]) - int(os.environ["WINGPT_MAX_TOKENS"]),
        "generation": int(os.environ["WINGPT_MAX_TOKENS"]),
        "profile": "workflow_codex/macos-context-profile.json",
    },
    "max_rounds": 0,
    "run_until_complete": True,
    "prompt_sha256": sha(os.environ["PROMPT"]),
    "seeded_inputs": [
        provenance,
        {"staged_path": "AGENTS.md", "sha256": sha(contract), "role": "round_execution_contract"},
    ],
    "external_components": {
        "skills": 7,
        "anonymous_http_mcp_endpoints": 5,
        "anonymous_http_mcp_tools": 31,
        "tooluniverse_compact_tools": 5,
        "strict_research_phases_expose_external_mcp": False,
        "authenticated_or_subscription_components": 0,
    },
    "frozen_files": [{"file": item, "sha256": sha(workflow / item)} for item in critical],
    "engineering_tests": "JS recovery, macOS runtime, research quality, main self-test, anonymous MCP, ToolUniverse, and life-sciences smoke passed",
    "research_gate": "both cores use staged user CSV; validate_research_bundle valid=true and complete_task required",
    "research_workspace_initially_empty_before_supplied_input": True,
    "source_policy": "immutable user CSV plus verified hash-addressed public raw cache only",
}
(supervisor / "run-manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
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
  --require-artifact "report/main.tex" \
  --require-artifact "report/main.pdf" \
  --require-artifact "results/summary.json" \
  --require-artifact "results/analysis_manifest.json" \
  --require-artifact "results/core_analysis/core_result.json" \
  --require-artifact "results/cd8_analysis/core_result.json" \
  --require-artifact "results/cd8_analysis/summary.json" \
  --require-artifact "README.md"
