#!/usr/bin/env node
"use strict";

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const workflowRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const installRoot = path.join(workflowRoot, ".runtime", "anonymous-http-mcp");

fs.rmSync(installRoot, { recursive: true, force: true });
console.log(`Removed anonymous HTTP MCP installation: ${installRoot}`);
