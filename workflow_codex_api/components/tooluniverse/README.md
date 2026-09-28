# ToolUniverse MCP Server (Pattern 2: Native uv with Bundled Source)

This bundle demonstrates **Pattern 2** - the RECOMMENDED approach for Python MCPBs.

## Pattern 2 vs Pattern 3 Comparison

| Aspect | Pattern 2 (This Bundle) | Pattern 3 (v7 Bundle) |
|--------|------------------------|----------------------|
| **Source Location** | Bundled in `src/` | Fetched from PyPI |
| **pyproject.toml** | Lists direct dependencies | Lists `tooluniverse>=1.0.14` |
| **manifest args** | `--directory ${__dirname}` | `-m tooluniverse_mcp.cli` |
| **Bundle Size** | ~14MB (includes source) | ~228KB (thin wrapper) |
| **PyPI Required** | No | Yes |
| **Self-contained** | Yes | No (requires PyPI) |

## How It Works

1. Claude Desktop runs: `uv run --directory ${__dirname} --python 3.12 python -m tooluniverse.smcp_server`
2. uv reads `pyproject.toml` in the bundle directory
3. uv installs dependencies (first run: ~200MB download, then cached)
4. Python runs the bundled source code from `src/tooluniverse/`

## Key Manifest Difference

**Pattern 2 (RECOMMENDED):**
```json
"args": [
    "run",
    "--directory", "${__dirname}",
    "--python", "3.12",
    "python", "-m", "tooluniverse.smcp_server"
]
```

**Pattern 3 (Alternative):**
```json
"args": [
    "run",
    "--python", "3.12",
    "python", "-m", "tooluniverse_mcp.cli"
]
```

## When to Use Each Pattern

- **Pattern 2** (this bundle): When you control the source and don't want PyPI dependency
- **Pattern 3** (v7): When a PyPI package already exists and you want smaller bundles

## Requirements

- uv must be installed (Claude Desktop provides this)
- Python 3.10-3.13 (pinned to 3.12 for onnxruntime compatibility)
- First run downloads ~200MB of dependencies
