#!/usr/bin/env node

import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
Object.assign(process.env, {
  CODEX_HOME: path.join(root, ".runtime", "codex-home"),
  CODEX_CLI_PATH: path.join(root, "codex-local.cmd"),
  THREECA_CACHE: path.join(root, ".threeca", "cache"),
  PYTHONNOUSERSITE: "1",
  NODE_REPL_DISABLE_ANALYTICS: "1",
  BROWSER_USE_DISABLE_AMBIENT_NETWORK: "1",
});
await import("./Qwen3.5-4B.js");
