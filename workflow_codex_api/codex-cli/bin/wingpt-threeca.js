"use strict";

import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { scientificPython } from "./wingpt-platform.js";

function boundedResult(stdout) {
  if (stdout.length <= 16000) return stdout;
  try {
    const payload = JSON.parse(stdout);
    const field = Array.isArray(payload.studies) ? "studies" : Array.isArray(payload.entries) ? "entries" : null;
    if (field) {
      const total = payload[field].length;
      let kept = total;
      let compact;
      // ponytail: catalog/directory lists are small; replace linear trim only if their size becomes significant.
      do {
        kept = Math.max(0, kept - 1);
        compact = { ...payload, [field]: payload[field].slice(0, kept), ...(field === "entries" ? { entries_truncated: true } : {}), workflow_truncation: { [`total_${field}`]: total, [`returned_${field}`]: kept, instruction: field === "studies" ? "Narrow the search before requesting more catalog data." : "Inspect one actual listed file or subdirectory for content." } };
      } while (kept > 0 && JSON.stringify(compact, null, 2).length > 16000);
      const json = JSON.stringify(compact, null, 2);
      if (json.length <= 16000) return json;
    }
  } catch {}
  return `${stdout.slice(0, 8000)}\n...[3CA OUTPUT TRUNCATED: kept first 8000 and last 8000 of ${stdout.length} characters; narrow the search or save CLI output to a workspace file]...\n${stdout.slice(-8000)}`;
}

export function createThreeCaTools(functionTool, workflowRoot, workspace = workflowRoot) {
  const executable = scientificPython(workflowRoot);
  const cli = path.join(workflowRoot, "tools", "tool43CA", "CLI", "src", "threeca.py");
  const cache = path.join(workflowRoot, ".threeca", "cache");
  const text = (description) => ({ type: "string", description });
  const integer = (description, minimum = 0) => ({ type: "integer", minimum, description });
  const definitions = [
    functionTool("refresh_catalog", "Refresh all 3CA study tables.", {}),
    functionTool("search_studies", "Search the cached 3CA catalog. Use this first for 3CA requests.", {
      query: text("Author, disease, title, or keyword"), category: text("Cancer category"), disease: text("Disease"), technology: text("Technology"), min_samples: integer("Minimum samples"), min_cells: integer("Minimum cells"), asset: { type: "string", enum: ["", "data", "metadata"] },
    }),
    functionTool("get_study", "Get one study by stable 3CA id.", { study_id: text("Stable id such as 3ca:20764"), discover_assets: { type: "boolean" } }, ["study_id"]),
    functionTool("get_page", "Fetch a page under weizmann.ac.il/sites/3CA.", { url_or_path: text("3CA URL or path"), force: { type: "boolean" }, max_chars: integer("Maximum returned text characters") }, ["url_or_path"]),
    functionTool("search_cached_pages", "Search locally cached 3CA page text.", { query: text("Search text"), limit: integer("Maximum matches", 1) }, ["query"]),
    functionTool("crawl_site", "Cache all discoverable 3CA content pages.", { force: { type: "boolean" } }),
    functionTool("plan_asset", "Resolve and inspect a 3CA asset before downloading.", { target: text("Study id or discovered Dropbox URL"), kind: text("Asset kind") }, ["target"]),
    functionTool("download_asset", "Download a validated 3CA asset into the local cache without a workflow size ceiling.", { target: text("Study id or discovered Dropbox URL"), kind: text("Asset kind"), extract: { type: "boolean" } }, ["target"]),
    functionTool("inspect_dataset", "Inspect a cached table/archive, or list actual names in a directory (listing is not matrix validation).", { path: text("Absolute or cache-relative path"), sample_rows: integer("Rows to preview", 1) }, ["path"]),
    functionTool("verify_dataset", "Hash and validate a file inside the 3CA cache.", { path: text("Absolute or cache-relative path") }, ["path"]),
  ];
  const names = new Set(definitions.map((tool) => tool.function.name));

  return {
    definitions,
    installed: fs.existsSync(executable),
    handles: (name) => names.has(name),
    execute(name, args) {
      if (!fs.existsSync(executable)) throw new Error(`tool43CA is not installed: ${executable}`);
      const cliArgs = commandArgs(name, args, cache);
      const result = spawnSync(executable, [cli, "--pretty", "--cache", cache, ...cliArgs], {
        cwd: workspace,
        encoding: "utf8",
        timeout: 0,
        maxBuffer: 64 * 1024 * 1024,
        env: { ...process.env, THREECA_CACHE: cache },
      });
      if (result.error) throw result.error;
      if (result.status !== 0) throw new Error((result.stderr || result.stdout || `threeca exited with ${result.status}`).trim());
      return boundedResult(result.stdout);
    },
  };
}

function pushOption(result, flag, value) {
  if (value !== undefined && value !== null && value !== "" && value !== false) result.push(flag, String(value));
}

function cachePath(input, cache) {
  const candidate = path.resolve(cache, input);
  const relative = path.relative(cache, candidate);
  if (relative.startsWith("..") || path.isAbsolute(relative)) throw new Error(`3CA dataset path leaves the local cache: ${input}`);
  const real = fs.realpathSync(candidate);
  const realRelative = path.relative(fs.realpathSync(cache), real);
  if (realRelative.startsWith("..") || path.isAbsolute(realRelative)) throw new Error(`3CA dataset path resolves outside the local cache: ${input}`);
  return real;
}

function commandArgs(name, args, cache) {
  if (name === "refresh_catalog") return ["refresh"];
  if (name === "search_studies") {
    const result = ["search", args.query || ""];
    pushOption(result, "--category", args.category); pushOption(result, "--disease", args.disease); pushOption(result, "--technology", args.technology);
    pushOption(result, "--min-samples", args.min_samples); pushOption(result, "--min-cells", args.min_cells); pushOption(result, "--asset", args.asset);
    return result;
  }
  if (name === "get_study") return ["show", args.study_id, ...(args.discover_assets ? ["--discover-assets"] : [])];
  if (name === "get_page") {
    const result = ["page", args.url_or_path];
    if (args.force) result.push("--force"); pushOption(result, "--max-chars", args.max_chars);
    return result;
  }
  if (name === "search_cached_pages") { const result = ["page-search", args.query]; pushOption(result, "--limit", args.limit); return result; }
  if (name === "crawl_site") { const result = ["crawl"]; if (args.force) result.push("--force"); return result; }
  if (name === "plan_asset") { const result = ["plan", args.target]; pushOption(result, "--kind", args.kind); return result; }
  if (name === "download_asset") {
    const result = ["download", args.target]; pushOption(result, "--kind", args.kind); if (args.extract) result.push("--extract"); return result;
  }
  if (name === "inspect_dataset") { const result = ["inspect", cachePath(args.path, cache)]; pushOption(result, "--sample-rows", args.sample_rows); return result; }
  if (name === "verify_dataset") return ["verify", cachePath(args.path, cache)];
  throw new Error(`Unknown 3CA tool: ${name}`);
}
