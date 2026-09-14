# metabolic-scrna-p030-method

## Scientific question

Use this paper record as a benchmark-governance reference; it is not an agent-visible scored discovery task.

## Inputs

- `metabolic_genes_input_v1.csv`: fixed, unsigned user-supplied gene symbols.
- `data_manifest.public.json`: paper-associated public data objects and acquisition routes.

The paper, supplementary figures, author results, and candidate claims are curator-only and must not be mounted in the agent workspace.

## Required submission

- `submission/metrics.json` (JSON)
- `submission/claims.jsonl` (JSONL)
- `submission/provenance.json` (JSON)
- `submission/report.md` (Markdown)

## Hard gates

- gene-symbol and overlap coverage reported
- biological replicate is the inferential unit
- negative-control gene sets included
- batch, library-size, and mitochondrial-quality confounding assessed
- RNA-derived activity is not reported as measured flux
- all required files conform to the output contract

Report negative or inconclusive results when warranted. Cluster labels are arbitrary; evidence must be based on label-invariant comparisons and replicate-aware statistics.
