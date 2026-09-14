[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$sourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$agentsRoot = 'C:\Users\User\.agents'
$mcpRoot = Join-Path $agentsRoot 'mcp\threeca'
$skillRoot = Join-Path $agentsRoot 'skills\threeca-access'
$binRoot = Join-Path $agentsRoot 'bin'
$venvPython = Join-Path $mcpRoot '.venv\Scripts\python.exe'

New-Item -ItemType Directory -Force -Path $mcpRoot, $skillRoot, (Join-Path $skillRoot 'agents'), (Join-Path $skillRoot 'references'), $binRoot | Out-Null

if (-not (Test-Path -LiteralPath $venvPython)) {
    py -3 -m venv (Join-Path $mcpRoot '.venv')
}

& $venvPython -m pip install --quiet --disable-pip-version-check -r (Join-Path $sourceRoot 'MCP\requirements.txt')
& $venvPython -m pip install --quiet --disable-pip-version-check --force-reinstall --no-deps (Join-Path $sourceRoot 'CLI')
$generatedPaths = @(
    (Join-Path $sourceRoot 'CLI\build'),
    (Join-Path $sourceRoot 'CLI\src\threeca_access.egg-info'),
    (Join-Path $sourceRoot 'CLI\src\__pycache__'),
    (Join-Path $sourceRoot 'MCP\__pycache__')
)
foreach ($generatedPath in $generatedPaths) {
    $fullPath = [IO.Path]::GetFullPath($generatedPath)
    $allowedRoot = [IO.Path]::GetFullPath((Join-Path $sourceRoot ''))
    if (-not $fullPath.StartsWith($allowedRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to clean generated path outside source root: $fullPath"
    }
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue -LiteralPath $fullPath
}
Copy-Item -Force -LiteralPath (Join-Path $sourceRoot 'MCP\server.py') -Destination (Join-Path $mcpRoot 'server.py')
Copy-Item -Force -LiteralPath (Join-Path $mcpRoot '.venv\Scripts\threeca.exe') -Destination (Join-Path $binRoot 'threeca.exe')
Remove-Item -Force -ErrorAction SilentlyContinue -LiteralPath (Join-Path $binRoot 'threeca.cmd')
Copy-Item -Force -LiteralPath (Join-Path $sourceRoot 'SKILL\threeca-access\SKILL.md') -Destination (Join-Path $skillRoot 'SKILL.md')
Copy-Item -Force -LiteralPath (Join-Path $sourceRoot 'SKILL\threeca-access\agents\openai.yaml') -Destination (Join-Path $skillRoot 'agents\openai.yaml')
Copy-Item -Force -LiteralPath (Join-Path $sourceRoot 'SKILL\threeca-access\references\tool-reference.md') -Destination (Join-Path $skillRoot 'references\tool-reference.md')

$registered = codex mcp list | Select-String -Pattern '^threeca\s'
if ($registered) {
    codex mcp remove threeca | Out-Null
}
codex mcp add threeca -- $venvPython (Join-Path $mcpRoot 'server.py') | Out-Null

& (Join-Path $binRoot 'threeca.exe') --version
codex mcp get threeca
