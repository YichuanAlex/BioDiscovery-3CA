import requests
from .base_tool import BaseTool
from .tool_registry import register_tool


@register_tool("EFOTool")
class EFOTool(BaseTool):
    """
    Tool to lookup Experimental Factor Ontology (EFO) IDs for diseases via the EMBL-EBI OLS API.
    """

    def __init__(self, tool_config, base_url="https://www.ebi.ac.uk/ols4/api/search"):
        super().__init__(tool_config)
        self.base_url = base_url

    def run(self, arguments):
        disease = arguments.get("disease")
        rows = arguments.get("rows", 1)
        if not disease:
            return {"error": "`disease` parameter is required."}
        return self._search(disease, rows)

    def _search(self, disease, rows):
        params = {"ontology": "efo", "q": disease, "rows": rows}
        try:
            response = requests.get(self.base_url, params=params, timeout=20)
            response.raise_for_status()
        except requests.RequestException as e:
            return {"error": "OLS API request failed.", "details": str(e)}

        data = response.json().get("response", {})
        docs = data.get("docs", [])
        if not docs:
            return None

        if rows == 1:
            doc = docs[0]
            return {"efo_id": doc.get("short_form"), "name": doc.get("label")}

        return [
            {"efo_id": doc.get("short_form"), "name": doc.get("label")} for doc in docs
        ]
