import json
from typing import Any, Dict
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from tooluniverse.tool_registry import register_tool
from tooluniverse.exceptions import (
    ToolError,
    ToolAuthError,
    ToolRateLimitError,
    ToolUnavailableError,
    ToolValidationError,
    ToolConfigError,
    ToolDependencyError,
    ToolServerError,
)


def _http_get(
    url: str,
    headers: Dict[str, str] | None = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    req = Request(url, headers=headers or {})
    try:
        with urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            try:
                return json.loads(data.decode("utf-8", errors="ignore"))
            except Exception:
                return {"raw": data.decode("utf-8", errors="ignore")}
    except HTTPError as e:
        # ENCODE API may return 404 even with valid JSON data
        # Read the response body from the error
        try:
            data = e.read()
            parsed = json.loads(data.decode("utf-8", errors="ignore"))
            # If we got valid JSON, return it even though status was 404
            return parsed
        except Exception:
            # If we can't parse, re-raise the original error
            raise


@register_tool(
    "ENCODESearchTool",
    config={
        "name": "ENCODE_search_experiments",
        "type": "ENCODESearchTool",
        "description": "Search ENCODE experiments",
        "parameter": {
            "type": "object",
            "properties": {
                "assay_title": {"type": "string"},
                "target": {"type": "string"},
                "organism": {"type": "string"},
                "status": {"type": "string", "default": "released"},
                "limit": {"type": "integer", "default": 10},
            },
        },
        "settings": {"base_url": "https://www.encodeproject.org", "timeout": 30},
    },
)
class ENCODESearchTool:
    def __init__(self, tool_config=None):
        self.tool_config = tool_config or {}

    def handle_error(self, exception: Exception) -> ToolError:
        """Classify exceptions into structured ToolError."""
        error_str = str(exception).lower()
        if any(
            kw in error_str
            for kw in ["auth", "unauthorized", "401", "403", "api key", "token"]
        ):
            return ToolAuthError(f"Authentication failed: {exception}")
        elif any(
            kw in error_str for kw in ["rate limit", "429", "quota", "limit exceeded"]
        ):
            return ToolRateLimitError(f"Rate limit exceeded: {exception}")
        elif any(
            kw in error_str
            for kw in [
                "unavailable",
                "timeout",
                "connection",
                "network",
                "not found",
                "404",
            ]
        ):
            return ToolUnavailableError(f"Tool unavailable: {exception}")
        elif any(
            kw in error_str for kw in ["validation", "invalid", "schema", "parameter"]
        ):
            return ToolValidationError(f"Validation error: {exception}")
        elif any(kw in error_str for kw in ["config", "configuration", "setup"]):
            return ToolConfigError(f"Configuration error: {exception}")
        elif any(
            kw in error_str for kw in ["import", "module", "dependency", "package"]
        ):
            return ToolDependencyError(f"Dependency error: {exception}")
        else:
            return ToolServerError(f"Unexpected error: {exception}")

    def run(self, arguments: Dict[str, Any]):
        # Read from fields.endpoint or settings.base_url
        fields = self.tool_config.get("fields", {})
        settings = self.tool_config.get("settings", {})
        endpoint = fields.get(
            "endpoint",
            settings.get("base_url", "https://www.encodeproject.org/search/"),
        )
        # Extract base URL if endpoint includes /search/
        if endpoint.endswith("/search/"):
            base = endpoint[:-7]  # Remove "/search/"
        else:
            base = endpoint.rstrip("/")
        timeout = int(settings.get("timeout", 30))

        query: Dict[str, Any] = {"type": "Experiment", "format": "json"}
        for key in ("assay_title", "target", "organism", "status", "limit"):
            if arguments.get(key) is not None:
                query[key] = arguments[key]

        # ENCODE API expects specific parameter format
        # Build URL with proper query string
        url = f"{base}/search/?{urlencode(query, doseq=True)}"
        try:
            data = _http_get(
                url, headers={"Accept": "application/json"}, timeout=timeout
            )
            return {
                "source": "ENCODE",
                "endpoint": "search",
                "query": query,
                "data": data,
                "success": True,
            }
        except Exception as e:
            return {
                "error": str(e),
                "source": "ENCODE",
                "endpoint": "search",
                "success": False,
            }


@register_tool(
    "ENCODEFilesTool",
    config={
        "name": "ENCODE_list_files",
        "type": "ENCODEFilesTool",
        "description": "List ENCODE files",
        "parameter": {
            "type": "object",
            "properties": {
                "file_type": {"type": "string"},
                "assay_title": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
            },
        },
        "settings": {"base_url": "https://www.encodeproject.org", "timeout": 30},
    },
)
class ENCODEFilesTool:
    def __init__(self, tool_config=None):
        self.tool_config = tool_config or {}

    def handle_error(self, exception: Exception) -> ToolError:
        """Classify exceptions into structured ToolError."""
        error_str = str(exception).lower()
        if any(
            kw in error_str
            for kw in ["auth", "unauthorized", "401", "403", "api key", "token"]
        ):
            return ToolAuthError(f"Authentication failed: {exception}")
        elif any(
            kw in error_str for kw in ["rate limit", "429", "quota", "limit exceeded"]
        ):
            return ToolRateLimitError(f"Rate limit exceeded: {exception}")
        elif any(
            kw in error_str
            for kw in [
                "unavailable",
                "timeout",
                "connection",
                "network",
                "not found",
                "404",
            ]
        ):
            return ToolUnavailableError(f"Tool unavailable: {exception}")
        elif any(
            kw in error_str for kw in ["validation", "invalid", "schema", "parameter"]
        ):
            return ToolValidationError(f"Validation error: {exception}")
        elif any(kw in error_str for kw in ["config", "configuration", "setup"]):
            return ToolConfigError(f"Configuration error: {exception}")
        elif any(
            kw in error_str for kw in ["import", "module", "dependency", "package"]
        ):
            return ToolDependencyError(f"Dependency error: {exception}")
        else:
            return ToolServerError(f"Unexpected error: {exception}")

    def run(self, arguments: Dict[str, Any]):
        # Read from fields.endpoint or settings.base_url
        fields = self.tool_config.get("fields", {})
        settings = self.tool_config.get("settings", {})
        endpoint = fields.get(
            "endpoint",
            settings.get("base_url", "https://www.encodeproject.org/search/"),
        )
        # Extract base URL if endpoint includes /search/
        if endpoint.endswith("/search/"):
            base = endpoint[:-7]  # Remove "/search/"
        else:
            base = endpoint.rstrip("/")
        timeout = int(settings.get("timeout", 30))

        query: Dict[str, Any] = {"type": "File", "format": "json"}
        for key in ("file_type", "assay_title", "limit"):
            if arguments.get(key):
                query[key] = arguments[key]

        url = f"{base}/search/?{urlencode(query)}"
        try:
            data = _http_get(
                url, headers={"Accept": "application/json"}, timeout=timeout
            )
            return {
                "source": "ENCODE",
                "endpoint": "search",
                "query": query,
                "data": data,
                "success": True,
            }
        except Exception as e:
            return {
                "error": str(e),
                "source": "ENCODE",
                "endpoint": "search",
                "success": False,
            }
