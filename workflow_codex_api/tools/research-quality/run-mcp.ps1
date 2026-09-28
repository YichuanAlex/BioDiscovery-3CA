param([Parameter(Mandatory = $true)][string]$Workspace)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$env:RESEARCH_WORKSPACE = [IO.Path]::GetFullPath($Workspace)
$env:PYTHONPATH = $PSScriptRoot
& (Join-Path $root 'tools\tool43CA\.venv\Scripts\python.exe') (Join-Path $PSScriptRoot 'mcp_server.py')
if ($LASTEXITCODE -ne 0) { throw "research-quality MCP exited with code $LASTEXITCODE." }
