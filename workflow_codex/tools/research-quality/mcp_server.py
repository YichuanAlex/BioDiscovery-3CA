"""stdio MCP facade for workflow-local research-quality tools."""

import os

from mcp.server.fastmcp import FastMCP

import research_quality
from metabolic_states import analyze_metabolic_states as run_metabolic_states

mcp = FastMCP("research-quality")


def _workspace() -> str:
    value = os.environ.get("RESEARCH_WORKSPACE")
    if not value:
        raise ValueError("RESEARCH_WORKSPACE is required")
    return value


@mcp.tool()
def fetch_reactome_metabolic_genes() -> dict:
    """Build a versioned human metabolic-gene set from Reactome's Metabolism hierarchy."""
    return research_quality.fetch_reactome_metabolic_genes(_workspace())


@mcp.tool()
def search_pubmed(query: str, max_results: int = 20) -> dict:
    """Search PubMed through NCBI E-utilities and cache structured metadata with provenance."""
    return research_quality.search_pubmed(_workspace(), query, max_results)


@mcp.tool()
def verify_doi(doi: str) -> dict:
    """Verify a DOI, publisher DOI URL, or stable 3ca:ID through Crossref and cache exact publication fields."""
    return research_quality.verify_doi(_workspace(), doi)


@mcp.tool()
def inspect_research_table(path: str, key_columns: list[str] | None = None) -> dict:
    """Count rows and unique entity keys in a workspace CSV/TSV before joining or interpreting it."""
    return research_quality.inspect_table(_workspace(), path, key_columns)


@mcp.tool()
def audit_analysis_code(path: str) -> dict:
    """Run Ruff undefined-name checks plus single-cell scientific anti-pattern checks on Python code."""
    return research_quality.audit_analysis_code(_workspace(), path)


@mcp.tool()
def prepare_3ca_dataset(source_path: str, destination: str = "inputs") -> dict:
    """Copy/hash an actual extracted raw-count dataset from the 3CA cache and return exact workspace paths. Reject TPM."""
    return research_quality.prepare_3ca_dataset(_workspace(), source_path, destination)


@mcp.tool()
def analyze_metabolic_states(
    expression_path: str,
    cells_path: str,
    genes_path: str,
    metabolic_genes_path: str,
    cell_id_column: str = "cell_name",
    output_dir: str = "results/core_analysis",
    random_baselines: int = 19,
    subset_field: str | None = None,
    subset_values: list[str] | None = None,
) -> dict:
    """Run the vetted full-cell Scanpy/Leiden metabolic clustering and matched-control analysis."""
    return run_metabolic_states(
        _workspace(), expression_path, cells_path, genes_path, metabolic_genes_path,
        cell_id_column=cell_id_column, output_dir=output_dir, random_baselines=random_baselines,
        subset_field=subset_field, subset_values=subset_values,
    )


@mcp.tool()
def build_research_report(tex_path: str = "report/main.tex", pdf_path: str = "report/main.pdf") -> dict:
    """Compile the exact report target with propagated LaTeX/BibTeX failures."""
    return research_quality.build_report(_workspace(), tex_path, pdf_path)


@mcp.tool()
def validate_research_bundle(manifest_path: str = "results/analysis_manifest.json") -> dict:
    """Validate analysis grain, labels, provenance, figures, references, and report freshness."""
    return research_quality.validate_bundle(_workspace(), manifest_path)


if __name__ == "__main__":
    mcp.run(transport="stdio")
