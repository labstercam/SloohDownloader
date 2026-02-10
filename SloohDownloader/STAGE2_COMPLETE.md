# Stage 2 Complete - Download Engine

## Overview

Stage 2 implements the complete download engine for the Slooh Image Downloader. This includes:
- Complete Slooh API integration with authentication
- Multi-threaded download manager with rate limiting
- Template-based file organization system
- Batch download coordinator
- CLI commands for downloading images

## New Modules

### slooh_client.py (Enhanced)

**Purpose**: Full Slooh API integration using .NET HttpClient

**Key Features**:
- Session token management and cookie handling
- User authentication with login/password
- Get missions with pagination
- Get pictures with pagination
- Iterator methods (`get_all_missions`, `get_all_pictures`) for batch retrieval
- Automatic timestamp parsing (UTC)
- Error handling and retry logic

**API Methods**:
```python
client = SloohClient('https://app.slooh.com', logger)

# Authentication
client.get_session_token()              # Get session token
client.login(username, password)         # Authenticate user
client.get_user_gravity_status()        # Get user points/status

# Missions
response = client.get_missions(first=1, max_count=50)
for mission in client.get_all_missions(batch_size=50):
    # Process mission

# Pictures
response = client.get_pictures(first=1, max_count=50, mission_id=0)
for picture in client.get_all_pictures(batch_size=50):
    # Process picture
```

**Response Structure**:
- Missions: `imageList`, `totalCount`, `firstMissionNumber`
- Pictures: `imageList`, `totalCount`, `firstImageNumber`
- Each item includes: title, timestamp, telescope, instrument, download URL

### download_manager.py

**Purpose**: Multi-threaded file downloader with rate limiting

**Key Features**:
- .NET ThreadPool for concurrent downloads
- Rate limiting (default: 30 requests/minute)
- Retry logic with exponential backoff (default: 3 retries)
- Progress tracking and callbacks
- MD5 hash verification (optional)
- File timestamp preservation
- Thread-safe operations

**Usage**:
```python
from download_manager import DownloadManager, DownloadTask

manager = DownloadManager(config.config, logger)

# Create tasks
tasks = []
task = DownloadTask(
    url='https://example.com/image.jpg',
    destination='path/to/save/image.jpg',
    image_id='12345',
    metadata={'title': 'M31', 'timestamp': '2024-01-15T10:30:00Z'}
)
tasks.append(task)

# Set callbacks
def on_progress(progress):
    print("Progress: {0}%".format(progress['percent']))

manager.on_progress = on_progress

# Download all
stats = manager.download(tasks)
print("Downloaded: {0}, Failed: {1}".format(stats['completed'], stats['failed']))
```

**Statistics**:
- Total tasks, completed, failed counts
- Total bytes downloaded
- List of completed and failed tasks with details

### file_organizer.py

**Purpose**: Organize files into template-based folder structure

**Key Features**:
- Template-based folder structure: `{object}/{telescope}/{type}`
- Template-based filename: `{telescope}_{filename}`
- Automatic object name extraction from titles (M31, NGC7000, etc.)
- Image type detection (FITS, Luminance, RGB, Narrowband)
- Filename sanitization (removes invalid characters)
- Duplicate handling (skip, overwrite, rename)
- Folder statistics

**Templates**:
Available placeholders:
- `{object}` - Object name extracted from title (e.g., M31, NGC7000)
- `{telescope}` - Telescope name
- `{instrument}` - Instrument/filter name
- `{format}` - File format (FITS, JPEG, or Pictures)
- `{filename}` - Original filename
- `{title}` - Full image title
- `{date}` - Date (YYYY-MM-DD)
- `{year}`, `{month}`, `{day}` - Date components

**File Formats**:
- `.fits` or `.fit` files → `FITS` subfolder
- `.jpg` or `.jpeg` files → `JPEG` subfolder
- `.png` files → `Pictures` subfolder

