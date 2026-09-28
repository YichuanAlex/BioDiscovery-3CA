"""
Ensembl REST API Tool

This tool provides access to the Ensembl genome browser database for gene
lookup, sequence retrieval, variant information, and homology data.
"""

import re
import requests
from typing import Dict, Any, Optional
from .base_tool import BaseTool
from .tool_registry import register_tool


class EnsemblRESTTool(BaseTool):
    """Base class for Ensembl REST API tools."""

    def __init__(self, tool_config):
        super().__init__(tool_config)
        self.base_url = "https://rest.ensembl.org"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "ToolUniverse/1.0",
            }
        )
        self.timeout = 30

    def _make_request(
        self, endpoint: str, params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make a request to the Ensembl API."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            return {
                "status": "success",
                "data": data,
                "url": url,
                "content_type": response.headers.get(
                    "content-type", "application/json"
                ),
            }

        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "error": f"Ensembl API request failed: {str(e)}",
                "url": url,
            }

    def run(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given arguments."""
        return self._make_request(self.endpoint, arguments)


@register_tool("EnsemblLookupGene")
class EnsemblLookupGene(EnsemblRESTTool):
    """Lookup gene information by ID or symbol."""

    # Ensembl stable gene IDs look like ENSG00000139618
    _GENE_ID_PATTERN = re.compile(r"^ENS[A-Z]*G[0-9]+$", re.IGNORECASE)

    def __init__(self, tool_config):
        super().__init__(tool_config)
        self.endpoint = "/lookup/id"

    def run(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Lookup gene by ID or symbol."""
        gene_id = arguments.get("gene_id", "")
        if not gene_id:
            return {"status": "error", "error": "gene_id is required"}

        # Route to correct endpoint depending on whether we received a stable ID
        # (e.g., ENSG...) or a gene symbol (e.g., KRAS).
        is_stable_id = bool(self._GENE_ID_PATTERN.match(gene_id))
        if is_stable_id:
            endpoint = f"{self.endpoint}/{gene_id}"
            params = {"expand": 1}
            if "species" in arguments:
                params["species"] = arguments["species"]
        else:
            # Lookup by symbol requires the species in the URL path; default to human
            species = arguments.get("species", "homo_sapiens")
            endpoint = f"/lookup/symbol/{species}/{gene_id}"
            params = {"expand": 1}

        result = self._make_request(endpoint, params)

        # Add gene_id to result for reference
        if result.get("status") == "success":
            result["gene_id"] = gene_id

        return result


@register_tool("EnsemblGetSequence")
class EnsemblGetSequence(EnsemblRESTTool):
    """Get DNA or protein sequences by region or gene ID."""

    def __init__(self, tool_config):
        super().__init__(tool_config)
        self.endpoint = "/sequence/id"

    def run(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get sequence by gene ID or region."""
        sequence_id = arguments.get("sequence_id", "")
        if not sequence_id:
            return {"status": "error", "error": "sequence_id is required"}

        # Ensembl API requires the ID in the URL path
        endpoint = f"{self.endpoint}/{sequence_id}"
        params = {
            "type": arguments.get("type", "genomic"),  # genomic, cds, protein
            "multiple_sequences": "true",
        }

        # Add species if specified
        if "species" in arguments:
            params["species"] = arguments["species"]

        result = self._make_request(endpoint, params)

        # Add sequence_id to result for reference
        if result.get("status") == "success":
            result["sequence_id"] = sequence_id

        return result


@register_tool("EnsemblGetVariants")
class EnsemblGetVariants(EnsemblRESTTool):
    """Get variant information for a genomic region."""

    def __init__(self, tool_config):
        super().__init__(tool_config)
        self.endpoint = "/overlap/id"

    def run(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get variants for a region."""
        region = arguments.get("region", "")
        if not region:
            return {
                "status": "error",
                "error": "region is required (e.g., '1:1000000..2000000')",
            }

        # Ensembl API requires the region in the URL path with species
        species = arguments.get("species", "human")
        endpoint = f"/overlap/region/{species}/{region}"
        params = {"feature": "variation", "content-type": "application/json"}

        result = self._make_request(endpoint, params)

        # Add region to result for reference
        if result.get("status") == "success":
            result["region"] = region

        return result
