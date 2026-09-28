$ErrorActionPreference = 'Stop'
$nodePath = Join-Path $PSScriptRoot '.runtime\node-v24.21.0-win-x64\node.exe'
if (-not (Test-Path -LiteralPath $nodePath -PathType Leaf)) { throw 'Project-local Node.js runtime is missing.' }
& $nodePath (Join-Path $PSScriptRoot 'scripts\uninstall-anonymous-http-mcp.mjs')
if ($LASTEXITCODE -ne 0) { throw "Anonymous HTTP MCP uninstaller exited with code $LASTEXITCODE." }