**Usage**:
```python
organizer = FileOrganizer(config.config, logger)

# Get destination path for a picture
dest_path = organizer.get_destination_path(picture_data)

# Check if file exists
exists, path = organizer.check_exists(picture_data)

# Get folder statistics
stats = organizer.get_folder_stats()
print("Total files: {0}, Total size: {1} MB".format(
    stats['total_files'], stats['total_size_mb']))
```

### batch_manager.py

**Purpose**: Coordinate batch downloads with all components

**Key Features**:
- Integrates slooh_client, download_manager, file_organizer, download_tracker
- Skip already downloaded images (via tracker)
- Skip existing files (via filesystem check)
- Session tracking
- Progress callbacks
- Download statistics
- Resume failed downloads

**Usage**:
```python
batch_manager = BatchManager(
    config.config, slooh_client, download_manager, 
    file_organizer, download_tracker, logger)

# Download all new images
stats = batch_manager.download_all_pictures()

# Download specific mission
stats = batch_manager.download_mission(mission_id=12345)

# Download since last session
stats = batch_manager.download_new_since_last_session()

# Resume failed downloads
stats = batch_manager.resume_failed_downloads()
```

**Session Statistics**:
```python
{
    'total_available': 1500,      # Total images on Slooh
    'already_downloaded': 1200,   # In tracker
    'skipped_existing': 50,       # File exists but not in tracker
    'queued': 250,                # New to download
    'downloaded': 245,            # Successfully downloaded
    'failed': 5,                  # Failed to download
    'total_bytes': 104857600      # Total bytes (100 MB)
}
```

## CLI Commands (main.py Enhanced)

### --configure
Interactive configuration setup. Prompts for:
- Slooh username and password
- Download folder location
- Batch size

### --test
Test authentication and API access:
1. Connect to Slooh
2. Authenticate with credentials
3. Test API access (get missions)

### --download
Download all new images:
- Checks tracker for already downloaded images
- Checks filesystem for existing files
- Downloads only new images
- Shows progress and statistics

### --download-all
Download ALL images (bypass tracker):
- Prompts for confirmation
- Downloads all images even if already tracked
- Use with caution!

### --mission <id>
Download specific mission:
```bash
ipy src/main.py --mission 12345
```

### --retry
Retry failed downloads from last session:
- Gets failed downloads from tracker
- Attempts to re-download each
- Updates tracker with results

### --stats
Show download statistics:
- Total images downloaded
- Success rate
- Total sessions
- Total size
- Last download date
- Folder statistics

## Configuration Options (Stage 2)

```json
{
  "download": {
    "batch_size": 50,           // Images per API request
    "threads": 4,                // Concurrent download threads
    "rate_limit": 30,            // Max requests per minute (0 = unlimited)
    "timeout": 300,              // HTTP timeout in seconds
    "max_retries": 3,            // Retry attempts for failed downloads
    "retry_delay": 5,            // Seconds between retries
    "skip_existing": true,       // Skip if file exists
    "check_tracker": true,       // Check download tracker
    "handle_duplicates": "skip", // skip, overwrite, or rename
    "verify_hash": false         // Verify MD5 hash (not used by Slooh)
  },
  "folders": {
    "base_path": "SloohImages",                     // Root download folder
    "template": "{object}/{telescope}/{format}",    // Folder structure
    "filename_template": "{telescope}_{filename}",  // Filename pattern
    "organize_by": "object",                        // object, date, or telescope
    "unknown_object": "Unknown"                     // Name for unidentified objects
  }
}
```

## Test Scripts

### test_slooh_client.py
Tests Slooh API client functionality:
1. Get session token
2. Authenticate with credentials
3. Get missions
4. Get pictures
5. Test iterator methods

Run: `ipy tests/test_slooh_client.py`

**Note**: Requires valid Slooh credentials in config.json

### test_file_organizer.py
Tests file organization without downloads:
1. Sanitize filenames
2. Extract object names from titles
3. Determine image types
4. Generate destination paths
5. Check file existence
6. Handle duplicates
7. Get folder statistics

Run: `ipy tests/test_file_organizer.py`

### test_download_manager.py
Tests download manager functionality:
1. Create download tasks
2. Initialize download manager
3. Get progress information
4. Rate limiting logic
5. Download small test file (from httpbin.org)
6. Get download statistics

