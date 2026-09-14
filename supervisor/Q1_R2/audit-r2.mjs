// Read-only supervision of research files; generated audit outputs stay in this supervisor directory.
import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));
const task = "C:\\Users\\User\\Desktop\\agentic\\3CA\\Q1_R2";
const home = "C:\\Users\\User\\Desktop\\agentic\\workflow_codex\\.runtime\\codex-home";
const csv = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
const jobFile = path.join(home, "tasks", `${createHash("sha256").update(task.toLowerCase()).digest("hex").slice(0,24)}.json`);
let job = null, checkpointReadError = null;
if (fs.existsSync(jobFile)) {
  try { job = JSON.parse(fs.readFileSync(jobFile,"utf8")); }
  catch(error) { checkpointReadError = error.message; }
}
const sessions = [], rows = [];
let originalInputs = 0, engineContinuations = 0, reasoningResponses = 0, missingReasoning = 0;
fs.mkdirSync(path.join(root, "logs"), { recursive: true });
const walk = (directory) => !fs.existsSync(directory) ? [] : fs.readdirSync(directory, { withFileTypes: true }).flatMap(item => item.isDirectory() ? walk(path.join(directory, item.name)) : item.isFile() ? [path.join(directory, item.name)] : []);
for (const file of walk(path.join(home, "sessions")).filter(file => file.endsWith(".jsonl"))) {
  const raw = fs.readFileSync(file, "utf8"), lines = raw.trimEnd().split("\n");
  const events = []; let partial = 0;
  for (const line of lines) { try { events.push(JSON.parse(line)); } catch { partial++; } }
  const metadataIndex = events.findIndex(event => event.type === "session_meta");
  if (metadataIndex < 0 || events[metadataIndex].payload.cwd !== task) continue;
  fs.copyFileSync(file, path.join(root, "logs", path.basename(file)));
  const calls = new Map();
  for (const event of events) {
    const payload = event.payload, meta = payload.workflow || {};
    if (event.type === "response_item" && payload.type === "message" && payload.role === "user") {
      if (meta.synthetic) engineContinuations++; else originalInputs++;
    }
    if (meta.event === "model_response") {
      const reply = meta.raw_response?.choices?.[0]?.message || {};
      if ([reply.reasoning, reply.reasoning_content, reply.reasoning_details].some(value => value != null && value !== "")) reasoningResponses++; else missingReasoning++;
    }
    if (payload.type === "function_call") calls.set(payload.call_id, { timestamp: event.timestamp, name: payload.name, args: payload.arguments });
    if (payload.type === "function_call_output") {
      const call = calls.get(payload.call_id) || {};
      const failed = payload.output.startsWith("ERROR:") || /(?:^|\n)exit_code=(?!0\b)/.test(payload.output);
      rows.push([path.basename(file), call.timestamp, event.timestamp, payload.call_id, payload.name, failed ? "failed" : /identical tool call|limit for this request/.test(payload.output) ? "guarded" : "returned_not_semantically_validated", call.args, payload.output]);
      calls.delete(payload.call_id);
    }
  }
  sessions.push({ file, bytes: Buffer.byteLength(raw), sha256: createHash("sha256").update(raw).digest("hex"), events: events.length, partial_lines: partial, noncanonical_metadata_order: metadataIndex !== 0, pending_tool_calls: [...calls.values()] });
}
const artifacts = walk(task).map(file => ({ path: path.relative(task, file), bytes: fs.statSync(file).size }));
const latestManifestPath = fs.readdirSync(root).filter(name => /^run-manifest.*\.json$/.test(name)).map(name => path.join(root, name)).sort((a,b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs)[0];
const manifest = latestManifestPath ? JSON.parse(fs.readFileSync(latestManifestPath, "utf8").replace(/^\uFEFF/, "")) : null;
const attempt = manifest?.attempt || 1;
const resultFile = path.join(root, attempt === 1 ? "runner-result.json" : `runner-result-attempt${attempt}.json`);
const runner = fs.existsSync(resultFile) ? JSON.parse(fs.readFileSync(resultFile, "utf8").replace(/^\uFEFF/, "")) : null;
const audit = { snapshot_at: new Date().toISOString(), task, status: runner?.runner_success === false ? "runner_failed" : job?.status || "not_started", checkpoint_status: job?.status, phase: job?.phase, next_action: job?.next_action, rounds: job?.rounds, last_error: job?.last_error, sessions, tools: rows.length, failed_tools: rows.filter(row => row[5] === "failed").length, original_user_inputs: originalInputs, supervisor_research_interventions: Math.max(0, originalInputs - 1), engine_continuations: engineContinuations, reasoning_responses: reasoningResponses, responses_without_returned_reasoning: missingReasoning, artifacts, runner, semantic_acceptance: runner?.runner_success === false ? "not_accepted" : "pending_independent_review", caveat: "Tool return, exit 0 and artifact existence do not establish scientific correctness. Missing reasoning is not reconstructed. Persisted running status is not liveness; runner failure overrides a stale checkpoint." };
audit.attempt = attempt;
audit.supervisor_operational_restarts = manifest?.supervisor_operational_restarts || 0;
audit.checkpoint_read_error = checkpointReadError;
if (!runner && checkpointReadError) audit.status = "checkpoint_unreadable";
fs.writeFileSync(path.join(root, "audit.json"), JSON.stringify(audit, null, 2), "utf8");
fs.writeFileSync(path.join(root, "tool-timeline.csv"), [["session", "called_at", "returned_at", "call_id", "tool", "status", "arguments", "full_output"], ...rows].map(row => row.map(csv).join(",")).join("\n"), "utf8");
console.log(JSON.stringify({ status: audit.status, phase: audit.phase, rounds: audit.rounds, tool_results: audit.tools, failed_tools: audit.failed_tools, engine_continuations: engineContinuations, supervisor_research_interventions: audit.supervisor_research_interventions, reasoning_responses: reasoningResponses, artifacts: artifacts.length, runner }, null, 2));
