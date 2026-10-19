param(
    [Parameter(Position=0, Mandatory=$true)][string]$Action,
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$ActionArguments
)
$ErrorActionPreference = 'Stop'
$entryPoint = Join-Path $PSScriptRoot 'tools/run.py'
$pythonCommand = (Get-Command python -ErrorAction Stop).Source
& $pythonCommand $entryPoint $Action @ActionArguments
exit $LASTEXITCODE
