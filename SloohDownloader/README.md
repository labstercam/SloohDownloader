# Slooh Image Downloader

A Windows Forms GUI application for **bulk downloading** your Slooh astronomical images to your PC. Built with IronPython and .NET for easy management and organization of your personal Slooh image library.

## Purpose

This downloader is designed to help you **download all your Slooh images in bulk** for local management on your PC. The recommended workflow is to **periodically download recent images by date** to ensure you have a complete local archive of all your Slooh observations.

### Key Features
- **Bulk Download**: Download hundreds or thousands of images efficiently
- **Date-Based Downloads**: Easily download all images from a specific date range
- **Download Tracking**: Never re-download the same image twice (unless you want to)
- **Organized Storage**: Automatically organize images by object, telescope, and format
- **Multi-threaded**: Fast parallel downloads with configurable thread count
- **Batch Processing**: Process downloads in batches of 50 for better progress tracking

### Important: Download Tracker Behavior
⚠️ **The download tracker only records what images have been downloaded - it does NOT monitor your file system.**

- If you delete downloaded files, they remain marked as "downloaded" in the tracker
- Use **Force Redownload** option to re-download images regardless of tracker status
- The tracker prevents accidental duplicate downloads during normal operations
- Tracker file: `data/download_tracker.json`

## IronPython Limitations & Workarounds

### Key Limitations
1. **No async/await support** - IronPython 3.x doesn't fully support Python 3.5+ async syntax
   - **Workaround**: Using .NET threading and Task-based async pattern via CLR
2. **Limited modern Python library support** - Many PyPI packages don't work
   - **Workaround**: Direct use of .NET libraries (System.Net.Http, etc.)
3. **Python 3.x compatible** - IronPython 3.4+ supports Python 3 syntax (f-strings, etc.)
   - **Benefit**: Modern Python 3 syntax available

### Design Decisions for Simplicity
- **No SQLite database** - Uses simple JSON files for tracking
  - Perfect for thousands of images
  - Easy to inspect and edit manually
  - No external dependencies
  - Automatic backup with each save
- **Pure Python + .NET** - No complex dependencies to install
- **Single file tracking** - All download history in one JSON file

### Advantages of IronPython
- Direct .NET integration - can use all .NET libraries
- Easy distribution - single executable possible
- Windows Forms GUI - native-looking interface
- No additional runtime needed if .NET is installed
- Can share code/types with main C# application

## Prerequisites

- IronPython 3.4+ (Python 3 compatible)
- .NET Framework 4.6.2 or later (or .NET 6.0+)
- Windows OS (for Windows Forms GUI)
- Active Slooh account with login credentials

**That's it! No database, no external packages needed.**

## Quick Start

### 1. Install IronPython

**Option 1: Using Chocolatey (Recommended)**
```bash
choco install ironpython
```

**Option 2: Direct Download**
Download from: https://ironpython.net/

### 2. Run the Application

**Option 1: Using PowerShell Launcher (Easiest)**
```powershell
.\launch.ps1
```
Double-click `launch.ps1` in the repository root, or run from PowerShell.

**Option 2: Direct Launch**
```bash
cd SloohDownloader\src
ipy gui_main.py
```

**Option 3: Create Desktop Shortcut**
- Right-click `launch.ps1` → **Send to** → **Desktop (create shortcut)**
- Double-click the shortcut anytime to launch

The GUI will launch with a modern Windows Forms interface.

### 3. Configure Settings (First Time)

1. **Go to Configuration Tab**
   - Enter your Slooh username and password
   - Set download folder location
   - Configure threads (default: 4), rate limit (default: 30 req/min), retries (default: 3)
   - Set file organization template (default: `{object}/{telescope}/{format}`)
   - Click **Save Configuration**

2. **Go to Download Tab**
   - Click **Login** button to authenticate
   - Wait for "Logged in successfully" message

You're ready to download!

## Recommended Workflow: Periodic Downloads by Date

The best way to use this downloader is to **periodically download recent images** to ensure you have everything:

### First Time Download
1. Go to **Advanced Tab**
2. Set **Start Date** to when you started using Slooh (e.g., `2024-01-01`)
3. Leave **End Date** empty (downloads up to today)
4. Return to **Download Tab**
5. Check **All Missions** (unless you want specific missions only)
6. Click **Start Download**

### Periodic Updates (Monthly/Weekly)
1. Go to **Advanced Tab**
2. Set **Start Date** to your last download date (e.g., `2025-01-01`)
3. Leave **End Date** empty
4. Return to **Download Tab**
5. Click **Start Download**
6. Only new images will be downloaded (tracker prevents duplicates)

