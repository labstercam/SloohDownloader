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

# Find IronPython executable
$IpyPath = $null

# 1. Check if ipy is in PATH
$IpyCommand = Get-Command ipy -ErrorAction SilentlyContinue
if ($IpyCommand) {
    $IpyPath = $IpyCommand.Source
    Write-Host "Found IronPython in PATH: $IpyPath" -ForegroundColor Cyan
}

# 2. Check common installation directories
if (-not $IpyPath) {
    $CommonPaths = @(
        "C:\Program Files\IronPython 3.4\ipy.exe",
        "C:\Program Files (x86)\IronPython 3.4\ipy.exe",
        "C:\Program Files\IronPython 3.4\net462\ipy.exe",
        "C:\Program Files (x86)\IronPython 3.4\net462\ipy.exe",
        "$env:ProgramFiles\IronPython 3.4\ipy.exe",
        "${env:ProgramFiles(x86)}\IronPython 3.4\ipy.exe"
    )
    
    foreach ($Path in $CommonPaths) {
        if (Test-Path $Path) {
            $IpyPath = $Path
            Write-Host "Found IronPython at: $IpyPath" -ForegroundColor Cyan
            break
        }
    }
}

# 3. Check for local IronPython installation relative to script
if (-not $IpyPath) {
    $LocalPaths = @(
        (Join-Path $ScriptDir "IronPython\ipy.exe"),
        (Join-Path $ScriptDir "IronPython\net462\ipy.exe"),
        (Join-Path $ScriptDir "..\IronPython\ipy.exe"),
        (Join-Path $ScriptDir "bin\IronPython\ipy.exe")
    )
    
    foreach ($Path in $LocalPaths) {
        if (Test-Path $Path) {
            $IpyPath = $Path
            Write-Host "Found IronPython at: $IpyPath" -ForegroundColor Cyan
            break
        }
    }
}

# If still not found, show error
if (-not $IpyPath) {
    Write-Host "Error: IronPython not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "Searched locations:" -ForegroundColor Yellow
    Write-Host "  - System PATH" -ForegroundColor Yellow
    Write-Host "  - C:\Program Files\IronPython 3.4\" -ForegroundColor Yellow
    Write-Host "  - $ScriptDir\IronPython\" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please install IronPython:" -ForegroundColor Yellow
    Write-Host "  Option 1: choco install ironpython" -ForegroundColor Yellow
    Write-Host "  Option 2: Download from https://ironpython.net/" -ForegroundColor Yellow
    Write-Host "  Option 3: Extract IronPython to: $ScriptDir\IronPython\" -ForegroundColor Yellow
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
    & $IpyPath gui_main.py
} finally {
    Pop-Location
}
