"""
Slooh Image Downloader - Download Manager
Handles multi-threaded downloads with retry logic and rate limiting.
"""

import clr
clr.AddReference('System')
clr.AddReference('System.Net.Http')
from System import Uri, Threading, TimeSpan
from System.Net.Http import HttpClient, HttpClientHandler
from System.IO import FileStream, FileMode, FileAccess
from System.Threading import ThreadPool, WaitCallback
import time
import os
from datetime import datetime
import hashlib
import threading  # Use Python's threading for locks


def parse_iso_timestamp(timestamp_str):
    """Parse ISO timestamp manually (Python 3.4 compatible)"""
    # Format: 2026-02-08T19:10:57Z or 2026-02-08T19:10:57+00:00
    timestamp_str = timestamp_str.replace('Z', '+00:00')
    if '+' in timestamp_str:
        timestamp_str = timestamp_str.split('+')[0]
    return datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S')


class DownloadTask(object):
    """Represents a single download task"""
    
    def __init__(self, url, destination, image_id, metadata=None):
        """
        Initialize download task.
        
        Args:
            url: URL to download from
            destination: Local file path to save to
            image_id: Unique identifier for the image
            metadata: Additional metadata dictionary
        """
        self.url = url
        self.destination = destination
        self.image_id = image_id
        self.metadata = metadata or {}
        self.status = 'pending'  # pending, downloading, completed, failed
        self.error = None
        self.start_time = None
        self.end_time = None
        self.file_size = 0
        self.retries = 0


