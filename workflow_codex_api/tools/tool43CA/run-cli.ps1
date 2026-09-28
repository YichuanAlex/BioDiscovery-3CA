[CmdletBinding()]
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$CliArgs)

$ErrorActionPreference = 'Stop'
$workflowRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$cacheRoot = Join-Path $workflowRoot '.threeca\cache'
& (Join-Path $PSScriptRoot '.venv\Scripts\threeca.exe') --cache $cacheRoot @CliArgs
if ($LASTEXITCODE -ne 0) { throw "threeca CLI exited with code $LASTEXITCODE." }
