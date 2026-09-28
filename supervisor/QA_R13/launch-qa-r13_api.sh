#!/bin/bash
set -euo pipefail

PROJECT_ROOT="/Users/bytedance/Downloads/BioDiscovery-3CA"
WORKFLOW_ROOT="$PROJECT_ROOT/workflow_codex_api"
SOURCE_WORKFLOW_ROOT="$PROJECT_ROOT/workflow_codex"
TASK_ROOT="$PROJECT_ROOT/3CA/QA_R13"
SUPERVISOR_ROOT="$PROJECT_ROOT/supervisor/QA_R13"
PROMPT="$SUPERVISOR_ROOT/prompt_api.txt"
CONTRACT="$SUPERVISOR_ROOT/workspace-AGENTS_api.md"
INPUT_SOURCE="$PROJECT_ROOT/3CA/QA_R10/inputs/metabolic_genes_total.csv"
EXPECTED_INPUT_SHA256="7503180d29693bd1e654ea93281db0e3ec4177ff44842c8b02f6a098402e41a9"

shopt -s nullglob dotglob
task_entries=("$TASK_ROOT"/*)
if (( ${#task_entries[@]} != 0 )); then
  echo "QA_R13 must be empty before immutable input staging." >&2
  exit 64
fi

source "$WORKFLOW_ROOT/macos-env_api.sh"
TASK_HASH="$("$WINGPT_PYTHON" -c 'import hashlib,pathlib,sys; print(hashlib.sha256(str(pathlib.Path(sys.argv[1]).resolve()).lower().encode()).hexdigest()[:24])' "$TASK_ROOT")"
if [[ -e "$CODEX_HOME/tasks/$TASK_HASH.json" ]]; then
  echo "QA_R13 API checkpoint already exists." >&2
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

export PROJECT_ROOT WORKFLOW_ROOT SOURCE_WORKFLOW_ROOT TASK_ROOT SUPERVISOR_ROOT PROMPT CONTRACT INPUT_SOURCE EXPECTED_INPUT_SHA256
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
    "codex-cli/bin/wingpt_api.js",
    "codex-cli/bin/codex_api.js",
    "scripts/macos_runtime_api.py",
    "macos-env_api.sh",
    "run-wingpt_api.sh",
    "codex-cli/bin/wingpt-http-mcp.js",
    "codex-cli/bin/wingpt-tooluniverse-mcp.js",
    "codex-cli/bin/wingpt-research.js",
    "codex-cli/bin/wingpt-threeca.js",
    "skills/anthropic-life-sciences/manifest.json",
    "components/tooluniverse/workflow-install.json",
    "components/tooluniverse/workflow-tool-schema.json",
]
manifest = {
    "round": "QA_R13",
    "started_at": now,
    "platform": platform.platform(),
    "workflow": str(workflow),
    "task": str(task),
    "supervisor": str(supervisor),
    "runner_pid": int(os.environ["RUNNER_PID"]),
    "provider": "deepseek-api",
    "model": os.environ["WINGPT_MODEL"],
    "base_url": os.environ["WINGPT_API_URL"],
    "credential_source": "protected environment file; value excluded",
    "thinking": {"type": "enabled", "reasoning_effort": os.environ["WINGPT_REASONING_EFFORT"]},
    "context": {
        "model_documented": int(os.environ["WINGPT_MODEL_CONTEXT_TOKENS"]),
        "workflow_context": int(os.environ["WINGPT_CONTEXT_TOKENS"]),
        "maximum_prompt": int(os.environ["WINGPT_CONTEXT_TOKENS"]) - int(os.environ["WINGPT_MAX_TOKENS"]),
        "generation": int(os.environ["WINGPT_MAX_TOKENS"]),
    },
    "max_rounds": 0,
    "run_until_complete": True,
    "prompt_sha256": sha(os.environ["PROMPT"]),
    "seeded_inputs": [
        provenance,
        {"staged_path": "AGENTS.md", "sha256": sha(contract), "role": "round_execution_contract"},
    ],
    "cache_policy": {
        "public_raw_cache": "shared read-only by content hash from workflow_codex/.threeca/cache",
        "api_checkpoint_and_sessions": "isolated under workflow_codex_api/.runtime_api",
        "prior_research_artifacts_reused": False,
    },
    "external_components": {
        "skills": 7,
        "anonymous_http_mcp_endpoints": 5,
        "anonymous_http_mcp_tools": 31,
        "tooluniverse_compact_tools": 5,
        "strict_research_phases_expose_external_mcp": False,
    },
    "frozen_files": [{"file": item, "sha256": sha(workflow / item)} for item in critical],
    "engineering_tests": "API syntax, API runtime unit tests, mocked DeepSeek tool-call continuity, live API status, and live main self-test passed",
    "research_gate": "both cores use staged user CSV; validate_research_bundle valid=true and complete_task required",
    "research_workspace_initially_empty_before_supplied_input": True,
    "source_policy": "immutable user CSV plus verified hash-addressed public raw cache only",
}
(supervisor / "run-manifest_api.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
PY

echo "$$" > "$SUPERVISOR_ROOT/runner_api.pid"
exec "$WORKFLOW_ROOT/run-wingpt_api.sh" \
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