Run: `ipy tests/test_download_manager.py`

## Example Workflow

### First-Time Setup
```bash
# Configure credentials
ipy src/main.py --configure
  Username: your_username
  Password: ********
  Root download folder [SloohImages]: D:\Astronomy\Slooh
  Batch size [50]: 50

# Test configuration
ipy src/main.py --test
```

### Regular Usage
```bash
# Download new images since last session
ipy src/main.py --download

# Check statistics
ipy src/main.py --stats
```

### If Downloads Fail
```bash
# Retry failed downloads
ipy src/main.py --retry
```

## Folder Structure Example

With default templates, images are organized as:
```
SloohImages/
├── M31/
│   ├── Chile One/
│   │   ├── JPEG/
│   │   │   ├── Chile One_image_001.jpg
│   │   │   └── Chile One_image_002.jpg
│   │   └── FITS/
│   │       └── Chile One_image_003.fits
│   └── Chile Two/
│       └── Pictures/
│           └── Chile Two_image_004.png
├── NGC7000/
│   └── Canary One/
│       ├── JPEG/
│       │   └── Canary One_image_005.jpg
│       └── FITS/
│           └── Canary One_image_006.fits
└── Unknown/
    └── Generic Telescope/
        └── JPEG/
            └── Generic Telescope_image_007.jpg
```

## Performance Considerations

### Threading
- Default 4 threads balances speed vs. system resources
- Can increase for faster connections: `"threads": 8`
- Monitor CPU/network usage

### Rate Limiting
- Default 30 requests/minute prevents Slooh API throttling
- Can disable: `"rate_limit": 0` (not recommended)
- Slooh may have undocumented rate limits

### Batch Size
- Default 50 images per API call
- Larger batches = fewer API calls
- Balance with memory usage

### Skip Existing
- `"skip_existing": true` - Fast, checks filesystem
- `"check_tracker": true` - Even faster, checks JSON only
- Both enabled = optimal performance

## Error Handling

### Network Errors
- Automatic retry with exponential backoff
- Max 3 retries by default
- Logs all errors to file

### Authentication Errors
- Clear error messages
- Prompts to reconfigure credentials
- Session token refresh on expiry

### File System Errors
- Creates directories as needed
- Handles invalid characters in filenames
- Detects and reports disk space issues

## Troubleshooting

### "Authentication failed"
- Verify credentials: `ipy src/main.py --configure`
- Test connection: `ipy src/main.py --test`

### "Rate limit reached"
- Increase `"retry_delay"` in config
- Reduce `"rate_limit"` (requests per minute)

### "Failed to download"
- Check internet connection
- Run `--retry` to resume
- Check logs in `data/logs/`

### "File exists"
- By design - prevents re-downloading
- Use `"handle_duplicates": "rename"` to keep both
- Use `--download-all` to force re-download

## Next Steps (Stage 3)

Stage 3 will add Windows Forms GUI:
- Visual progress display with live updates
- Start/Stop/Pause download controls
- Configuration editor
- Download history browser
- Image preview thumbnails
- Statistics dashboard

## Technical Notes

### .NET Integration
- Uses `System.Net.Http.HttpClient` for HTTP requests
- Uses `System.Threading.ThreadPool` for concurrent downloads
- Uses `System.IO` for file operations
- No external Python packages required

### JSON Tracking
- All download history in `data/download_tracker.json`
- Automatic backup on every save
- Easy to inspect, edit, or reset
- Scales to thousands of images

### Thread Safety
- All shared data protected by locks
- Safe to call from multiple threads
- Progress callbacks are thread-safe

## Known Issues

1. **Progress callbacks may lag** - Due to threading, console updates might appear delayed
2. **Large batch sizes** - May cause memory issues with thousands of images
3. **Long filenames** - Windows has 260 character path limit (handled via sanitization)

## Support

For issues or questions:
1. Check logs in `data/logs/`
2. Run tests: `ipy tests/test_slooh_client.py`
3. Review configuration in `config/config.json`
4. Check main README.md for general information
