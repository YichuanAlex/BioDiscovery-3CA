import os
import json
import sys
from pathlib import Path

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


EXPECTED = {
    "refresh_catalog",
    "search_studies",
    "get_study",
    "get_page",
    "search_cached_pages",
    "crawl_site",
    "plan_asset",
    "download_asset",
    "inspect_dataset",
    "verify_dataset",
}


async def check() -> None:
    root = Path(__file__).resolve().parent
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(root / "MCP" / "server.py")],
        env={**os.environ, "THREECA_CACHE": str(root.parent.parent / ".threeca" / "cache")},
    )
    async with stdio_client(parameters) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {tool.name for tool in tools.tools}
            assert names == EXPECTED, (names, EXPECTED)
            called = set()

            async def call(name, arguments):
                result = await session.call_tool(name, arguments)
                assert not result.isError, result
                called.add(name)
                return json.loads(result.content[0].text)

            await call("refresh_catalog", {})
            studies = (await call("search_studies", {"asset": "metadata"}))["studies"]
            cache = Path(parameters.env["THREECA_CACHE"])
            manifests = [json.loads(path.read_text(encoding="utf-8")) for path in (cache / "downloads").glob("*/*.manifest.json")]
            cached_urls = {item["source_url"] for item in manifests if Path(item.get("path", "")).is_file()}
            study = next((item for item in studies if item["assets"]["metadata"] in cached_urls), studies[0])
            fetched = await call("get_study", {"study_id": study["id"]})
            assert fetched["publication_verification_call"]["arguments"] == {"doi": study["id"]}, "MCP must use current local source, not a stale installed copy"
            await call("get_page", {"url_or_path": study["category_url"]})
            await call("search_cached_pages", {"query": study["title"], "limit": 1})
            # A one-page engineering call is not a workflow crawl/download limit.
            await call("crawl_site", {"max_pages": 1})
            await call("plan_asset", {"target": study["id"], "kind": "metadata"})
            download = await call("download_asset", {"target": study["id"], "kind": "metadata", "extract": True})
            await call("inspect_dataset", {"path": download["path"]})
            verified = await call("verify_dataset", {"path": download["path"]})
            assert verified["sha256"] == download["sha256"], verified
            assert called == EXPECTED, called
    print("PASS: all 10 tool43CA MCP tools actually called, including live catalog, metadata download/extraction, inspection and SHA-256 verification.")


if __name__ == "__main__":
    anyio.run(check)