### Alternative: Use Start Image Number
- Set **Start Image Number** to 1 (most recent)
- Set **Max Images** to desired count (e.g., 100 for last 100 images)
- Click **Start Download**

## Application Features

### Download Tab
- **Mission Selection**: Download specific missions or all missions
- **Filters**:
  - Telescope filter (multi-select)
  - Object name filter (partial match)
  - Image type filter (PNG, FITS, or Both)
- **Download Controls**:
  - Start, Pause, Resume, Stop buttons
  - Real-time progress display with batch tracking
  - Status updates: "Batch #3: Downloading 25 of 50"
- **Download Settings**:
  - Max Images: Limit total files to download
  - Max Scan: Limit API pagination depth
  - Start Image Number: Begin from specific photoroll position
  - Shows date preview for start image

### Configuration Tab
- **Credentials**: Slooh username and password (saved to config)
- **Download Settings**:
  - Threads: Concurrent download threads (default: 4)
  - Rate Limit: Max API requests per minute (default: 30)
  - Max Retries: Retry attempts for failed downloads (default: 3)
- **Folder Settings**:
  - Base Path: Root download directory
  - Template: File organization pattern (e.g., `{object}/{telescope}/{format}`)
- All changes saved to `config/config.json`

### Advanced Tab
- **Date Range Filters**: Start Date and End Date (YYYY-MM-DD format)
- **Download Options**:
  - Dry Run: Preview what will be downloaded
  - Force Redownload: Ignore tracker and re-download everything
- **Export Options**:
  - Export to CSV: Full download history
  - Export to HTML: Formatted report
  - Export Statistics: Summary report

### History Tab
- View all download sessions
- See images downloaded per session
- Export session data

### Statistics Tab
- Total images downloaded
- Total storage used
- Images by telescope breakdown
- Images by object breakdown
- Recent downloads list

## GUI Features

### Real-Time Updates
- **Batch Progress**: "Starting Batch #1", "Batch #1 completed - 48 files saved for 12 objects"
- **Progress Bar**: Shows current batch progress with file counts
- **Log Window**: Real-time status messages and download progress
- **Statistics**: Live updates of downloaded/failed counts

### Control Features
- **Pause**: Pause downloads and resume later (same session)
- **Stop**: Stop downloads completely
- **Auto-Login**: Automatically logs in on startup with saved credentials
- **Thread-Safe**: All UI updates are thread-safe for smooth operation## Download Tracker Explained

### What the Tracker Does
✅ Records every successfully downloaded image  
✅ Prevents duplicate downloads in future sessions  
✅ Stores: image ID, filename, file path, download date, file size, metadata  
✅ Saved to: `data/download_tracker.json`

### What the Tracker Does NOT Do
❌ Does NOT monitor your file system  
❌ Does NOT detect if you delete files  
❌ Does NOT verify file existence on disk  
❌ Does NOT update if you move files

### When to Use Force Redownload
Use **Force Redownload** checkbox when:
- You deleted downloaded files and want them back
- Files were corrupted and need to be re-downloaded
- You moved files and want fresh copies
- You want to download everything again regardless of history

### Tracker File Location
- Primary: `data/download_tracker.json`
- Backups: `data/download_tracker_backup_YYYYMMDD_HHMMSS.json`
- Created automatically on first download
- Backed up automatically before each save

## Project Structure

```
Repository Root/
├── launch.ps1                  # PowerShell launcher (double-click to start!)
├── README.md                   # Project overview
├── QUICKSTART.md               # Quick start guide  
├── RELEASE.md                  # Release documentation
└── SloohDownloader/
    ├── README.md               # This file - complete documentation
    ├── QUICKSTART.md           # Detailed quick start guide
    ├── config/
    │   └── config.json         # Configuration (created on first run)
    ├── data/
    │   ├── download_tracker.json  # Download history (auto-created)
    │   └── logs/               # Log files
    └── src/
        ├── gui_main.py         # Main GUI application
        ├── config_manager.py   # Configuration handling
        ├── download_tracker.py # JSON-based download tracking
        ├── logger.py           # Logging system with GUI callbacks
        ├── slooh_client.py     # Slooh API client
        ├── download_manager.py # Multi-threaded downloader
        ├── batch_manager.py    # Batch coordinator
        ├── file_organizer.py   # File organization
        └── report_generator.py # Export reports (CSV, HTML)
```

