"use strict";

import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

function boundedResult(stdout) {
  if (stdout.length <= 6000) return stdout;
  try {
    const payload = JSON.parse(stdout);
    if (Array.isArray(payload.studies)) {
      const total = payload.studies.length;
      let kept = total;
      let compact;
      // ponytail: the catalog is small; replace this linear trim only if study count becomes large enough to matter.
      do {
        kept = Math.max(0, kept - 1);
        compact = { ...payload, studies: payload.studies.slice(0, kept), workflow_truncation: { total_studies: total, returned_studies: kept, instruction: "Narrow the search before requesting more catalog data." } };
      } while (kept > 0 && JSON.stringify(compact, null, 2).length > 6000);
      const json = JSON.stringify(compact, null, 2);
      if (json.length <= 6000) return json;
    }
  } catch {}
  return `${stdout.slice(0, 3000)}\n...[3CA OUTPUT TRUNCATED: kept first 3000 and last 3000 of ${stdout.length} characters; narrow the search or save CLI output to a workspace file]...\n${stdout.slice(-3000)}`;
}

export function createThreeCaTools(functionTool, workflowRoot, workspace = workflowRoot) {
  const executable = path.join(workflowRoot, "tools", "tool43CA", ".venv", "Scripts", "threeca.exe");
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
    functionTool("crawl_site", "Cache discoverable 3CA content pages.", { max_pages: integer("Maximum pages", 1), force: { type: "boolean" } }),
    functionTool("plan_asset", "Resolve and inspect a 3CA asset before downloading.", { target: text("Study id or discovered Dropbox URL"), kind: text("Asset kind") }, ["target"]),
    functionTool("download_asset", "Download a validated 3CA asset into the local cache.", { target: text("Study id or discovered Dropbox URL"), kind: text("Asset kind"), extract: { type: "boolean" }, max_bytes: integer("Download limit", 1), max_extract_bytes: integer("Extraction limit", 1) }, ["target"]),
    functionTool("inspect_dataset", "Inspect a table or archive inside the 3CA cache.", { path: text("Absolute or cache-relative path"), sample_rows: integer("Rows to preview", 1) }, ["path"]),
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
      const result = spawnSync(executable, ["--pretty", "--cache", cache, ...cliArgs], {
        cwd: workspace,
        encoding: "utf8",
        timeout: name === "crawl_site" || name === "download_asset" ? 3600000 : 180000,
        maxBuffer: 4 * 1024 * 1024,
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
  if (name === "crawl_site") { const result = ["crawl"]; pushOption(result, "--max-pages", args.max_pages); if (args.force) result.push("--force"); return result; }
  if (name === "plan_asset") { const result = ["plan", args.target]; pushOption(result, "--kind", args.kind); return result; }
  if (name === "download_asset") {
    const result = ["download", args.target]; pushOption(result, "--kind", args.kind); pushOption(result, "--max-bytes", args.max_bytes); pushOption(result, "--max-extract-bytes", args.max_extract_bytes); if (args.extract) result.push("--extract"); return result;
  }
  if (name === "inspect_dataset") { const result = ["inspect", cachePath(args.path, cache)]; pushOption(result, "--sample-rows", args.sample_rows); return result; }
  if (name === "verify_dataset") return ["verify", cachePath(args.path, cache)];
  throw new Error(`Unknown 3CA tool: ${name}`);
}
