"""
gnomAD GraphQL API Tool

This tool provides access to the gnomAD (Genome Aggregation Database) for
population genetics data, variant frequencies, and gene constraint metrics using GraphQL.
"""

import requests
from typing import Dict, Any
from .base_tool import BaseTool
from .tool_registry import register_tool
from .graphql_tool import execute_query


class gnomADGraphQLTool(BaseTool):
    """Base class for gnomAD GraphQL API tools."""

    def __init__(self, tool_config):
        super().__init__(tool_config)
        self.endpoint_url = "https://gnomad.broadinstitute.org/api"
        self.query_schema = tool_config.get("query_schema", "")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "ToolUniverse/1.0",
            }
        )
        self.timeout = 30

    def run(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute GraphQL query with given arguments."""
        try:
            result = execute_query(
                endpoint_url=self.endpoint_url,
                query=self.query_schema,
                variables=arguments,
            )

            if result is None:
                return {
                    "status": "error",
                    "error": "No data returned from gnomAD API",
                    "data": None,
                }

            return {"status": "success", "data": result, "url": self.endpoint_url}

        except Exception as e:
            return {
                "status": "error",
                "error": f"gnomAD GraphQL request failed: {str(e)}",
                "data": None,
            }


@register_tool("gnomADGetGeneConstraints")
class gnomADGetGeneConstraints(gnomADGraphQLTool):
    """Get gene constraint metrics from gnomAD."""

    def __init__(self, tool_config):
        super().__init__(tool_config)
        # Set default query schema if not provided in config
        if not self.query_schema:
            self.query_schema = """
query GeneConstraints($geneSymbol: String!) {
  gene(gene_symbol: $geneSymbol, reference_genome: GRCh38) {
    symbol
    gene_id
    exac_constraint {
      exp_lof
      obs_lof
      pLI
      exp_mis
      obs_mis
      exp_syn
      obs_syn
    }
    gnomad_constraint {
      exp_lof
      obs_lof
      oe_lof
      pLI
      exp_mis
      obs_mis
      oe_mis
      exp_syn
      obs_syn
      oe_syn
    }
  }
}
"""

    def run(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get gene constraints."""
        gene_symbol = arguments.get("gene_symbol", "")
        if not gene_symbol:
            return {"status": "error", "error": "gene_symbol is required"}

        # Convert gene_symbol to geneSymbol for GraphQL variable
        graphql_args = {"geneSymbol": gene_symbol}

        result = super().run(graphql_args)

        # Add gene_symbol to result for reference
        if result.get("status") == "success":
            result["gene_symbol"] = gene_symbol

        return result
