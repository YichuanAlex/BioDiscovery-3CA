"use strict";

import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

export function createResearchTools(functionTool, workflowRoot, workspace) {
  const python = path.join(workflowRoot, "tools", "tool43CA", ".venv", "Scripts", "python.exe");
  const cli = path.join(workflowRoot, "tools", "research-quality", "research_quality.py");
  const text = (description) => ({ type: "string", description });
  const definitions = [
    functionTool("fetch_reactome_metabolic_genes", "Build and save a versioned human metabolic-gene set from Reactome's Metabolism hierarchy.", {}),
    functionTool("search_pubmed", "Search NCBI PubMed and save structured results with source URLs and response hashes.", { query: text("PubMed query"), max_results: { type: "integer", minimum: 1 } }, ["query"]),
    functionTool("verify_doi", "Resolve exact Crossref publication metadata from a DOI, publisher DOI URL, or stable 3CA study ID. For the dataset's original reference pass its 3ca:ID directly; do not guess its journal/title with generic web search.", { doi: text("DOI, publisher URL, or stable 3ca:ID") }, ["doi"]),
    functionTool("inspect_research_table", "Count rows and unique entity keys in a workspace CSV/TSV before interpreting or joining it.", { path: text("Workspace-relative table path"), key_columns: { type: "array", items: { type: "string" } } }, ["path"]),
    functionTool("audit_analysis_code", "Reject undefined Python names and known invalid single-cell analysis patterns before an expensive run.", { path: text("Workspace-relative Python file") }, ["path"]),
    functionTool("prepare_3ca_dataset", "Prepare a cached public raw-count 3CA dataset into the workspace and return exact expression/cells/genes paths, dimensions and hashes. Use download_asset's actual extracted_path; do not copy using PowerShell. TPM/normalized matrices are explicitly rejected so choose another raw-count dataset.", { source_path: text("Actual extracted_path in the workflow 3CA cache"), destination: text("Workspace subdirectory; defaults to inputs") }, ["source_path"]),
    functionTool("analyze_metabolic_states", "Run the tested sparse Scanpy/Leiden metabolic clustering engine on all cells or one exact metadata subset. It audits CSV/text gene symbols, preserves exact and unique case-insensitive mappings, computes multi-seed stability, matched controls, cell-type associations within replicates, true labels, summaries, and figures. Run once globally and once for an observed cell-type subset when the question asks both.", {
      expression_path: text("Workspace-relative raw-count Matrix Market file"),
      cells_path: text("Workspace-relative one-row-per-cell CSV"),
      genes_path: text("Workspace-relative one-gene-per-line file"),
      metabolic_genes_path: text("Workspace-relative gene-set CSV with a symbol column, TSV, or one-symbol-per-line text file"),
      cell_id_column: text("Unique cell id column; defaults to cell_name"),
      output_dir: text("Workspace-relative output directory; defaults to results/core_analysis"),
      random_baselines: { type: "integer", minimum: 2, description: "Number of size-matched random gene-set controls; default 19" },
      subset_field: text("Optional exact cell-metadata field for a within-cell-type analysis"),
      subset_values: { type: "array", minItems: 1, items: { type: "string" }, description: "Observed metadata values to include; requires subset_field" },
    }, ["expression_path", "cells_path", "genes_path", "metabolic_genes_path"]),
    functionTool("build_research_report", "Compile the exact declared report/main.tex to report/main.pdf with pdflatex, optional BibTeX, repeated LaTeX passes, propagated exit codes, and PDF parsing. Call after the final TeX edit.", { tex_path: text("Workspace-relative TeX path; defaults to report/main.tex"), pdf_path: text("Matching same-directory PDF path; defaults to report/main.pdf") }),
    functionTool("validate_research_bundle", "Validate the research manifest, entity grain, labels, sources, citations, figures, and current PDF.", { manifest_path: text("Workspace-relative manifest path") }),
  ];
  const names = new Set(definitions.map((tool) => tool.function.name));
  const execute = (name, args = {}) => {
    if (!fs.existsSync(python) || !fs.existsSync(cli)) throw new Error("Workflow-local research-quality runtime is not installed.");
    const command = ["--workspace", workspace, "--pretty"];
    if (name === "fetch_reactome_metabolic_genes") command.push("reactome-metabolic-genes");
    else if (name === "search_pubmed") { command.push("pubmed-search", args.query); if (args.max_results) command.push("--max-results", String(args.max_results)); }
    else if (name === "verify_doi") command.push("verify-doi", args.doi);
    else if (name === "inspect_research_table") { command.push("inspect-table", args.path); for (const key of args.key_columns || []) command.push("--key-column", key); }
    else if (name === "audit_analysis_code") command.push("audit-analysis-code", args.path);
    else if (name === "prepare_3ca_dataset") { command.push("prepare-3ca-dataset", args.source_path); if (args.destination) command.push("--destination", args.destination); }
    else if (name === "analyze_metabolic_states") {
      command.push("analyze-metabolic-states", "--expression-path", args.expression_path, "--cells-path", args.cells_path, "--genes-path", args.genes_path, "--metabolic-genes-path", args.metabolic_genes_path);
      if (args.cell_id_column) command.push("--cell-id-column", args.cell_id_column);
      if (args.output_dir) command.push("--output-dir", args.output_dir);
      if (args.random_baselines) command.push("--random-baselines", String(args.random_baselines));
      if (args.subset_field) command.push("--subset-field", args.subset_field);
      for (const value of args.subset_values || []) command.push("--subset-value", value);
    }
    else if (name === "build_research_report") { command.push("build-report"); if (args.tex_path) command.push("--tex-path", args.tex_path); if (args.pdf_path) command.push("--pdf-path", args.pdf_path); }
    else if (name === "validate_research_bundle") command.push("validate", args.manifest_path || "results/analysis_manifest.json");
    else throw new Error(`Unknown research tool: ${name}`);
    const result = spawnSync(python, [cli, ...command], { cwd: workspace, encoding: "utf8", timeout: 0, maxBuffer: 64 * 1024 * 1024, env: { ...process.env, PYTHONPATH: path.dirname(cli) } });
    if (result.error) throw result.error;
    if (result.status !== 0) throw new Error((result.stdout || result.stderr || `research-quality exited with ${result.status}`).trim());
    return result.stdout.length <= 16000 ? result.stdout : `${result.stdout.slice(0, 8000)}\n...[RESEARCH OUTPUT TRUNCATED; full metadata is saved in the workspace]...\n${result.stdout.slice(-8000)}`;
  };
  return { definitions, handles: (name) => names.has(name), execute };
}
