#!/usr/bin/env pwsh
<#
Forwarder to scripts\run.ps1
#>
param(
    [switch]$NoVenv
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Forward = Join-Path $ScriptDir 'scripts\run.ps1'

if (Test-Path $Forward) {
    & $Forward @PSBoundParameters
} else {
    Write-Host 'scripts\run.ps1 not found; falling back to src\main.py' -ForegroundColor Yellow
    python (Join-Path $ScriptDir 'src\main.py')
}
