import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from pypdf import PdfWriter

import research_quality


class ResearchQualityTest(unittest.TestCase):
    def test_latex_failure_summary_points_to_prior_text_underscore(self):
        with tempfile.TemporaryDirectory() as temporary:
            tex = Path(temporary) / "main.tex"
            tex.write_text("\\documentclass{article}\n\\author{QA_R5 report}\n\\begin{document}\n\\includegraphics{../figures/metabolic_umap.pdf}\n\\maketitle\n\\end{document}\n", encoding="utf-8")
            summary = research_quality._latex_failure_summary(tex, "pdflatex pass 1", 1, "main.tex:5: Missing $ inserted.")
            self.assertIn("Reported diagnostic: main.tex:5: Missing $ inserted.", summary)
            self.assertIn("2: \\author{QA_R5 report}", summary)
            self.assertNotIn("includegraphics", summary.split("Possible unescaped", 1)[1])
            self.assertLess(len(summary), 2000)

    def test_cached_dataset_staging(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            cache = parent / "cache"
            source = cache / "raw.extracted"
            source.mkdir(parents=True)
            root = parent / "workspace"
            root.mkdir()
            (source / "Exp_data_UMIcounts.mtx").write_text("%%MatrixMarket matrix coordinate integer general\n2 3 2\n1 1 2\n2 3 4\n", encoding="ascii")
            (source / "Cells.csv").write_text("cell_name,patient\nc1,p1\nc2,p1\nc3,p2\n", encoding="utf-8")
            (source / "Genes.txt").write_text("A\nA\n", encoding="utf-8")
            with patch.object(research_quality, "THREECA_CACHE", cache):
                staged = research_quality.prepare_3ca_dataset(str(root), str(source))
                self.assertEqual(staged["n_cells"], 3)
                self.assertEqual(staged["duplicate_symbol_rows"], 1)
                self.assertTrue((root / staged["expression_path"]).is_file())
                self.assertEqual(research_quality.prepare_3ca_dataset(str(root), str(source)), staged)
                (root / staged["cells_path"]).write_text("changed", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "overwrite different"):
                    research_quality.prepare_3ca_dataset(str(root), str(source))
                (source / "Exp_data_UMIcounts.mtx").rename(source / "Exp_data_TPM.mtx")
                with self.assertRaisesRegex(ValueError, "not TPM"):
                    research_quality.prepare_3ca_dataset(str(root), str(source))
                with self.assertRaisesRegex(ValueError, "leaves workspace"):
                    research_quality.prepare_3ca_dataset(str(root), str(parent))

    def test_analysis_code_audit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bad = root / "bad.py"
            bad.write_text("import numpy as np\nscore = adjusted_rand_score(labels, np.arange(len(labels)))\n", encoding="utf-8")
            result = research_quality.audit_analysis_code(str(root), "bad.py")
            self.assertFalse(result["valid"])
            self.assertTrue(result["ruff_findings"])
            self.assertTrue(result["scientific_findings"])

    def test_grain_and_bundle_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "results").mkdir()
            (root / "report").mkdir()
            (root / "figures").mkdir()
            (root / "sources" / "literature").mkdir(parents=True)
            (root / "sources" / "genes.txt").write_text("A\nB\n", encoding="utf-8")
            (root / "results" / "labels.csv").write_text("cell_id,cluster\nc1,0\nc2,1\n", encoding="utf-8")
            table = research_quality.inspect_table(str(root), "results/labels.csv", ["cell_id"])
            self.assertTrue(table["grain_valid"])
            (root / "sources" / "literature" / "paper.json").write_text(json.dumps({"source": "Crossref REST API", "doi": "10.1/test"}), encoding="utf-8")
            (root / "report" / "main.tex").write_text(r"\includegraphics{../figures/result.pdf}\cite{paper}", encoding="utf-8")
            for pdf in (root / "figures" / "result.pdf", root / "report" / "main.pdf"):
                writer = PdfWriter()
                writer.add_blank_page(width=72, height=72)
                writer.add_metadata({"/Title": "research report text"})
                with pdf.open("wb") as stream:
                    writer.write(stream)
            (root / "results" / "summary.json").write_text('{"ok":true}', encoding="utf-8")
            manifest = {
                "schema_version": 1,
                "dataset": {"study_id": "3ca:1", "source_url": "https://example.test", "sha256": "a" * 64, "n_cells": 2, "n_genes": 2, "matrix_orientation": "cells_by_genes", "cell_id_field": "cell_id"},
                "feature_set": {"name": "metabolism", "source_url": "https://reactome.org", "retrieved_at": "now", "sha256": research_quality._sha256_file(root / "sources" / "genes.txt"), "genes_path": "sources/genes.txt", "source_gene_count": 2, "matched_gene_count": 2},
                "analysis": {"input_unit": "cell", "rows_analyzed": 2, "unique_cells_analyzed": 2, "random_seeds": [1, 2, 3], "baselines": [{"name": "all genes"}], "confounders_checked": ["patient"], "methods": [{"name": "kmeans", "labels_path": "results/labels.csv", "cell_id_column": "cell_id", "label_column": "cluster", "n_clusters": 2}]},
                "references": [{"key": "paper", "doi": "10.1/test", "metadata_path": "sources/literature/paper.json"}],
                "artifacts": {"tex": "report/main.tex", "pdf": "report/main.pdf", "summary": "results/summary.json", "figures": ["figures/result.pdf"]},
            }
            (root / "results" / "analysis_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            result = research_quality.validate_bundle(str(root))
            self.assertIn("PDF is invalid or a placeholder", result["errors"])
            manifest["analysis"]["unique_cells_analyzed"] = 1
            (root / "results" / "analysis_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            self.assertIn("analysis rows must be one unique row per analyzed cell", research_quality.validate_bundle(str(root))["errors"])


if __name__ == "__main__":
    unittest.main()
