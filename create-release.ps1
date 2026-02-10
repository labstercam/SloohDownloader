#!/usr/bin/env pwsh
# Slooh Image Downloader - Release Package Creator
# Creates a clean zip file for distribution

param(
    [string]$Version = "1.0.0",
    [string]$OutputDir = "releases"
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }

Write-Info "=========================================="
Write-Info " Slooh Image Downloader Release Builder"
Write-Info "=========================================="
Write-Info ""

# Get script directory
$ScriptDir = $PSScriptRoot
$TempDir = Join-Path $env:TEMP "SloohDownloader_Release_$([guid]::NewGuid())"
$PackageDir = Join-Path $TempDir "SloohDownloader"

Write-Info "Version: $Version"
Write-Info "Source: $ScriptDir"
Write-Info "Temp: $TempDir"
Write-Info ""

# Create temporary directory
Write-Info "Creating temporary directory..."
New-Item -ItemType Directory -Path $PackageDir -Force | Out-Null

# Copy root files
Write-Info "Copying root files..."
$RootFiles = @(
    "launch.ps1",
    "create-shortcut.ps1",
    "LICENSE",
    "README.md"
)

foreach ($file in $RootFiles) {
    $source = Join-Path $ScriptDir $file
    if (Test-Path $source) {
        Copy-Item -Path $source -Destination $PackageDir -Force
        Write-Success "  [OK] $file"
    } else {
        Write-Warning "  [SKIP] $file (not found)"
    }
}

# Create SloohDownloader subdirectory in package
$SloohDir = Join-Path $PackageDir "SloohDownloader"
New-Item -ItemType Directory -Path $SloohDir -Force | Out-Null

# Copy documentation files
Write-Info "Copying documentation..."
$DocFiles = @(
    "README.md",
    "QUICKSTART.md",
    "API_DOCUMENTATION.md"
)

foreach ($file in $DocFiles) {
    $source = Join-Path (Join-Path $ScriptDir "SloohDownloader") $file
    if (Test-Path $source) {
        Copy-Item -Path $source -Destination $SloohDir -Force
        Write-Success "  [OK] $file"
    } else {
        Write-Warning "  [SKIP] $file (not found)"
    }
}

# Copy src directory (all Python files)
Write-Info "Copying source code..."
$SrcSource = Join-Path (Join-Path $ScriptDir "SloohDownloader") "src"
$SrcDest = Join-Path $SloohDir "src"

if (Test-Path $SrcSource) {
    Copy-Item -Path $SrcSource -Destination $SrcDest -Recurse -Force
    # Remove any __pycache__ or .pyc files
    Get-ChildItem -Path $SrcDest -Include "__pycache__","*.pyc" -Recurse -Force | Remove-Item -Recurse -Force
    Write-Success "  [OK] src/ directory (*.py files)"
} else {
    Write-Error "  [ERROR] src/ directory not found!"
    exit 1
}

# Copy screenshots directory (if exists)
Write-Info "Copying screenshots..."
$ScreenshotsSource = Join-Path (Join-Path $ScriptDir "SloohDownloader") "screenshots"
$ScreenshotsDest = Join-Path $SloohDir "screenshots"

if (Test-Path $ScreenshotsSource) {
    Copy-Item -Path $ScreenshotsSource -Destination $ScreenshotsDest -Recurse -Force
    $ImageCount = (Get-ChildItem -Path $ScreenshotsDest -File).Count
    Write-Success "  [OK] screenshots/ directory ($ImageCount images)"
} else {
    Write-Warning "  [SKIP] screenshots/ directory (not found)"
}

# Copy config directory (template only)
Write-Info "Copying configuration template..."
$ConfigDest = Join-Path $SloohDir "config"
New-Item -ItemType Directory -Path $ConfigDest -Force | Out-Null

