# Release Documentation

This document provides step-by-step instructions for creating a new release of Slooh Image Downloader.

## Pre-Release Checklist

Before creating a release, ensure:

- [ ] All code changes are committed and pushed to `main` branch
- [ ] Version numbers are updated (if applicable)
- [ ] Documentation is up to date (README, QUICKSTART, etc.)
- [ ] Release package created and tested (see below)
- [ ] CHANGELOG updated with release notes
- [ ] All tests pass successfully
- [ ] Code has been tested on target Windows versions

## Testing the Release Package

Before publishing, test the release package:

```powershell
# Run automated tests
.\test-release.ps1 -Version "1.0.0"
```

This script verifies:
- Package exists and extracts correctly
- All required files are present
- No user data is included
- Directory structure is correct
- Launch script is valid
- Package size is reasonable

All tests must pass before proceeding with the release.

## Version Numbering

This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., 1.0.0)
- **MAJOR** - Incompatible API changes
- **MINOR** - New functionality (backwards compatible)
- **PATCH** - Bug fixes (backwards compatible)

### Suggested Versioning:
- First public release: **v1.0.0**
- Bug fixes: **v1.0.1**, **v1.0.2**, etc.
- New features: **v1.1.0**, **v1.2.0**, etc.
- Breaking changes: **v2.0.0**, **v3.0.0**, etc.

## Creating the Release Package

Before creating a GitHub release, build the distribution package:

### Option 1: Using Batch File (Easiest)

```cmd
create-release.bat 1.0.0
```

Replace `1.0.0` with your version number.

### Option 2: Using PowerShell Script

```powershell
powershell -ExecutionPolicy Bypass -File .\create-release.ps1 -Version "1.0.0"
```

### What Gets Included

The release package automatically includes:
- ✅ `launch.ps1` - PowerShell launcher
- ✅ `LICENSE` - License file
- ✅ `README.md` - Project overview
- ✅ `SloohDownloader/` - Complete application folder
  - Documentation (README, QUICKSTART, API_DOCUMENTATION)
  - Source code (`src/*.py`)
  - Configuration template (`config/config.template.json`)
  - Empty `data/` and `logs/` directories
  - Test scripts (`tests/`)

### What Gets Excluded

- ❌ `config/config.json` - User credentials
- ❌ `data/download_tracker.json` - Download history
- ❌ `data/*.backup` - Backup files
- ❌ `STAGE*.md` - Development notes
- ❌ `.git/`, `.gitignore` - Git files
- ❌ User data and logs

### Output

The script creates: `releases/SloohDownloader-vX.X.X.zip`

This zip file is ready to upload to GitHub releases!

## Creating a Release on GitHub

### Step 1: Navigate to Releases

1. Go to your repository: `https://github.com/labstercam/SloohDownloader`
2. Click on **"Releases"** in the right sidebar (or go to `/releases`)
3. Click **"Draft a new release"** button

### Step 2: Create New Tag

1. Click **"Choose a tag"** dropdown
2. Type your new version tag (e.g., `v1.0.0`)
3. Click **"Create new tag: v1.0.0 on publish"**

**Tag Format**: Use `v` prefix followed by version number (e.g., `v1.0.0`, `v1.1.0`)

### Step 3: Set Release Details

1. **Release Title**: Enter a descriptive title (e.g., "Slooh Image Downloader v1.0.0")
2. **Target Branch**: Ensure `main` is selected
3. **Description**: Copy the release notes from the template below

### Step 4: Add Release Notes

Copy and customize the release notes template provided in the next section.

### Step 5: Upload Release Package

1. Click **"Attach binaries by dropping them here or selecting them"**
2. Select `releases/SloohDownloader-vX.X.X.zip` from your local folder
3. Wait for upload to complete
4. The zip file will appear in the release assets

### Step 6: Publish

1. Review all information
2. Choose **"Set as the latest release"** (if this is the latest)
3. Click **"Publish release"**

## Release Notes Template

Copy and customize the following template for your release:

