$ErrorActionPreference = 'Stop'

$expectedRoot = 'C:\Users\User\Desktop\agentic\workflow_codex'
$root = [IO.Path]::GetFullPath($PSScriptRoot)
if (-not $root.Equals($expectedRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Wrong workflow path: $root"
}
if (Test-Path -LiteralPath 'C:\Users\User\Desktop\agentic\workflow\_codex') {
    throw 'The obsolete workflow\_codex path still exists.'
}
if (Test-Path -LiteralPath (Join-Path $root '.codex\config.toml')) {
    throw 'Project-scoped Codex MCP config would couple this workflow to the installed Codex.'
}

$activeFiles = @(
    (Join-Path $root 'run-wingpt.ps1'),
    (Join-Path $root 'start-wingpt-server.ps1'),
    (Join-Path $root 'codex-cli\bin\codex.js'),
    (Join-Path $root 'codex-cli\bin\wingpt.js'),
    (Join-Path $root 'codex-cli\bin\wingpt-threeca.js'),
    (Join-Path $root 'codex-cli\bin\wingpt-research.js'),
    (Join-Path $root 'tools\tool43CA\install.ps1'),
    (Join-Path $root 'tools\tool43CA\run-cli.ps1'),
    (Join-Path $root 'tools\tool43CA\run-mcp.ps1'),
    (Join-Path $root 'tools\tool43CA\MCP\server.py'),
    (Join-Path $root 'tools\tool43CA\CLI\src\threeca.py'),
    (Join-Path $root 'tools\tool43CA\SKILL\threeca-access\SKILL.md'),
    (Join-Path $root 'tools\research-quality\research_quality.py'),
    (Join-Path $root 'tools\research-quality\metabolic_states.py'),
    (Join-Path $root 'tools\research-quality\mcp_server.py'),
    (Join-Path $root 'tools\research-quality\SKILL.md')
)
$forbidden = @(
    'C:\Users\User\.codex',
    'C:\Users\User\.agents',
    'C:\Users\User\AppData\Local\OpenAI\Codex',
    'C:\Users\User\Desktop\agentic\workflow\_codex'
)
foreach ($file in $activeFiles) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Missing active workflow file: $file" }
    $content = Get-Content -LiteralPath $file -Raw
    foreach ($path in $forbidden) {
        if ($content.IndexOf($path, [StringComparison]::OrdinalIgnoreCase) -ge 0) {
            throw "Isolation violation in $file`: $path"
        }
    }
}

$localCodexEntry = Get-Content -LiteralPath (Join-Path $root 'codex-cli\bin\codex.js') -Raw
if ($localCodexEntry -notmatch 'wingpt\.js' -or $localCodexEntry -notmatch 'CODEX_HOME' -or $localCodexEntry -notmatch 'THREECA_CACHE' -or $localCodexEntry -match 'codex\.exe') {
    throw 'Project codex entry does not exclusively route to the local wingpt agent.'
}

$localArtifacts = @(
    (Join-Path $root 'tools\tool43CA\.venv\Scripts\threeca.exe'),
    (Join-Path $root 'tools\tool43CA\MCP\server.py'),
    (Join-Path $root 'tools\tool43CA\SKILL\threeca-access\SKILL.md'),
    (Join-Path $root 'tools\research-quality\research_quality.py'),
    (Join-Path $root 'tools\research-quality\metabolic_states.py'),
    (Join-Path $root 'tools\research-quality\mcp_server.py')
)
foreach ($artifact in $localArtifacts) {
    $resolved = [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $artifact).Path)
    if (-not $resolved.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "Artifact resolves outside workflow: $resolved"
    }
}
$links = Get-ChildItem -LiteralPath (Join-Path $root 'tools\tool43CA'), (Join-Path $root 'tools\research-quality') -Recurse -Force -Attributes ReparsePoint -ErrorAction SilentlyContinue
if ($links) { throw "Workflow tools contain external links: $($links.FullName -join ', ')" }

Write-Host 'PASS: exact path, no installed-Codex references, no project Codex auto-discovery config, no external tool links.'
