#!/usr/bin/env pwsh
# Slooh Image Downloader - Pre-Release Testing Script
# Tests the release package before publishing

param(
    [string]$Version = "1.0.0"
)

$ErrorActionPreference = "Stop"

# Colors
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }
function Write-Step { param([string]$Step, [string]$Desc) Write-Host "`n[$Step] $Desc" -ForegroundColor Yellow }

$TestsPassed = 0
$TestsFailed = 0
$Warnings = @()

Write-Info "=============================================="
Write-Info " Slooh Image Downloader - Pre-Release Tests"
Write-Info "=============================================="
Write-Info "Version: $Version"
Write-Info ""

# Test 1: Release package exists
Write-Step "1/10" "Checking release package exists"
$ZipPath = "releases\SloohDownloader-v$Version.zip"
if (Test-Path $ZipPath) {
    Write-Success "✓ Release package found: $ZipPath"
    $TestsPassed++
} else {
    Write-Error "✗ Release package not found: $ZipPath"
    Write-Error "  Run: .\create-release.bat $Version"
    $TestsFailed++
    exit 1
}

# Test 2: Extract to temp location
Write-Step "2/10" "Extracting release package"
$TestDir = Join-Path $env:TEMP "SloohDownloader_Test_$([guid]::NewGuid())"
try {
    Expand-Archive -Path $ZipPath -DestinationPath $TestDir -Force
    Write-Success "✓ Extracted to: $TestDir"
    $TestsPassed++
} catch {
    Write-Error "✗ Failed to extract package: $_"
    $TestsFailed++
    exit 1
}

$ExtractedRoot = Join-Path $TestDir "SloohDownloader"

# Test 3: Check root files
Write-Step "3/10" "Checking root files"
$RootFiles = @("launch.ps1", "LICENSE", "README.md")
$RootMissing = @()
foreach ($file in $RootFiles) {
    $path = Join-Path $ExtractedRoot $file
    if (Test-Path $path) {
        Write-Success "  ✓ $file"
    } else {
        Write-Error "  ✗ Missing: $file"
        $RootMissing += $file
    }
}
if ($RootMissing.Count -eq 0) {
    Write-Success "✓ All root files present"
    $TestsPassed++
} else {
    Write-Error "✗ Missing root files: $($RootMissing -join ', ')"
    $TestsFailed++
}

# Test 4: Check documentation
Write-Step "4/10" "Checking documentation files"
$DocFiles = @("README.md", "QUICKSTART.md", "API_DOCUMENTATION.md")
$AppDir = Join-Path $ExtractedRoot "SloohDownloader"
$DocMissing = @()
foreach ($file in $DocFiles) {
    $path = Join-Path $AppDir $file
    if (Test-Path $path) {
        Write-Success "  ✓ $file"
    } else {
        Write-Error "  ✗ Missing: $file"
        $DocMissing += $file
    }
}
if ($DocMissing.Count -eq 0) {
    Write-Success "✓ All documentation files present"
    $TestsPassed++
} else {
    Write-Error "✗ Missing documentation: $($DocMissing -join ', ')"
    $TestsFailed++
}

# Test 5: Check source files
Write-Step "5/10" "Checking source code files"
$SrcDir = Join-Path $AppDir "src"
if (Test-Path $SrcDir) {
    $PyFiles = Get-ChildItem -Path $SrcDir -Filter "*.py"
    if ($PyFiles.Count -ge 8) {
        Write-Success "✓ Found $($PyFiles.Count) Python source files"
        $TestsPassed++
    } else {
        Write-Warning "⚠ Only found $($PyFiles.Count) Python files (expected 9+)"
        $Warnings += "Few source files found"
        $TestsPassed++
    }
} else {
    Write-Error "✗ src/ directory missing"
    $TestsFailed++
}

# Test 6: Check config template
Write-Step "6/10" "Checking configuration template"
$ConfigTemplate = Join-Path $AppDir "config\config.template.json"
if (Test-Path $ConfigTemplate) {
    Write-Success "✓ config.template.json present"
    $TestsPassed++
} else {
    Write-Error "✗ config.template.json missing"
    $TestsFailed++
}

