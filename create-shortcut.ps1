#!/usr/bin/env pwsh
# Create Desktop Shortcut for Slooh Image Downloader
# This script creates a shortcut on your desktop to launch the application

$ScriptDir = $PSScriptRoot
$LaunchScriptPath = Join-Path $ScriptDir "launch.ps1"

# Check if launch.ps1 exists
if (-not (Test-Path $LaunchScriptPath)) {
    Write-Host "Error: Could not find launch.ps1 at: $LaunchScriptPath" -ForegroundColor Red
    pause
    exit 1
}

# Get desktop path
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "Slooh Image Downloader.lnk"

# Create shortcut using WScript.Shell COM object
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)

# Set shortcut properties
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$LaunchScriptPath`""
$Shortcut.WorkingDirectory = $ScriptDir
$Shortcut.WindowStyle = 1  # Normal window
$Shortcut.Description = "Launch Slooh Image Downloader"

# Set icon if available (use PowerShell icon by default)
$IconPath = Join-Path $ScriptDir "SloohDownloader\icon.ico"
if (Test-Path $IconPath) {
    $Shortcut.IconLocation = $IconPath
} else {
    $Shortcut.IconLocation = "powershell.exe,0"
}

# Save the shortcut
$Shortcut.Save()

Write-Host "Desktop shortcut created successfully!" -ForegroundColor Green
Write-Host "Location: $ShortcutPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now double-click the 'Slooh Image Downloader' icon on your desktop to launch the application." -ForegroundColor Yellow
pause
