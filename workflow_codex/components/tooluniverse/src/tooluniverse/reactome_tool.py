# reactome_graph_tool.py

import requests
import re
from .base_tool import BaseTool
from .tool_registry import register_tool

# Reactome Content Service Base URL
REACTOME_BASE_URL = "https://reactome.org/ContentService"


@register_tool("ReactomeRESTTool")
class ReactomeRESTTool(BaseTool):
    """
    Generic Reactome Content Service REST tool.
    If there is no "fields.extract_path" in config or its value is empty, returns complete JSON;
    Otherwise, drills down according to the "dot-separated path" in extract_path and returns corresponding sub-node.
    """

    def __init__(self, tool_config):
        super().__init__(tool_config)
        self.endpoint_template = tool_config["endpoint"]  # e.g. "/data/pathway/{stId}"
        self.method = tool_config.get("method", "GET").upper()  # Default to GET
        self.param_schema = tool_config["parameter"][
            "properties"
        ]  # Parameter schema (including required)
        self.required_params = tool_config["parameter"].get(
            "required", []
        )  # List of required parameters
        # If config has fields and it contains extract_path, take it. Otherwise None.
        self.extract_path = None
        if "fields" in tool_config and isinstance(tool_config["fields"], dict):
            ep = tool_config["fields"].get("extract_path", None)
            if ep is not None and isinstance(ep, str) and ep.strip() != "":
                # Only effective when extract_path is a non-empty string
                self.extract_path = ep.strip()

    def _build_url(self, arguments: dict) -> str:
        """
        Combines endpoint_template (containing {xxx}) with path parameters from arguments to generate complete URL.
        For example endpoint_template="/data/pathway/{stId}", arguments={"stId":"R-HSA-73817"}
        → Returns "https://reactome.org/ContentService/data/pathway/R-HSA-73817"
        """
        url_path = self.endpoint_template
        # Find all {xxx} placeholders and replace with values from arguments
        for key in re.findall(r"\{([^{}]+)\}", self.endpoint_template):
            if key not in arguments:
                raise ValueError(f"Missing path parameter '{key}'")
            url_path = url_path.replace(f"{{{key}}}", str(arguments[key]))
        return REACTOME_BASE_URL + url_path

    def run(self, arguments: dict):
        # 1. Validate required parameters (check from required_params list)
        for required_param in self.required_params:
            if required_param not in arguments:
                return {"error": f"Parameter '{required_param}' is required."}

        # 2. Build URL, replace {xxx} placeholders
        try:
            url = self._build_url(arguments)
        except ValueError as e:
            return {"error": str(e)}

        # 3. Find remaining arguments besides path parameters as query parameters
        path_keys = re.findall(r"\{([^{}]+)\}", self.endpoint_template)
        query_params = {}
        for k, v in arguments.items():
            if k not in path_keys:
                query_params[k] = v

        # 4. Make HTTP request
        try:
            if self.method == "GET":
                resp = requests.get(url, params=query_params, timeout=10)
            else:
                # If POST support needed in future, can extend here
                resp = requests.post(url, json=query_params, timeout=10)
        except Exception as e:
            return {"error": f"Failed to request Reactome Content Service: {str(e)}"}

        # 5. Check HTTP status code
        if resp.status_code != 200:
            return {
                "error": f"Reactome API returned HTTP {resp.status_code}",
                "detail": resp.text,
            }

        # 6. Parse JSON
        try:
            data = resp.json()
        except ValueError:
            return {
                "error": "Unable to parse Reactome returned JSON.",
                "content": resp.text,
            }

        # 7. If no extract_path in config, return complete JSON
        if not self.extract_path:
            return data

        # 8. Otherwise drill down according to "dot-separated path" in extract_path
        fragment = data
        for part in self.extract_path.split("."):
            if isinstance(fragment, dict) and part in fragment:
                fragment = fragment[part]
            else:
                return {"error": f"Path '{self.extract_path}' not found in JSON."}
        return fragment
