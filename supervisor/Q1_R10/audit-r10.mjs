// Read-only supervision of research/runtime inputs; generated audit outputs stay here.
import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));
const workflow = "C:\\Users\\User\\Desktop\\agentic\\workflow_codex";
const task = "C:\\Users\\User\\Desktop\\agentic\\3CA\\Q1_R10";
const home = path.join(workflow, ".runtime", "codex-home");
const csv = value => `"${String(value ?? "").replaceAll('"', '""')}"`;
const walk = directory => !fs.existsSync(directory) ? [] : fs.readdirSync(directory, { withFileTypes: true }).flatMap(item => item.isDirectory() ? walk(path.join(directory, item.name)) : item.isFile() ? [path.join(directory, item.name)] : []);
const fileHash = file => createHash("sha256").update(fs.readFileSync(file)).digest("hex");
const jobFile = path.join(home, "tasks", `${createHash("sha256").update(task.toLowerCase()).digest("hex").slice(0, 24)}.json`);
const manifestFile = path.join(root, "run-manifest.json"), resultFile = path.join(root, "runner-result.json");
const manifest = fs.existsSync(manifestFile) ? JSON.parse(fs.readFileSync(manifestFile, "utf8").replace(/^\uFEFF/, "")) : null;
const runner = fs.existsSync(resultFile) ? JSON.parse(fs.readFileSync(resultFile, "utf8").replace(/^\uFEFF/, "")) : null;
let job = null, checkpointReadError = null;
if (fs.existsSync(jobFile)) try { job = JSON.parse(fs.readFileSync(jobFile, "utf8")); } catch (error) { checkpointReadError = error.message; }
fs.mkdirSync(path.join(root, "logs"), { recursive: true });
const sessions = [], rows = [], toolCounts = {};
let originalInputs = 0, engineContinuations = 0, reasoningPresent = 0, reasoningMissing = 0, thinkingEnabled = 0, loopBreakers = 0, loopRecoveries = 0, structuredActions = 0, structuredRequests = 0, reusedResults = 0;
// Prefer live runtime logs; retain mirrored originals if runtime sessions disappear.
const sessionFiles = new Map([...walk(path.join(root, "logs")), ...walk(path.join(home, "sessions"))].filter(file => file.endsWith(".jsonl")).map(file => [path.basename(file), file]));
for (const file of sessionFiles.values()) {
  const raw = fs.readFileSync(file, "utf8"), events = []; let partial = 0;
  for (const line of raw.trimEnd().split("\n")) try { events.push(JSON.parse(line)); } catch { partial++; }
  const metadataIndex = events.findIndex(event => event.type === "session_meta");
  if (metadataIndex < 0 || events[metadataIndex].payload.cwd !== task || (manifest?.started_at && Date.parse(events[metadataIndex].timestamp) < Date.parse(manifest.started_at))) continue;
  const mirror = path.join(root, "logs", path.basename(file));
  if (path.resolve(file).toLowerCase() !== path.resolve(mirror).toLowerCase()) fs.copyFileSync(file, mirror);
  const calls = new Map();
  for (const event of events) {
    const payload = event.payload || {}, meta = payload.workflow || {};
    if (event.type === "response_item" && payload.type === "message" && payload.role === "user") meta.synthetic ? engineContinuations++ : originalInputs++;
    if (event.type === "event_msg" && meta.event === "assistant_response") {
      if (meta.generation?.thinking_enabled) thinkingEnabled++;
      meta.reasoning_present ? reasoningPresent++ : reasoningMissing++;
    }
    if (meta.event === "tool_result_reused") reusedResults++;
    if (meta.event === "structured_action") structuredActions++;
    if (meta.event === "model_request" && meta.action_mode === "structured_json") structuredRequests++;
    if (meta.event === "loop_breaker") loopBreakers++;
    if (meta.event === "loop_recovery") loopRecoveries++;
    if (payload.type === "function_call") calls.set(payload.call_id, { timestamp: event.timestamp, name: payload.name, args: payload.arguments });
    if (payload.type === "function_call_output") {
      const call = calls.get(payload.call_id) || {};
      const failed = payload.output.startsWith("ERROR:") || /(?:^|\n)exit_code=(?!0\b)/.test(payload.output);
      const guarded = /identical tool call|limit (?:for this request|is reached)/.test(payload.output);
      toolCounts[payload.name] = (toolCounts[payload.name] || 0) + 1;
      rows.push([path.basename(file), call.timestamp, event.timestamp, payload.call_id, payload.name, failed ? "failed" : guarded ? "guarded" : "returned_not_semantically_validated", call.args, payload.output]);
      calls.delete(payload.call_id);
    }
  }
  sessions.push({ file, source_in_runtime: path.resolve(file).toLowerCase().startsWith(path.resolve(home).toLowerCase() + path.sep), bytes: Buffer.byteLength(raw), sha256: createHash("sha256").update(raw).digest("hex"), events: events.length, partial_lines: partial, noncanonical_metadata_order: metadataIndex !== 0, pending_tool_calls: [...calls.values()] });
}
const artifacts = walk(task).map(file => ({ path: path.relative(task, file), bytes: fs.statSync(file).size }));
const requiredArtifacts = ["report/main.tex", "report/main.pdf", "results/summary.json", "README.md"].map(file => ({ file, present: fs.existsSync(path.join(task, file)) && fs.statSync(path.join(task, file)).isFile() && fs.statSync(path.join(task, file)).size > 0 }));
let freeBytes = null;
try { const disk = fs.statfsSync(task); freeBytes = Number(disk.bavail) * Number(disk.bsize); } catch {}
const frozenHashMismatches = (manifest?.frozen_files || []).filter(item => !fs.existsSync(path.join(workflow, item.file)) || fileHash(path.join(workflow, item.file)) !== item.sha256);
let runnerAlive = false;
if (manifest?.runner_pid) try { process.kill(manifest.runner_pid, 0); runnerAlive = true; } catch {}
const audit = { snapshot_at: new Date().toISOString(), task, status: runner?.status === "stopped_by_user" ? "stopped_by_user" : runner?.runner_success === false ? "runner_failed" : runner?.runner_success === true ? "runner_finished" : (job?.status === "running" && !runnerAlive ? "runner_missing" : job?.status || "not_started"), runner_alive: runnerAlive, checkpoint_status: job?.status, phase: job?.phase, next_action: job?.next_action, rounds: job?.rounds, model: job?.model, model_mismatch: !!(job && manifest?.model && job.model !== manifest.model), reused_actual_results: reusedResults, asset_references: job?.asset_references || [], catalog_searches: job?.catalog_searches || 0, web_searches: job?.web_searches || 0, catalog_references: job?.catalog_references || [], discovery_cooldown: job?.discovery_cooldown || 0, last_error: job?.last_error, sessions, tools: rows.length, tool_counts: toolCounts, failed_tools: rows.filter(row => row[5] === "failed").length, guarded_tools: rows.filter(row => row[5] === "guarded").length, loop_breakers: loopBreakers, loop_recoveries: loopRecoveries, structured_actions: structuredActions, structured_requests: structuredRequests, original_user_inputs: originalInputs, supervisor_research_interventions: Math.max(0, originalInputs - 1), engine_continuations: engineContinuations, thinking_enabled_responses: thinkingEnabled, reasoning_present_responses: reasoningPresent, reasoning_missing_responses: reasoningMissing, artifacts, required_artifacts: requiredArtifacts, free_bytes: freeBytes, runner, run_until_complete: manifest?.run_until_complete === true, max_rounds: manifest?.max_rounds, frozen_hash_mismatches: frozenHashMismatches.map(item => item.file), semantic_acceptance: runner?.runner_success === false ? "not_accepted" : "pending_independent_review", supervisor_operational_restarts: manifest?.supervisor_operational_restarts || 0, checkpoint_read_error: checkpointReadError, caveat: "Tool return, exit 0 and artifact existence do not establish scientific correctness. Missing reasoning is not reconstructed. Persisted state is not process liveness." };
audit.structural_completion_candidate = runner?.runner_success === true && job?.status === "completed_candidate" && requiredArtifacts.every(item => item.present) && audit.frozen_hash_mismatches.length === 0 && !audit.model_mismatch;
fs.writeFileSync(path.join(root, "audit.json"), JSON.stringify(audit, null, 2), "utf8");
fs.writeFileSync(path.join(root, "tool-timeline.csv"), [["session", "called_at", "returned_at", "call_id", "tool", "status", "arguments", "full_output"], ...rows].map(row => row.map(csv).join(",")).join("\n"), "utf8");
console.log(JSON.stringify({ status: audit.status, runner_alive: runnerAlive, phase: audit.phase, rounds: audit.rounds, model: audit.model, model_mismatch: audit.model_mismatch, reused_actual_results: reusedResults, asset_reference_count: audit.asset_references.length, structured_actions: structuredActions, structured_requests: structuredRequests, catalog_searches: audit.catalog_searches, catalog_reference_count: audit.catalog_references.length, discovery_cooldown: audit.discovery_cooldown, tool_results: audit.tools, tool_counts: toolCounts, failed_tools: audit.failed_tools, guarded_tools: audit.guarded_tools, loop_breakers: loopBreakers, loop_recoveries: loopRecoveries, engine_continuations: audit.engine_continuations, supervisor_research_interventions: audit.supervisor_research_interventions, thinking_enabled_responses: thinkingEnabled, reasoning_present_responses: reasoningPresent, artifacts: artifacts.length, required_artifacts: requiredArtifacts, free_bytes: freeBytes, run_until_complete: audit.run_until_complete, max_rounds: audit.max_rounds, frozen_hash_mismatches: audit.frozen_hash_mismatches, structural_completion_candidate: audit.structural_completion_candidate, runner }, null, 2));
