$ErrorActionPreference = 'Stop'
$workflowRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$previousCache = [Environment]::GetEnvironmentVariable('THREECA_CACHE', 'Process')
$previousNoUserSite = [Environment]::GetEnvironmentVariable('PYTHONNOUSERSITE', 'Process')
try {
    $env:THREECA_CACHE = Join-Path $workflowRoot '.threeca\cache'
    $env:PYTHONNOUSERSITE = '1'
    & (Join-Path $PSScriptRoot '.venv\Scripts\python.exe') (Join-Path $PSScriptRoot 'MCP\server.py')
    if ($LASTEXITCODE -ne 0) { throw "threeca MCP exited with code $LASTEXITCODE." }
} finally {
    [Environment]::SetEnvironmentVariable('THREECA_CACHE', $previousCache, 'Process')
    [Environment]::SetEnvironmentVariable('PYTHONNOUSERSITE', $previousNoUserSite, 'Process')
}
