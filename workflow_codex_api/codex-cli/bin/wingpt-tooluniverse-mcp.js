#!/usr/bin/env node
"use strict";

import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { once } from "node:events";
import { fileURLToPath } from "node:url";
import readline from "node:readline";

const PREFIX = "tooluniverse__";
const ALLOWED = new Set(["list_tools", "grep_tools", "get_tool_info", "execute_tool", "find_tools"]);
const PROTOCOL_VERSION = "2025-06-18";
const MAX_MESSAGE_BYTES = 16 * 1024;
const DEFAULT_TIMEOUT_MS = 45_000;
const modulePath = fileURLToPath(import.meta.url);
const workflowRoot = path.resolve(path.dirname(modulePath), "..", "..");
const defaultPython = path.join(workflowRoot, ".runtime", "macos", "tooluniverse", "bin", "python");
const defaultEntry = path.join(workflowRoot, "components", "tooluniverse", "src", "run_stdio.py");
const defaultCache = path.join(workflowRoot, "components", "tooluniverse", "workflow-tool-schema.json");
const forbiddenEnvironment = /(?:API_KEY|ACCESS_TOKEN|AUTHORIZATION|BEARER|CREDENTIAL|SECRET|PASSWORD|SUBSCRIPTION|ACCOUNT)/i;

function canonicalJson(value) {
  if (Array.isArray(value)) return value.map(canonicalJson);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, canonicalJson(value[key])]));
  }
  return value;
}

function schemaDigest(tools) {
  return createHash("sha256").update(JSON.stringify(canonicalJson(tools))).digest("hex");
}

function boundedText(value, limit = MAX_MESSAGE_BYTES) {
  const text = typeof value === "string" ? value : JSON.stringify(value);
  const bytes = Buffer.from(text, "utf8");
  if (bytes.length <= limit) return text;
  const marker = Buffer.from(`\n...[TOOLUNIVERSE OUTPUT TRUNCATED: ${bytes.length} bytes total]...\n`);
  const side = Math.max(0, Math.floor((limit - marker.length - 8) / 2));
  return Buffer.concat([bytes.subarray(0, side), marker, bytes.subarray(bytes.length - side)]).toString("utf8");
}

function cleanEnvironment(python, componentRoot, isolatedHome) {
  const environment = {};
  for (const [key, value] of Object.entries(process.env)) {
    if (value !== undefined && !forbiddenEnvironment.test(key)) environment[key] = value;
  }
  delete environment.PYTHONHOME;
  delete environment.PYTHONPATH;
  return {
    ...environment,
    HOME: isolatedHome,
    XDG_CONFIG_HOME: path.join(isolatedHome, ".config"),
    XDG_CACHE_HOME: path.join(isolatedHome, ".cache"),
    PATH: `${path.dirname(python)}:${environment.PATH || "/usr/bin:/bin"}`,
    PYTHONNOUSERSITE: "1",
    PYTHONIOENCODING: "utf-8",
    TOOLUNIVERSE_STDIO_MODE: "1",
    TOOLUNIVERSE_COMPACT_MODE: "1",
    TOOLUNIVERSE_COMPONENT_ROOT: componentRoot,
  };
}

function normalizeSchema(schema) {
  if (!schema || typeof schema !== "object" || Array.isArray(schema)) {
    return { type: "object", properties: {}, additionalProperties: false };
  }
  return {
    ...schema,
    type: "object",
    properties: schema.properties && typeof schema.properties === "object" ? schema.properties : {},
  };
}

