"""Archive and classify every observable local-workflow event for Q1."""
import csv
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path

SUP = Path(__file__).resolve().parent
SESSION_ROOT = Path(r"C:\Users\User\Desktop\agentic\workflow_codex\.runtime\codex-home\sessions")
TASK = r"C:\Users\User\Desktop\agentic\3CA\Q1"
ARCHIVE = SUP / "logs"
ARCHIVE.mkdir(exist_ok=True)
SOURCES = SUP / "sources"
SOURCES.mkdir(exist_ok=True)
rows, sessions = [], []
for source in sorted(SESSION_ROOT.rglob("*.jsonl")):
    events = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not events or events[0].get("payload", {}).get("cwd", "").lower() != TASK.lower():
        continue
    shutil.copy2(source, ARCHIVE / source.name)
    counts = Counter(e["payload"].get("workflow", {}).get("event") for e in events)
    pending = {}
    for event in events:
        w = event["payload"].get("workflow", {})
        if w.get("event") == "tool_call":
            pending[w["call_id"]] = (event["timestamp"], w)
        elif w.get("event") == "tool_result":
            start, call = pending.pop(w["call_id"], ("", {}))
            result = str(w.get("result", ""))
            status = "returned_unvalidated"
            if result.startswith("ERROR:") or ("exit_code=" in result and not result.rstrip().endswith("exit_code=0")):
                status = "failed"
            elif "identical tool call" in result or "limit for this request" in result:
                status = "loop_guard"
            elif "Cookies must be enabled" in result and len(result) < 1500:
                status = "unusable_source_challenge"
            elif result.rstrip().endswith("exit_code=0"):
                status = "command_exit_0_not_semantic_proof"
            if w.get("name") in ("read_webpage", "get_page", "get_study"):
                (SOURCES / (w["call_id"] + ".txt")).write_text(result, encoding="utf-8")
            rows.append({"session": source.name, "started_at": start, "returned_at": event["timestamp"],
                         "turn_id": w.get("turn_id"), "round": w.get("round"), "tool": w.get("name"),
                         "status": status, "arguments": json.dumps(call.get("arguments", {}), ensure_ascii=False),
                         "result_excerpt": result[:700]})
    sessions.append({"file": source.name, "bytes": source.stat().st_size,
                     "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                     "events": len(events), "workflow_event_counts": dict(counts),
                     "pending_tools_at_snapshot": len(pending)})
with (SUP / "tool-timeline.csv").open("w", newline="", encoding="utf-8-sig") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else ["session"])
    writer.writeheader()
    writer.writerows(rows)
record = {"scope": "Every saved observable workflow event; private internal reasoning is not inferred or reconstructed",
          "snapshot_note": "Active sessions may be incomplete; rerun this audit after final exit",
          "sessions": sessions, "tool_count": len(rows), "tool_status_counts": dict(Counter(r["status"] for r in rows))}
(SUP / "session-audit.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
print("ARCHIVED:", len(sessions), "Q1 sessions; classified", len(rows), "tool results.")
