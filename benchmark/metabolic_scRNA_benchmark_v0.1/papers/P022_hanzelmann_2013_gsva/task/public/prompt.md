# metabolic-scrna-p022-q1

## Scientific question

Using only the provided fixed metabolic-gene set as expression features after documented symbol and coverage QC, determine whether the cells contain distinct, reproducible transcriptional metabolic states. Compare against expression-matched random gene sets and a full-transcriptome representation; quantify stability across seeds and biological-replicate bootstraps, and test transfer to held-out patients or samples.

## Inputs

- `metabolic_genes_input_v1.csv`: fixed, unsigned user-supplied gene symbols.
- `data_manifest.public.json`: paper-associated public data objects and acquisition routes.

The paper, supplementary figures, author results, and candidate claims are curator-only and must not be mounted in the agent workspace.

## Required submission

- `submission/cluster_assignments.tsv` (TSV)
- `submission/state_summary.tsv` (TSV)
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