function boundToolResult(result) {
  if (!result || typeof result !== "object") return result;
  const bounded = { ...result };
  if (Array.isArray(bounded.content)) {
    bounded.content = bounded.content.map((item) => item?.type === "text"
      ? { ...item, text: boundedText(item.text, MAX_MESSAGE_BYTES - 1024) }
      : item);
  }
  let encoded = Buffer.byteLength(JSON.stringify(bounded));
  if (encoded <= MAX_MESSAGE_BYTES) return bounded;
  bounded.content = [{
    type: "text",
    text: boundedText(JSON.stringify(result), MAX_MESSAGE_BYTES - 1024),
  }];
  delete bounded.structuredContent;
  encoded = Buffer.byteLength(JSON.stringify(bounded));
  if (encoded > MAX_MESSAGE_BYTES) {
    bounded.content[0].text = boundedText(bounded.content[0].text, MAX_MESSAGE_BYTES - 2048);
  }
  return bounded;
}

export class ToolUniverseStdioClient {
  constructor(options = {}) {
    this.python = options.python || process.env.WINGPT_TOOLUNIVERSE_PYTHON || defaultPython;
    this.entry = options.entry || process.env.WINGPT_TOOLUNIVERSE_ENTRY || defaultEntry;
    this.timeoutMs = Number(options.timeoutMs || process.env.WINGPT_TOOLUNIVERSE_TIMEOUT_MS || DEFAULT_TIMEOUT_MS);
    this.child = null;
    this.nextId = 1;
    this.pending = new Map();
    this.stderr = "";
    this.exiting = false;
  }

  async start() {
    if (this.child) return;
    if (!Number.isInteger(this.timeoutMs) || this.timeoutMs < 1000) {
      throw new Error("ToolUniverse timeout must be an integer of at least 1000 ms.");
    }
    if (!fs.existsSync(this.python) || !fs.existsSync(this.entry)) {
      throw new Error("ToolUniverse is not installed. Run ./install-tooluniverse-macos.sh.");
    }
    const componentRoot = path.resolve(this.entry, "..", "..");
    const isolatedHome = path.join(workflowRoot, ".runtime", "macos", "tooluniverse-home");
    fs.mkdirSync(isolatedHome, { recursive: true, mode: 0o700 });
    this.child = spawn(this.python, ["-I", this.entry], {
      cwd: componentRoot,
      env: cleanEnvironment(this.python, componentRoot, isolatedHome),
      stdio: ["pipe", "pipe", "pipe"],
    });
    this.child.stderr.setEncoding("utf8");
    this.child.stderr.on("data", (chunk) => {
      this.stderr = boundedText(`${this.stderr}${chunk}`, 4096);
      if (process.env.WINGPT_TOOLUNIVERSE_VERBOSE === "1") process.stderr.write(chunk);
    });
    const lines = readline.createInterface({ input: this.child.stdout, crlfDelay: Infinity });
    lines.on("line", (line) => this.onLine(line));
    this.child.once("exit", (code, signal) => {
      const error = new Error(`ToolUniverse child exited (${code ?? signal}). ${this.stderr}`.trim());
      for (const request of this.pending.values()) {
        clearTimeout(request.timer);
        request.reject(error);
      }
      this.pending.clear();
      this.child = null;
    });
    await this.request("initialize", {
      protocolVersion: PROTOCOL_VERSION,
      capabilities: {},
      clientInfo: { name: "workflow-codex-tooluniverse-adapter", version: "1" },
    });
    this.notify("notifications/initialized");
  }

  onLine(line) {
    if (Buffer.byteLength(line, "utf8") > 8 * 1024 * 1024) {
      this.stop("SIGKILL");
      return;
    }
    let message;
    try {
      message = JSON.parse(line);
    } catch {
      return;
    }
    const pending = this.pending.get(message.id);
    if (!pending) return;
    clearTimeout(pending.timer);
    this.pending.delete(message.id);
    if (message.error) pending.reject(new Error(`ToolUniverse MCP ${message.error.code}: ${message.error.message}`));
    else pending.resolve(message.result);
  }