class DownloadManager(object):
    """Manages multi-threaded downloads with rate limiting and retry logic"""
    
    def __init__(self, config, logger=None):
        """
        Initialize download manager.
        
        Args:
            config: Configuration dictionary with download settings
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        
        # Download settings
        self.max_retries = config.get('download.max_retries', 3)
        self.retry_delay = config.get('download.retry_delay', 5)
        self.rate_limit = config.get('download.rate_limit', 30)  # requests per minute
        self.timeout = config.get('download.timeout', 300)  # seconds
        self.thread_count = config.get('download.threads', 4)
        self.verify_hash = config.get('download.verify_hash', False)
        
        # Setup HTTP client
        self.handler = HttpClientHandler()
        self.handler.UseCookies = False
        self.client = HttpClient(self.handler)
        self.client.Timeout = TimeSpan.FromSeconds(self.timeout)
        
        # Threading
        self.active_downloads = []
        self.completed_downloads = []
        self.failed_downloads = []
        self.lock = threading.Lock()  # Use Python threading
        
        # Rate limiting
        self.download_times = []
        self.rate_limit_lock = threading.Lock()  # Use Python threading
        
        # Progress tracking
        self.total_tasks = 0
        self.completed_count = 0
        self.failed_count = 0
        self.total_bytes = 0
        
        # Control flags
        self.is_cancelled = False
        self.is_paused = False
        
        # Callbacks
        self.on_progress = None
        self.on_complete = None
        self.on_error = None
    
    def _log(self, level, message):
        """Internal logging helper"""
        if self.logger:
            if level == 'debug':
                self.logger.debug(message)
            elif level == 'info':
                self.logger.info(message)
            elif level == 'warning':
                self.logger.warning(message)
            elif level == 'error':
                self.logger.error(message)
    
    def _wait_for_rate_limit(self):
        """Enforce rate limiting"""
        if self.rate_limit <= 0:
            return
        
        with self.rate_limit_lock:
            now = time.time()
            
            # Remove old timestamps (older than 1 minute)
            self.download_times = [t for t in self.download_times if now - t < 60]
            
            # Check if we've hit the rate limit
            if len(self.download_times) >= self.rate_limit:
                # Wait until we can proceed
                oldest = self.download_times[0]
                wait_time = 60 - (now - oldest)
                
                if wait_time > 0:
                    self._log('debug', "Rate limit reached. Waiting {0:.1f}s...".format(wait_time))
                    time.sleep(wait_time)
            
            # Record this download time
            self.download_times.append(time.time())
    
    def _download_file(self, task):
        """
        Download a single file.
        
        Args:
            task: DownloadTask instance
            
        Returns:
            bool: True if successful
        """
        task.status = 'downloading'
        task.start_time = datetime.now()
        
        try:
            # Check if cancelled
            if self.is_cancelled:
                task.status = 'cancelled'
                task.error = 'Download cancelled by user'
                return False
            
            # Wait while paused
            while self.is_paused:
                if self.is_cancelled:
                    task.status = 'cancelled'
                    task.error = 'Download cancelled by user'
                    return False
                time.sleep(0.5)
            
            # Wait for rate limit
            self._wait_for_rate_limit()
            
            # Create destination directory if needed
            dest_dir = os.path.dirname(task.destination)
            if dest_dir and not os.path.exists(dest_dir):
                try:
                    os.makedirs(dest_dir)
                except OSError as e:
                    # Ignore "already exists" error (race condition with multiple threads)
                    if e.errno != 183 and not os.path.exists(dest_dir):
                        raise
            
            # Log full destination path
            self._log('info', "Saving to: {0}".format(task.destination))
            
            # Download file
            self._log('debug', "Downloading: {0}".format(task.url))
            
            response = self.client.GetAsync(task.url).Result
            response.EnsureSuccessStatusCode()
            
            # Save to file
            content = response.Content.ReadAsByteArrayAsync().Result
            task.file_size = len(content)
            
            with open(task.destination, 'wb') as f:
                f.write(content)
            
            # Verify hash if requested
            if self.verify_hash and 'md5' in task.metadata:
                file_hash = self._calculate_md5(task.destination)
                expected_hash = task.metadata['md5']
                
                if file_hash != expected_hash:
                    raise Exception("Hash mismatch: expected {0}, got {1}".format(
                        expected_hash, file_hash))
            
            # Set file timestamp if provided
            if 'timestamp' in task.metadata:
                try:
                    timestamp = task.metadata['timestamp']
                    if isinstance(timestamp, str):
                        timestamp = parse_iso_timestamp(timestamp)
                    
                    # Set both creation and modification time
                    timestamp_ticks = int((timestamp - datetime(1970, 1, 1)).total_seconds())
                    os.utime(task.destination, (timestamp_ticks, timestamp_ticks))
                except Exception as e:
                    self._log('warning', "Failed to set file timestamp: {0}".format(str(e)))
            
            task.status = 'completed'
            task.end_time = datetime.now()
            
            self._log('info', "Downloaded: {0} ({1} bytes)".format(
                os.path.basename(task.destination), task.file_size))
            
            return True
            
        except Exception as e:
            task.error = str(e)
            task.status = 'failed'
            task.end_time = datetime.now()
            
            self._log('error', "Download failed: {0} - {1}".format(task.url, str(e)))
            
            return False
    
    def _calculate_md5(self, filepath):
        """Calculate MD5 hash of file"""
        md5 = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                md5.update(chunk)
        return md5.hexdigest()
    
    def _download_worker(self, task):
        """
        Worker function for threaded downloads.
        
        Args:
            task: DownloadTask instance
        """
        try:
            # Retry loop
            for attempt in range(self.max_retries):
                # Check if cancelled
                if self.is_cancelled:
                    task.status = 'cancelled'
                    with self.lock:
                        self.failed_downloads.append(task)
                        self.failed_count += 1
                    return
                
                task.retries = attempt
                
                if self._download_file(task):
                    # Success
                    with self.lock:
                        self.completed_downloads.append(task)
                        self.completed_count += 1
                        self.total_bytes += task.file_size
                    
                    if self.on_complete:
                        self.on_complete(task)
                    
                    return
                
                # Failed - retry if possible
                if attempt < self.max_retries - 1:
                    self._log('warning', "Retry {0}/{1} for: {2}".format(
                        attempt + 1, self.max_retries - 1, task.url))
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
            
            # All retries failed
            with self.lock:
                self.failed_downloads.append(task)
                self.failed_count += 1
            
            if self.on_error:
                self.on_error(task)
                
        except Exception as e:
            self._log('error', "Worker exception: {0}".format(str(e)))
            
            with self.lock:
                self.failed_downloads.append(task)
                self.failed_count += 1
            
            if self.on_error:
                self.on_error(task)
        finally:
            with self.lock:
                self.active_downloads.remove(task)
            
            if self.on_progress:
                self.on_progress(self.get_progress())
    
    def download(self, tasks):
        """
        Download multiple files using thread pool.
        
        Args:
            tasks: List of DownloadTask instances
            
        Returns:
            dict: Download statistics
        """
        if not tasks:
            return self.get_statistics()
        
        self.total_tasks = len(tasks)
        self.completed_count = 0
        self.failed_count = 0
        self.total_bytes = 0
        
        self._log('info', "Starting download of {0} files...".format(self.total_tasks))
        
        # Queue all tasks
        for task in tasks:
            with self.lock:
                self.active_downloads.append(task)
            
            # Queue work on thread pool
            ThreadPool.QueueUserWorkItem(
                WaitCallback(lambda state: self._download_worker(state)), task)
        
        # Wait for all downloads to complete
        while True:
            with self.lock:
                active_count = len(self.active_downloads)
            
            if active_count == 0:
                break
            
            # Check if cancelled - abort remaining tasks
            if self.is_cancelled:
                self._log('info', "Download cancelled - waiting for active tasks to abort...")
                # Wait a bit more for threads to finish their current operation
                time.sleep(1.0)
                # Mark any remaining active tasks as cancelled
                with self.lock:
                    for task in self.active_downloads:
                        if task.status == 'downloading':
                            task.status = 'cancelled'
                            task.error = 'Cancelled by user'
                break
            
            time.sleep(0.5)
        
        stats = self.get_statistics()
        self._log('info', "Download complete: {0} succeeded, {1} failed, {2} MB total".format(
            stats['completed'], stats['failed'], stats['total_mb']))
        
        return stats
    
    def get_progress(self):
        """
        Get current download progress.
        
        Returns:
            dict: Progress information
        """
        with self.lock:
            return {
                'total': self.total_tasks,
                'completed': self.completed_count,
                'current': self.completed_count,  # Alias for GUI compatibility
                'failed': self.failed_count,
                'active': len(self.active_downloads),
                'percent': (self.completed_count * 100.0 / self.total_tasks) if self.total_tasks > 0 else 0
            }
    
    def get_statistics(self):
        """
        Get download statistics.
        
        Returns:
            dict: Statistics dictionary
        """
        return {
            'total': self.total_tasks,
            'completed': self.completed_count,
            'failed': self.failed_count,
            'total_bytes': self.total_bytes,
            'total_mb': round(self.total_bytes / (1024.0 * 1024.0), 2),
            'completed_tasks': self.completed_downloads,
            'failed_tasks': self.failed_downloads
        }
    
    def clear(self):
        """Clear completed and failed downloads"""
        with self.lock:
            self.completed_downloads = []
            self.failed_downloads = []
    
    def reset_control_flags(self):
        """Reset control flags for a new download session"""
        self.is_cancelled = False
        self.is_paused = False
    
    def close(self):
        """Close HTTP client"""
        if self.client:
            self.client.Dispose()
    
    def __del__(self):
        """Cleanup"""
        self.close()
