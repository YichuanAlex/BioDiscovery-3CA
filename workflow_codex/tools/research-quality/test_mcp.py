import os
import json
import tempfile
from pathlib import Path

import anyio
import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy.io import mmwrite
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

EXPECTED = {"fetch_reactome_metabolic_genes", "search_pubmed", "verify_doi", "inspect_research_table", "audit_analysis_code", "prepare_3ca_dataset", "analyze_metabolic_states", "build_research_report", "validate_research_bundle"}


async def check() -> None:
    root = Path(__file__).resolve().parent
    cache = root.parents[1] / ".threeca" / "cache"
    with tempfile.TemporaryDirectory() as workspace, tempfile.TemporaryDirectory(dir=cache) as cached_source:
        table = Path(workspace) / "table.csv"
        table.write_text("cell_id,value\nc1,1\nc1,2\n", encoding="utf-8")
        (Path(workspace) / "valid.py").write_text("x = 1\nprint(x)\n", encoding="utf-8")
        source = Path(cached_source)
        rng = np.random.default_rng(21)
        counts = rng.poisson(3, size=(240, 120))
        counts[:20, :60] += rng.poisson(10, size=(20, 60))
        counts[20:40, 60:] += rng.poisson(10, size=(20, 60))
        mmwrite(source / "Exp_data_UMIcounts.mtx", sp.csr_matrix(counts))
        (source / "Genes.txt").write_text("\n".join(f"G{i}" for i in range(240)) + "\n", encoding="utf-8")
        pd.DataFrame({"cell_name": [f"c{i}" for i in range(120)], "patient": [f"p{i % 2}" for i in range(120)], "cell_type": ["A" if i < 60 else "B" for i in range(120)]}).to_csv(source / "Cells.csv", index=False)
        (Path(workspace) / "synthetic_metabolic.txt").write_text("\n".join(f"G{i}" for i in range(40)) + "\n", encoding="utf-8")
        (Path(workspace) / "report").mkdir()
        (Path(workspace) / "report" / "main.tex").write_text("\\documentclass{article}\n\\begin{document}\nResearch tool build check.\n\\end{document}\n", encoding="utf-8")
        (Path(workspace) / "invalid_manifest.json").write_text('{"schema_version":1}', encoding="utf-8")
        parameters = StdioServerParameters(
            command=str(root.parent / "tool43CA" / ".venv" / "Scripts" / "python.exe"),
            args=[str(root / "mcp_server.py")],
            env={**os.environ, "RESEARCH_WORKSPACE": workspace, "PYTHONPATH": str(root)},
        )
        async with stdio_client(parameters) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                tools = await session.list_tools()
                assert {tool.name for tool in tools.tools} == EXPECTED
                result = await session.call_tool("inspect_research_table", {"path": "table.csv", "key_columns": ["cell_id"]})
                assert not result.isError, result
                result = await session.call_tool("audit_analysis_code", {"path": "valid.py"})
                assert not result.isError, result
                result = await session.call_tool("prepare_3ca_dataset", {"source_path": workspace})
                assert result.isError, "Staging must reject sources outside the workflow cache"
                result = await session.call_tool("prepare_3ca_dataset", {"source_path": cached_source})
                assert not result.isError, result
                staged = json.loads(result.content[0].text)
                result = await session.call_tool("analyze_metabolic_states", {"expression_path": staged["expression_path"], "cells_path": staged["cells_path"], "genes_path": staged["genes_path"], "metabolic_genes_path": "synthetic_metabolic.txt"})
                assert not result.isError, result
                analyzed = json.loads(result.content[0].text)
                assert analyzed["cells_analyzed"] == 120 and analyzed["n_clusters"] >= 2, analyzed
                result = await session.call_tool("build_research_report", {})
                assert not result.isError and json.loads(result.content[0].text)["valid"], result
                result = await session.call_tool("validate_research_bundle", {"manifest_path": "invalid_manifest.json"})
                assert not result.isError and not json.loads(result.content[0].text)["valid"], result
                for name, arguments in [("fetch_reactome_metabolic_genes", {}), ("search_pubmed", {"query": "single cell metabolism", "max_results": 1}), ("verify_doi", {"doi": "10.1038/s41586-020-2649-2"})]:
                    result = await session.call_tool(name, arguments)
                    assert not result.isError, result
                result = await session.call_tool("verify_doi", {"doi": "3ca:20773"})
                assert not result.isError, result
                publication = json.loads(result.content[0].text)
                assert publication["doi"] == "10.1038/s41588-022-01061-8" and publication["container_title"] == ["Nature Genetics"], publication
    print("PASS: all nine research-quality MCP tools actually called; synthetic analysis, native report build, staging/bundle boundaries and live APIs passed.")


if __name__ == "__main__":
    anyio.run(check)