```markdown
# Slooh Image Downloader v1.0.0

A standalone Windows desktop application for bulk downloading Slooh astronomical images. Built with IronPython and .NET Windows Forms.

## 🎯 What's New in v1.0.0

### Core Features
- ✅ **Bulk Download**: Multi-threaded bulk downloading with configurable thread count
- ✅ **Download Tracking**: JSON-based tracker prevents duplicate downloads
- ✅ **Smart Organization**: Template-based file organization (`{object}/{telescope}/{format}`)
- ✅ **Batch Processing**: Process downloads in batches of 50 with detailed progress
- ✅ **Pause/Resume/Stop**: Full control over download sessions

### Filtering Options
- ✅ **Date Range Filter**: Download images from specific date ranges
- ✅ **Telescope Filter**: Multi-select filter for specific telescopes
- ✅ **Object Filter**: Filter by object name (partial match)
- ✅ **Image Type Filter**: Choose PNG, FITS, or both

### User Interface
- ✅ **Windows Forms GUI**: Native Windows interface with 5 tabs
  - Download Tab: Main download controls and filters
  - Configuration Tab: Settings and credentials
  - History Tab: Download session history
  - Statistics Tab: Download statistics and breakdowns
  - Advanced Tab: Advanced options and maintenance tools
- ✅ **Real-Time Progress**: Batch progress with file counts
- ✅ **Auto-Login**: Automatically logs in with saved credentials
- ✅ **Live Statistics**: Real-time download statistics

### Advanced Features
- ✅ **Rate Limiting**: Configurable API request rate (default: 30 req/min)
- ✅ **Retry Logic**: Automatic retry with exponential backoff (default: 3 retries)
- ✅ **Force Redownload**: Re-download images regardless of tracker
- ✅ **Dry Run Mode**: Preview downloads without downloading
- ✅ **Export Reports**: CSV and HTML export of download history
- ✅ **Maintenance Tools**: Verify downloads, find orphaned files, clean tracker

## 📋 System Requirements

- **OS**: Windows 7 or later (64-bit recommended)
- **IronPython**: 3.4 or later
- **.NET Framework**: 4.6.2 or later (usually pre-installed)
- **Disk Space**: Varies based on image collection size
- **Internet**: Active connection for API access

## 🚀 Quick Start

### Installation

1. **Install IronPython**:
   ```powershell
   choco install ironpython
   ```
   Or download from: https://ironpython.net/

2. **Download this release**:
   - Download `SloohDownloader-vX.X.X.zip` from the Assets section below
   - **Do not** download "Source code" - use the SloohDownloader ZIP file

3. **Extract to your Documents folder**:
   - Right-click the ZIP → **Extract All**
   - Recommended location: `C:\Users\YourName\Documents\SloohDownloader`
   - Choose any folder where you have write access (avoid Program Files)

4. **Launch the application**:
   - Navigate to the extracted folder
   - Double-click `launch.ps1` to launch
   
   Or from PowerShell:
   ```powershell
   cd C:\Users\YourName\Documents\SloohDownloader
   .\launch.ps1
   ```

### First-Time Setup

1. **Configuration Tab**:
   - Enter your Slooh username and password
   - Set download folder location
   - Click **Save Configuration**

2. **Download Tab**:
   - Click **Login** button
   - Wait for "Logged in successfully"

3. **Start Downloading**:
   - Check **All Missions**
   - Click **Start Download**

## 📖 Documentation

- **[README.md](README.md)**: Project overview and key features
- **[SloohDownloader/README.md](SloohDownloader/README.md)**: Complete feature documentation
- **[SloohDownloader/QUICKSTART.md](SloohDownloader/QUICKSTART.md)**: Step-by-step quick start guide
- **[SloohDownloader/API_DOCUMENTATION.md](SloohDownloader/API_DOCUMENTATION.md)**: Slooh API documentation

## 🔧 Configuration

All configuration is done through the GUI Configuration Tab. Settings are saved to `config/config.json`.

**Key Settings**:
- **Threads**: Concurrent downloads (default: 4)
- **Rate Limit**: API requests per minute (default: 30)
- **Max Retries**: Retry attempts for failures (default: 3)
- **Base Path**: Root download directory
- **Template**: File organization pattern (default: `{object}/{telescope}/{format}`)

## 📊 Known Issues

None at this time. Please report issues at: https://github.com/labstercam/SloohDownloader/issues

## 🤝 Contributing

Contributions are welcome! Please open an issue or pull request.

## 📄 License

MIT License - Copyright (c) 2021-2026 Calteo

See [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This is an unofficial community tool. Not affiliated with or endorsed by Slooh. Use responsibly and respect Slooh's terms of service.

---

**Full Changelog**: https://github.com/labstercam/SloohDownloader/commits/v1.0.0
```

## Alternative: Shorter Release Notes

For a more concise release, use this shorter template:

```markdown
# Slooh Image Downloader v1.0.0

Windows desktop application for bulk downloading Slooh astronomical images.

## Features

- Multi-threaded bulk downloads with pause/resume/stop
- Smart filtering (date, telescope, object, image type)
- Download tracking to prevent duplicates
- Template-based file organization
- Windows Forms GUI with real-time progress
- Export reports (CSV, HTML)

## Requirements

- Windows 7+
- IronPython 3.4+ ([Download](https://ironpython.net/))
- .NET Framework 4.6.2+

## Quick Start

```bash
# Install IronPython
choco install ironpython

# Launch application
.\launch.ps1
```

See [README.md](README.md) for complete documentation.

## License

MIT License - See [LICENSE](LICENSE)

---

**Note**: This is an unofficial community tool not affiliated with Slooh.
```

## Post-Release Steps

After publishing the release:

1. **Verify Release**: Check that the release appears correctly on GitHub
2. **Test Download**: Download the release zip and verify it works
3. **Update Links**: Ensure any documentation links point to the correct release
4. **Announce**: Share the release (if applicable)
5. **Monitor Issues**: Watch for any bug reports from users

## Creating Subsequent Releases

For bug fixes or new features:

1. Update version number in documentation (if tracking versions)
2. Create a new tag following semantic versioning
3. Update release notes to describe changes
4. Reference previous version: "Upgrading from v1.0.0..."

### Example Bug Fix Release (v1.0.1)

```markdown
# Slooh Image Downloader v1.0.1

Bug fix release.

## Changes

- Fixed: [Brief description of bug fix]
- Fixed: [Another bug fix]
- Improved: [Performance or usability improvement]

## Upgrading from v1.0.0

Simply download and replace files. Configuration and tracker files are compatible.

**Full Changelog**: https://github.com/labstercam/SloohDownloader/compare/v1.0.0...v1.0.1
```

## Tips

- **Keep it Simple**: First release can be straightforward
- **Highlight Key Features**: Focus on what makes the tool useful
- **Include Prerequisites**: Make installation clear
- **Link to Docs**: Point users to detailed documentation
- **Be Honest**: Note any known issues or limitations
- **Format Well**: Use markdown formatting for readability

## GitHub Release Automation (Optional)

For future releases, consider:
- GitHub Actions to automate releases
- CHANGELOG.md file to track changes
- Automated version bumping
- Release draft generation from commits
