# Changelog

All notable changes to Slooh Image Downloader will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-10

### Added

#### Core Features
- Multi-threaded bulk download engine with configurable thread count (default: 4)
- JSON-based download tracking system to prevent duplicate downloads
- Batch processing system (50 images per batch) with detailed progress tracking
- Pause/Resume/Stop controls for download sessions
- Rate limiting with configurable requests per minute (default: 30)
- Automatic retry logic with exponential backoff (default: 3 retries)

#### Filtering & Selection
- Date range filtering (start date and end date)
- Multi-select telescope filter
- Object name filter (case-insensitive partial match)
- Image type filter (PNG, FITS, or both)
- Start image number selection with date preview
- Max images and max scan limits for controlled downloads

#### File Organization
- Template-based file organization system
- Support for placeholders: `{object}`, `{telescope}`, `{format}`, `{date}`, `{mission}`
- Automatic directory creation and path sanitization
- Metadata preservation with timestamps

#### User Interface
- Windows Forms GUI with native Windows look and feel
- Five-tab interface (Download, Configuration, History, Statistics, Advanced)
- Real-time progress tracking with batch information
- Live statistics and download counts
- Comprehensive log window with thread-safe updates
- Auto-login with saved credentials
- Dark-themed progress indicators

#### Advanced Features
- Dry run mode to preview downloads
- Force redownload option to bypass tracker
- Export reports in CSV and HTML formats
- Statistics reports with download breakdowns
- Maintenance tools (verify downloads, find orphaned files, clean tracker)
- Configuration management with JSON storage
- Automatic backup of download tracker

#### Distribution
- PowerShell launcher script (`launch.ps1`) for easy startup
- Automated release packaging system
- Comprehensive documentation (README, QUICKSTART, API_DOCUMENTATION)

### Technical Details
- Built with IronPython 3.4+
- Uses .NET Framework 4.6.2+
- Direct .NET integration for HTTP client and threading
- No external dependencies required
- Windows Forms for native GUI

### Documentation
- Complete user documentation with step-by-step guides
- API documentation for Slooh endpoints
- Troubleshooting guides
- Release creation guides

---

## Release Notes Template

For future releases, use this template:

## [X.Y.Z] - YYYY-MM-DD

### Added
- New features go here

### Changed
- Changes to existing functionality

### Deprecated
- Features marked for removal

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security patches
