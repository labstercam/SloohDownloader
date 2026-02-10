# -*- coding: utf-8 -*-
"""
Simple JSON-based download tracker - No database required!
Tracks downloaded images using plain JSON files for simplicity.
"""

import json
import os
from datetime import datetime
import shutil


class DownloadTracker(object):
    """
    Simple file-based tracking of downloaded images using JSON.
    Much simpler than SQLite - perfect for thousands of images.
    """
    
    def __init__(self, tracker_file):
        """
        Initialize download tracker
        
        Args:
            tracker_file: Path to JSON file for tracking downloads
        """
        self.tracker_file = tracker_file
        self.backup_file = tracker_file + ".backup"
        self.data = {
            'images': {},  # Key: "image_id:type", Value: image info
            'sessions': [],
            'metadata': {
                'created': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'version': '1.0'
            }
        }
        self.current_session = None
        
    def load(self):
        """Load tracking data from JSON file"""
        if os.path.exists(self.tracker_file):
            try:
                with open(self.tracker_file, 'r') as f:
                    self.data = json.load(f)
                return True
            except Exception as e:
                print("Warning: Could not load tracker file: {0}".format(str(e)))
                # Try backup
                if os.path.exists(self.backup_file):
                    print("Attempting to load from backup...")
                    try:
                        with open(self.backup_file, 'r') as f:
                            self.data = json.load(f)
                        print("Loaded from backup successfully")
                        return True
                    except:
                        pass
                return False
        return True  # New file, empty data is OK
        
    def save(self):
        """Save tracking data to JSON file with automatic backup"""
        try:
            # Update metadata
            self.data['metadata']['last_updated'] = datetime.now().isoformat()
            
            # Create backup of existing file
            if os.path.exists(self.tracker_file):
                shutil.copy2(self.tracker_file, self.backup_file)
            
            # Ensure directory exists
            tracker_dir = os.path.dirname(self.tracker_file)
            if tracker_dir and not os.path.exists(tracker_dir):
                os.makedirs(tracker_dir)
            
            # Write new file
            with open(self.tracker_file, 'w') as f:
                json.dump(self.data, f, indent=2)
            
            return True
            
        except Exception as e:
            print("Error saving tracker file: {0}".format(str(e)))
            return False
            
    def create_session(self):
        """
        Start a new download session
        
        Returns:
            Session ID (index in sessions list)
        """
        session = {
            'session_id': len(self.data['sessions']),
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'images_downloaded': 0,
            'images_failed': 0,
            'total_bytes': 0,
            'status': 'running'
        }
        
        self.data['sessions'].append(session)
        self.current_session = session
        self.save()
        
        return session['session_id']
        
    def update_session(self, session_id, images_downloaded=0, images_failed=0,
                      total_bytes=0, status=None):
        """
        Update session statistics
        
        Args:
            session_id: Session ID to update
            images_downloaded: Number of successfully downloaded images
            images_failed: Number of failed downloads
            total_bytes: Total bytes downloaded
            status: Session status (running, completed, failed, aborted)
        """
        if session_id < len(self.data['sessions']):
            session = self.data['sessions'][session_id]
            session['images_downloaded'] += images_downloaded
            session['images_failed'] += images_failed
            session['total_bytes'] += total_bytes
            
            if status:
                session['status'] = status
                
            session['end_time'] = datetime.now().isoformat()
            
            if self.current_session and self.current_session['session_id'] == session_id:
                self.current_session = session
                
            self.save()
            
    def is_image_downloaded(self, image_id, image_type):
        """
        Check if an image has already been downloaded
        
        Args:
            image_id: Slooh image ID
            image_type: Type of image (FITS, PNG, JPG)
            
        Returns:
            True if already downloaded, False otherwise
        """
        key = "{0}:{1}".format(image_id, image_type)
        return key in self.data['images']
        
    def record_download(self, image_id, customer_image_id, mission_id, filename,
                       download_url, file_path, file_size, md5_hash, image_type,
                       telescope_name, object_name, session_id, photoroll_position=None):
        """
        Record a completed download
        
        Args:
            image_id: Slooh image ID
            customer_image_id: Customer-specific image ID
            mission_id: Mission ID
            filename: Original filename
            download_url: URL used for download
            file_path: Local file path where saved
            file_size: File size in bytes
            md5_hash: MD5 hash of file (optional)
            image_type: Type (FITS, PNG, JPG)
            telescope_name: Telescope name
            object_name: Object/target name
            session_id: Session ID
            photoroll_position: Position in photoRoll (1-based, optional)
            
        Returns:
            True if successful
        """
        try:
            key = "{0}:{1}".format(image_id, image_type)
            
            self.data['images'][key] = {
                'image_id': image_id,
                'customer_image_id': customer_image_id,
                'mission_id': mission_id,
                'filename': filename,
                'download_url': download_url,
                'file_path': file_path,
                'file_size': file_size,
                'md5_hash': md5_hash,
                'image_type': image_type,
                'telescope_name': telescope_name,
                'object_name': object_name,
                'photoroll_position': photoroll_position,
                'download_date': datetime.now().isoformat(),
                'session_id': session_id
            }
            
            # Don't save after every record (performance), caller will save
            return True
            
        except Exception as e:
            print("Error recording download: {0}".format(str(e)))
            return False
            
    def get_last_download_date(self):
        """
        Get the date of the most recent download
        
        Returns:
            ISO format date string or None
        """
        if not self.data['images']:
            return None
            
        try:
            # Find the most recent download_date
            dates = [img['download_date'] for img in self.data['images'].values() 
                    if 'download_date' in img]
            
            if dates:
                return max(dates)
            return None
            
        except Exception as e:
            print("Error getting last download date: {0}".format(str(e)))
            return None
            
    def get_statistics(self):
        """
        Get download statistics
        
        Returns:
            Dictionary with statistics
        """
        try:
            stats = {
                'total_images': len(self.data['images']),
                'total_sessions': len(self.data['sessions']),
                'total_bytes': 0,
                'by_type': {},
                'by_telescope': {},
                'by_object': {}
            }
            
            # Analyze images
            for img_key, img in self.data['images'].items():
                # Total bytes
                stats['total_bytes'] += img.get('file_size', 0)
                
                # By type
                img_type = img.get('image_type', 'Unknown')
                stats['by_type'][img_type] = stats['by_type'].get(img_type, 0) + 1
                
                # By telescope
                telescope = img.get('telescope_name', 'Unknown')
                stats['by_telescope'][telescope] = stats['by_telescope'].get(telescope, 0) + 1
                
                # By object
                obj_name = img.get('object_name', 'Unknown')
                stats['by_object'][obj_name] = stats['by_object'].get(obj_name, 0) + 1
            
            # Session totals
            for session in self.data['sessions']:
                stats['total_bytes'] += session.get('total_bytes', 0)
            
            return stats
            
        except Exception as e:
            print("Error getting statistics: {0}".format(str(e)))
            return None
            
    def get_downloaded_images(self, filter_type=None, filter_object=None, 
                             filter_telescope=None):
        """
        Get list of downloaded images with optional filtering
        
        Args:
            filter_type: Filter by image type (FITS, PNG, JPG)
            filter_object: Filter by object name
            filter_telescope: Filter by telescope name
            
        Returns:
            List of image records
        """
        results = []
        
        for img_key, img in self.data['images'].items():
            # Apply filters
            if filter_type and img.get('image_type') != filter_type:
                continue
            if filter_object and img.get('object_name') != filter_object:
                continue
            if filter_telescope and img.get('telescope_name') != filter_telescope:
                continue
                
            results.append(img)
        
        return results
        
    def backup(self, backup_path=None):
        """
        Create a backup of the tracking file
        
        Args:
            backup_path: Path for backup file (optional)
            
        Returns:
            True if successful
        """
        try:
            if backup_path is None:
                # Create timestamped backup
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = "{0}.{1}.backup".format(self.tracker_file, timestamp)
            
            shutil.copy2(self.tracker_file, backup_path)
            print("Backup created: {0}".format(backup_path))
            return True
            
        except Exception as e:
            print("Backup error: {0}".format(str(e)))
            return False
            
    def clear_session_data(self, keep_last_n=10):
        """
        Remove old session data to keep file size manageable
        
        Args:
            keep_last_n: Number of recent sessions to keep
        """
        if len(self.data['sessions']) > keep_last_n:
            self.data['sessions'] = self.data['sessions'][-keep_last_n:]
            self.save()
            print("Cleaned up old sessions, kept last {0}".format(keep_last_n))
    
    def verify_downloads(self):
        """
        Verify that all tracked downloads still exist on disk.
        
        Returns:
            dict: Verification results with missing, valid, and error counts
        """
        results = {
            'total': len(self.data['images']),
            'valid': 0,
            'missing': 0,
            'errors': 0,
            'missing_files': []
        }
        
        for img_key, img in self.data['images'].items():
            file_path = img.get('file_path', '')
            
            if not file_path:
                results['errors'] += 1
                continue
            
            if os.path.exists(file_path):
                results['valid'] += 1
            else:
                results['missing'] += 1
                results['missing_files'].append({
                    'image_id': img.get('image_id'),
                    'filename': img.get('filename'),
                    'file_path': file_path,
                    'object_name': img.get('object_name')
                })
        
        return results
    
    def find_orphaned_files(self, base_path):
        """
        Find files in the download directory that are not tracked.
        
        Args:
            base_path: Base download directory to scan
            
        Returns:
            list: List of orphaned file paths
        """
        tracked_paths = set()
        for img in self.data['images'].values():
            file_path = img.get('file_path', '')
            if file_path:
                tracked_paths.add(os.path.abspath(file_path))
        
        orphaned = []
        
        # Scan directory for files
        if os.path.exists(base_path):
            for root, dirs, files in os.walk(base_path):
                for filename in files:
                    # Skip non-image files
                    if not filename.lower().endswith(('.fits', '.fit', '.png', '.jpg', '.jpeg')):
                        continue
                    
                    full_path = os.path.abspath(os.path.join(root, filename))
                    
                    if full_path not in tracked_paths:
                        orphaned.append(full_path)
        
        return orphaned
    
    def remove_missing_from_tracker(self):
        """
        Remove entries for files that no longer exist on disk.
        
        Returns:
            int: Number of entries removed
        """
        to_remove = []
        
        for img_key, img in self.data['images'].items():
            file_path = img.get('file_path', '')
            if file_path and not os.path.exists(file_path):
                to_remove.append(img_key)
        
        for key in to_remove:
            del self.data['images'][key]
        
        if to_remove:
            self.save()
        
        return len(to_remove)
    
    def get_failed_downloads(self, session_id=None):
        """
        Get list of failed downloads from sessions.
        
        Args:
            session_id: Specific session ID (None = all sessions)
            
        Returns:
            list: List of failed download info
        """
        # This requires storing failure info, which we'll add to sessions
        failed = []
        
        for session in self.data['sessions']:
            if session_id is not None and session.get('session_id') != session_id:
                continue
            
            # Check for failed images in session
            failed_count = session.get('images_failed', 0)
            if failed_count > 0:
                failed.append({
                    'session_id': session.get('session_id'),
                    'start_time': session.get('start_time'),
                    'failed_count': failed_count
                })
        
        return failed
