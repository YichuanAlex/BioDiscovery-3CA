import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const fixture = fs.mkdtempSync(path.join(os.tmpdir(), 'Qwen3.5-4B-r7-audit-'));
try {
  const workflow = path.join(fixture, 'workflow'), task = path.join(fixture, 'task');
  const sessions = path.join(workflow, '.runtime', 'codex-home', 'sessions');
  fs.mkdirSync(sessions, { recursive: true }); fs.mkdirSync(task);
  const source = fs.readFileSync(new URL('./audit-r7.mjs', import.meta.url), 'utf8');
  fs.writeFileSync(path.join(fixture, 'audit-r7.mjs'), source.replace(/^const workflow = .*;$/m, `const workflow = ${JSON.stringify(workflow)};`).replace(/^const task = .*;$/m, `const task = ${JSON.stringify(task)};`));
  fs.writeFileSync(path.join(fixture, 'run-manifest.json'), JSON.stringify({ started_at: '2026-01-01T00:00:00Z', runner_pid: process.pid }));
  const session = path.join(sessions, 'rollout-test.jsonl');
  fs.writeFileSync(session, JSON.stringify({ timestamp: '2026-01-02T00:00:00Z', type: 'session_meta', payload: { cwd: task } }) + '\n');
  const run = () => { const result = spawnSync(process.execPath, [path.join(fixture, 'audit-r7.mjs')], { encoding: 'utf8' }); assert.equal(result.status, 0, result.stderr); return JSON.parse(fs.readFileSync(path.join(fixture, 'audit.json'), 'utf8')); };
  const live = run(); assert.equal(live.sessions.length, 1); assert.equal(live.sessions[0].source_in_runtime, true);
  fs.unlinkSync(session);
  const mirrored = run(); assert.equal(mirrored.sessions.length, 1); assert.equal(mirrored.sessions[0].source_in_runtime, false); assert.equal(mirrored.sessions[0].sha256, live.sessions[0].sha256); assert.equal(mirrored.structural_completion_candidate, false);
  console.log('PASS: R7 audit reads mirrored original logs after runtime disappearance without losing or double-counting the session.');
} finally { fs.rmSync(fixture, { recursive: true, force: true }); }
