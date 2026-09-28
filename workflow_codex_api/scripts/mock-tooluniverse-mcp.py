#!/usr/bin/env python3
"""Deterministic JSON-lines MCP fixture for the ToolUniverse adapter smoke test."""

import json
import os
import re
import sys
import time


TOOLS = [
    {
        "name": name,
        "description": f"Mock {name}",
        "inputSchema": {
            "type": "object",
            "properties": {"mode": {"type": "string"}},
            "additionalProperties": True,
        },
    }
    for name in (
        "list_tools",
        "grep_tools",
        "get_tool_info",
        "execute_tool",
        "find_tools",
        "not_compact",
    )
]

if marker := os.environ.get("WINGPT_TOOLUNIVERSE_MOCK_START_LOG"):
    with open(marker, "a", encoding="utf-8") as stream:
        stream.write(f"{os.getpid()}\n")


def send(message: dict) -> None:
    sys.stdout.write(json.dumps(message, separators=(",", ":")) + "\n")
    sys.stdout.flush()


for line in sys.stdin:
    request = json.loads(line)
    request_id = request.get("id")
    method = request.get("method")
    if request_id is None:
        continue
    if method == "initialize":
        result = {
            "protocolVersion": "2025-06-18",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "mock-tooluniverse", "version": "1"},
        }
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        arguments = request.get("params", {}).get("arguments", {})
        mode = arguments.get("mode")
        if mode == "hang":
            time.sleep(10)
        if mode == "large":
            text = "x" * 40000
        elif mode == "environment":
            forbidden = re.compile(
                r"API_KEY|ACCESS_TOKEN|AUTHORIZATION|BEARER|CREDENTIAL|SECRET|PASSWORD|SUBSCRIPTION|ACCOUNT",
                re.IGNORECASE,
            )
            text = json.dumps({"leaked": sorted(key for key in os.environ if forbidden.search(key))})
        else:
            text = json.dumps(request["params"], sort_keys=True)
        result = {"content": [{"type": "text", "text": text}]}
    else:
        send({"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "Method not found"}})
        continue
    send({"jsonrpc": "2.0", "id": request_id, "result": result})
