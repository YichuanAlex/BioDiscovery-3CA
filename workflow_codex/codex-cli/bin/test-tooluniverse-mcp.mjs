#!/usr/bin/env node
"use strict";

import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";
import { once } from "node:events";
import { fileURLToPath } from "node:url";
import readline from "node:readline";
import { setTimeout as delay } from "node:timers/promises";
import {
  ToolUniverseStdioClient,
  cacheToolUniverseSchemas,
  createToolUniverseMcpTools,
} from "./wingpt-tooluniverse-mcp.js";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const mockEntry = path.join(root, "scripts", "mock-tooluniverse-mcp.py");
const actualEntry = path.join(root, "components", "tooluniverse", "src", "run_stdio.py");
const actualPython = path.join(root, ".runtime", "macos", "tooluniverse", "bin", "python");
const actualCache = path.join(root, "components", "tooluniverse", "workflow-tool-schema.json");
const expectedNames = [
  "tooluniverse__list_tools",
  "tooluniverse__grep_tools",
  "tooluniverse__get_tool_info",
  "tooluniverse__execute_tool",
  "tooluniverse__find_tools",
].sort();

async function mockSmoke() {
  const fixture = fs.mkdtempSync(path.join(os.tmpdir(), "tooluniverse-cache-"));
  const cachePath = path.join(fixture, "compact-schema.json");
  const startLog = path.join(fixture, "starts.log");
  const previousStartLog = process.env.WINGPT_TOOLUNIVERSE_MOCK_START_LOG;
  process.env.WINGPT_TOOLUNIVERSE_MOCK_START_LOG = startLog;
  try {
    const cache = await cacheToolUniverseSchemas(cachePath, {
      python: "/usr/bin/python3",
      entry: mockEntry,
      timeoutMs: 1000,
    });
    assert.equal(cache.tool_count, 5);
    assert.match(cache.tools_sha256, /^[a-f0-9]{64}$/);
    assert.equal(fs.readFileSync(startLog, "utf8").trim().split("\n").length, 1);

    const bridge = createToolUniverseMcpTools(
      (name, description, properties, required) => ({ function: { name, description, parameters: { properties, required } } }),
      { python: "/usr/bin/python3", entry: mockEntry, timeoutMs: 1000, cachePath },
    );
    assert.deepEqual(bridge.definitions.map((tool) => tool.function.name).sort(), expectedNames);
    assert.equal(bridge.client.child, null, "Reading cached schemas must not start stdio.");
    assert.equal(fs.readFileSync(startLog, "utf8").trim().split("\n").length, 1);
    const lazyResult = await bridge.execute("tooluniverse__list_tools", { mode: "ordinary" });
    assert.match(lazyResult, /"name": "list_tools"/);
    const lazyPid = bridge.client.child.pid;
    assert.equal(fs.readFileSync(startLog, "utf8").trim().split("\n").length, 2);
    await bridge.close();
    assert.throws(() => process.kill(lazyPid, 0));

    const tampered = JSON.parse(fs.readFileSync(cachePath, "utf8"));
    tampered.tools[0].description = "tampered";
    fs.writeFileSync(cachePath, JSON.stringify(tampered));
    assert.throws(
      () => createToolUniverseMcpTools(() => ({}), { cachePath }),
      /cache failed validation/,
    );
  } finally {
    if (previousStartLog === undefined) delete process.env.WINGPT_TOOLUNIVERSE_MOCK_START_LOG;
    else process.env.WINGPT_TOOLUNIVERSE_MOCK_START_LOG = previousStartLog;
    fs.rmSync(fixture, { recursive: true, force: true });
  }

  const client = new ToolUniverseStdioClient({
    python: "/usr/bin/python3",
    entry: mockEntry,
    timeoutMs: 1000,
  });
  const tools = await client.listTools();
  assert.deepEqual(tools.map((tool) => tool.name).sort(), expectedNames);
  assert.equal(tools.some((tool) => tool.name.endsWith("not_compact")), false);

  const ordinary = await client.call("tooluniverse__list_tools", { mode: "ordinary" });
  assert.match(ordinary.content[0].text, /"name": "list_tools"/);
  const environment = await client.call("tooluniverse__list_tools", { mode: "environment" });
  assert.deepEqual(JSON.parse(environment.content[0].text), { leaked: [] });
  const large = await client.call("tooluniverse__execute_tool", { mode: "large" });
  assert.ok(Buffer.byteLength(JSON.stringify(large)) <= 16 * 1024);
  assert.match(large.content[0].text, /TRUNCATED/);
  await assert.rejects(client.call("tooluniverse__not_compact", {}), /not approved/);
  await client.stop();

  const timeoutClient = new ToolUniverseStdioClient({
    python: "/usr/bin/python3",
    entry: mockEntry,
    timeoutMs: 1000,
  });
  await timeoutClient.listTools();
  const childPid = timeoutClient.child.pid;
  await assert.rejects(timeoutClient.call("tooluniverse__execute_tool", { mode: "hang" }), /timed out/);
  await delay(200);
  assert.throws(() => process.kill(childPid, 0));
  console.log("ToolUniverse adapter mock smoke: PASS");
}

