"""
Slooh Image Downloader - Configuration Manager
Handles loading, saving, and validating configuration settings.
"""

import clr
clr.AddReference('System')
from System import IO, Environment
from System.IO import File, Path, Directory
import json
import os


class ConfigurationManager(object):
    """Manages application configuration with JSON persistence"""
    
    def __init__(self, config_path=None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to config file. If None, uses default location.
        """
        if config_path is None:
            # Default to config/config.json relative to script location
            script_dir = Path.GetDirectoryName(__file__)
            config_path = Path.Combine(script_dir, '..', 'config', 'config.json')
        
        self.config_path = Path.GetFullPath(config_path)
        self.template_path = Path.Combine(
            Path.GetDirectoryName(self.config_path),
            'config.template.json'
        )
        self.config = None
        
    def load(self):
        """
        Load configuration from file. Creates default if not exists.
        
        Returns:
            dict: Configuration dictionary
            
        Raises:
            Exception: If configuration cannot be loaded or created
        """
        # If config doesn't exist, create with defaults
        if not File.Exists(self.config_path):
            self._create_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            
            # Expand paths to absolute
            self._expand_paths()
            
            return self.config
            
        except Exception as e:
            raise Exception("Failed to load configuration: {0}".format(str(e)))
    
    def save(self):
        """
        Save current configuration to file.
        
        Raises:
            Exception: If configuration cannot be saved
        """
        if self.config is None:
            raise Exception("No configuration loaded to save")
        
        try:
            # Ensure directory exists
            config_dir = Path.GetDirectoryName(self.config_path)
            if not Directory.Exists(config_dir):
                Directory.CreateDirectory(config_dir)
            
            # Write configuration
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
                
        except Exception as e:
            raise Exception("Failed to save configuration: {0}".format(str(e)))
    
    def get(self, key_path, default=None):
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path (e.g., 'slooh.username')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        if self.config is None:
            self.load()
        
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path, value):
        """
        Set configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path (e.g., 'slooh.username')
            value: Value to set
        """
        if self.config is None:
            self.load()
        
        keys = key_path.split('.')
        target = self.config
        
        # Navigate to parent of target key
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        
        # Set the value
        target[keys[-1]] = value
    
    def _create_default_config(self):
        """Create default configuration"""
        self.config = {
            'slooh': {
                'username': '',
                'password': '',
                'base_url': 'https://app.slooh.com'
            },
            'folders': {
                'base_path': 'SloohImages',
                'template': '{object}/{telescope}/{format}',
                'filename_template': '{telescope}_{filename}',
                'organize_by': 'object',
                'unknown_object': 'Unknown'
            },
            'download': {
                'root_folder': None,
                'batch_size': 50,
                'threads': 4,
                'rate_limit': 30,
                'timeout': 300,
                'max_retries': 3,
                'retry_delay': 5,
                'skip_existing': True,
                'check_tracker': True,
                'handle_duplicates': 'skip',
                'verify_hash': False
            },
            'tracking': {
                'tracker_file': 'data/download_tracker.json',
                'backup_on_save': True
            },

            'logging': {
                'log_folder': 'logs',
                'log_level': 'INFO',
                'max_log_size_mb': 10,
                'keep_logs_days': 30
            }
        }
        
        # Save default config
        self.save()
        print("Created default configuration file: {0}".format(self.config_path))
    
    def set_credentials(self, username, password):
        """
        Set Slooh credentials
        
        Args:
            username: Slooh username/email
            password: Slooh password
        """
        if self.config is None:
            self.load()
        
        self.set('slooh.username', username)
        self.set('slooh.password', password)
    
    def get_all(self):
        """
        Get all configuration settings
        
        Returns:
            dict: Complete configuration dictionary
        """
        if self.config is None:
            self.load()
        
        return self.config
    
    def validate(self):
        """
        Validate required configuration keys exist
        
        Returns:
            bool: True if valid, False otherwise
        """
        if self.config is None:
            self.load()
        
        required_keys = [
            'slooh.base_url',
            'download.root_folder'
        ]
        
        for key_path in required_keys:
            value = self.get(key_path)
            if value is None or (isinstance(value, str) and value.strip() == ''):
                return False
        
        return True
    
    def _create_from_template(self):
        """Create config file from template (legacy - not used)"""
        # This method is no longer used - we create defaults directly
        pass
    
    def _validate(self):
        """Validate required configuration keys exist (legacy - use validate() instead)"""
        pass
    
    def _expand_paths(self):
        """Expand relative paths to absolute paths"""
        # Get base directory (where config file is located)
        base_dir = Path.GetDirectoryName(Path.GetDirectoryName(self.config_path))
        
        # Paths to expand
        path_keys = [
            'download.root_folder',
            'database.path',
            'database.backup_path',
            'logging.log_folder'
        ]
        
        for key_path in path_keys:
            path = self.get(key_path)
            if path and not Path.IsPathRooted(path):
                # Relative path - make it absolute based on base_dir
                abs_path = Path.GetFullPath(Path.Combine(base_dir, path))
                self.set(key_path, abs_path)
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [
            self.get('download.root_folder'),
            self.get('database.backup_path'),
            self.get('logging.log_folder'),
            Path.GetDirectoryName(self.get('database.path'))
        ]
        
        for directory in directories:
            if directory and not Directory.Exists(directory):
                try:
                    Directory.CreateDirectory(directory)
                    print("Created directory: {0}".format(directory))
                except Exception as e:
                    print("Warning: Could not create directory {0}: {1}".format(
                        directory, str(e)))
    
    def has_credentials(self):
        """Check if Slooh credentials are configured"""
        username = self.get('slooh.username', '').strip()
        password = self.get('slooh.password', '').strip()
        return username != '' and password != ''
    
    def __str__(self):
        """String representation (hides sensitive data)"""
        if self.config is None:
            return "ConfigurationManager(not loaded)"
        
        # Create safe copy for display
        safe_config = dict(self.config)
        if 'slooh' in safe_config:
            if 'password' in safe_config['slooh']:
                safe_config['slooh']['password'] = '***HIDDEN***'
        
        return json.dumps(safe_config, indent=2)


# Convenience function for quick config access
_global_config = None

def get_config():
    """Get global configuration instance"""
    global _global_config
    if _global_config is None:
        _global_config = ConfigurationManager()
        _global_config.load()
    return _global_config
