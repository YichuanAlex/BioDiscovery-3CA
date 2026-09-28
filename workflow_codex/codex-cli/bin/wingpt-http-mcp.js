"use strict";

import fs from "node:fs";
import { createHash } from "node:crypto";

const PROTOCOL_VERSION = "2025-06-18";
const DEFAULT_TIMEOUT_MS = 15_000;
const DEFAULT_CALL_TIMEOUT_MS = 45_000;
const MAX_RESPONSE_BYTES = 8 * 1024 * 1024;
const MAX_TOOL_OUTPUT_BYTES = 16 * 1024;
const MAX_TOOLS_PER_SERVER = 96;
const MANIFEST_VERSION = 1;

export const ANONYMOUS_SCIENCE_MCP_ENDPOINTS = Object.freeze([
  { prefix: "pubmed", url: "https://pubmed.mcp.claude.com/mcp" },
  { prefix: "biorxiv", url: "https://hcls.mcp.claude.com/biorxiv/mcp" },
  { prefix: "clinicaltrials", url: "https://hcls.mcp.claude.com/clinical_trials/mcp" },
  { prefix: "chembl", url: "https://hcls.mcp.claude.com/chembl/mcp" },
  { prefix: "opentargets", url: "https://mcp.platform.opentargets.org/mcp" },
]);

function safeName(value) {
  return String(value).toLowerCase().replace(/[^a-z0-9_-]+/g, "_").replace(/^_+|_+$/g, "");
}

function canonicalJson(value) {
  if (Array.isArray(value)) return value.map(canonicalJson);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, canonicalJson(value[key])]));
  }
  return value;
}

function sha256(value) {
  return createHash("sha256").update(typeof value === "string" ? value : JSON.stringify(canonicalJson(value))).digest("hex");
}

function boundedText(value, limit = MAX_TOOL_OUTPUT_BYTES) {
  const text = typeof value === "string" ? value : JSON.stringify(value);
  const bytes = Buffer.from(text, "utf8");
  if (bytes.length <= limit) return text;
  const marker = Buffer.from(`\n...[MCP OUTPUT TRUNCATED: ${bytes.length} bytes total]...\n`);
  // Reserve eight bytes because decoding two slices cut inside UTF-8 code points can add replacements.
  const side = Math.floor((limit - marker.length - 8) / 2);
  return Buffer.concat([bytes.subarray(0, side), marker, bytes.subarray(bytes.length - side)]).toString("utf8");
}

function jsonRpcError(payload) {
  if (!payload?.error) return null;
  const detail = payload.error.data === undefined ? "" : ` ${boundedText(payload.error.data, 2000)}`;
  return new Error(`MCP ${payload.error.code}: ${payload.error.message || "request failed"}${detail}`);
}

function parseSse(text) {
  const messages = [];
  for (const block of text.split(/\r?\n\r?\n/)) {
    const data = block.split(/\r?\n/).filter((line) => line.startsWith("data:"))
      .map((line) => line.slice(5).replace(/^ /, "")).join("\n");
    if (!data || data === "[DONE]") continue;
    try { messages.push(JSON.parse(data)); } catch { /* Ignore keepalives and non-JSON SSE events. */ }
  }
  return messages;
}

async function readBounded(response, maxBytes = MAX_RESPONSE_BYTES) {
  const declared = Number(response.headers.get("content-length") || 0);
  if (declared > maxBytes) throw new Error(`MCP response exceeds ${maxBytes} bytes.`);
  if (!response.body) return "";
  const reader = response.body.getReader();
  const chunks = [];
  let total = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    total += value.byteLength;
    if (total > maxBytes) {
      await reader.cancel();
      throw new Error(`MCP response exceeds ${maxBytes} bytes.`);
    }
    chunks.push(Buffer.from(value));
  }
  return Buffer.concat(chunks).toString("utf8");
}

function responsePayload(contentType, text, id) {
  const candidates = /text\/event-stream/i.test(contentType) ? parseSse(text) : [JSON.parse(text)];
  const payload = candidates.find((item) => item?.id === id)
    || candidates.find((item) => item?.result !== undefined || item?.error);
  if (!payload) throw new Error("MCP response did not contain a JSON-RPC result.");
  const error = jsonRpcError(payload);
  if (error) throw error;
  return payload.result;
}

