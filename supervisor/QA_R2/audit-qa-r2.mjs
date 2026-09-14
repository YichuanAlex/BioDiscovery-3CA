import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));
const workflow = "C:\\Users\\User\\Desktop\\agentic\\workflow_codex";
const task = "C:\\Users\\User\\Desktop\\agentic\\3CA\\QA_R2";
const home = path.join(workflow, ".runtime", "codex-home");
const readJson = (file) => JSON.parse(fs.readFileSync(file, "utf8").replace(/^\uFEFF/, ""));
const manifestPath = path.join(root, "run-manifest.json");
const manifest = fs.existsSync(manifestPath) ? readJson(manifestPath) : null;
const jobFile = path.join(home, "tasks", createHash("sha256").update(task.toLowerCase()).digest("hex").slice(0, 24) + ".json");
let job = null;
let checkpointReadError = null;
if (fs.existsSync(jobFile)) try { job = readJson(jobFile); } catch (error) { checkpointReadError = error.message; }

let runnerProcess = null;
if (manifest?.runner_pid) {
  const command = `$p=Get-CimInstance Win32_Process -Filter "ProcessId = ${Number(manifest.runner_pid)}"; if($p){[pscustomobject]@{Name=$p.Name;ExecutablePath=$p.ExecutablePath;CommandLine=$p.CommandLine;CreationDate=$p.CreationDate.ToUniversalTime().ToString('o')} | ConvertTo-Json -Compress}`;
  const result = spawnSync("C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe", ["-NoProfile", "-Command", command], { encoding: "utf8" });
  if (result.status === 0 && result.stdout.trim()) try { runnerProcess = JSON.parse(result.stdout); } catch {}
}
const runnerIdentityMatch = Boolean(
  runnerProcess
  && String(runnerProcess.Name).toLowerCase() === "powershell.exe"
  && String(runnerProcess.ExecutablePath || "").toLowerCase().endsWith("\\windowspowershell\\v1.0\\powershell.exe")
  && String(runnerProcess.CommandLine || "").toLowerCase().includes("launch-qa-r2.ps1")
  && creationTimeMatches()
);
function creationTimeMatches() {
  const created = Date.parse(runnerProcess?.CreationDate || "");
  const started = Date.parse(manifest?.started_at || "");
  return Number.isFinite(created) && Number.isFinite(started) && created >= started - 5000;
}

const required = job?.required_artifacts || ["report/main.tex", "report/main.pdf", "results/summary.json", "results/analysis_manifest.json", "results/core_analysis/core_result.json", "results/cd8_analysis/core_result.json", "results/cd8_analysis/summary.json", "README.md"];
const artifacts = required.map((relative) => {
  const file = path.join(task, relative);
  return { path: relative, present: fs.existsSync(file) && fs.statSync(file).isFile() && fs.statSync(file).size > 0, bytes: fs.existsSync(file) && fs.statSync(file).isFile() ? fs.statSync(file).size : 0 };
});
const frozenMismatches = [];
for (const frozen of manifest?.frozen_files || []) {
  const file = path.join(workflow, frozen.file);
  const actual = fs.existsSync(file) ? createHash("sha256").update(fs.readFileSync(file)).digest("hex") : null;
  if (actual !== frozen.sha256) frozenMismatches.push({ file: frozen.file, expected: frozen.sha256, actual });
}
const toolCounts = {};
for (const message of job?.messages || []) for (const call of message.tool_calls || []) toolCounts[call.function.name] = (toolCounts[call.function.name] || 0) + 1;
let researchValidation = null;
const analysisManifest = path.join(task, "results", "analysis_manifest.json");
if (fs.existsSync(analysisManifest) && fs.existsSync(path.join(task, "report", "main.pdf"))) {
  const python = path.join(workflow, "tools", "tool43CA", ".venv", "Scripts", "python.exe");
  const cli = path.join(workflow, "tools", "research-quality", "research_quality.py");
  const validation = spawnSync(python, [cli, "--workspace", task, "validate", "results/analysis_manifest.json"], { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
  if (validation.stdout.trim()) try { researchValidation = JSON.parse(validation.stdout); } catch { researchValidation = { valid: false, errors: ["Validator returned non-JSON output"] }; }
}
const runnerResultPath = path.join(root, "runner-result.json");
const runnerResult = fs.existsSync(runnerResultPath) ? readJson(runnerResultPath) : null;
const status = runnerResult?.runner_success === true ? "runner_finished" : runnerResult?.runner_success === false ? "runner_failed" : job?.status === "running" && !runnerIdentityMatch ? "runner_missing" : job?.status || (manifest ? "starting" : "not_started");
const audit = {
  snapshot_at: new Date().toISOString(), task, status,
  runner_pid: manifest?.runner_pid, runner_process: runnerProcess, runner_identity_match: runnerIdentityMatch,
  checkpoint_status: job?.status, checkpoint_read_error: checkpointReadError, phase: job?.phase, next_action: job?.next_action, rounds: job?.rounds,
  tool_counts: toolCounts, artifacts, required_artifacts: required, research_validation: researchValidation,
  frozen_hash_mismatches: frozenMismatches,
  structural_completion_candidate: runnerResult?.runner_success === true && job?.status === "completed_candidate" && artifacts.every((item) => item.present) && researchValidation?.valid === true && frozenMismatches.length === 0,
  semantic_acceptance: "pending_independent_review",
  caveat: "PID liveness requires matching executable, command line, and creation time. Structural completion does not establish biological validity."
};
fs.writeFileSync(path.join(root, "audit.json"), JSON.stringify(audit, null, 2), "utf8");
console.log(JSON.stringify(audit, null, 2));
