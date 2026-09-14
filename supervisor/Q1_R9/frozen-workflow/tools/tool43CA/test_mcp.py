import os
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
        command=str(root / ".venv" / "Scripts" / "python.exe"),
        args=[str(root / "MCP" / "server.py")],
        env={**os.environ, "THREECA_CACHE": str(root.parent.parent / ".threeca" / "cache")},
    )
    async with stdio_client(parameters) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {tool.name for tool in tools.tools}
            assert names == EXPECTED, (names, EXPECTED)
            result = await session.call_tool("search_cached_pages", {"query": "__mcp_self_test__", "limit": 1})
            assert not result.isError, result
    print("PASS: tool43CA MCP initialized, listed all 10 tools, and completed a tool call.")


if __name__ == "__main__":
    anyio.run(check)
