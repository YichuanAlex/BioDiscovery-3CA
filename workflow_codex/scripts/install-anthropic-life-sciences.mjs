#!/usr/bin/env node
"use strict";

import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

const workflowRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repositoryRoot = path.dirname(workflowRoot);
const destinationRoot = path.join(workflowRoot, "skills", "anthropic-life-sciences");
const temporaryRoot = `${destinationRoot}.install-${process.pid}`;
const bioRoot = path.join(repositoryRoot, "anthropics-knowledge-work-plugins", "bio-research", "skills");
const lifeSciencesRoot = path.join(repositoryRoot, "anthropics-life-sciences");

const bioSkillNames = [
  "instrument-data-to-allotrope",
  "nextflow-development",
  "scientific-problem-selection",
  "scvi-tools",
  "single-cell-rna-qc",
  "start",
];
const clinicalSkillName = "clinical-trial-protocol-skill";

function sha256(buffer) {
  return createHash("sha256").update(buffer).digest("hex");
}

function sourceRelative(absolutePath) {
  return path.relative(repositoryRoot, absolutePath).replaceAll("\\", "/");
}

function collectFiles(root) {
  const files = [];
  const pending = [root];
  while (pending.length) {
    const directory = pending.pop();
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      const absolute = path.join(directory, entry.name);
      if (entry.isSymbolicLink()) throw new Error(`Refusing symbolic link in skill source: ${absolute}`);
      if (entry.isDirectory()) pending.push(absolute);
      else if (entry.isFile()) files.push(absolute);
      else throw new Error(`Unsupported skill source entry: ${absolute}`);
    }
  }
  return files.sort((left, right) => left.localeCompare(right));
}

function inventory(root) {
  const files = collectFiles(root).map((absolute) => {
    const content = fs.readFileSync(absolute);
    return {
      path: path.relative(root, absolute).replaceAll("\\", "/"),
      bytes: content.length,
      sha256: sha256(content),
    };
  });
  const treeSha256 = sha256(Buffer.from(files.map((file) => `${file.path}\0${file.bytes}\0${file.sha256}`).join("\n")));
  return { files, tree_sha256: treeSha256 };
}

