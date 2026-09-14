"""Read-only acceptance audit; writes evidence only in the supervisor directory."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.sparse import load_npz

SUP = Path(__file__).resolve().parent
TASK = Path(r"C:\Users\User\Desktop\agentic\3CA\Q1")
REF = Path(r"C:\Users\User\Desktop\3ca\Q1")
summary = json.loads((TASK / "results/summary.json").read_text())
baseline = json.loads((REF / "results/summary.json").read_text())
assert summary == baseline, "Recomputed metrics differ from reference; investigate, never overwrite"
matrix = load_npz(TASK / "data/expression_log2_tpm10.npz")
assert matrix.shape == (23686, 4645) and matrix.nnz == 20564439
assert np.isfinite(matrix.data).all()
assert len(pd.read_csv(TASK / "data/genes.csv")) == matrix.shape[0]
assert len(pd.read_csv(TASK / "data/cells.csv")) == matrix.shape[1]
assert len(pd.read_csv(TASK / "data/samples.csv")) == 19
assignments = pd.read_csv(TASK / "results/tables/cell_assignments.csv")
assert len(assignments) == 4645
tables = sorted((TASK / "results/tables").glob("*.csv"))
assert len(tables) == 9
assert len(pd.read_csv(TASK / "results/tables/matched_random_gene_sets.csv")) == 20
assert len(pd.read_csv(TASK / "results/tables/matched_random_classification.csv")) == 20
files = []
for file in sorted((TASK / "results").rglob("*")):
    if file.is_file():
        files.append({"path": str(file.relative_to(TASK)), "bytes": file.stat().st_size,
                      "sha256": hashlib.sha256(file.read_bytes()).hexdigest()})
for stem in ("figure1_dataset_and_design", "figure2_metabolic_separation", "figure3_robustness_and_interpretation"):
    for extension in ("pdf", "png", "svg", "tiff"):
        assert (TASK / "results/figures" / (stem + "." + extension)).stat().st_size > 1000
record = {"status": "PASS", "scope": "data, computed metrics, table populations/counts, figure files",
          "report_status": "pending separate PDF/content audit", "matrix_shape": list(matrix.shape),
          "nnz": matrix.nnz, "exact_reference_metric_match": True, "files": files}
(SUP / "analysis-audit.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
print("PASS: sparse inputs, computed regression, 20 matched controls, 9 tables, 12 figure exports.")