  async request(method, params = {}) {
    if (!this.child) await this.start();
    const id = this.nextId++;
    const frame = JSON.stringify({ jsonrpc: "2.0", id, method, params });
    if (Buffer.byteLength(frame, "utf8") > MAX_MESSAGE_BYTES) {
      throw new Error(`ToolUniverse request exceeds ${MAX_MESSAGE_BYTES} bytes.`);
    }
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`ToolUniverse ${method} timed out after ${this.timeoutMs} ms.`));
        this.stop("SIGKILL");
      }, this.timeoutMs);
      this.pending.set(id, { resolve, reject, timer });
      this.child.stdin.write(`${frame}\n`);
    });
  }

  notify(method, params) {
    if (!this.child) return;
    this.child.stdin.write(`${JSON.stringify({ jsonrpc: "2.0", method, ...(params ? { params } : {}) })}\n`);
  }

  async listTools() {
    const result = await this.request("tools/list", {});
    const tools = Array.isArray(result?.tools) ? result.tools : [];
    const selected = tools.filter((tool) => ALLOWED.has(tool?.name));
    if (selected.length !== ALLOWED.size) {
      throw new Error(`Compact ToolUniverse exposed ${selected.length} approved tools; expected ${ALLOWED.size}.`);
    }
    return selected.map((tool) => ({
      ...tool,
      name: `${PREFIX}${tool.name}`,
      inputSchema: normalizeSchema(tool.inputSchema),
    }));
  }

  async call(prefixedName, args) {
    if (!prefixedName.startsWith(PREFIX)) throw new Error("ToolUniverse tool prefix is required.");
    const name = prefixedName.slice(PREFIX.length);
    if (!ALLOWED.has(name)) throw new Error(`ToolUniverse tool is not approved in compact mode: ${name}`);
    return boundToolResult(await this.request("tools/call", { name, arguments: args || {} }));
  }

  async stop(signal = "SIGTERM") {
    if (!this.child || this.exiting) return;
    this.exiting = true;
    const child = this.child;
    const exited = child.exitCode !== null || child.signalCode !== null
      ? Promise.resolve()
      : once(child, "exit").then(() => undefined);
    try { child.stdin.end(); } catch { /* already closed */ }
    try { child.kill(signal); } catch { /* already exited */ }
    const timer = setTimeout(() => {
      if (child.exitCode === null && child.signalCode === null) try { child.kill("SIGKILL"); } catch { /* already exited */ }
    }, 1500);
    await exited;
    clearTimeout(timer);
    if (this.child === child) this.child = null;
    this.exiting = false;
  }
}

function validateCachedTools(cache) {
  if (!cache || cache.schema_version !== 1 || cache.mode !== "local-stdio-compact"
    || cache.tool_count !== ALLOWED.size || !Array.isArray(cache.tools) || cache.tools.length !== ALLOWED.size
    || !/^[a-f0-9]{64}$/.test(cache.tools_sha256 || "")
    || schemaDigest(cache.tools) !== cache.tools_sha256) {
    throw new Error("ToolUniverse compact schema cache failed validation; reinstall ToolUniverse.");
  }
  const names = cache.tools.map((tool) => tool?.name);
  const expected = [...ALLOWED].map((name) => `${PREFIX}${name}`);
  if (new Set(names).size !== ALLOWED.size || expected.some((name) => !names.includes(name))) {
    throw new Error("ToolUniverse compact schema cache does not contain exactly the five approved tools.");
  }
  return cache.tools.map((tool) => ({
    ...tool,
    description: String(tool.description || tool.name).slice(0, 1200),
    inputSchema: normalizeSchema(tool.inputSchema),
  }));
}

export function loadToolUniverseSchemaCache(cachePath = process.env.WINGPT_TOOLUNIVERSE_CACHE || defaultCache) {
  if (!fs.existsSync(cachePath)) {
    throw new Error(`ToolUniverse compact schema cache is missing: ${cachePath}. Reinstall ToolUniverse.`);
  }
  return validateCachedTools(JSON.parse(fs.readFileSync(cachePath, "utf8")));
}

