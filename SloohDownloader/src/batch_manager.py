"""
Slooh Image Downloader - Batch Manager
Coordinates batch downloads with API client, download manager, and file organizer.
"""

from datetime import datetime
import os


class BatchManager(object):
    """Manages batch download operations"""
    
    def __init__(self, config, slooh_client, download_manager, file_organizer, 
                 download_tracker, logger=None):
        """
        Initialize batch manager.
        
        Args:
            config: Configuration manager instance
            slooh_client: SloohClient instance
            download_manager: DownloadManager instance
            file_organizer: FileOrganizer instance
            download_tracker: DownloadTracker instance
            logger: Logger instance
        """
        self.config = config
        self.slooh = slooh_client
        self.downloader = download_manager
        self.organizer = file_organizer
        self.tracker = download_tracker
        self.logger = logger
        
        # Batch settings
        self.batch_size = config.get('download.batch_size', 50)
        self.check_tracker = config.get('download.check_tracker', True)
        self.handle_duplicates = config.get('download.handle_duplicates', 'skip')
        
        # Statistics
        self.session_stats = {
            'total_available': 0,
            'already_downloaded': 0,
            'queued': 0,
            'downloaded': 0,
            'failed': 0,
            'total_bytes': 0
        }
        
        # Control flags
        self.is_cancelled = False
        
        # Callbacks
        self.on_batch_start = None
        self.on_batch_complete = None
        self.on_progress = None
    
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
    
    def _matches_filters(self, picture, filters):
        """
        Check if a picture matches the provided filters.
        
        Args:
            picture: Picture dictionary
            filters: Dictionary with filter criteria
            
        Returns:
            tuple: (matches: bool, stop_scanning: bool)
                - matches: True if picture matches all filters
                - stop_scanning: True if we should stop scanning (date filter optimization)
        """
        # Telescope filter (multiple selection with case-insensitive contains)
        if 'telescopes' in filters and filters['telescopes']:
            telescope_name = picture.get('telescopeName', '')
            telescope_name_lower = telescope_name.lower()
            # Check if any selected telescope matches (case-insensitive contains)
            matched = False
            for selected_telescope in filters['telescopes']:
                if selected_telescope.lower() in telescope_name_lower:
                    matched = True
                    break
            if not matched:
                return (False, False)
        
        # Legacy single telescope filter (for backward compatibility)
        if 'telescope' in filters and filters['telescope']:
            telescope_name = picture.get('telescopeName', '').lower()
            if filters['telescope'].lower() not in telescope_name:
                return (False, False)
        
        # Object filter (searches in imageTitle which contains object name)
        if 'object' in filters and filters['object']:
            image_title = picture.get('imageTitle', '').lower()
            if filters['object'].lower() not in image_title:
                return (False, False)
        
        # Picture types filter (multi-select)
        if 'picture_types' in filters and filters['picture_types']:
            image_type = picture.get('imageType', '').lower()
            # Check if image type is in the list of selected types
            if image_type not in filters['picture_types']:
                return (False, False)
        
        # Legacy single picture type filter (for backward compatibility)
        if 'picture_type' in filters and filters['picture_type']:
            image_type = picture.get('imageType', '').lower()
            filter_type = filters['picture_type'].lower()
            # Match: png matches png, fits matches FITS, jpeg matches jpeg
            if image_type != filter_type:
                return (False, False)
        
        # Image type filter
        if 'image_type' in filters and filters['image_type']:
            image_type = picture.get('imageType', '')
            if image_type != filters['image_type']:
                return (False, False)
        
        # Date range filter (inclusive - includes entire start and end days)
        if 'start_date' in filters or 'end_date' in filters:
            timestamp_str = picture.get('timestamp', '')
            if timestamp_str:
                try:
                    # Parse ISO timestamp
                    date_str = timestamp_str.replace('Z', '').split('+')[0].split('.')[0]
                    pic_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
                    
                    if 'start_date' in filters and filters['start_date']:
                        start_date = filters['start_date']
                        if isinstance(start_date, str):
                            # Parse start_date from YYYY-MM-DD format
                            # Set time to 00:00:00 to include entire start day
                            start_date = datetime.strptime(start_date, '%Y-%m-%d')
                        if pic_date < start_date:
                            # Picture is older than start date
                            # Since photoroll is in reverse chronological order (newest first),
                            # all subsequent pictures will also be older, so signal to stop scanning
                            return (False, True)
                    
                    if 'end_date' in filters and filters['end_date']:
                        end_date = filters['end_date']
                        if isinstance(end_date, str):
                            # Parse end_date from YYYY-MM-DD format
                            # Set time to 23:59:59 to include entire end day
                            end_date = datetime.strptime(end_date, '%Y-%m-%d')
                            end_date = end_date.replace(hour=23, minute=59, second=59)
                        if pic_date > end_date:
                            # Picture is newer than end date - keep scanning for older pictures
                            return (False, False)
                except:
                    pass  # Skip date comparison if parsing fails
        
        return (True, False)
    
    def _should_download(self, picture, force_redownload=False):
        """
        Check if a picture should be downloaded.
        
        Args:
            picture: Picture dictionary
            force_redownload: If True, ignore tracker and force download
            
        Returns:
            tuple: (should_download: bool, reason: str)
        """
        # Force redownload bypasses all checks
        if force_redownload:
            return (True, 'force_redownload')
        
        image_id = str(picture.get('imageId', picture.get('customerImageId', 0)))
        image_type = picture.get('imageType', 'png')
        
        # Check tracker only (file system is NOT checked)
        if self.check_tracker and self.tracker.is_image_downloaded(image_id, image_type):
            return (False, 'already_in_tracker')
        
        return (True, 'new')
    
    def download_all_pictures(self, mission_id=0, max_total=None, max_scan=None, start_image=1, filters=None, dry_run=False, force_redownload=False):
        """
        Download all pictures, optionally filtered by mission.
        
        Args:
            mission_id: Mission ID to filter by (0 = all pictures)
            max_total: Maximum total images to download (None = unlimited)
            max_scan: Maximum number of pictures to scan from API (None = all available)
            start_image: Starting image number in photoroll (1 = most recent, default)
            filters: Dictionary with optional filters:
                - telescope: Filter by telescope name (contains match)
                - object: Filter by object name (contains match)
                - image_type: Filter by image type (FITS, PNG, JPG)
                - start_date: Start date (datetime or ISO string)
                - end_date: End date (datetime or ISO string)
            dry_run: If True, only preview what would be downloaded
            force_redownload: If True, ignore tracker and re-download everything
            
        Returns:
            dict: Download session statistics
        """
        if not self.slooh.is_authenticated:
            raise Exception("Not authenticated. Call slooh.login() first.")
        
        self._log('info', "Starting batch download session...")
        self._log('info', "Mission ID filter: {0} (0 = all missions)".format(mission_id))
        
        if force_redownload:
            self._log('info', "Force redownload: ENABLED (will re-download tracked images)")
        
        if max_scan:
            self._log('info', "Max scan limit: {0} pictures".format(max_scan))
        
        if start_image and start_image > 1:
            self._log('info', "Starting from image #{0}".format(start_image))
        
        # Log filter criteria
        if filters:
            if 'telescopes' in filters and filters['telescopes']:
                self._log('info', "Telescope filter: {0}".format(', '.join(filters['telescopes'])))
            if 'object' in filters and filters['object']:
                self._log('info', "Object filter: {0}".format(filters['object']))
            if 'image_type' in filters and filters['image_type']:
                self._log('info', "Image type filter: {0}".format(filters['image_type']))
        
        # Start new session
        session_id = self.tracker.create_session()
        
        # Reset statistics
        self.session_stats = {
            'total_available': 0,
            'already_downloaded': 0,
            'skipped_existing': 0,
            'queued': 0,
            'downloaded': 0,
            'failed': 0,
            'total_bytes': 0,
            'session_id': session_id,
            'current_batch': 0  # Track batch number for logging
        }
        
        if self.on_batch_start:
            self.on_batch_start(self.session_stats)
        
        # Prepare download tasks
        tasks = []
        batch_download_size = 50  # Process 50 pictures at a time to avoid memory issues
        fits_missions_fetched = set()  # Track missions we've already fetched FITS for
        
        try:
            # Iterate through all pictures
            scanned_count = 0
            for picture in self.slooh.get_all_pictures(
                mission_id=mission_id, 
                batch_size=self.batch_size,
                max_scan=max_scan,
                start_image=start_image):
                
                # Check if cancelled
                if self.is_cancelled or self.downloader.is_cancelled:
                    self._log('info', "Download cancelled - stopping picture scan")
                    break
                
                scanned_count += 1
                self.session_stats['total_available'] += 1
                
                # Log first few pictures to help debug filters
                if scanned_count <= 3:
                    self._log('debug', "Sample picture {0}: title='{1}', type='{2}', telescope='{3}'".format(
                        scanned_count, 
                        picture.get('imageTitle', 'N/A'),
                        picture.get('imageType', 'N/A'),
                        picture.get('telescopeName', 'N/A')))
                
                # Apply filters if provided
                if filters:
                    matches, stop_scanning = self._matches_filters(picture, filters)
                    if not matches:
                        if stop_scanning:
                            # Optimization: photoroll is in reverse chronological order (newest first)
                            # If we've reached pictures older than start_date, stop scanning
                            self._log('info', "Reached pictures older than start_date filter - stopping scan (scanned {0} total)".format(scanned_count))
                            break
                        continue
                
                # Check if we should download
                should_download, reason = self._should_download(picture, force_redownload)
                
                if not should_download:
                    if reason == 'already_in_tracker':
                        self.session_stats['already_downloaded'] += 1
                        self._log('info', "Skipping (already in tracker): {0} [{1}]".format(
                            picture.get('imageTitle', 'Unknown'),
                            picture.get('imageType', 'UNKNOWN')))
                    continue
                
                # Create download task
                from download_manager import DownloadTask
                
                url = picture.get('imageDownloadURL')
                if not url:
                    self._log('warning', "No download URL for image {0}".format(
                        picture.get('imageId')))
                    continue
                
                dest_path = self.organizer.get_destination_path(picture)
                image_id = str(picture.get('imageId', picture.get('customerImageId', 0)))
                
                self._log('info', "Queueing: {0} [{1}] -> {2}".format(
                    picture.get('imageTitle', 'Unknown'),
                    picture.get('imageType', 'UNKNOWN'),
                    os.path.basename(dest_path)))
                
                # Extract only essential metadata to avoid circular references
                essential_metadata = {
                    'customerImageId': picture.get('customerImageId', ''),
                    'missionId': picture.get('missionId', ''),
                    'imageType': picture.get('imageType', 'png'),  # Default to 'png' for regular pictures
                    'telescopeName': picture.get('telescopeName', ''),
                    'objectName': picture.get('imageTitle', ''),
                    'photoRoll_position': picture.get('photoRoll_position')
                }
                
                task = DownloadTask(
                    url=url,
                    destination=dest_path,
                    image_id=image_id,
                    metadata=essential_metadata
                )
                
                tasks.append(task)
                self.session_stats['queued'] += 1
                
                # Also fetch FITS files for this mission if not already done
                mission_id_str = picture.get('missionId', '') or picture.get('scheduledMissionId', '')
                self._log('debug', "Checking FITS for image: missionId='{0}', scheduledMissionId='{1}', imageId='{2}'".format(
                    picture.get('missionId', 'N/A'),
                    picture.get('scheduledMissionId', 'N/A'),
                    picture.get('imageId', 'N/A')))
                
                if mission_id_str and mission_id_str != '0' and mission_id_str not in fits_missions_fetched:
                    fits_missions_fetched.add(mission_id_str)
                    mission_id_int = int(mission_id_str)
                    
                    self._log('info', "Fetching FITS files for mission {0}...".format(mission_id_int))
                    
                    try:
                        fits_count = 0
                        for fits_file in self.slooh.get_mission_fits(mission_id_int):
                            # Copy image title and telescope from parent image BEFORE filtering
                            fits_file['imageTitle'] = picture.get('imageTitle', 'Unknown')
                            fits_file['telescopeName'] = picture.get('telescopeName', 'Unknown')
                            fits_file['displayDate'] = picture.get('displayDate', '')
                            fits_file['displayTime'] = picture.get('displayTime', '')
                            
                            # Apply same filters to FITS files
                            if filters:
                                matches, stop_scanning = self._matches_filters(fits_file, filters)
                                if not matches:
                                    # Note: don't stop scanning FITS files based on date,
                                    # as they all belong to the same mission
                                    continue
                            
                            # Check if should download
                            fits_should_download, fits_reason = self._should_download(fits_file, force_redownload)
                            if not fits_should_download:
                                continue
                            
                            fits_url = fits_file.get('imageDownloadURL')
                            if not fits_url:
                                continue
                            
                            fits_dest_path = self.organizer.get_destination_path(fits_file)
                            # Use actual Slooh imageId from FITS file
                            fits_image_id = str(fits_file.get('imageId', '0'))
                            
                            self._log('info', "Queueing: {0} [{1}] -> {2}".format(
                                fits_file.get('imageTitle', 'Unknown'),
                                'FITS',
                                os.path.basename(fits_dest_path)))
                            
                            fits_metadata = {
                                'missionId': mission_id_str,
                                'imageType': 'FITS',
                                'telescopeName': fits_file.get('telescopeName', 'Unknown'),
                                'objectName': fits_file.get('imageTitle', ''),
                                'instrumentName': fits_file.get('instrumentName', 'Unknown')
                            }
                            
                            fits_task = DownloadTask(
                                url=fits_url,
                                destination=fits_dest_path,
                                image_id=fits_image_id,
                                metadata=fits_metadata
                            )
                            
                            tasks.append(fits_task)
                            self.session_stats['queued'] += 1
                            fits_count += 1
                            
                            # Check max limit
                            if max_total and self.session_stats['queued'] >= max_total:
                                break
                        
                        self._log('info', "Found {0} FITS files for mission {1}".format(
                            fits_count, mission_id_int))
                        
                    except Exception as e:
                        self._log('warning', "Failed to fetch FITS for mission {0}: {1}".format(
                            mission_id_int, str(e)))
                elif mission_id_str == '0' or not mission_id_str:
                    self._log('debug', "Skipping FITS fetch: mission_id is 0 or empty")
                elif mission_id_str in fits_missions_fetched:
                    self._log('debug', "Skipping FITS fetch: mission {0} already fetched".format(mission_id_str))
                
                # Process in batches to avoid memory issues
                if not dry_run and len(tasks) >= batch_download_size:
                    # Check if cancelled before starting batch
                    if self.is_cancelled or self.downloader.is_cancelled:
                        self._log('info', "Download cancelled - skipping batch processing")
                        break
                    self.session_stats['current_batch'] += 1
                    self._download_batch(tasks, session_id)
                    tasks = []  # Clear for next batch
                
                # Check max limit
                if max_total and self.session_stats['queued'] >= max_total:
                    self._log('info', "Reached maximum download limit: {0}".format(max_total))
                    break
            
            # Download all tasks (or just preview in dry-run)
            if tasks and not self.is_cancelled and not self.downloader.is_cancelled:
                if dry_run:
                    self._log('info', "=" * 60)
                    self._log('info', "DRY RUN: Found {0} images that would be downloaded".format(len(tasks)))
                    self._log('info', "=" * 60)
                    # List the files
                    for i, task in enumerate(tasks, 1):
                        self._log('info', "  {0}. {1}".format(i, os.path.basename(task.destination)))
                    self._log('info', "=" * 60)
                    self._log('info', "DRY RUN COMPLETE - No files were downloaded")
                    # Update stats to show what would have been downloaded
                    self.session_stats['queued'] = len(tasks)
                    self.session_stats['downloaded'] = 0
                    self.session_stats['failed'] = 0
                else:
                    self.session_stats['current_batch'] += 1
                    batch_num = self.session_stats['current_batch']
                    self._log('info', "="*60)
                    self._log('info', "Starting Batch #{0}".format(batch_num))
                    self._log('info', "Saving {0} files for Batch #{1}".format(len(tasks), batch_num))
                    
                    # Enhance progress callback to include batch info (same as _download_batch)
                    original_progress_callback = self.downloader.on_progress
                    def progress_callback(progress):
                        progress['batch_number'] = batch_num
                        progress['batch_size'] = len(tasks)
                        if original_progress_callback:
                            original_progress_callback(progress)
                    
                    self.downloader.on_progress = progress_callback
                    
                    # Execute downloads
                    download_stats = self.downloader.download(tasks)
                
                    # Update session statistics
                    self.session_stats['downloaded'] = download_stats['completed']
                    self.session_stats['failed'] = download_stats['failed']
                    self.session_stats['total_bytes'] = download_stats['total_bytes']
                    
                    # Count unique objects in this batch
                    unique_objects = set()
                    for task in self.downloader.completed_downloads:
                        if task.metadata and 'objectName' in task.metadata:
                            unique_objects.add(task.metadata['objectName'])
                    
                    self._log('info', "Batch #{0} completed - {1} files saved for {2} objects".format(
                        batch_num, download_stats['completed'], len(unique_objects)))
                    self._log('info', "="*60)
                    
                    # Record successful downloads in tracker
                    for task in self.downloader.completed_downloads:
                        metadata = task.metadata or {}
                        self.tracker.record_download(
                            image_id=task.image_id,
                            customer_image_id=metadata.get('customerImageId', ''),
                            mission_id=metadata.get('missionId', ''),
                            filename=os.path.basename(task.destination),
                            download_url=task.url,
                            file_path=task.destination,
                            file_size=task.file_size,
                            md5_hash=metadata.get('md5_hash', ''),
                            image_type=metadata.get('imageType', 'png'),  # Default to 'png' for consistency
                            telescope_name=metadata.get('telescopeName', ''),
                            object_name=metadata.get('objectName', ''),
                            session_id=session_id,
                            photoroll_position=metadata.get('photoRoll_position')
                        )
                    
                    # Save tracker
                    self.tracker.save()
                
            else:
                # Report what happened when no new downloads
                if self.session_stats['already_downloaded'] > 0:
                    self._log('info', "No new images to download ({0} already in tracker)".format(
                        self.session_stats['already_downloaded']))
                else:
                    self._log('info', "No new images to download")
            
            # End session
            self.tracker.update_session(
                session_id=session_id,
                images_downloaded=self.session_stats['downloaded'],
                images_failed=self.session_stats['failed'],
                total_bytes=self.session_stats['total_bytes']
            )
            
            self.tracker.save()
            
        except Exception as e:
            self._log('error', "Batch download failed: {0}".format(str(e)))
            raise
        finally:
            if self.on_batch_complete:
                self.on_batch_complete(self.session_stats)
        
        return self.session_stats
    
    def _download_batch(self, tasks, session_id):
        """Download a batch of tasks"""
        batch_num = self.session_stats['current_batch']
        self._log('info', "="*60)
        self._log('info', "Starting Batch #{0}".format(batch_num))
        self._log('info', "Saving {0} files for Batch #{1}".format(len(tasks), batch_num))
        
        # Enhance progress callback to include batch info
        original_progress_callback = self.downloader.on_progress
        def batch_progress_callback(progress):
            # Add batch info to progress dict
            progress['batch_number'] = batch_num
            progress['batch_size'] = len(tasks)
            if original_progress_callback:
                original_progress_callback(progress)
        
        self.downloader.on_progress = batch_progress_callback
        
        # Execute downloads using the download manager
        download_stats = self.downloader.download(tasks)
        
        # Restore original callback
        self.downloader.on_progress = original_progress_callback
        
        # Update session statistics
        self.session_stats['downloaded'] += download_stats['completed']
        self.session_stats['failed'] += download_stats['failed']
        self.session_stats['total_bytes'] += download_stats['total_bytes']
        
        # Count unique objects in this batch
        unique_objects = set()
        for task in self.downloader.completed_downloads:
            if task.metadata and 'objectName' in task.metadata:
                unique_objects.add(task.metadata['objectName'])
        
        self._log('info', "Batch #{0} completed - {1} files saved for {2} objects".format(
            batch_num, download_stats['completed'], len(unique_objects)))
        self._log('info', "="*60)
        
        # Record successful downloads in tracker
        for task in self.downloader.completed_downloads:
            metadata = task.metadata or {}
            self.tracker.record_download(
                image_id=task.image_id,
                customer_image_id=metadata.get('customerImageId', ''),
                mission_id=metadata.get('missionId', ''),
                filename=os.path.basename(task.destination),
                download_url=task.url,
                file_path=task.destination,
                file_size=task.file_size,
                md5_hash=metadata.get('md5_hash', ''),
                image_type=metadata.get('imageType', 'FITS'),
                telescope_name=metadata.get('telescopeName', ''),
                object_name=metadata.get('objectName', ''),
                session_id=session_id,
                photoroll_position=metadata.get('photoRoll_position')
            )
        
        # Save tracker after each batch
        self.tracker.save()
    
    def download_new_since_last_session(self):
        """
        Download only pictures added since last successful session.
        
        Returns:
            dict: Download session statistics
        """
        # Get last download date
        last_date = self.tracker.get_last_download_date()
        
        if last_date:
            self._log('info', "Downloading images since last session: {0}".format(last_date))
        else:
            self._log('info', "No previous sessions found. Downloading all images...")
        
        # Download all (will skip existing via tracker)
        return self.download_all_pictures()
    
    def download_mission(self, mission_id):
        """
        Download all pictures from a specific mission.
        
        Args:
            mission_id: Mission ID
            
        Returns:
            dict: Download session statistics
        """
        self._log('info', "Downloading mission {0}...".format(mission_id))
        return self.download_all_pictures(mission_id=mission_id)
    
    def download_by_date_range(self, start_date, end_date):
        """
        Download pictures within a date range.
        
        Args:
            start_date: Start date (datetime or ISO string)
            end_date: End date (datetime or ISO string)
            
        Returns:
            dict: Download session statistics
        """
        # Parse ISO timestamps manually (Python 3.4 compatible)
        if isinstance(start_date, str):
            start_date_str = start_date.replace('Z', '+00:00')
            if '+' in start_date_str:
                start_date_str = start_date_str.split('+')[0]
            start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%S')
        if isinstance(end_date, str):
            end_date_str = end_date.replace('Z', '+00:00')
            if '+' in end_date_str:
                end_date_str = end_date_str.split('+')[0]
            end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M:%S')
        
        self._log('info', "Downloading images from {0} to {1}...".format(
            start_date.date(), end_date.date()))
        
        # This would need filtering in get_all_pictures
        # For now, download all and filter will happen via tracker
        return self.download_all_pictures()
    
    def resume_failed_downloads(self):
        """
        Retry failed downloads from last session.
        
        Returns:
            dict: Download session statistics
        """
        # TODO: Tracker doesn't currently store individual failed downloads
        # This would require enhancing download_tracker.py to record failed attempts
        self._log('warning', "Resume failed downloads feature not yet implemented")
        return self.session_stats
        
        # Placeholder for future implementation when tracker supports it:
        # failed_images = self.tracker.get_failed_downloads()
        # if not failed_images:
        #     self._log('info', "No failed downloads to retry")
        #     return self.session_stats
        # self._log('info', "Retrying {0} failed downloads...".format(len(failed_images)))
        
        # Create download tasks
        from download_manager import DownloadTask
        tasks = []
        
        for image_id, image_data in failed_images.items():
            metadata = image_data.get('metadata', {})
            
            url = metadata.get('imageDownloadURL')
            if not url:
                continue
            
            dest_path = image_data.get('filepath') or self.organizer.get_destination_path(metadata)
            
            task = DownloadTask(
                url=url,
                destination=dest_path,
                image_id=image_id,
                metadata=metadata
            )
            
            tasks.append(task)
        
        # Download
        if tasks:
            session_id = self.tracker.create_session()
            download_stats = self.downloader.download(tasks)
            
            # Update tracker
            for task in self.downloader.completed_downloads:
                metadata = task.metadata or {}
                self.tracker.record_download(
                    image_id=task.image_id,
                    customer_image_id=metadata.get('customer_image_id', ''),
                    mission_id=metadata.get('mission_id', ''),
                    filename=os.path.basename(task.destination),
                    download_url=task.url,
                    file_path=task.destination,
                    file_size=task.file_size,
                    md5_hash=metadata.get('md5_hash', ''),
                    image_type=metadata.get('image_type', 'FITS'),
                    telescope_name=metadata.get('telescope_name', ''),
                    object_name=metadata.get('object_name', ''),
                    session_id=session_id
                )
            
            self.tracker.update_session(
                session_id=session_id,
                images_downloaded=download_stats['completed'],
                images_failed=download_stats['failed'],
                total_bytes=download_stats['total_bytes']
            )
            
            self.tracker.save()
            
            return download_stats
        
        return self.session_stats
    
    def get_session_stats(self):
        """Get current session statistics"""
        return self.session_stats.copy()