async function proxyMockSmoke() {
  const fixture = fs.mkdtempSync(path.join(os.tmpdir(), "tooluniverse-proxy-cache-"));
  const cachePath = path.join(fixture, "compact-schema.json");
  await cacheToolUniverseSchemas(cachePath, {
    python: "/usr/bin/python3",
    entry: mockEntry,
    timeoutMs: 1000,
  });
  const node = process.execPath;
  const adapter = path.join(root, "codex-cli", "bin", "wingpt-tooluniverse-mcp.js");
  const child = spawn(node, [adapter], {
    env: {
      ...process.env,
      WINGPT_TOOLUNIVERSE_PYTHON: "/usr/bin/python3",
      WINGPT_TOOLUNIVERSE_ENTRY: mockEntry,
      WINGPT_TOOLUNIVERSE_TIMEOUT_MS: "1000",
      WINGPT_TOOLUNIVERSE_CACHE: cachePath,
    },
    stdio: ["pipe", "pipe", "pipe"],
  });
  const pending = new Map();
  const lines = readline.createInterface({ input: child.stdout, crlfDelay: Infinity });
  lines.on("line", (line) => {
    const message = JSON.parse(line);
    pending.get(message.id)?.(message);
    pending.delete(message.id);
  });
  const request = (id, method, params = {}) => new Promise((resolve) => {
    pending.set(id, resolve);
    child.stdin.write(`${JSON.stringify({ jsonrpc: "2.0", id, method, params })}\n`);
  });
  const initialized = await request(1, "initialize");
  assert.equal(initialized.result.serverInfo.name, "workflow-codex-tooluniverse");
  const listed = await request(2, "tools/list");
  assert.deepEqual(listed.result.tools.map((tool) => tool.name).sort(), expectedNames);
  const called = await request(3, "tools/call", {
    name: "tooluniverse__list_tools",
    arguments: { mode: "ordinary" },
  });
  assert.match(called.result.content[0].text, /"name": "list_tools"/);
  child.stdin.end();
  await Promise.race([
    once(child, "exit"),
    delay(3000).then(() => {
      child.kill("SIGKILL");
      throw new Error("stdio proxy did not clean up after stdin closed.");
    }),
  ]);
  assert.equal(child.exitCode, 0);
  fs.rmSync(fixture, { recursive: true, force: true });
  console.log("ToolUniverse stdio proxy mock smoke: PASS");
}

async function actualSmoke() {
  const client = new ToolUniverseStdioClient({
    python: actualPython,
    entry: actualEntry,
    cachePath: actualCache,
    timeoutMs: Number(process.env.WINGPT_TOOLUNIVERSE_SMOKE_TIMEOUT_MS || "120000"),
  });
  try {
    const tools = await client.listTools();
    assert.deepEqual(tools.map((tool) => tool.name).sort(), expectedNames);
    assert.ok(Buffer.byteLength(JSON.stringify({ tools })) <= 16 * 1024);
    const result = await client.call("tooluniverse__list_tools", { mode: "names", limit: 1 });
    assert.ok(Buffer.byteLength(JSON.stringify(result)) <= 16 * 1024);
    assert.notEqual(result.isError, true);
    console.log("ToolUniverse adapter actual smoke: PASS");
  } finally {
    await client.stop();
  }
}

const mode = process.argv[2] || "--all";
if (!["--mock", "--actual", "--all"].includes(mode)) {
  throw new Error("Usage: test-tooluniverse-mcp.mjs [--mock|--actual|--all]");
}
if (mode !== "--actual") {
  await mockSmoke();
  await proxyMockSmoke();
}
if (mode !== "--mock") await actualSmoke();
