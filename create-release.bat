@echo off
REM Slooh Image Downloader - Release Package Creator (Batch Wrapper)
REM Simple wrapper to run the PowerShell release script

echo.
echo ============================================
echo  Slooh Image Downloader Release Creator
echo ============================================
echo.

REM Check if version is provided
set VERSION=%1
if "%VERSION%"=="" set VERSION=1.0.0

echo Creating release package v%VERSION%...
echo.

REM Run PowerShell script with bypass policy
powershell -ExecutionPolicy Bypass -File "%~dp0create-release.ps1" -Version "%VERSION%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Release created successfully!
) else (
    echo.
    echo Release creation failed!
    pause
    exit /b 1
)