export async function cacheToolUniverseSchemas(cachePath = defaultCache, options = {}) {
  const client = new ToolUniverseStdioClient(options);
  try {
    const tools = await client.listTools();
    const cache = {
      schema_version: 1,
      mode: "local-stdio-compact",
      tool_count: tools.length,
      tools_sha256: schemaDigest(tools),
      tools,
    };
    validateCachedTools(cache);
    fs.mkdirSync(path.dirname(cachePath), { recursive: true });
    const temporary = `${cachePath}.${process.pid}.tmp`;
    fs.writeFileSync(temporary, `${JSON.stringify(cache, null, 2)}\n`, { encoding: "utf8", mode: 0o600 });
    fs.renameSync(temporary, cachePath);
    return cache;
  } finally {
    await client.stop();
  }
}

export function createToolUniverseMcpTools(functionTool, options = {}) {
  const client = new ToolUniverseStdioClient(options);
  const listing = loadToolUniverseSchemaCache(options.cachePath);
  const definitions = listing.map((tool) => functionTool(
    tool.name,
    String(tool.description || tool.name).slice(0, 1200),
    tool.inputSchema.properties,
    tool.inputSchema.required || [],
  ));
  return {
    definitions,
    handles: (name) => name.startsWith(PREFIX) && ALLOWED.has(name.slice(PREFIX.length)),
    execute: async (name, args) => {
      const result = await client.call(name, args);
      if (result?.isError) {
        const text = result.content?.map((item) => item?.text || JSON.stringify(item)).join("\n") || "ToolUniverse call failed.";
        throw new Error(boundedText(text));
      }
      return boundedText(result?.content?.map((item) => item?.text || JSON.stringify(item)).join("\n") || result || "");
    },
    close: () => client.stop(),
    client,
  };
}

async function runProxy() {
  const bridge = createToolUniverseMcpTools((name, description, properties, required) => ({
    name,
    description,
    inputSchema: { type: "object", properties, required, additionalProperties: false },
  }));
  const client = bridge.client;
  const input = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
  const shutdown = () => {
    client.stop();
    input.close();
  };
  process.once("SIGINT", shutdown);
  process.once("SIGTERM", shutdown);
  const write = (message) => process.stdout.write(`${JSON.stringify(message)}\n`);
  for await (const line of input) {
    let request;
    try {
      if (Buffer.byteLength(line, "utf8") > MAX_MESSAGE_BYTES) throw new Error(`Request exceeds ${MAX_MESSAGE_BYTES} bytes.`);
      request = JSON.parse(line);
      if (request.method === "initialize") {
        write({ jsonrpc: "2.0", id: request.id, result: {
          protocolVersion: PROTOCOL_VERSION,
          capabilities: { tools: {} },
          serverInfo: { name: "workflow-codex-tooluniverse", version: "1" },
        } });
      } else if (request.method === "tools/list") {
        write({ jsonrpc: "2.0", id: request.id, result: { tools: bridge.definitions } });
      } else if (request.method === "tools/call") {
        write({ jsonrpc: "2.0", id: request.id, result: await client.call(request.params?.name || "", request.params?.arguments || {}) });
      } else if (request.id !== undefined) {
        write({ jsonrpc: "2.0", id: request.id, error: { code: -32601, message: "Method not found" } });
      }
    } catch (error) {
      if (request?.id !== undefined) write({ jsonrpc: "2.0", id: request.id, error: { code: -32000, message: error.message } });
    }
  }
  await bridge.close();
}

if (process.argv[1] && path.resolve(process.argv[1]) === modulePath) {
  const cacheIndex = process.argv.indexOf("--cache-schema");
  if (cacheIndex >= 0) {
    const cachePath = process.argv[cacheIndex + 1];
    if (!cachePath) throw new Error("--cache-schema requires an output path.");
    const cache = await cacheToolUniverseSchemas(path.resolve(cachePath));
    console.log(`Cached ${cache.tool_count} ToolUniverse schemas (${cache.tools_sha256}).`);
  } else {
    await runProxy();
  }
}
