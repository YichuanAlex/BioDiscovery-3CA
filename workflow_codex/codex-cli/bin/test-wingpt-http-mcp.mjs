import assert from "node:assert/strict";
import http from "node:http";
import {
  createAnonymousScienceMcpTools,
  probeAnonymousScienceMcpEndpoints,
} from "./wingpt-http-mcp.js";

const requests = [];
const server = http.createServer(async (request, response) => {
  let body = "";
  for await (const chunk of request) body += chunk;
  const message = JSON.parse(body);
  requests.push({
    path: request.url,
    method: message.method,
    session: request.headers["mcp-session-id"],
    authorization: request.headers.authorization,
  });
  if (request.url === "/auth") {
    response.writeHead(401, { "WWW-Authenticate": "Bearer" });
    response.end("authentication required");
    return;
  }
  if (request.url === "/slow") {
    setTimeout(() => {
      response.writeHead(200, { "Content-Type": "application/json" });
      response.end(JSON.stringify({ jsonrpc: "2.0", id: message.id, result: {} }));
    }, 500);
    return;
  }
  if (message.method === "notifications/initialized") {
    response.writeHead(202);
    response.end();
    return;
  }
  const isSse = request.url === "/sse";
  let result;
  if (message.method === "initialize") {
    result = { protocolVersion: "2025-06-18", capabilities: { tools: {} }, serverInfo: { name: "mock", version: "1" } };
  } else if (message.method === "tools/list") {
    result = {
      tools: [
        {
          name: isSse ? "search-papers" : "lookup",
          description: "Read public scientific records",
          inputSchema: { type: "object", properties: { query: { type: "string" } }, required: ["query"], additionalProperties: false },
          annotations: { readOnlyHint: true },
        },
        {
          name: "write-record",
          description: "Must never be exposed",
          inputSchema: { type: "object" },
          annotations: { destructiveHint: true },
        },
      ],
    };
  } else if (message.method === "tools/call") {
    result = {
      content: [{
        type: "text",
        text: isSse ? `SSE_OK:${message.params.arguments.query}:${"x".repeat(20_000)}` : `JSON_OK:${message.params.name}:${message.params.arguments.query}`,
      }],
    };
  }
  const payload = JSON.stringify({ jsonrpc: "2.0", id: message.id, result });
  const headers = message.method === "initialize" ? { "Mcp-Session-Id": `${isSse ? "sse" : "json"}-session` } : {};
  if (isSse) {
    response.writeHead(200, { ...headers, "Content-Type": "text/event-stream" });
    response.end(`event: message\ndata: ${payload}\n\n`);
  } else {
    response.writeHead(200, { ...headers, "Content-Type": "application/json" });
    response.end(payload);
  }
});

await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
try {
  const { port } = server.address();
  const functionTool = (name, description, properties, required = []) => ({
    type: "function",
    function: { name, description, parameters: { type: "object", properties, required, additionalProperties: false } },
  });
  const probe = await probeAnonymousScienceMcpEndpoints({
    allowHttpForTests: true,
    timeoutMs: 200,
    callTimeoutMs: 500,
    endpoints: [
      { prefix: "json", url: `http://127.0.0.1:${port}/json` },
      { prefix: "sse", url: `http://127.0.0.1:${port}/sse` },
      { prefix: "auth", url: `http://127.0.0.1:${port}/auth` },
      { prefix: "slow", url: `http://127.0.0.1:${port}/slow` },
    ],
  });
  assert.equal(probe.authenticated_mcp_installed, false);
  assert.match(probe.manifest_sha256, /^[a-f0-9]{64}$/);
  assert.deepEqual(probe.endpoints.filter((item) => item.enabled).map((item) => item.prefix), ["json", "sse"]);
  assert(probe.endpoints.filter((item) => item.enabled).every((item) => /^[a-f0-9]{64}$/.test(item.tools_sha256)));
  assert(probe.endpoints.flatMap((item) => item.tools || []).every((item) => /^[a-f0-9]{64}$/.test(item.schema_sha256)));

  const adapter = await createAnonymousScienceMcpTools(functionTool, {
    allowHttpForTests: true,
    timeoutMs: 200,
    callTimeoutMs: 500,
    manifest: probe,
  });

  assert.deepEqual(adapter.connected, ["json", "sse"]);
  assert.deepEqual(adapter.failures.map((item) => item.prefix), ["auth", "slow"]);
  assert.deepEqual(adapter.definitions.map((item) => item.function.name), ["json__lookup", "sse__search-papers"]);
  assert.equal(adapter.definitions[0].function.parameters.additionalProperties, false);
  assert.equal(await adapter.execute("json__lookup", { query: "TP53" }), "JSON_OK:lookup:TP53");
  const sse = await adapter.execute("sse__search-papers", { query: "BRCA1" });
  assert.match(sse, /^SSE_OK:BRCA1:/);
  assert.match(sse, /MCP OUTPUT TRUNCATED/);
  assert(Buffer.byteLength(sse, "utf8") <= 16 * 1024);
  assert(requests.filter((item) => ["/json", "/sse"].includes(item.path)).every((item) => item.authorization === undefined));
  assert(requests.some((item) => item.path === "/json" && item.method === "tools/list" && item.session === "json-session"));
  assert(requests.some((item) => item.path === "/sse" && item.method === "tools/call" && item.session === "sse-session"));
  const absent = await createAnonymousScienceMcpTools(functionTool, { requireInstalled: true });
  assert.equal(absent.definitions.length, 0);
  assert.equal(absent.failures.length, 5);
  console.log("PASS: install probe/schema hashes, cached JSON/SSE runtime, prefixed tools/call, auth exclusion, timeout, failed-endpoint disablement, read-only filtering, session propagation, and 16 KiB truncation.");
} finally {
  await new Promise((resolve) => server.close(resolve));
}
