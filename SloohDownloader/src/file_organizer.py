"""
Slooh Image Downloader - File Organizer
Handles file naming and folder organization based on templates.
"""

import os
import re
from datetime import datetime


class FileOrganizer(object):
    """Organizes downloaded files into folder structure based on file format"""
    
    def __init__(self, config, logger=None):
        """
        Initialize file organizer.
        
        Args:
            config: Configuration dictionary with folder settings
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        
        # Get settings
        self.base_path = config.get('folders.base_path', 'SloohImages')
        self.folder_template = config.get('folders.template', '{object}/{telescope}/{format}')
        self.filename_template = config.get('folders.filename_template', '{telescope}_{filename}')
        self.unknown_object = config.get('folders.unknown_object', 'Unknown')
        self.organize_by = config.get('folders.organize_by', 'object')  # object, date, telescope
        
        # Ensure base path exists
        if not os.path.isabs(self.base_path):
            self.base_path = os.path.abspath(self.base_path)
        
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)
            self._log('info', "Created base directory: {0}".format(self.base_path))
    
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
    
    def _sanitize_name(self, name):
        """
        Sanitize a name for use in filesystem.
        
        Args:
            name: Name to sanitize
            
        Returns:
            str: Sanitized name
        """
        if not name:
            return self.unknown_object
        
        # Remove or replace invalid characters
        # Windows: < > : " / \ | ? *
        # Also replace multiple spaces with single space
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        name = re.sub(r'\s+', ' ', name)
        name = name.strip('. ')  # Remove leading/trailing dots and spaces
        
        # Ensure not empty
        if not name:
            return self.unknown_object
        
        return name
    
    def _extract_object_name(self, title):
        """
        Extract object name from image title.
        
        Args:
            title: Image title
            
        Returns:
            str: Object name or Unknown
        """
        if not title:
            return self.unknown_object
        
        # Common patterns in Slooh titles:
        # "Trifid Nebula (M20)" - keep both name and catalog
        # "M31 - Andromeda Galaxy" - keep both
        # "NGC 7000 - North America Nebula" - keep both
        # "Coalsack Cluster (NGC 4609)" - keep both
        
        title = title.strip()
        
        # Check for "Name (Catalog)" pattern - keep both
        if '(' in title and ')' in title:
            # Has parenthetical catalog designation - keep entire string
            return self._sanitize_name(title)
        
        # Check for "Catalog - Name" pattern - keep both
        if '-' in title:
            # Keep entire string if it has a dash (likely "Catalog - Name" format)
            return self._sanitize_name(title)
        
        # Use first part before comma
        if ',' in title:
            first_part = title.split(',')[0].strip()
            if first_part and len(first_part) > 2:
                return self._sanitize_name(first_part)
        
        # Use whole title if reasonable length
        if len(title) <= 50:
            return self._sanitize_name(title)
        
        # Use first 50 characters
        return self._sanitize_name(title[:50])
    
    def _format_date(self, timestamp):
        """
        Format timestamp for folder name.
        
        Args:
            timestamp: datetime object or ISO string
            
        Returns:
            str: Formatted date (YYYY-MM-DD)
        """
        if isinstance(timestamp, str):
            # Parse ISO format manually (Python 3.4 doesn't have fromisoformat)
            timestamp_str = timestamp.replace('Z', '+00:00')
            if '+' in timestamp_str:
                timestamp_str = timestamp_str.split('+')[0]
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S')
        
        return timestamp.strftime('%Y-%m-%d')
    
    def _get_image_type(self, picture_data):
        """
        Determine image format from file extension.
        
        Args:
            picture_data: Picture dictionary
            
        Returns:
            str: Image format folder name ('FITS', 'PNG', or 'JPEG')
        """
        # Get filename from download URL
        download_url = picture_data.get('imageDownloadURL', '')
        if download_url:
            # Extract filename from URL (last part after /)
            filename = download_url.split('/')[-1]
            # Remove any query parameters
            if '?' in filename:
                filename = filename.split('?')[0]
        else:
            filename = picture_data.get('imageDownloadFilename', 'image.jpg')
        
        ext = filename.lower()
        
        # Determine format based on extension
        if ext.endswith('.fits') or ext.endswith('.fit'):
            return 'FITS'
        elif ext.endswith('.jpg') or ext.endswith('.jpeg'):
            return 'JPEG'
        elif ext.endswith('.png'):
            return 'PNG'
        
        # Default to JPEG for unknown
        return 'JPEG'
    
    def get_destination_path(self, picture_data):
        """
        Generate destination path for a picture.
        
        Args:
            picture_data: Picture dictionary with metadata
            
        Returns:
            str: Full path where file should be saved
        """
        # Extract metadata
        title = picture_data.get('imageTitle', picture_data.get('title', ''))
        telescope = picture_data.get('telescopeName', 'Unknown')
        instrument = picture_data.get('instrumentName', 'Unknown')
        
        # Get the actual Slooh filename from the download URL
        download_url = picture_data.get('imageDownloadURL', '')
        if download_url:
            # Extract filename from URL (last part after /)
            filename = download_url.split('/')[-1]
            # Remove any query parameters
            if '?' in filename:
                filename = filename.split('?')[0]
        else:
            filename = picture_data.get('imageDownloadFilename', 'image.jpg')
        
        timestamp = picture_data.get('timestamp')
        
        # Build replacement dictionary
        replacements = {
            'object': self._extract_object_name(title),
            'telescope': self._sanitize_name(telescope),
            'instrument': self._sanitize_name(instrument),
            'type': self._get_image_type(picture_data),
            'format': self._get_image_type(picture_data),  # Alias for clarity
            'filename': filename,
            'title': self._sanitize_name(title) if title else 'Untitled'
        }
        
        # Add date components if timestamp available
        if timestamp:
            if isinstance(timestamp, str):
                # Parse ISO format manually (Python 3.4 doesn't have fromisoformat)
                # Format: 2026-02-08T19:10:57Z or 2026-02-08T19:10:57+00:00
                timestamp_str = timestamp.replace('Z', '+00:00')
                if '+' in timestamp_str:
                    timestamp_str = timestamp_str.split('+')[0]
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S')
            
            replacements.update({
                'date': timestamp.strftime('%Y-%m-%d'),
                'year': timestamp.strftime('%Y'),
                'month': timestamp.strftime('%m'),
                'day': timestamp.strftime('%d')
            })
        
        # Format folder path
        folder_path = self.folder_template
        for key, value in replacements.items():
            folder_path = folder_path.replace('{' + key + '}', value)
        
        # Format filename
        new_filename = self.filename_template
        for key, value in replacements.items():
            new_filename = new_filename.replace('{' + key + '}', value)
        
        # Combine into full path
        full_path = os.path.join(self.base_path, folder_path, new_filename)
        full_path = os.path.normpath(full_path)
        
        self._log('debug', "Destination path: {0}".format(full_path))
        
        return full_path
    
    def check_exists(self, picture_data):
        """
        Check if a picture already exists at its destination.
        
        Args:
            picture_data: Picture dictionary
            
        Returns:
            tuple: (exists: bool, path: str)
        """
        path = self.get_destination_path(picture_data)
        exists = os.path.exists(path)
        
        return (exists, path)
    
    def get_duplicate_path(self, original_path):
        """
        Generate a new path for a duplicate file.
        
        Args:
            original_path: Original file path
            
        Returns:
            str: New path with (n) suffix
        """
        directory = os.path.dirname(original_path)
        filename = os.path.basename(original_path)
        name, ext = os.path.splitext(filename)
        
        counter = 1
        while True:
            new_name = "{0} ({1}){2}".format(name, counter, ext)
            new_path = os.path.join(directory, new_name)
            
            if not os.path.exists(new_path):
                return new_path
            
            counter += 1
    
    def organize_file(self, source_path, picture_data, handle_duplicates='skip'):
        """
        Move or copy a file to its organized location.
        
        Args:
            source_path: Current file location
            picture_data: Picture metadata
            handle_duplicates: How to handle duplicates ('skip', 'overwrite', 'rename')
            
        Returns:
            tuple: (success: bool, destination: str, was_duplicate: bool)
        """
        if not os.path.exists(source_path):
            self._log('error', "Source file not found: {0}".format(source_path))
            return (False, None, False)
        
        # Get destination
        dest_path = self.get_destination_path(picture_data)
        
        # Check for duplicate
        is_duplicate = os.path.exists(dest_path)
        
        if is_duplicate:
            if handle_duplicates == 'skip':
                self._log('debug', "Skipping duplicate: {0}".format(dest_path))
                return (True, dest_path, True)
            elif handle_duplicates == 'rename':
                dest_path = self.get_duplicate_path(dest_path)
                self._log('debug', "Renaming duplicate to: {0}".format(dest_path))
            elif handle_duplicates == 'overwrite':
                self._log('debug', "Overwriting: {0}".format(dest_path))
        
        # Create destination directory
        dest_dir = os.path.dirname(dest_path)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        
        # Move file
        try:
            if source_path != dest_path:
                import shutil
                shutil.move(source_path, dest_path)
                self._log('info', "Organized: {0}".format(dest_path))
            
            return (True, dest_path, is_duplicate)
            
        except Exception as e:
            self._log('error', "Failed to organize file: {0}".format(str(e)))
            return (False, None, is_duplicate)
    
    def get_folder_stats(self):
        """
        Get statistics about organized folders.
        
        Returns:
            dict: Statistics dictionary
        """
        stats = {
            'base_path': self.base_path,
            'total_files': 0,
            'total_size': 0,
            'folders': {}
        }
        
        if not os.path.exists(self.base_path):
            return stats
        
        # Walk directory tree
        for root, dirs, files in os.walk(self.base_path):
            if files:
                rel_path = os.path.relpath(root, self.base_path)
                folder_size = 0
                
                for filename in files:
                    filepath = os.path.join(root, filename)
                    try:
                        file_size = os.path.getsize(filepath)
                        folder_size += file_size
                        stats['total_size'] += file_size
                        stats['total_files'] += 1
                    except:
                        pass
                
                stats['folders'][rel_path] = {
                    'count': len(files),
                    'size': folder_size,
                    'size_mb': round(folder_size / (1024.0 * 1024.0), 2)
                }
        
        stats['total_size_mb'] = round(stats['total_size'] / (1024.0 * 1024.0), 2)
        
        return stats
