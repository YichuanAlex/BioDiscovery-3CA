#!/usr/bin/env node
"use strict";

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  ANONYMOUS_SCIENCE_MCP_ENDPOINTS,
  probeAnonymousScienceMcpEndpoints,
} from "../codex-cli/bin/wingpt-http-mcp.js";

const workflowRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const installRoot = path.join(workflowRoot, ".runtime", "anonymous-http-mcp");
const manifestPath = path.join(installRoot, "manifest.json");
const temporaryPath = `${manifestPath}.${process.pid}.tmp`;
const timeoutMs = Number(process.env.WINGPT_MCP_INSTALL_TIMEOUT_MS || "20000");

if (!Number.isInteger(timeoutMs) || timeoutMs < 1000) {
  throw new Error("WINGPT_MCP_INSTALL_TIMEOUT_MS must be an integer of at least 1000.");
}

const manifest = await probeAnonymousScienceMcpEndpoints({ timeoutMs });
if (manifest.endpoints.length !== ANONYMOUS_SCIENCE_MCP_ENDPOINTS.length) {
  throw new Error("Anonymous HTTP MCP probe did not cover the five approved endpoints.");
}

fs.mkdirSync(installRoot, { recursive: true });
fs.writeFileSync(temporaryPath, `${JSON.stringify(manifest, null, 2)}\n`, { encoding: "utf8", mode: 0o600 });
try {
  fs.renameSync(temporaryPath, manifestPath);
} catch (error) {
  if (!["EEXIST", "EPERM"].includes(error.code)) throw error;
  fs.rmSync(manifestPath, { force: true });
  fs.renameSync(temporaryPath, manifestPath);
}

for (const endpoint of manifest.endpoints) {
  const status = endpoint.enabled ? `enabled (${endpoint.tools.length} tools, ${endpoint.tools_sha256})` : `disabled (${endpoint.error})`;
  console.log(`${endpoint.prefix}: ${status}`);
}
console.log(`Anonymous HTTP MCP manifest: ${manifestPath}`);
