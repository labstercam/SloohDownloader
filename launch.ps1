#!/usr/bin/env pwsh
# Slooh Image Downloader - Launch Script
# Launches the GUI application with IronPython

# Get the directory where this script is located
$ScriptDir = $PSScriptRoot

# Set the working directory to the src folder relative to this script
$SrcPath = Join-Path $ScriptDir "SloohDownloader\src"

# Check if the src directory exists
if (-not (Test-Path $SrcPath)) {
    Write-Host "Error: Could not find src directory at: $SrcPath" -ForegroundColor Red
    Write-Host "Please ensure this script is in the repository root directory." -ForegroundColor Red
    pause
    exit 1
}

# Check if gui_main.py exists
$GuiMainPath = Join-Path $SrcPath "gui_main.py"
if (-not (Test-Path $GuiMainPath)) {
    Write-Host "Error: Could not find gui_main.py at: $GuiMainPath" -ForegroundColor Red
    pause
    exit 1
}

# Check if IronPython is available
$IpyCommand = Get-Command ipy -ErrorAction SilentlyContinue
if (-not $IpyCommand) {
    Write-Host "Error: IronPython (ipy) not found in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install IronPython:" -ForegroundColor Yellow
    Write-Host "  Option 1: choco install ironpython" -ForegroundColor Yellow
    Write-Host "  Option 2: Download from https://ironpython.net/" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

# Launch the GUI application
Write-Host "Launching Slooh Image Downloader..." -ForegroundColor Green
Write-Host "Working directory: $SrcPath" -ForegroundColor Cyan

# Change to the src directory and launch
Push-Location $SrcPath
try {
    & ipy gui_main.py
} finally {
    Pop-Location
}