## Application Status

**✅ Production-Ready with Full Feature Set**

All core features are implemented and tested:
- Multi-threaded bulk downloads with batch processing
- Comprehensive filtering (date, telescope, object, image type)
- Download tracking to prevent duplicates
- Organized file storage with configurable templates
- Real-time progress with batch status updates
- Pause/Resume/Stop controls
- Export and reporting capabilities
- Windows Forms GUI with 5 tabs (Download, Configuration, History, Statistics, Advanced)

## IronPython Design & Architecture

### Why IronPython?
- **Direct .NET Integration**: Use all .NET libraries seamlessly
- **Windows Forms GUI**: Native-looking Windows interface
- **No External Dependencies**: Pure Python + .NET only
- **Easy Distribution**: Single executable possible
- **Python 3 Syntax**: Modern Python 3 features available

### Design Decisions for Simplicity
- **No SQLite Database**: Uses simple JSON files for tracking
  - Perfect for thousands of images
  - Easy to inspect and edit manually
  - No external dependencies
  - Automatic backup with each save
- **No async/await**: Uses .NET threading and Task-based async via CLR
- **No PyPI packages**: Direct use of .NET libraries (System.Net.Http, etc.)

### Advantages
✅ Direct .NET integration - all .NET libraries available  
✅ Windows Forms GUI - native Windows look and feel  
✅ No runtime dependencies - just .NET Framework  
✅ Single file distribution possible  
✅ Can share code with main C# Slooh.Explorer project

## Configuration

All configuration is done through the **Configuration Tab** in the GUI. Settings are automatically saved to `config/config.json`.

### Configuration Settings

**Credentials**:
- `credentials.username`: Your Slooh login username
- `credentials.password`: Your Slooh login password

**Download Settings**:
- `download.threads`: Number of concurrent downloads (default: 4)
- `download.rate_limit`: Max API requests per minute (default: 30)
- `download.max_retries`: Retry attempts for failed downloads (default: 3)
- `download.batch_size`: Images processed per batch (default: 50)

**Folder Settings**:
- `folders.base_path`: Root directory for downloads
- `folders.template`: File organization pattern
  - Available placeholders: `{object}`, `{telescope}`, `{format}`, `{date}`, `{mission}`
  - Example: `{object}/{telescope}/{format}` creates: `NGC6992/Chile-One/PNG/`

**Tracking**:
- `tracking.tracker_file`: Path to download tracker JSON (default: `data/download_tracker.json`)

**Logging**:
- `logging.enabled`: Enable/disable logging (default: true)
- `logging.log_level`: DEBUG, INFO, WARNING, ERROR (default: INFO)
- `logging.log_folder`: Log file directory (default: `data/logs`)

## Troubleshooting

### "IronPython not found"
- Install IronPython: `choco install ironpython`
- Or download from: https://ironpython.net/
- Ensure `ipy.exe` is in your PATH

### "Authentication failed"
- Verify username and password in Configuration tab
- Check internet connection
- Ensure you can log into https://app.slooh.com in browser

### "Files not downloading"
- Check Configuration tab for correct base path
- Verify folder has write permissions
- Check log window for errors
- Try "Force Redownload" if tracker may be blocking

### "Duplicate files appearing"
- This is expected with "Force Redownload" enabled
- Disable "Force Redownload" to respect tracker
- Tracker only prevents duplicates when Force Redownload is OFF

### "Download Tracker out of sync with files"
- Tracker doesn't monitor file system
- Use "Force Redownload" to re-download deleted files
- Or manually edit `data/download_tracker.json` (advanced users)

### "Batch progress not showing"
- Logger messages appear in log window (bottom panel)
- Check that log window is visible
- Look for "Starting Batch #N" messages

## Tips for Best Results

1. **Use Date Filters**: Download recent images by date range for incremental updates
2. **Check History Tab**: Review what's been downloaded before starting new downloads
3. **Use Dry Run First**: Preview downloads before committing (Advanced tab)
4. **Set Reasonable Limits**: Use Max Images to test with small batches first
5. **Monitor Progress**: Watch batch progress in log window for detailed status
6. **Pause If Needed**: Use Pause button if you need to temporarily stop
7. **Regular Backups**: Tracker is automatically backed up, but backup your images separately

## License

MIT License - Copyright (c) 2021-2026 Calteo

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Disclaimer

This is an unofficial community tool. Not affiliated with or endorsed by Slooh. Use responsibly and respect Slooh's terms of service.
