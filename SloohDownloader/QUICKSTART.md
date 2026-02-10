# Quick Start Guide - Slooh Image Downloader

## What Is This?

A standalone Windows application to **download all your Slooh astronomical images in bulk** for local management on your PC. Built with IronPython and Windows Forms for a native Windows experience.

### Best Use: Periodic Downloads by Date

The recommended workflow is to **periodically download recent images by date** to maintain a complete local archive:
- First time: Download everything from your start date
- Monthly/Weekly: Download new images since last download
- The tracker prevents re-downloading images you already have

## Prerequisites

You need IronPython and Windows:

### Install IronPython

**Option 1: Using Chocolatey (Recommended)**
```powershell
choco install ironpython
```

**Option 2: Manual Download**
Download from: https://ironpython.net/download/

**Verify Installation**:
```powershell
ipy --version
```

You should see something like: `IronPython 3.4.0`

## Installation

### Step 1: Download the Application

1. Go to the **[Releases page](https://github.com/labstercam/SloohDownloader/releases)**
2. Download the latest `SloohDownloader-vX.X.X.zip` file
3. Save it to your Downloads folder

### Step 2: Extract the Files

1. **Right-click** the downloaded ZIP file
2. Select **Extract All...**
3. Choose a location where you have write access:
   - **Recommended**: `C:\Users\YourName\Documents\SloohDownloader`
   - **Also good**: `C:\Users\YourName\Desktop\SloohDownloader`
   - **Avoid**: `C:\Program Files\` (requires admin rights)
4. Click **Extract**

### Step 3: Launch the Application

**Option 1: Using PowerShell Launcher (Easiest)**
1. Navigate to the extracted folder
2. Double-click `launch.ps1`
3. If prompted about execution policy, click **Run anyway**

**Option 2: From PowerShell**
```powershell
cd C:\Users\YourName\Documents\SloohDownloader
.\launch.ps1
```

**Option 3: Direct Launch**
```powershell
cd SloohDownloader\src
ipy gui_main.py
```

**Option 4: Create Desktop Shortcut**
1. Right-click `launch.ps1`
2. Select **Send to** → **Desktop (create shortcut)**
3. Double-click the shortcut anytime to launch

A Windows Forms GUI will appear with tabs: Download, Configuration, History, Statistics, Advanced.

## Quick Start (First Time Setup)

### Step 1: Configure Your Settings

1. **Click on the Configuration Tab**

2. **Enter Your Slooh Credentials**:
   - Username: Your Slooh login
   - Password: Your Slooh password
   - Click **Save Configuration**

3. **Configure Download Settings** (or keep defaults):
   - Threads: `4` (concurrent downloads)
   - Rate Limit: `30` (requests per minute)
   - Max Retries: `3` (retry attempts)

4. **Set Download Folder**:
   - Base Path: Choose where to save images (e.g., `C:\Slooh\Images`)
   - Template: `{object}/{telescope}/{format}` (organizes by object, then telescope)
   - Click **Save Configuration**

### Step 2: Login to Slooh

1. **Go back to Download Tab**

2. **Click the Login button**

3. **Wait for success message**: "Logged in successfully"

4. **Status bar** should show: "Connected to Slooh"

You're ready to download!

## Your First Download - Get Everything

### Option 1: Download All Images from a Date

1. **Click on Advanced Tab**
   - Start Date: Enter your Slooh start date (e.g., `2024-01-01`)
   - End Date: Leave empty (downloads to today)

2. **Go back to Download Tab**
   - Check **All Missions** checkbox
   - Leave other settings at defaults

3. **Click Start Download**

4. **Watch the Progress**:
   - Log window shows: "Starting Batch #1", "Batch #1 completed - X files saved for Y objects"
   - Progress bar shows: "Batch #3: Downloading 25 of 50"
   - Statistics update in real-time

### Option 2: Download Recent 100 Images

1. **Stay on Download Tab**
   - Start Image Number: `1` (most recent)
   - Max Images: `100`
   - Check **All Missions**

2. **Click Start Download**

The date preview will show you the date of image #1 before downloading.

## Periodic Updates - Download Only New Images

After your initial download, here's how to get new images monthly or weekly:

### Monthly/Weekly Download Routine

1. **Go to Advanced Tab**
   - Start Date: Enter your last download date (e.g., `2025-01-01`)
   - End Date: Leave empty (or today's date)

2. **Go to Download Tab**
   - Check **All Missions**
   - Click **Start Download**

3. **The tracker automatically prevents duplicates**
   - Only new images will be downloaded
   - Already downloaded images are skipped
   - Status shows: "Skipping (already in tracker): ..."

This is the **recommended workflow** for maintaining your local Slooh archive!

## Understanding the Download Tracker

### What It Does ✅
- Records every successfully downloaded image
- Prevents re-downloading the same image
- Stores metadata: image ID, filename, path, date, size

### What It Does NOT Do ❌
- **Does NOT monitor your file system**
- **Does NOT detect if you delete files**
- **Does NOT update when you move files**

### When to Use Force Redownload

Use the **Force Redownload** checkbox (Advanced Tab) when:
- You deleted files and want them back
- Files were corrupted
- You want fresh copies of everything

**Warning**: Force Redownload ignores the tracker and downloads everything again, creating duplicates if files still exist.

## Using Filters

### Filter by Telescope

**Download Tab → Telescope Filter**:
- Check specific telescopes (e.g., Chile-One, Canary-Two)
- Leave all unchecked = download from all telescopes

### Filter by Object

**Download Tab → Object Filter**:
- Enter object name: `M31`, `NGC`, `Orion`, etc.
- Case-insensitive partial match
- Example: "NGC" matches NGC6992, NGC7000, etc.

### Filter by Image Type

**Download Tab → Image Type Filter**:
- **All (PNG + FITS)**: Download both processed images and FITS files
- **Processed Images Only (PNG)**: Skip FITS files
- **FITS Only**: Skip processed images

### Filter by Date Range

**Advanced Tab → Date Range**:
- Start Date: `2025-01-01` (YYYY-MM-DD format)
- End Date: `2025-01-31` (or leave empty for "to today")
- Efficiently stops scanning when images too old

## Troubleshooting

### "IronPython not found" or "'ipy' is not recognized"
- Install IronPython: `choco install ironpython`
- Or download from: https://ironpython.net/
- Ensure `ipy.exe` is in your PATH
- Try full path: `C:\Program Files\IronPython 3.4\ipy.exe`

### "GUI doesn't launch"
- Try using `.\launch.ps1` from repository root (recommended)
- Check IronPython version: `ipy --version` (need 3.4+)
- Verify .NET Framework 4.6.2+ is installed
- If running directly: Ensure you're in `SloohDownloader\src\` directory
- Check console for error messages

### "Login failed" or "Authentication failed"
- Verify username and password in Configuration tab
- Click **Save Configuration** after entering credentials
- Check internet connection
- Test login at: https://app.slooh.com
- Look for error in log window

### "Files not downloading"
- Check base path in Configuration tab has write permissions
- Verify folder exists or app can create it
- Check log window for specific errors
- Try smaller Max Images setting first (e.g., 10)

### "Duplicates being created"
- Check if **Force Redownload** is enabled (Advanced tab)
- Disable Force Redownload to respect tracker
- Tracker file: `data/download_tracker.json`

### "Download Tracker out of sync"
- Tracker doesn't monitor file system
- If you deleted files, they stay marked as downloaded
- Use **Force Redownload** to re-download
- Or manually edit/delete `data/download_tracker.json` (advanced)

### "Progress not showing" or "Log window empty"
- Logger messages appear in bottom log panel
- Check panel is visible (may need to resize)
- Look for batch messages: "Starting Batch #N"
- Status bar shows overall progress

### "Downloads are slow"
- Increase threads in Configuration tab (try 8 or 16)
- Check your internet connection speed
- Slooh API rate limiting may apply (30 req/min default)
- FITS files are larger and take longer

### "Start Image date preview not showing"
- Wait a few seconds for background fetch
- Check internet connection
- Verify you're logged in
- Look for status message in status bar

## File Locations

### Configuration
- **Config File**: `config/config.json`
- Created automatically on first run
- Edit via Configuration tab (recommended)
- Or edit manually with text editor

### Download Tracker
- **Tracker**: `data/download_tracker.json`
- Created on first download
- Backed up automatically: `data/download_tracker_backup_*.json`
- Contains all download history

### Logs
- **Log Files**: `data/logs/SloohDownloader_YYYYMMDD_HHMMSS.log`
- New log file per session
- Contains detailed operation logs
- Useful for troubleshooting

### Downloaded Images
- **Location**: Set in Configuration → Base Path
- **Organization**: Based on template (default: `{object}/{telescope}/{format}`)
- **Example**: `C:\Slooh\Images\NGC6992\Chile-One\PNG\NGC6992_20240115.png`

## Tips for Success

### First-Time Users
1. **Start Small**: Use Max Images = 10 for your first download
2. **Test Filters**: Use Dry Run to preview before downloading
3. **Check Organization**: Verify template creates folders you like
4. **Monitor Progress**: Watch log window for batch progress

### Regular Users
1. **Use Date Filters**: Download by date range for incremental updates
2. **Set Regular Schedule**: Weekly or monthly downloads
3. **Check History Tab**: Review what you've downloaded
4. **Monitor Statistics**: See your archive grow over time

### Power Users
1. **Adjust Threads**: Increase for faster downloads (8-16 threads)
2. **Use Start Image Number**: Resume from specific points
3. **Combine Filters**: Telescope + Object + Date for precise downloads
4. **Export Reports**: Generate CSV for analysis in Excel

## What's Next?

### After Your First Download
1. **Check History Tab**: See your download session
2. **View Statistics Tab**: See breakdown by telescope/object
3. **Browse Your Files**: Open base path and explore organized images
4. **Plan Next Download**: Set up date filter for next time

### Regular Maintenance
- **Weekly/Monthly**: Download new images by date
- **Backup Tracker**: Occasionally backup `download_tracker.json`
- **Review Statistics**: Monitor your growing archive
- **Update Filters**: Adjust as your interests change

## Getting Help

### Documentation
- **README.md**: Complete feature documentation and configuration guide
- **QUICKSTART.md**: This quick start guide

### Troubleshooting
- Check log files in `data/logs/` for detailed error information
- Review error messages in the GUI log window (bottom panel)
- Verify configuration settings in Configuration tab
- Start with small downloads (Max Images = 10) to test setup
- Use Dry Run mode to preview downloads before committing

## Application is Production-Ready!

All core features are implemented and tested:
- ✅ Multi-threaded downloads
- ✅ Batch processing with progress
- ✅ Date filtering and optimization
- ✅ Download tracking to prevent duplicates
- ✅ Comprehensive filtering options
- ✅ Export and reporting
- ✅ Pause/Resume/Stop controls

**Ready for bulk downloading your Slooh image library!**

## Download Settings Explained

### Max Images
- Limits **total individual files** downloaded
- Counts PNG and FITS files separately
- Example: Max Images = 50 downloads up to 50 files
- **Soft limit**: May exceed slightly due to batching

### Max Scan
- Limits **number of pictures scanned** from API
- Controls how deep the pagination goes
- Example: Max Scan = 500 scans first 500 pictures
- Useful for quick tests or partial downloads

### Start Image Number
- Start from specific position in photoroll
- 1 = most recent image
- Shows date preview for that image
- Useful for resuming after interruption

## Control Buttons

### Start Download
- Begins download process
- Scans API for matching images
- Processes in batches of 50

### Pause
- Temporarily pauses download
- Finishes current file
- Click again to Resume
- **Note**: Pause only works within the same session

### Stop
- Stops download completely
- Ends current session
- Cannot resume (must start new download)

## Advanced Features

### Dry Run Mode

**Advanced Tab → Dry Run checkbox**:
- Preview what will be downloaded
- Shows file list without downloading
- Perfect for testing filters
- No files downloaded, no tracker updates

### Export Reports

**Advanced Tab or File Menu**:
- **Export to CSV**: Full download history spreadsheet
- **Export to HTML**: Formatted report for viewing
- **Export Statistics**: Summary of downloads

### Session History

**History Tab**:
- View all past download sessions
- See how many images per session
- Review dates and times
- Export session data
