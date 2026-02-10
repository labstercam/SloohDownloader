"""
Slooh Image Downloader - Logger
Simple logging system with file and console output.
"""

import clr
clr.AddReference('System')
from System import DateTime, IO
from System.IO import File, Path, Directory, StreamWriter, FileMode
from datetime import datetime as py_datetime


class Logger(object):
    """Simple logging system for IronPython"""
    
    # Log levels
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4
    
    LEVEL_NAMES = {
        DEBUG: 'DEBUG',
        INFO: 'INFO',
        WARNING: 'WARNING',
        ERROR: 'ERROR',
        CRITICAL: 'CRITICAL'
    }
    
    def __init__(self, name='SloohDownloader', log_folder=None, level=INFO):
        """
        Initialize logger.
        
        Args:
            name: Logger name
            log_folder: Folder for log files
            level: Minimum log level to record
        """
        self.name = name
        self.level = level
        self.log_folder = log_folder
        self.log_file_path = None
        self.writer = None
        self.callbacks = []  # List of callback functions for custom handlers (e.g., GUI)
        
        if log_folder:
            self._setup_log_file()
    
    def _setup_log_file(self):
        """Setup log file with timestamp"""
        if not Directory.Exists(self.log_folder):
            Directory.CreateDirectory(self.log_folder)
        
        # Create log file with timestamp
        timestamp = py_datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = "{0}_{1}.log".format(self.name, timestamp)
        self.log_file_path = Path.Combine(self.log_folder, filename)
        
        # Open file stream for appending
        self.writer = StreamWriter(self.log_file_path, True)
    
    def _write(self, level, message):
        """Internal write method"""
        if level < self.level:
            return
        
        # Format log entry
        timestamp = py_datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        level_name = self.LEVEL_NAMES.get(level, 'UNKNOWN')
        formatted = "[{0}] {1}: {2}".format(timestamp, level_name, message)
        
        # Write to console
        print(formatted)
        
        # Write to file if configured
        if self.writer:
            try:
                self.writer.WriteLine(formatted)
                self.writer.Flush()
            except Exception as e:
                print("Error writing to log file: {0}".format(str(e)))
        
        # Call registered callbacks (e.g., GUI handlers)
        for callback in self.callbacks:
            try:
                callback(level, message)
            except Exception as e:
                print("Error in log callback: {0}".format(str(e)))
    
    def debug(self, message):
        """Log debug message"""
        self._write(self.DEBUG, message)
    
    def info(self, message):
        """Log info message"""
        self._write(self.INFO, message)
    
    def warning(self, message):
        """Log warning message"""
        self._write(self.WARNING, message)
    
    def error(self, message):
        """Log error message"""
        self._write(self.ERROR, message)
    
    def critical(self, message):
        """Log critical message"""
        self._write(self.CRITICAL, message)
    
    def exception(self, message, exc):
        """Log exception with stack trace"""
        full_message = "{0}\nException: {1}".format(message, str(exc))
        self._write(self.ERROR, full_message)
    
    def add_callback(self, callback):
        """Add a callback function to receive log messages
        
        Args:
            callback: Function with signature callback(level, message)
        """
        if callback not in self.callbacks:
            self.callbacks.append(callback)
    
    def remove_callback(self, callback):
        """Remove a callback function
        
        Args:
            callback: The callback function to remove
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def close(self):
        """Close log file"""
        if self.writer:
            self.writer.Close()
            self.writer = None
    
    def __del__(self):
        """Cleanup"""
        self.close()


# Global logger instance
_global_logger = None

def get_logger(name='SloohDownloader', config=None):
    """Get or create global logger instance"""
    global _global_logger
    if _global_logger is None:
        log_folder = None
        level = Logger.INFO
        
        if config:
            if config.get('logging.enabled', True):
                log_folder = config.get('logging.log_folder')
            
            level_name = config.get('logging.log_level', 'INFO').upper()
            level_map = {
                'DEBUG': Logger.DEBUG,
                'INFO': Logger.INFO,
                'WARNING': Logger.WARNING,
                'ERROR': Logger.ERROR,
                'CRITICAL': Logger.CRITICAL
            }
            level = level_map.get(level_name, Logger.INFO)
        
        _global_logger = Logger(name, log_folder, level)
    
    return _global_logger
