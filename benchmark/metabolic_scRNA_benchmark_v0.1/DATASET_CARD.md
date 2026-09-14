# Metabolic scRNA-seq Benchmark v0.1 - curation release

This repository instantiates the first-stage rules for the question: can a fixed metabolic-gene list reveal reproducible transcriptional metabolic states across all cells, across cell types, and within CD8+ T cells?

## What is complete

- 30 deduplicated, DOI-identified paper records selected for direct biology, metabolic inference, gene-set scoring, single-cell integration, statistics, and benchmark governance.
- One clean paper folder per record with `origin`, `metadata`, `data`, `task/public`, `curation`, and `provenance`.
- Lawful PMC/Europe PMC/official-publisher/local-user retrieval attempts with SI enabled and typed failures; 30/30 papers have local main text and 16/30 have supporting information.
- Frozen user input gene set: 1988 unique symbols. Current HGNC/MGI audit infers 1555 mouse-only candidates and leaves 82 unresolved; the 1719-symbol human-mapped file is a candidate, not a silent replacement.
- Separate private root at `C:\Users\User\Desktop\agentic\dataset\metabolic_scRNA_benchmark_v0.1_private` containing only draft, non-scoreable claim/rubric records.

## What is deliberately not claimed

This is a curation release, not a leaderboard release. No task is scoreable until public omics inputs are materialized and checksummed, candidate claims are independently reproduced, sensitivities and negative controls are run, graders are adversarially tested, and a domain plus computational curator sign off. The build does not invent missing PDFs, supplement files, licences, accessions, or gold numbers.

## Runtime boundary

For an agent run, mount only `papers/<paper>/task/public`, the chosen immutable data snapshot, and an explicitly curator-approved gene-set version. Never mount `origin`, `curation`, or the separate private root.

## Acceptance report

See `构建与验收报告.md` for file-level QA, gene-species validation, release boundaries, and the next promotion gate.

## Paper inventory

| ID | Tier | Axis | Role | Paper | Origin status |
|---|---:|---|---|---|---|
| P001 | A | Q1 | direct_biological_benchmark | Hallmarks of transcriptional intratumour heterogeneity across a thousand tumours | downloaded_with_si |
| P002 | A | Q1 | direct_biological_benchmark | Metabolic landscape of the tumor microenvironment at single cell resolution | downloaded_with_si |
| P003 | A | Q3 | direct_biological_benchmark | Pan-cancer T cell atlas links a cellular stress response state to immunotherapy resistance | downloaded_with_si |
| P004 | A | Q3 | direct_biological_benchmark | Pan-cancer single-cell landscape of tumor-infiltrating T cells | full_text_available_si_not_found |
| P005 | A | Q3 | direct_biological_benchmark | Landscape of Infiltrating T Cells in Liver Cancer Revealed by Single-Cell Sequencing | full_text_available_si_not_found |
| P006 | B | Q3 | direct_biological_benchmark | A transcriptionally and functionally distinct PD-1+ CD8+ T cell pool with predictive potential in non-small-cell lung cancer treated with PD-1 blockade | downloaded_with_si |
| P007 | A | Q2 | direct_biological_benchmark | A Cancer Cell Program Promotes T Cell Exclusion and Resistance to Checkpoint Blockade | full_text_available_si_not_found |
| P008 | A | Q3 | direct_biological_benchmark | A functional single-cell metabolic survey identifies Elovl1 as a target to enhance CD8+ T cell fitness in solid tumours | downloaded_with_si |
| P009 | B | Q2 | direct_biological_benchmark | Spatiotemporal Immune Landscape of Colorectal Cancer Liver Metastasis at Single-Cell Level | full_text_available_si_not_found |
| P010 | A | Q2 | direct_biological_benchmark | A pan-cancer blueprint of the heterogeneous tumor microenvironment revealed by single-cell profiling | downloaded_with_si |
| P011 | A | Q3 | direct_biological_benchmark | Single-cell CRISPR screens in vivo map T cell fate regulomes in cancer | downloaded_with_si |
| P012 | B | Q3 | orthogonal_biological_validation | pH sensing controls tissue inflammation by modulating cellular metabolism and endo-lysosomal function of immune cells | downloaded_with_si |
| P013 | A | Q1 | metabolic_inference_method | Metabolic modeling of single Th17 cells reveals regulators of autoimmunity | full_text_available_si_not_found |
| P014 | A | Q1 | metabolic_inference_method | A graph neural network model to estimate cell-wise metabolic flux using single-cell RNA-seq data | full_text_available_si_not_found |
| P015 | A | Q2 | metabolic_inference_method | Characterizing cancer metabolism from bulk and single-cell RNA-seq data using METAFlux | downloaded_with_si |
| P016 | A | Q1 | metabolic_inference_method | Integration of single-cell RNA-seq data into population models to characterize cancer metabolism | downloaded_with_si |
| P017 | C | Q2 | orthogonal_biological_validation | Met-Flow, a strategy for single-cell metabolic analysis highlights dynamic changes in immune subpopulations | downloaded_with_si |
| P018 | B | Q2 | metabolic_communication_method | MEBOCOST maps metabolite-mediated intercellular communications using single-cell RNA-seq | full_text_available_si_not_found |
| P019 | A | Q1 | gene_set_scoring_method | Functional interpretation of single cell similarity maps | downloaded_with_si |
| P020 | A | Q1 | gene_set_scoring_method | UCell: Robust and scalable single-cell gene signature scoring | full_text_available_si_not_found |
| P021 | A | Q1 | gene_set_scoring_method | UCell and pyUCell: single-cell gene signature scoring for R and Python | full_text_available_si_not_found |
| P022 | A | Q1 | gene_set_scoring_method | GSVA: gene set variation analysis for microarray and RNA-Seq data | full_text_available_si_not_found |
| P023 | A | Q1 | gene_set_scoring_method | decoupleR: ensemble of computational methods to infer biological activities from omics data | full_text_available_si_not_found |
| P024 | A | Q1 | method_benchmark | Benchmarking algorithms for pathway activity transformation of single-cell RNA-seq data | full_text_available_si_not_found |
| P025 | A | Q1 | method_benchmark | Robustness and applicability of transcription factor and pathway analysis tools on single-cell RNA-seq data | full_text_available_si_not_found |
| P026 | A | Q1 | gene_set_scoring_method | Inferring pathway activity from single-cell and spatial transcriptomics data with PaaSc | downloaded_with_si |
| P027 | A | Q2 | quality_control_benchmark | Benchmarking atlas-level data integration in single-cell genomics | downloaded_with_si |
| P028 | A | Q3 | statistical_guardrail | Confronting false discoveries in single-cell differential expression | downloaded_with_si |
| P029 | A | Q2 | statistical_guardrail | A practical solution to pseudoreplication bias in single-cell studies | downloaded_with_si |
| P030 | C | METHOD | benchmark_governance_reference | The current landscape and emerging challenges of benchmarking single-cell methods | full_text_available_si_not_found |

## Next release gate

Promote the smallest executable pilot first: P001/P002 for metabolic-state clustering, P003/P004 for within-CD8 states, P014/P015 for alternative metabolic inference, and P028/P029 as statistical hard-gate tasks. Resolve the 82 unmapped gene symbols and materialize exact public matrices before any task is labelled scoreable.

## Licence and access

Each paper and upstream dataset retains its own licence. Local copies are for user-authorized research curation. Redistribution is false by default until an object-level licence audit records otherwise. Controlled EGA objects remain pointers and must never enter the public release.