function parseSkillMetadata(skillFile) {
  const content = fs.readFileSync(skillFile, "utf8");
  const frontmatter = /^---\r?\n([\s\S]*?)\r?\n---/.exec(content)?.[1] || "";
  const field = (name) => {
    const match = new RegExp(`^${name}:\\s*(.+)$`, "m").exec(frontmatter);
    return match ? match[1].trim().replace(/^["']|["']$/g, "") : "";
  };
  const name = field("name");
  const description = field("description");
  if (!name || !description) throw new Error(`Missing name/description frontmatter: ${skillFile}`);
  return { name, description };
}

function copySkill(source, target) {
  if (!fs.statSync(source).isDirectory()) throw new Error(`Skill source is not a directory: ${source}`);
  if (!fs.existsSync(path.join(source, "SKILL.md"))) throw new Error(`Skill source lacks SKILL.md: ${source}`);
  fs.cpSync(source, target, { recursive: true, dereference: false, errorOnExist: true });
}

function sameInventory(left, right) {
  return left.tree_sha256 === right.tree_sha256;
}

function main() {
  for (const sourceRoot of [bioRoot, lifeSciencesRoot]) {
    if (!fs.existsSync(sourceRoot)) throw new Error(`Required source is missing: ${sourceRoot}`);
  }
  fs.rmSync(temporaryRoot, { recursive: true, force: true });
  fs.mkdirSync(temporaryRoot, { recursive: true });
  try {
    const skills = [];
    for (const directoryName of bioSkillNames) {
      const source = path.join(bioRoot, directoryName);
      const target = path.join(temporaryRoot, directoryName);
      copySkill(source, target);
      const metadata = parseSkillMetadata(path.join(source, "SKILL.md"));
      const installed = inventory(target);
      const alternative = path.join(lifeSciencesRoot, directoryName);
      skills.push({
        name: metadata.name,
        directory: directoryName,
        description: metadata.description,
        canonical_source: sourceRelative(source),
        source_kind: "bio-research-canonical",
        ...(fs.existsSync(alternative) ? {
          duplicate_source: sourceRelative(alternative),
          duplicate_identical_to_canonical: sameInventory(inventory(source), inventory(alternative)),
        } : {}),
        ...installed,
      });
    }

    const clinicalSource = path.join(lifeSciencesRoot, clinicalSkillName);
    const clinicalTarget = path.join(temporaryRoot, clinicalSkillName);
    copySkill(clinicalSource, clinicalTarget);
    const clinicalMetadata = parseSkillMetadata(path.join(clinicalSource, "SKILL.md"));
    skills.push({
      name: clinicalMetadata.name,
      directory: clinicalSkillName,
      description: clinicalMetadata.description,
      canonical_source: sourceRelative(clinicalSource),
      source_kind: "life-sciences-unique",
      ...inventory(clinicalTarget),
    });

    if (skills.length !== 7) throw new Error(`Expected 7 installed skills, found ${skills.length}.`);
    const manifest = {
      schema_version: 2,
      package: "anthropic-life-sciences",
      installed_skill_count: skills.length,
      duplicate_policy: "bio-research is canonical when a skill exists in both source collections",
      authenticated_mcp_installed: false,
      runtime: {
        platform: "macOS arm64",
        installer: "setup-life-sciences-macos.sh",
        smoke_test: "test-life-sciences-macos.sh",
        isolation_root: ".runtime/macos/life-sciences",
        profiles: {
          scverse: {
            skills: ["single-cell-rna-qc", "scvi-tools", "nextflow-development Python helpers", "clinical-trial-protocol-skill"],
            python: "3.12",
            requirements: "scripts/life-sciences-scverse-requirements.txt",
          },
          allotrope: {
            skills: ["instrument-data-to-allotrope"],
            python: "3.11",
            requirements: "scripts/life-sciences-allotrope-requirements.txt",
            exact_pins: true,
            note: "pandas 2.3.3 satisfies allotropy 0.1.55's declared pandas>=2.2.0 requirement",
          },
          nextflow: {
            skills: ["nextflow-development"],
            openjdk: "17.0.18",
            nextflow: "25.04.8",
            execution: "local process executor; no Docker required for the bundled smoke test",
          },
        },
      },
      skills,
    };
    fs.writeFileSync(path.join(temporaryRoot, "manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
    fs.writeFileSync(path.join(temporaryRoot, "README.md"), `# Anthropic Life Sciences skills

This directory contains seven local, unauthenticated skills. Their macOS dependencies are isolated
under \`.runtime/macos/life-sciences\`; the workflow's main Python and the system Python are not
modified.

Install or reconcile the pinned runtimes:

\`\`\`bash
./setup-life-sciences-macos.sh
\`\`\`

Validate Python imports, skill CLIs, Allotrope exact pins, Java, and a local Nextflow process:

\`\`\`bash
./test-life-sciences-macos.sh
\`\`\`

Use \`.runtime/macos/life-sciences/scverse/bin/python\` for single-cell QC, scvi-tools, the
Nextflow Python helpers, and the clinical sample-size calculator. Use
\`.runtime/macos/life-sciences/allotrope/bin/python\` only for Allotrope conversion. Add
\`.runtime/macos/life-sciences/nextflow/bin\` to \`PATH\` for local Nextflow execution and set
\`JAVA_HOME\` to \`.runtime/macos/life-sciences/nextflow/lib/jvm\`. Full resolved package snapshots are written to
\`.runtime/macos/life-sciences/locks\`.

No account, subscription MCP, or Docker runtime is installed by this setup.
`, "utf8");

    fs.mkdirSync(path.dirname(destinationRoot), { recursive: true });
    fs.rmSync(destinationRoot, { recursive: true, force: true });
    fs.renameSync(temporaryRoot, destinationRoot);
    console.log(`Installed ${skills.length} local skills at ${destinationRoot}`);
  } catch (error) {
    fs.rmSync(temporaryRoot, { recursive: true, force: true });
    throw error;
  }
}

main();