$TemplateSource = Join-Path (Join-Path (Join-Path $ScriptDir "SloohDownloader") "config") "config.template.json"
if (Test-Path $TemplateSource) {
    Copy-Item -Path $TemplateSource -Destination $ConfigDest -Force
    Write-Success "  [OK] config.template.json"
} else {
    Write-Warning "  [SKIP] config.template.json (not found)"
}

# Create empty data and logs directories
Write-Info "Creating empty directories..."
$DataDir = Join-Path $SloohDir "data"
$LogsDir = Join-Path $SloohDir "logs"
New-Item -ItemType Directory -Path $DataDir -Force | Out-Null
New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null
Write-Success "  [OK] data/ (empty)"
Write-Success "  [OK] logs/ (empty)"

# Create README in data folder
$DataReadme = @"
# Data Directory

This directory will contain:
- download_tracker.json - Your download history (auto-created)
- Backup files (auto-created)

These files are created automatically when you start downloading images.
"@
Set-Content -Path (Join-Path $DataDir "README.txt") -Value $DataReadme

# Create README in logs folder
$LogsReadme = @"
# Logs Directory

Application log files will be saved here automatically.
"@
Set-Content -Path (Join-Path $LogsDir "README.txt") -Value $LogsReadme

# Copy tests directory (optional)
$TestsSource = Join-Path (Join-Path $ScriptDir "SloohDownloader") "tests"
$TestsDest = Join-Path $SloohDir "tests"

if (Test-Path $TestsSource) {
    Write-Info "Copying tests..."
    Copy-Item -Path $TestsSource -Destination $TestsDest -Recurse -Force
    Write-Success "  [OK] tests/ directory"
}

# Create output directory
Write-Info ""
Write-Info "Creating release package..."
$OutputPath = Join-Path $ScriptDir $OutputDir
if (-not (Test-Path $OutputPath)) {
    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
}

# Create zip file
$ZipName = "SloohDownloader-v$Version.zip"
$ZipPath = Join-Path $OutputPath $ZipName

if (Test-Path $ZipPath) {
    Write-Warning "Removing existing release file: $ZipName"
    Remove-Item -Path $ZipPath -Force
}

# Compress the package
Write-Info "Compressing files..."
Compress-Archive -Path "$TempDir\*" -DestinationPath $ZipPath -CompressionLevel Optimal

# Clean up temp directory
Write-Info "Cleaning up..."
Remove-Item -Path $TempDir -Recurse -Force

# Get file size
$ZipSize = (Get-Item $ZipPath).Length / 1KB
$ZipSizeMB = [math]::Round($ZipSize / 1024, 2)

Write-Info ""
Write-Success "=========================================="
Write-Success " Release Package Created Successfully!"
Write-Success "=========================================="
Write-Success ""
Write-Success "Package: $ZipPath"
Write-Success "Size: $ZipSizeMB MB"
Write-Success ""
Write-Info "Package Contents:"
Write-Info "  - launch.ps1 (launcher script)"
Write-Info "  - create-shortcut.ps1 (desktop shortcut creator)"
Write-Info "  - LICENSE"
Write-Info "  - README.md"
Write-Info "  - SloohDownloader/"
Write-Info "      - README.md (full documentation)"
Write-Info "      - QUICKSTART.md"
Write-Info "      - API_DOCUMENTATION.md"
Write-Info "      - src/ (Python source files)"
Write-Info "      - screenshots/ (application screenshots)"
Write-Info "      - config/config.template.json"
Write-Info "      - data/ (empty, for download tracker)"
Write-Info "      - logs/ (empty, for log files)"
Write-Info "      - tests/ (test scripts)"
Write-Success ""
Write-Success "Ready to upload to GitHub releases!"
Write-Success ""

# Open folder
$OpenFolder = Read-Host "Open releases folder? (Y/n)"
if ($OpenFolder -ne 'n' -and $OpenFolder -ne 'N') {
    Invoke-Item $OutputPath
}
