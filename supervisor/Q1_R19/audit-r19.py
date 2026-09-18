#!/usr/bin/env python3
"""Write a read-only execution snapshot for the Mac R19 workflow."""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path("/Users/bytedance/Downloads/BioDiscovery-3CA")
WORKFLOW = PROJECT / "workflow_codex"
TASK = PROJECT / "3CA" / "Q1_R19"
SUPERVISOR = PROJECT / "supervisor" / "Q1_R19"
REQUIRED = [
    "results/core_analysis/core_result.json",
    "report/main.tex",
    "report/main.pdf",
    "results/summary.json",
    "results/analysis_manifest.json",
    "README.md",
]


def process_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


task_hash = hashlib.sha256(str(TASK.resolve()).lower().encode()).hexdigest()[:24]
checkpoint_path = WORKFLOW / ".runtime" / "codex-home" / "tasks" / f"{task_hash}.json"
checkpoint = None
checkpoint_error = None
if checkpoint_path.exists():
    try:
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        checkpoint_error = str(error)

pid_path = SUPERVISOR / "runner.pid"
runner_pid = int(pid_path.read_text().strip()) if pid_path.exists() else None
artifacts = []
for relative in REQUIRED:
    target = TASK / relative
    artifacts.append(
        {
            "file": relative,
            "present": target.is_file() and target.stat().st_size > 0,
            "bytes": target.stat().st_size if target.is_file() else None,
        }
    )

status = {
    "snapshot_at": datetime.now(timezone.utc).isoformat(),
    "round": "Q1_R19",
    "runner_pid": runner_pid,
    "runner_alive": process_alive(runner_pid),
    "checkpoint_path": str(checkpoint_path),
    "checkpoint_error": checkpoint_error,
    "checkpoint_status": checkpoint.get("status") if checkpoint else None,
    "rounds": checkpoint.get("rounds") if checkpoint else None,
    "phase": checkpoint.get("phase") if checkpoint else None,
    "next_action": checkpoint.get("next_action") if checkpoint else None,
    "required_artifacts": artifacts,
    "structural_completion_candidate": all(item["present"] for item in artifacts),
    "scientific_semantic_acceptance": "pending_independent_review",
}
(SUPERVISOR / "audit.json").write_text(
    json.dumps(status, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print(json.dumps(status, ensure_ascii=False, indent=2))
