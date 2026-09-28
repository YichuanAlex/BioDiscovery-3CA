import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy.io import mmwrite
from pypdf import PdfWriter, PdfReader
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

from metabolic_states import ENGINE, _sha256, _collapse_gene_symbols, analyze_metabolic_states
import research_quality


class MetabolicStatesTest(unittest.TestCase):
    def test_synthetic_full_pipeline(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "data").mkdir()
            (root / "sources").mkdir()
            rng = np.random.default_rng(7)
            cells, genes = 360, 60
            matrix = rng.poisson(0.3, size=(genes, cells))
            matrix[:10, : cells // 2] += rng.poisson(5, size=(10, cells // 2))
            matrix[10:20, cells // 2 :] += rng.poisson(5, size=(10, cells // 2))
            mmwrite(root / "data" / "counts.mtx", sp.csr_matrix(matrix))
            gene_names = [f"G{i}" for i in range(genes)]
            gene_names[-1] = gene_names[0]
            collapsed, symbols, codes = _collapse_gene_symbols(sp.csr_matrix(matrix), gene_names)
            np.testing.assert_array_equal(collapsed[0].toarray().ravel(), matrix[0] + matrix[-1])
            np.testing.assert_array_equal(np.asarray(collapsed.sum(axis=0)).ravel(), matrix.sum(axis=0))
            self.assertEqual((len(symbols), codes[-1]), (genes - 1, 0))
            (root / "data" / "genes.txt").write_text("\n".join(gene_names) + "\n", encoding="utf-8")
            pd.DataFrame(
                {
                    "cell_name": [f"c{i}" for i in range(cells)],
                    "patient": [f"p{i % 3}" for i in range(cells)],
                    "sample": [f"s{i % 6}" for i in range(cells)],
                    "cell_type": ["A" if i < cells // 2 else "B" for i in range(cells)],
                    "complexity": (matrix > 0).sum(axis=0),
                }
            ).to_csv(root / "data" / "cells.csv", index=False)
            pd.DataFrame({"symbol": ["g0", *gene_names[1:20]]}).to_csv(root / "sources" / "metabolic.csv", index=False)
            result = analyze_metabolic_states(
                str(root),
                "data/counts.mtx",
                "data/cells.csv",
                "data/genes.txt",
                "sources/metabolic.csv",
                seeds=[0, 1, 2],
                resolutions=[0.5, 1.0],
                random_baselines=2,
                min_counts=0,
                min_genes=1,
                max_mito_percent=100,
                min_feature_cells=2,
                min_metabolic_genes=10,
                metric_cells=120,
            )
            self.assertEqual(result["engine"], ENGINE)
            labels = pd.read_csv(root / result["labels_path"])
            self.assertEqual(len(labels), cells)
            self.assertEqual(labels["cell_name"].nunique(), cells)
            self.assertGreaterEqual(labels["cluster"].nunique(), 2)
            core = json.loads((root / result["core_result_path"]).read_text(encoding="utf-8"))
            self.assertEqual(core["facts"]["cells_analyzed"], cells)
            self.assertEqual(core["facts"]["source_genes"], genes)
            self.assertEqual(core["facts"]["unique_gene_symbols"], genes - 1)
            self.assertEqual(core["facts"]["duplicate_symbol_rows_aggregated"], 1)
            self.assertTrue((root / core["outputs"]["source_feature_mapping_path"]).is_file())
            self.assertEqual(len(core["outputs"]["figures"]), 2)
            self.assertEqual(core["methods"]["control_partition"]["seed"], 0)
            self.assertIn("HVG", core["facts"]["baseline_silhouette_summary"])
            self.assertEqual(core["facts"]["random_control_comparison"]["random_controls_total"], 2)
            self.assertEqual(core["facts"]["gene_set_audit"]["case_insensitive_unique_matches"], 1)
            self.assertTrue((root / core["outputs"]["gene_set_mapping_path"]).is_file())
            self.assertEqual(core["facts"]["within_replicate_summary"]["replicates_analyzed"], 3)
            self.assertGreaterEqual(core["facts"]["cluster_size_summary"]["minimum_cells"], 1)
            self.assertEqual(core["facts"]["resolution_selection"]["primary_criterion"], "highest median silhouette across seeds")
            for figure in result["figures"]:
                self.assertEqual(Path(figure).suffix, ".pdf")
                self.assertTrue("UMAP" in "".join(page.extract_text() or "" for page in PdfReader(root / figure).pages) or "HVG" in "".join(page.extract_text() or "" for page in PdfReader(root / figure).pages))
            self.assertEqual(core["facts"]["conclusion"], "inconclusive")
            self.assertNotIn("stratified_permutation", core["facts"])
            self.assertTrue((root / "results/core_analysis/within_replicate_sensitivity.csv").is_file())
            within = pd.read_csv(root / "results/core_analysis/within_replicate_sensitivity.csv")
            self.assertEqual(len(within), 3)
            self.assertTrue((within["status"] == "descriptive_only").all())

            global_summary_hash = _sha256(root / "results/summary.json")
            subset_result = analyze_metabolic_states(
                str(root),
                "data/counts.mtx",
                "data/cells.csv",
                "data/genes.txt",
                "sources/metabolic.csv",
                output_dir="results/subset_analysis",
                seeds=[0, 1, 2],
                resolutions=[0.5, 1.0],
                random_baselines=2,
                min_counts=0,
                min_genes=1,
                max_mito_percent=100,
                min_feature_cells=2,
                min_metabolic_genes=10,
                metric_cells=100,
                subset_field="patient",
                subset_values=["p0"],
            )
            self.assertEqual(subset_result["analysis_scope"]["source_cells_selected"], 120)
            self.assertEqual(_sha256(root / "results/summary.json"), global_summary_hash)
            self.assertEqual(subset_result["summary_path"], "results/subset_analysis/summary.json")
            subset_core = json.loads((root / subset_result["core_result_path"]).read_text(encoding="utf-8"))
            self.assertEqual(subset_core["facts"]["source_cells"], cells)
            self.assertEqual(subset_core["facts"]["subset"]["values"], ["p0"])
            self.assertTrue(all(path.startswith("figures/subset_analysis/") for path in subset_result["figures"]))

            report = root / "report"
            report.mkdir()
            tex = report / "main.tex"
            facts = core["facts"]
            comparison = facts["random_control_comparison"]
            within_summary = facts["within_replicate_summary"]
            cluster_sizes = facts["cluster_size_summary"]
            report_text = (
                "\\usepackage{booktabs}\n"
                "\\begin{document}\n"
                "\\begin{figure}\\includegraphics{../figures/metabolic_umap.pdf}\\caption{Metabolic map.}\\label{fig:map}\\end{figure}\n"
                "\\begin{figure}\\includegraphics{../figures/clustering_diagnostics.pdf}\\caption{Diagnostics.}\\label{fig:diagnostics}\\end{figure}\n"
                "Figures \\ref{fig:map} and \\ref{fig:diagnostics} show the results.\n"
                "\\begin{table}\\caption{Metrics.}\\label{tab:metrics}\\begin{tabular}{ll}\\toprule Metric & Value \\\\ \\midrule Cells & 360 \\\\ \\bottomrule\\end{tabular}\\end{table}\n"
                "Table \\ref{tab:metrics} reports the analysis population.\n"
                "\\begin{equation}x'_{ig}=\\log(1+10^4 x_{ig}/\\sum_g x_{ig})\\label{eq:norm}\\end{equation}\n"
                "Equation \\ref{eq:norm} defines normalization, where i indexes cells and g indexes genes.\n"
                "The random-draw seed grid was 0, 1, and 2.\n"
                f"Cluster sizes ranged from {cluster_sizes['minimum_cells']} to {cluster_sizes['maximum_cells']} cells. "
                "Resolution was selected by highest median silhouette after a mean pairwise ARI stability filter, with mean pairwise ARI as tie-breaker. "
                f"{comparison['random_controls_exceeding_or_equal']} of {comparison['random_controls_total']} random controls met or exceeded the metabolic matched-k result; "
                "the add-one rank fraction is descriptive, not a biological P value. "
                f"Within-patient global-vs-within ARI ranged from {within_summary['global_vs_within_ari_min']:.3f} to {within_summary['global_vs_within_ari_max']:.3f}; "
                f"the weakest patient {within_summary['weakest_replicate']} was reported.\\cite{{paper}}\n"
                "\\end{document}\n"
            )
            tex.write_text(report_text, encoding="utf-8")
            writer = PdfWriter()
            page = writer.add_blank_page(width=300, height=300)
            font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
            page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})})
            stream = DecodedStreamObject()
            stream.set_data(b"BT /F1 12 Tf 30 200 Td (Exploratory metabolic-state report) Tj ET")
            page[NameObject("/Contents")] = writer._add_object(stream)
            writer.add_metadata({"/Title": "Synthetic validation " + "x" * 1000})
            with (report / "main.pdf").open("wb") as output:
                writer.write(output)
            (report / "main.log").write_text("Output written on main.pdf (1 page).\n", encoding="utf-8")
            metadata = root / "sources" / "paper.json"
            metadata.write_text(json.dumps({"source": "Crossref REST API", "doi": "10.1/test"}), encoding="utf-8")
            manifest = {
                "schema_version": 1,
                "dataset": {"study_id": "synthetic", "source_url": "https://example.test", "sha256": _sha256(root / "data/counts.mtx"), "expression_path": "data/counts.mtx", "cells_path": "data/cells.csv", "gene_names_path": "data/genes.txt", "n_cells": cells, "n_genes": genes, "matrix_orientation": "genes_by_cells", "cell_id_field": "cell_name"},
                "feature_set": {"name": "synthetic metabolic genes", "source_url": "https://example.test", "retrieved_at": "test", "sha256": _sha256(root / "sources/metabolic.csv"), "genes_path": "sources/metabolic.csv", "matched_genes_path": core["outputs"]["matched_genes_path"], "source_gene_count": 20, "matched_gene_count": 20},
                "analysis": {"engine": ENGINE, "core_result_path": result["core_result_path"], "core_result_sha256": result["core_result_sha256"], "input_unit": "cell", "rows_analyzed": cells, "unique_cells_analyzed": cells, "random_seeds": [0, 1, 2], "baselines": [{"name": "computed controls", "metrics": {"exceedance_fraction": core["facts"]["baseline_exceedance_fraction"]}, "result_path": core["outputs"]["baseline_metrics_path"]}], "confounders_checked": core["facts"]["confounders_checked"], "methods": [{"name": "Leiden", "labels_path": result["labels_path"], "cell_id_column": "cell_name", "label_column": "cluster", "n_clusters": result["n_clusters"], "metrics": core["facts"]["metrics"]}]},
                "references": [{"key": "paper", "doi": "10.1/test", "metadata_path": "sources/paper.json"}],
                "artifacts": {"tex": "report/main.tex", "pdf": "report/main.pdf", "summary": "results/summary.json", "figures": result["figures"]},
            }
            (root / "results/analysis_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            validation = research_quality.validate_bundle(str(root))
            self.assertTrue(validation["valid"], validation["errors"])
            unsafe_claims = {
                "The clustering is not significantly better.": "Report assigns statistical significance without a valid inferential test",
                "The result is worse than random.": "Report turns the random-control rank into a definitive better/worse claim",
                "The grouping is driven by cell type.": "Report makes a causal 'driven by' claim from descriptive association",
                "The states are strongly associated with subtype.": "Report applies an unvalidated qualitative threshold to an association metric",
                "There is no evidence of metabolic clusters.": "Report makes a definitive absence claim although the core conclusion is inconclusive",
                "Metabolic gene clustering is comparable to matched-k KMeans.": "Report directly compares Leiden and KMeans silhouette values as if they test the same claim",
                "Features were scaled with zero-centering.": "Report contradicts core feature scaling: zero_center=False",
                "The states show moderate association with subtype.": "Report applies an unvalidated qualitative threshold to an association metric",
                "The silhouette is comparable to random controls.": "Report applies an unsupported qualitative threshold to random-control or silhouette results",
                "Random controls indicate the states are not reproducible.": "Report turns descriptive random-control results into a definitive biological conclusion",
            }
            for claim, expected_error in unsafe_claims.items():
                tex.write_text(report_text.replace("\\end{document}", claim + "\n\\end{document}"), encoding="utf-8")
                self.assertIn(expected_error, research_quality.validate_bundle(str(root))["errors"])
            tex.write_text(report_text.replace("seed grid was 0, 1, and 2", "seed grid was 17, 42, and 73"), encoding="utf-8")
            self.assertIn("Report must state the actual core seed grid (0, 1, 2) in one seed sentence", research_quality.validate_bundle(str(root))["errors"])
            tex.write_text(report_text.replace(r"\log(1+10^4 x_{ig}/\sum_g x_{ig})", r"\log_1p(10^4 x_{ig}/\sum_g x_{ig})"), encoding="utf-8")
            self.assertIn("Report must typeset log1p as a standard log(1 + x) expression", research_quality.validate_bundle(str(root))["errors"])
            tex.write_text(report_text, encoding="utf-8")
            manifest["analysis"]["subgroup_analyses"] = [{
                "scope": {"field": "patient", "values": ["p0"]},
                "core_result_path": subset_result["core_result_path"],
                "core_result_sha256": subset_result["core_result_sha256"],
            }]
            (root / "results/analysis_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            question_errors = research_quality.validate_bundle(str(root))["errors"]
            for question in (1, 2, 3):
                self.assertIn(f"Report must contain a distinct Question {question} answer section", question_errors)
            self.assertTrue(any(error.startswith("Subgroup 1 report must") for error in question_errors), question_errors)
            del manifest["analysis"]["subgroup_analyses"]
            (root / "results/analysis_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            tex.write_text(
                report_text.replace(
                    f"{comparison['random_controls_exceeding_or_equal']} of {comparison['random_controls_total']} random controls met or exceeded",
                    r"50\% of random controls had silhouette above",
                ),
                encoding="utf-8",
            )
            validation = research_quality.validate_bundle(str(root))
            self.assertIn("Report must not reinterpret the add-one rank fraction as an observed percentage of random controls", validation["errors"])
            tex.write_text(report_text, encoding="utf-8")
            (report / "main.pdf").touch()
            manifest["analysis"]["methods"][0]["metrics"] = {"silhouette": 0.99}
            (root / "results/analysis_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            validation = research_quality.validate_bundle(str(root))
            self.assertFalse(validation["valid"])
            self.assertIn("analysis.methods[0] metrics or cluster count do not match core facts", validation["errors"])
            manifest["analysis"]["methods"][0]["metrics"] = core["facts"]["metrics"]
            (root / "results/analysis_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            labels["cluster"] = 0
            labels.to_csv(root / result["labels_path"], index=False)
            validation = research_quality.validate_bundle(str(root))
            self.assertFalse(validation["valid"])
            self.assertIn("Core result labels_sha256 does not match labels_path", validation["errors"])


if __name__ == "__main__":
    unittest.main()