async function fetchWithTimeout(fetchImpl, url, options, timeoutMs) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetchImpl(url, { ...options, signal: controller.signal });
  } catch (error) {
    if (controller.signal.aborted) throw new Error(`MCP request timed out after ${timeoutMs} ms.`);
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

class AnonymousMcpClient {
  constructor(endpoint, options) {
    this.endpoint = endpoint;
    this.fetchImpl = options.fetchImpl;
    this.timeoutMs = options.timeoutMs;
    this.callTimeoutMs = options.callTimeoutMs;
    this.sessionId = null;
    this.nextId = 1;
    this.initialized = false;
  }

  async request(method, params = {}, notification = false) {
    const id = notification ? undefined : this.nextId++;
    const body = { jsonrpc: "2.0", method, ...(notification ? {} : { id }), ...(params === undefined ? {} : { params }) };
    const headers = {
      "Content-Type": "application/json",
      Accept: "application/json, text/event-stream",
      "MCP-Protocol-Version": PROTOCOL_VERSION,
    };
    if (this.sessionId) headers["Mcp-Session-Id"] = this.sessionId;
    const response = await fetchWithTimeout(
      this.fetchImpl,
      this.endpoint.url,
      { method: "POST", headers, body: JSON.stringify(body), redirect: "error" },
      method === "tools/call" ? this.callTimeoutMs : this.timeoutMs,
    );
    if ([401, 402, 403, 407].includes(response.status) || response.headers.has("www-authenticate")) {
      throw new Error(`MCP endpoint requires authentication or subscription (HTTP ${response.status}).`);
    }
    if (!response.ok) throw new Error(`MCP HTTP ${response.status}.`);
    const returnedSession = response.headers.get("mcp-session-id");
    if (returnedSession) this.sessionId = returnedSession;
    const text = await readBounded(response);
    if (notification || response.status === 202 || response.status === 204 || !text.trim()) return null;
    return responsePayload(response.headers.get("content-type") || "application/json", text, id);
  }

  async initialize() {
    const result = await this.request("initialize", {
      protocolVersion: PROTOCOL_VERSION,
      capabilities: {},
      clientInfo: { name: "workflow-codex-anonymous-science", version: "1" },
    });
    if (!result?.protocolVersion) throw new Error("initialize did not return a protocolVersion.");
    this.serverInfo = result.serverInfo || null;
    await this.request("notifications/initialized", undefined, true);
    const listing = await this.request("tools/list", {});
    this.initialized = true;
    return listing;
  }
}

function normalizeInputSchema(schema) {
  if (!schema || typeof schema !== "object" || Array.isArray(schema)) {
    return { type: "object", properties: {}, additionalProperties: false };
  }
  const normalized = { ...schema, type: "object" };
  if (!normalized.properties || typeof normalized.properties !== "object" || Array.isArray(normalized.properties)) {
    normalized.properties = {};
  }
  return normalized;
}

function renderToolResult(result) {
  if (result?.isError) {
    const message = Array.isArray(result.content)
      ? result.content.map((item) => item?.text || JSON.stringify(item)).join("\n")
      : JSON.stringify(result);
    throw new Error(boundedText(message));
  }
  if (Array.isArray(result?.content)) {
    const rendered = result.content.map((item) => item?.type === "text" ? item.text : JSON.stringify(item)).join("\n");
    if (rendered) return boundedText(rendered);
  }
  return boundedText(result ?? "");
}

function validatedEndpoint(endpoint, allowHttpForTests = false) {
  const prefix = safeName(endpoint?.prefix);
  const url = new URL(endpoint?.url);
  if (!prefix || url.protocol !== "https:" && !allowHttpForTests) {
    throw new Error("Anonymous MCP endpoints must use HTTPS and a safe prefix.");
  }
  if (url.username || url.password) throw new Error("Credentials in MCP endpoint URLs are forbidden.");
  if (endpoint.headers || endpoint.token || endpoint.authorization) {
    throw new Error("Authenticated MCP configuration is forbidden.");
  }
  return { prefix, url: url.href };
}

function cachedTool(remote) {
  const inputSchema = normalizeInputSchema(remote.inputSchema);
  return {
    name: String(remote.name),
    description: String(remote.description || remote.name).slice(0, 1200),
    inputSchema,
    annotations: remote.annotations && typeof remote.annotations === "object" ? remote.annotations : {},
    schema_sha256: sha256(inputSchema),
  };
}

export async function probeAnonymousScienceMcpEndpoints(options = {}) {
  const fetchImpl = options.fetchImpl || globalThis.fetch;
  if (typeof fetchImpl !== "function") throw new Error("HTTP MCP requires a fetch implementation.");
  const endpoints = options.endpoints || ANONYMOUS_SCIENCE_MCP_ENDPOINTS;
  const results = await Promise.all(endpoints.map(async (configured) => {
    let endpoint;
    try {
      endpoint = validatedEndpoint(configured, options.allowHttpForTests);
      const client = new AnonymousMcpClient(endpoint, {
        fetchImpl,
        timeoutMs: options.timeoutMs || DEFAULT_TIMEOUT_MS,
        callTimeoutMs: options.callTimeoutMs || DEFAULT_CALL_TIMEOUT_MS,
      });
      const listing = await client.initialize();
      if (!Array.isArray(listing?.tools)) throw new Error("tools/list did not return a tools array.");
      const tools = listing.tools.slice(0, MAX_TOOLS_PER_SERVER).map(cachedTool);
      return {
        prefix: endpoint.prefix,
        url: endpoint.url,
        enabled: true,
        protocol_version: PROTOCOL_VERSION,
        server_info: client.serverInfo || null,
        tools,
        tools_sha256: sha256(tools),
      };
    } catch (error) {
      return {
        prefix: safeName(configured?.prefix),
        url: String(configured?.url || ""),
        enabled: false,
        error: error.message,
      };
    }
  }));
  const manifest = {
    schema_version: MANIFEST_VERSION,
    installed_at: new Date().toISOString(),
    authenticated_mcp_installed: false,
    endpoints: results,
  };
  manifest.manifest_sha256 = sha256(manifest);
  return manifest;
}

export function readAnonymousScienceMcpManifest(manifestPath) {
  if (!manifestPath || !fs.existsSync(manifestPath)) return null;
  const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  const hash = manifest.manifest_sha256;
  const unsigned = { ...manifest };
  delete unsigned.manifest_sha256;
  if (manifest.schema_version !== MANIFEST_VERSION
    || manifest.authenticated_mcp_installed !== false
    || !Array.isArray(manifest.endpoints)
    || hash !== sha256(unsigned)) {
    throw new Error("Anonymous HTTP MCP manifest is invalid or has been modified.");
  }
  const allowed = new Map(ANONYMOUS_SCIENCE_MCP_ENDPOINTS.map((item) => [item.prefix, item.url]));
  for (const endpoint of manifest.endpoints) {
    if (!allowed.has(endpoint.prefix) || allowed.get(endpoint.prefix) !== endpoint.url
      || typeof endpoint.enabled !== "boolean" || endpoint.enabled && !Array.isArray(endpoint.tools)) {
      throw new Error("Anonymous HTTP MCP manifest contains an unapproved endpoint.");
    }
    for (const tool of endpoint.tools || []) {
      if (tool.schema_sha256 !== sha256(normalizeInputSchema(tool.inputSchema))) {
        throw new Error(`Anonymous HTTP MCP cached schema hash mismatch: ${endpoint.prefix}/${tool.name}`);
      }
    }
  }
  return manifest;
}

export async function createAnonymousScienceMcpTools(functionTool, options = {}) {
  const fetchImpl = options.fetchImpl || globalThis.fetch;
  if (typeof fetchImpl !== "function") throw new Error("HTTP MCP requires a fetch implementation.");
  const manifest = options.manifest || readAnonymousScienceMcpManifest(options.manifestPath);
  const probe = manifest || (options.requireInstalled
    ? {
        endpoints: ANONYMOUS_SCIENCE_MCP_ENDPOINTS.map((endpoint) => ({
          ...endpoint,
          enabled: false,
          error: "not installed; run install-anonymous-http-mcp",
        })),
      }
    : await probeAnonymousScienceMcpEndpoints(options));
  const endpoints = probe.endpoints.filter((endpoint) => endpoint.enabled);
  const clients = new Map();
  const definitions = [];
  const failures = probe.endpoints.filter((endpoint) => !endpoint.enabled)
    .map(({ prefix, url, error }) => ({ prefix, url, error }));
  const toolRoutes = new Map();

  for (const endpoint of endpoints) {
    const validated = validatedEndpoint(endpoint, options.allowHttpForTests);
    const client = new AnonymousMcpClient(validated, {
      fetchImpl,
      timeoutMs: options.timeoutMs || DEFAULT_TIMEOUT_MS,
      callTimeoutMs: options.callTimeoutMs || DEFAULT_CALL_TIMEOUT_MS,
    });
    for (const remote of endpoint.tools) {
        if (remote?.annotations?.readOnlyHint === false || remote?.annotations?.destructiveHint === true) continue;
        const remoteName = String(remote?.name || "");
        const name = `${validated.prefix}__${safeName(remoteName)}`.slice(0, 128);
        if (!remoteName || !name || toolRoutes.has(name)) continue;
        const description = `[Anonymous read-only ${validated.prefix} MCP] ${String(remote.description || remoteName).slice(0, 1200)}`;
        const schema = normalizeInputSchema(remote.inputSchema);
        definitions.push(functionTool(name, description, schema.properties, schema.required || []));
        definitions.at(-1).function.parameters = schema;
        toolRoutes.set(name, { client, remoteName, prefix: validated.prefix, toolsSha256: endpoint.tools_sha256 });
    }
    clients.set(validated.prefix, client);
  }

  return {
    definitions,
    failures,
    connected: [...clients.keys()],
    handles: (name) => toolRoutes.has(name),
    async execute(name, args = {}) {
      const route = toolRoutes.get(name);
      if (!route) throw new Error(`Anonymous science MCP tool is not enabled: ${name}`);
      if (!route.client.initialized) {
        const listing = await route.client.initialize();
        const tools = Array.isArray(listing?.tools) ? listing.tools.slice(0, MAX_TOOLS_PER_SERVER).map(cachedTool) : [];
        if (sha256(tools) !== route.toolsSha256) {
          throw new Error(`MCP schema changed for ${route.prefix}; rerun the anonymous MCP installer.`);
        }
      }
      return renderToolResult(await route.client.request("tools/call", { name: route.remoteName, arguments: args }));
    },
  };
}
