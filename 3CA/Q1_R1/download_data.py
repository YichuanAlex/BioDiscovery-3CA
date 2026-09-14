"""
Download and preprocess Tirosh et al. 2016 melanoma scRNA-seq data.
Uses fixed local sources, verifies SHA256 and size, safely extracts,
applies log2(TPM/10+1) transform to sparse matrix, and saves outputs.
"""

import shutil
import tarfile
import hashlib
import json
import numpy as np
import pandas as pd
from scipy.io import mmread
from scipy.sparse import csr_matrix, save_npz
from pathlib import Path

# Fixed source paths
SOURCE_DATA = Path("C:/Users/User/Desktop/agentic/workflow_codex/.threeca/cache/downloads/2cd2280ff535/Data_Tirosh2016_Skin.tar.gz")
SOURCE_META = Path("C:/Users/User/Desktop/agentic/workflow_codex/.threeca/cache/downloads/5d6c9085d27a/Meta-data_Tirosh2016_Skin.tar.gz")
DATA_DIR = Path("data")
OUTPUT_DIR = Path("data")

def load_manifest(path: Path) -> dict:
    with open(path, "r") as f:
        return json.load(f)

# Expected values
EXPECTED_DATA_SIZE = 234_187_869
EXPECTED_DATA_SHA256 = "9e157aceb5a39add6e04c4d92db7f970bf19413a14a8c87a1262f9424f0818f6"
EXPECTED_META_SIZE = 127_155
EXPECTED_META_SHA256 = "741107ef4ad09cb19b9a22c8af40ce7440e24f18cf1012c2ebb4c03600fede17"

def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def verify_file(path: Path, expected_size: int, expected_sha256: str) -> None:
    actual_size = path.stat().st_size
    actual_sha = sha256_file(path)
    if actual_size != expected_size:
        raise ValueError(f"Size mismatch for {path}: expected {expected_size}, got {actual_size}")
    if actual_sha != expected_sha256:
        raise ValueError(f"SHA256 mismatch for {path}: expected {expected_sha256}, got {actual_sha}")
    print(f"  Verified {path}: size={actual_size}, sha256={actual_sha}")

def safe_extract_tar_gz(tar_path: Path, extract_dir: Path) -> None:
    """Safely extract tar.gz, rejecting member escape and absolute paths."""
    extract_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path, "r:gz") as tar:
        members = tar.getmembers()
        for m in members:
            if not (m.isfile() or m.isdir()):
                raise tarfile.TarError(f'Unsupported archive member: {m.name}')
            # Reject absolute paths first
            if m.name.startswith("/") or m.name.startswith("\\"):
                raise tarfile.TarError(f"Security violation: absolute path member: {m.name}")
            if m.isdir():
                m.name = m.name.rstrip("/")
            # Check for escape: member_resolved must equal extract_resolved or be under it
            member_resolved = (extract_dir / m.name).resolve()
            extract_resolved = extract_dir.resolve()
            if member_resolved != extract_resolved and extract_resolved not in member_resolved.parents:
                raise tarfile.TarError(f"Security violation: member escapes directory: {m.name} -> {member_resolved}")
        tar.extractall(path=extract_dir)
    print(f"  Extracted to {extract_dir}")

def main() -> None:
    print("=" * 60)
    print("Downloading and preprocessing Tirosh et al. 2016 data")
    print("=" * 60)

    # Ensure output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Copy and verify data archive ---
    dest_data = OUTPUT_DIR / "Data_Tirosh2016_Skin.tar.gz"
    if not dest_data.exists():
        shutil.copy2(SOURCE_DATA, dest_data)
        verify_file(dest_data, EXPECTED_DATA_SIZE, EXPECTED_DATA_SHA256)
    else:
        verify_file(dest_data, EXPECTED_DATA_SIZE, EXPECTED_DATA_SHA256)
    safe_extract_tar_gz(dest_data, OUTPUT_DIR)
    data_extract = OUTPUT_DIR / "Data_Tirosh2016_Skin"

    # --- Copy and verify metadata archive ---
    dest_meta = OUTPUT_DIR / "Meta-data_Tirosh2016_Skin.tar.gz"
    if not dest_meta.exists():
        shutil.copy2(SOURCE_META, dest_meta)
        verify_file(dest_meta, EXPECTED_META_SIZE, EXPECTED_META_SHA256)
    else:
        verify_file(dest_meta, EXPECTED_META_SIZE, EXPECTED_META_SHA256)
    safe_extract_tar_gz(dest_meta, OUTPUT_DIR)
    meta_extract = OUTPUT_DIR / "Meta-data_Tirosh2016_Skin"

    # --- Load expression matrix ---
    mtx_path = data_extract / "Exp_data_TPM.mtx"
    genes_path = data_extract / "Genes.txt"
    cells_path = data_extract / "Cells.csv"
    samples_path = data_extract / "Samples.csv"

    matrix = mmread(mtx_path)
    genes = pd.read_csv(genes_path, sep="\t", header=None, names=["gene"]).iloc[:, 0].tolist()
    cells_df = pd.read_csv(cells_path)
    samples_df = pd.read_csv(samples_path)

    print(f"Matrix shape: {matrix.shape[0]} genes x {matrix.shape[1]} cells")
    print(f"Non-zero entries: {matrix.nnz}")

    # --- Convert to CSR float32 and apply log2(TPM/10+1) ---
    matrix_csr = matrix.tocsr().astype(np.float32)
    # Only transform the data attribute, not the full matrix
    matrix_csr.data = np.log2(matrix_csr.data / 10.0 + 1.0)

    # --- Save expression matrix as npz ---
    npz_path = OUTPUT_DIR / "expression_log2_tpm10.npz"
    save_npz(npz_path, matrix_csr)
    print(f"Saved expression_log2_tpm10.npz: {npz_path}")

    # --- Save CSV files ---
    genes_csv = OUTPUT_DIR / "genes.csv"
    cells_csv = OUTPUT_DIR / "cells.csv"
    samples_csv = OUTPUT_DIR / "samples.csv"
    genes_df = pd.DataFrame(genes, columns=["gene"])
    genes_df.to_csv(genes_csv, index=False)
    cells_df.to_csv(cells_csv, index=False)
    samples_df.to_csv(samples_csv, index=False)
    print(f"Saved genes.csv, cells.csv, samples.csv")

    # --- Generate source manifest ---
    data_manifest = load_manifest(OUTPUT_DIR / "3ca-expression.manifest.json")
    meta_manifest = load_manifest(OUTPUT_DIR / "3ca-metadata.manifest.json")
    manifest = {
        "sources": [
            {
                "url": data_manifest["source_url"],
                "download_time": data_manifest["downloaded_at"],
                "source_path": str(dest_data),
                "size": dest_data.stat().st_size,
                "sha256": sha256_file(dest_data),
                "matrix_shape": [matrix.shape[0], matrix.shape[1]],
                "nnz": int(matrix.nnz)
            },
            {
                "url": meta_manifest["source_url"],
                "download_time": meta_manifest["downloaded_at"],
                "source_path": str(dest_meta),
                "size": dest_meta.stat().st_size,
                "sha256": sha256_file(dest_meta),
                "matrix_shape": None,
                "nnz": None
            }
        ]
    }
    manifest_path = OUTPUT_DIR / "source_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Saved source_manifest.json: {manifest_path}")

    print("\nDone!")

if __name__ == "__main__":
    main()
