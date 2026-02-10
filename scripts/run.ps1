#!/usr/bin/env pwsh
<#
.SYNOPSIS
Launcher script for UART Control Application (moved to scripts) on Windows PowerShell
#>

param(
    [switch]$NoVenv
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Join-Path $ScriptDir ".."
$VenvPath = Join-Path $ProjectRoot "venv"
$AppPath = Join-Path $ProjectRoot "src\main.py"

if (-not (Test-Path $AppPath)) {
    Write-Host "Error: Application file not found at $AppPath" -ForegroundColor Red
    exit 1
}

if (-not $NoVenv) {
    if (-not (Test-Path $VenvPath)) {
        Write-Host "Error: Virtual environment not found!" -ForegroundColor Red
        Write-Host "Please create it with: python -m venv venv" -ForegroundColor Yellow
        exit 1
    }
    $VenvActivate = Join-Path $VenvPath "Scripts\Activate.ps1"
    if (Test-Path $VenvActivate) { & $VenvActivate }
}

Write-Host "Starting UART Control Application..." -ForegroundColor Green
python $AppPath