# Test 7: Verify no user data included
Write-Step "7/10" "Verifying no user data included"
$BadFiles = @()
$ConfigJson = Join-Path $AppDir "config\config.json"
$TrackerJson = Join-Path $AppDir "data\download_tracker.json"
if (Test-Path $ConfigJson) {
    $BadFiles += "config.json"
}
if (Test-Path $TrackerJson) {
    $BadFiles += "download_tracker.json"
}
if ($BadFiles.Count -eq 0) {
    Write-Success "✓ No user data files included"
    $TestsPassed++
} else {
    Write-Error "✗ User data files found: $($BadFiles -join ', ')"
    $TestsFailed++
}

# Test 8: Check empty directories created
Write-Step "8/10" "Checking directory structure"
$DataDir = Join-Path $AppDir "data"
$LogsDir = Join-Path $AppDir "logs"
$DirsOk = $true
if (Test-Path $DataDir) {
    Write-Success "  ✓ data/ directory exists"
} else {
    Write-Error "  ✗ data/ directory missing"
    $DirsOk = $false
}
if (Test-Path $LogsDir) {
    Write-Success "  ✓ logs/ directory exists"
} else {
    Write-Error "  ✗ logs/ directory missing"
    $DirsOk = $false
}
if ($DirsOk) {
    Write-Success "✓ Directory structure correct"
    $TestsPassed++
} else {
    $TestsFailed++
}

# Test 9: Test launch script syntax
Write-Step "9/10" "Testing launch script"
$LaunchScript = Join-Path $ExtractedRoot "launch.ps1"
try {
    $null = [System.Management.Automation.PSParser]::Tokenize((Get-Content $LaunchScript -Raw), [ref]$null)
    Write-Success "✓ launch.ps1 syntax valid"
    $TestsPassed++
} catch {
    Write-Error "✗ launch.ps1 has syntax errors: $_"
    $TestsFailed++
}

# Test 10: Check package size
Write-Step "10/10" "Checking package size"
$ZipSize = (Get-Item $ZipPath).Length
$ZipSizeKB = [math]::Round($ZipSize / 1KB, 2)
$ZipSizeMB = [math]::Round($ZipSize / 1MB, 2)
if ($ZipSizeKB -lt 50) {
    Write-Warning "⚠ Package is very small: $ZipSizeKB KB"
    $Warnings += "Package size suspiciously small"
    $TestsPassed++
} elseif ($ZipSizeKB -gt 500) {
    Write-Warning "⚠ Package is large: $ZipSizeMB MB"
    $Warnings += "Package size larger than expected"
    $TestsPassed++
} else {
    Write-Success "✓ Package size reasonable: $ZipSizeKB KB"
    $TestsPassed++
}

# Cleanup
Write-Info "`nCleaning up test directory..."
Remove-Item -Path $TestDir -Recurse -Force -ErrorAction SilentlyContinue

# Summary
Write-Info "`n=============================================="
Write-Info " Test Results"
Write-Info "=============================================="
Write-Success "Passed: $TestsPassed/10"
if ($TestsFailed -gt 0) {
    Write-Error "Failed: $TestsFailed/10"
}
if ($Warnings.Count -gt 0) {
    Write-Warning "Warnings: $($Warnings.Count)"
    foreach ($warning in $Warnings) {
        Write-Warning "  - $warning"
    }
}

Write-Info ""

if ($TestsFailed -eq 0) {
    Write-Success "=============================================="
    Write-Success " All Tests Passed! ✓"
    Write-Success "=============================================="
    Write-Success ""
    Write-Success "Release package is ready for distribution!"
    Write-Success ""
    Write-Info "Next steps:"
    Write-Info "1. Commit all changes: git add . && git commit -m 'Release v$Version'"
    Write-Info "2. Push to GitHub: git push origin main"
    Write-Info "3. Create GitHub release (see RELEASE.md)"
    Write-Info "4. Upload: $ZipPath"
    Write-Success ""
    exit 0
} else {
    Write-Error "=============================================="
    Write-Error " Tests Failed! ✗"
    Write-Error "=============================================="
    Write-Error ""
    Write-Error "Fix the issues above before releasing."
    Write-Error ""
    exit 1
}
