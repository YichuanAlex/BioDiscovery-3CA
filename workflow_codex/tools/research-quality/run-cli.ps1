param([Parameter(ValueFromRemainingArguments = $true)][string[]]$CliArgs)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
& (Join-Path $root 'tools\tool43CA\.venv\Scripts\python.exe') (Join-Path $PSScriptRoot 'research_quality.py') @CliArgs
if ($LASTEXITCODE -ne 0) { throw "research-quality CLI exited with code $LASTEXITCODE." }
