import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const apiRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const sourceRoot = path.resolve(apiRoot, "..", "workflow_codex");
const node = path.join(sourceRoot, ".runtime", "macos", "tools", "bin", "node");
const cleanEnvironment = { ...process.env };
delete cleanEnvironment.PYTHONHOME;
delete cleanEnvironment.PYTHONPATH;

const engineSource = fs.readFileSync(path.join(apiRoot, "codex-cli", "bin", "wingpt_api.js"), "utf8");
assert.match(engineSource, /const recentLimit = recovery \? 8 : 48/);
assert.match(engineSource, /milestone\?\.phase === "report_and_manifest".*report\/main\.tex/s);
assert.match(engineSource, /milestone\?\.phase === "completion"/);
assert.match(engineSource, /verification_call_id: validEvidence\.call_id/);
assert.match(engineSource, /typeof reply\.reasoning_content === "string"/);

const adapter = spawnSync(
  node,
  [path.join(apiRoot, "codex-cli", "bin", "test-deepseek-api-adapter_api.mjs")],
  { cwd: apiRoot, env: cleanEnvironment, encoding: "utf8", timeout: 60_000 },
);
process.stdout.write(adapter.stdout || "");
process.stderr.write(adapter.stderr || "");
assert.equal(adapter.status, 0, "DeepSeek API adapter suite failed.");

console.log("PASS: isolated one-session lifecycle, bounded repair context, deterministic completion, and exact reasoning continuity.");
