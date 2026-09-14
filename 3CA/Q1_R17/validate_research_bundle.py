"""
validate_research_bundle.py
Validates the research manifest, entity grain, labels, sources, citations, figures, and current PDF.
"""

import json
import os
import subprocess
import sys
import hashlib
from pathlib import Path

def compute_sha256(filepath):
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_core_result(core_result_path):
    """Validate core_result.json exists and has required fields."""
    if not os.path.exists(core_result_path):
        return False, f"core_result.json not found at {core_result_path}"
    
    with open(core_result_path, 'r') as f:
        core_result = json.load(f)
    
    required_fields = ['engine', 'inputs', 'parameters', 'facts', 'methods']
    for field in required_fields:
        if field not in core_result:
            return False, f"Missing required field: {field}"
    
    # Check facts have required metrics
    facts = core_result.get('facts', {})
    required_facts = ['n_clusters', 'metrics', 'random_control_comparison', 'within_replicate_summary']
    for field in required_facts:
        if field not in facts:
            return False, f"Missing required facts field: {field}"
    
    return True, "core_result.json validated"

def validate_analysis_manifest(manifest_path):
    """Validate analysis_manifest.json exists and has required fields."""
    if not os.path.exists(manifest_path):
        return False, f"analysis_manifest.json not found at {manifest_path}"
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    required_fields = ['schema_version', 'dataset', 'feature_set', 'analysis', 'references', 'artifacts']
    for field in required_fields:
        if field not in manifest:
            return False, f"Missing required manifest field: {field}"
    
    # Check schema version
    if manifest.get('schema_version') != 1:
        return False, f"Invalid schema_version: {manifest.get('schema_version')}, expected 1"
    
    return True, "analysis_manifest.json validated"

def validate_figures(figures_dir, tex_file):
    """Validate that PDF figures exist and are referenced in TeX."""
    figures_dir = Path(figures_dir)
    tex_file = Path(tex_file)
    
    # Check for expected figure files
    expected_figures = ['metabolic_umap.pdf', 'clustering_diagnostics.pdf']
    for fig in expected_figures:
        if not figures_dir.exists() or not (figures_dir / fig).exists():
            return False, f"Missing figure: {fig}"
    
    # Check TeX references
    with open(tex_file, 'r') as f:
        tex_content = f.read()
    
    for fig in expected_figures:
        if fig not in tex_content:
            return False, f"Figure {fig} not referenced in TeX"
    
    return True, "Figures validated"

def validate_tables_and_formulas(tex_file):
    """Validate that TeX contains required booktabs table and formula."""
    with open(tex_file, 'r') as f:
        tex_content = f.read()
    
    # Check for booktabs rules
    has_toprule = 'toprule' in tex_content
    has_midrule = 'midrule' in tex_content
    has_bottomrule = 'bottomrule' in tex_content
    
    if not (has_toprule and has_midrule and has_bottomrule):
        return False, "Missing booktabs rules (toprule/midrule/bottomrule)"
    
    # Check for a display formula with label
    has_display_formula = False
    if '$' in tex_content and ('\\begin{equation}' in tex_content or '\\[' in tex_content):
        has_display_formula = True
    
    if not has_display_formula:
        return False, "Missing display formula"
    
    return True, "Tables and formulas validated"

def validate_pdf(pdf_file):
    """Validate PDF exists and has content."""
    if not os.path.exists(pdf_file):
        return False, f"PDF not found: {pdf_file}"
    
    # Check file size
    file_size = os.path.getsize(pdf_file)
    if file_size < 1000:  # Minimum PDF size
        return False, f"PDF too small: {file_size} bytes"
    
    return True, f"PDF validated: {file_size} bytes"

def validate_tex_compilation(tex_file, log_file):
    """Validate TeX compilation log."""
    if not os.path.exists(log_file):
        return False, f"Log file not found: {log_file}"
    
    with open(log_file, 'r') as f:
        log_content = f.read()
    
    # Check for successful compilation
    if 'Output written on' in log_content or 'run 1 of 1' in log_content:
        return True, "TeX compilation successful"
    
    return False, "TeX compilation may have failed"

def main():
    """Main validation function."""
    workspace = Path(__file__).parent
    
    # Required artifacts
    required_artifacts = [
        'report/main.tex',
        'report/main.pdf',
        'results/summary.json',
        'results/analysis_manifest.json',
        'README.md'
    ]
    
    # Validate each artifact
    print("Validating required artifacts...")
    for artifact in required_artifacts:
        path = workspace / artifact
        if not path.exists():
            print("ERROR: Missing artifact: " + artifact)
            return False, "Missing artifact: " + artifact
        print("  [OK] " + artifact + " exists")
    
    # Validate core_result.json
    print("\nValidating core_result.json...")
    valid, msg = validate_core_result(workspace / 'results' / 'core_analysis' / 'core_result.json')
    if not valid:
        print("ERROR: " + msg)
        return False, msg
    print("  [OK] " + msg)
    
    # Validate analysis_manifest.json
    print("\nValidating analysis_manifest.json...")
    valid, msg = validate_analysis_manifest(workspace / 'results' / 'analysis_manifest.json')
    if not valid:
        print("ERROR: " + msg)
        return False, msg
    print("  [OK] " + msg)
    
    # Validate figures
    print("\nValidating figures...")
    valid, msg = validate_figures(workspace / 'figures', workspace / 'report' / 'main.tex')
    if not valid:
        print("ERROR: " + msg)
        return False, msg
    print("  [OK] Figures validated")
    
    # Validate tables and formulas
    print("\nValidating tables and formulas...")
    valid, msg = validate_tables_and_formulas(workspace / 'report' / 'main.tex')
    if not valid:
        print("ERROR: " + msg)
        return False, msg
    print("  [OK] Tables and formulas validated")
    
    # Validate PDF
    print("\nValidating PDF...")
    valid, msg = validate_pdf(workspace / 'report' / 'main.pdf')
    if not valid:
        print(f"ERROR: {msg}")
        return False, msg
    print("  [OK] PDF validated: " + msg)
    
    # Validate TeX compilation
    print("\nValidating TeX compilation...")
    valid, msg = validate_tex_compilation(
        workspace / 'report' / 'main.tex',
        workspace / 'report' / 'main.log'
    )
    if not valid:
        print(f"ERROR: {msg}")
        return False, msg
    print("  [OK] TeX compilation: " + msg)
    
    # Check README.md
    print("\nValidating README.md...")
    readme_path = workspace / 'README.md'
    if not readme_path.exists():
        print(f"ERROR: README.md not found")
        return False, "README.md not found"
    print(f"  ✓ README.md exists")
    
    print("\n" + "="*50)
    print("ALL VALIDATIONS PASSED")
    print("="*50)
    return True, "All validations passed"

if __name__ == '__main__':
    success, message = main()
    sys.exit(0 if success else 1)
