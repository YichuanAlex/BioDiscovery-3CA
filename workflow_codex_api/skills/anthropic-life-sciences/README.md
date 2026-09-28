# Anthropic Life Sciences skills

This directory contains seven local, unauthenticated skills. Their macOS dependencies are isolated
under `.runtime/macos/life-sciences`; the workflow's main Python and the system Python are not
modified.

Install or reconcile the pinned runtimes:

```bash
./setup-life-sciences-macos.sh
```

Validate Python imports, skill CLIs, Allotrope exact pins, Java, and a local Nextflow process:

```bash
./test-life-sciences-macos.sh
```

Use `.runtime/macos/life-sciences/scverse/bin/python` for single-cell QC, scvi-tools, the
Nextflow Python helpers, and the clinical sample-size calculator. Use
`.runtime/macos/life-sciences/allotrope/bin/python` only for Allotrope conversion. Add
`.runtime/macos/life-sciences/nextflow/bin` to `PATH` for local Nextflow execution and set
`JAVA_HOME` to `.runtime/macos/life-sciences/nextflow/lib/jvm`. Full resolved package snapshots are written to
`.runtime/macos/life-sciences/locks`.

No account, subscription MCP, or Docker runtime is installed by this setup.
