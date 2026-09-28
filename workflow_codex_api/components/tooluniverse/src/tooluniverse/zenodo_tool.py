import requests
from .base_tool import BaseTool
from .tool_registry import register_tool


@register_tool("ZenodoTool")
class ZenodoTool(BaseTool):
    """
    Search Zenodo records with optional community filter.

    Parameters (arguments):
        query (str): Free text query
        max_results (int): Max results (default 10, max 200)
        community (str): Optional community slug to filter
    """

    def __init__(self, tool_config):
        super().__init__(tool_config)
        self.base_url = "https://zenodo.org/api/records"

    def run(self, arguments=None):
        arguments = arguments or {}
        query = arguments.get("query")
        max_results = int(arguments.get("max_results", 10))
        community = arguments.get("community")

        if not query:
            return {"error": "`query` parameter is required."}

        params = {
            "q": query,
            "size": max(1, min(max_results, 200)),
            "all_versions": 1,
        }
        # Only add communities filter if community is provided and not empty
        if community and community.strip():
            params["communities"] = community

        try:
            resp = requests.get(self.base_url, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            return {
                "error": "Network/API error calling Zenodo",
                "reason": str(e),
            }
        except ValueError:
            return {"error": "Failed to decode Zenodo response as JSON"}

        hits = data.get("hits", {}).get("hits", [])
        results = []
        for h in hits:
            md = h.get("metadata", {})
            title = md.get("title")
            creators = [c.get("name") for c in md.get("creators", []) if c.get("name")]
            publication_date = md.get("publication_date")
            doi = md.get("doi") or h.get("doi")
            url = h.get("links", {}).get("html")
            files = h.get("files", []) or h.get("links", {}).get("latest")
            results.append(
                {
                    "title": title,
                    "authors": creators,
                    "date": publication_date,
                    "doi": doi,
                    "url": url,
                    "files": files,
                    "source": "Zenodo",
                }
            )

        return results
