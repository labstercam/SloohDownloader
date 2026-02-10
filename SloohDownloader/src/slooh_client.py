"""
Slooh Image Downloader - Slooh API Client
Handles authentication and communication with Slooh API using .NET HttpClient.
"""

import clr
clr.AddReference('System')
clr.AddReference('System.Net.Http')
from System import Uri
from System.Net import CookieContainer, Cookie
from System.Net.Http import HttpClient, HttpClientHandler, StringContent
from System.Net.Http.Headers import MediaTypeWithQualityHeaderValue
from System.Text import Encoding
import json


class SloohClient(object):
    """Client for Slooh API operations"""
    
    def __init__(self, base_url, logger=None):
        """
        Initialize Slooh API client.
        
        Args:
            base_url: Base URL for Slooh API (e.g., https://app.slooh.com)
            logger: Logger instance for logging operations
        """
        self.base_url = base_url.rstrip('/')
        self.logger = logger
        
        # Setup HTTP client with cookie support
        self.cookie_container = CookieContainer()
        self.handler = HttpClientHandler()
        self.handler.CookieContainer = self.cookie_container
        self.handler.UseCookies = True
        
        self.client = HttpClient(self.handler)
        self.client.DefaultRequestHeaders.Accept.Add(
            MediaTypeWithQualityHeaderValue('application/json'))
        self.client.DefaultRequestHeaders.Add('User-Agent', 'SloohDownloader/1.0')
        
        # Session data
        self.session_token = None
        self.user_data = {}
        self.is_authenticated = False
    
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
    
    def _make_url(self, endpoint):
        """Create full URL from endpoint"""
        return "{0}{1}".format(self.base_url, endpoint)
    
    def _post_json(self, endpoint, data):
        """
        POST JSON data to endpoint.
        
        Args:
            endpoint: API endpoint path
            data: Dictionary to send as JSON
            
        Returns:
            Dictionary: Parsed JSON response
            
        Raises:
            Exception: If request fails
        """
        url = self._make_url(endpoint)
        json_string = json.dumps(data)
        
        self._log('debug', "POST {0}".format(url))
        self._log('debug', "Data: {0}".format(json_string))
        
        content = StringContent(json_string, Encoding.UTF8, 'application/json')
        
        try:
            response = self.client.PostAsync(url, content).Result
            response_text = response.Content.ReadAsStringAsync().Result
            
            self._log('debug', "Response status: {0}".format(response.StatusCode))
            self._log('debug', "Response: {0}".format(response_text[:500]))
            
            if not response.IsSuccessStatusCode:
                raise Exception("HTTP {0}: {1}".format(
                    response.StatusCode, response_text))
            
            return json.loads(response_text)
            
        except Exception as e:
            self._log('error', "Request failed: {0}".format(str(e)))
            raise
    
    def get_session_token(self):
        """
        Get session token from Slooh.
        
        Returns:
            str: Session token
            
        Raises:
            Exception: If token retrieval fails
        """
        self._log('info', "Requesting session token...")
        
        try:
            response = self.client.PostAsync(
                self._make_url('/api/app/generateSessionToken'),
                None
            ).Result
            
            response_text = response.Content.ReadAsStringAsync().Result
            response.EnsureSuccessStatusCode()
            
            self._log('debug', "Session token response: {0}".format(response_text))
            
            data = json.loads(response_text)
            
            # Check for session token (API returns 'sloohSessionToken')
            if 'sloohSessionToken' in data:
                self.session_token = data['sloohSessionToken']
                
                # Set session token cookie
                cookie = Cookie('_sloohsstkn', self.session_token)
                cookie.Domain = '.slooh.com'
                cookie.Path = '/'
                self.cookie_container.Add(Uri(self.base_url), cookie)
                
                self._log('debug', "Cookie set: _sloohsstkn={0}".format(self.session_token))
                self._log('debug', "Cookies in container: {0}".format(
                    self.cookie_container.Count))
                
                self._log('info', "Session token acquired")
                return self.session_token
            else:
                raise Exception("Session token not found in response")
                
        except Exception as e:
            self._log('error', "Failed to get session token: {0}".format(str(e)))
            raise
    
    def login(self, username, password):
        """
        Authenticate with Slooh using username and password.
        
        Args:
            username: Slooh username
            password: Slooh password
            
        Returns:
            dict: User information
            
        Raises:
            Exception: If authentication fails
        """
        self._log('info', "Authenticating user: {0}".format(username))
        
        # Get session token first
        if not self.session_token:
            self.get_session_token()
        
        # Prepare login request (match C# LogonRequest exactly)
        # Note: .NET JSON serializer uses camelCase by default
        login_data = {
            'username': username,
            'passwd': password,
            'productId': 'ee26fb6d-3351-11eb-83b9-0655cc43ca95',
            'locale': 'en'
        }
        
        try:
            response = self._post_json('/api/users/login', login_data)
            
            # Check for explicit API errors (loginError='true' means failure)
            if response.get('loginError') == 'true':
                error_msg = response.get('errorMsg', 'Login failed')
                error_code = response.get('errorCode', 'unknown')
                raise Exception("Login failed (code {0}): {1}".format(error_code, error_msg))
            
            # Check if we got user data (presence of userid indicates success)
            if 'userid' not in response and 'userId' not in response:
                raise Exception("Login failed: No user data in response")
            
            # Extract user data
            self.user_data = {
                'userId': response.get('userid') or response.get('userId'),
                'displayName': response.get('displayName'),
                'username': response.get('username'),
                'email': response.get('emailAddress'),
                'at': response.get('at'),
                'cid': response.get('cid'),
                'token': response.get('token'),
                'customerUuid': response.get('customerUuid'),
                'membershipType': response.get('membershipType'),
                'memberSince': response.get('memberSince')
            }
            
            self.is_authenticated = True
            self._log('info', "Successfully authenticated as: {0}".format(
                self.user_data.get('displayName', username)))
            
            return self.user_data
            
        except Exception as e:
            self._log('error', "Authentication failed: {0}".format(str(e)))
            self.is_authenticated = False
            raise
    
    def get_user_gravity_status(self):
        """
        Get user's gravity/points status.
        
        Returns:
            dict: Gravity status information
        """
        if not self.is_authenticated:
            raise Exception("Not authenticated. Call login() first.")
        
        self._log('debug', "Getting user gravity status...")
        
        request_data = {
            'sloohSessionToken': self.session_token,
            'at': self.user_data.get('at'),
            'cid': self.user_data.get('cid'),
            'token': self.user_data.get('token'),
            'productId': 'ee26fb6d-3351-11eb-83b9-0655cc43ca95',
            'locale': 'en'
        }
        
        response = self._post_json('/api/newdashboard/getUserGravityStatus', request_data)
        return response
    
    def get_missions(self, first=1, max_count=18):
        """
        Get user's mission images.
        
        Args:
            first: First mission number to retrieve (1-based)
            max_count: Maximum number of missions to retrieve
            
        Returns:
            dict: Missions response with mission list
        """
        if not self.is_authenticated:
            raise Exception("Not authenticated. Call login() first.")
        
        self._log('debug', "Getting missions (first={0}, max={1})...".format(first, max_count))
        
        request_data = {
            'sloohSessionToken': self.session_token,
            'at': self.user_data.get('at'),
            'cid': self.user_data.get('cid'),
            'token': self.user_data.get('token'),
            'productId': 'ee26fb6d-3351-11eb-83b9-0655cc43ca95',
            'locale': 'en',
            'maxMissionCount': max_count,
            'firstMissionNumber': first
        }
        
        response = self._post_json('/api/images/getMissionImages', request_data)
        
        # Parse timestamps like C# code does
        if 'imageList' in response and response['imageList']:
            from datetime import datetime
            for mission in response['imageList']:
                mission['title'] = mission.get('imageTitle', '').strip()
                
                # Parse display date and time (UTC)
                display_date = mission.get('displayDate', '')
                display_time = mission.get('displayTime', '').replace(' UTC', '')
                
                if display_date and display_time:
                    try:
                        # Try multiple date formats (API returns "Feb. 7, 2026" format)
                        timestamp = None
                        for fmt in ['%b. %d, %Y', '%B %d, %Y', '%Y-%m-%d']:
                            try:
                                timestamp = datetime.strptime(display_date, fmt)
                                break
                            except:
                                continue
                        
                        if timestamp:
                            # Parse time - handle both HH:MM and HH:MM:SS formats
                            time_formats = ['%H:%M:%S', '%H:%M']
                            clock = None
                            for time_fmt in time_formats:
                                try:
                                    clock = datetime.strptime(display_time, time_fmt)
                                    break
                                except:
                                    continue
                            
                            if clock:
                                timestamp = timestamp.replace(
                                    hour=clock.hour, 
                                    minute=clock.minute, 
                                    second=clock.second)
                                mission['timestamp'] = timestamp.isoformat() + 'Z'
                    except Exception as e:
                        self._log('warning', "Failed to parse timestamp: {0}".format(str(e)))
        
        return response
    
    def get_pictures(self, first=1, max_count=18, mission_id=0, view_type='missions'):
        """
        Get user's pictures, optionally filtered by mission.
        
        Args:
            first: First picture number to retrieve (1-based)
            max_count: Maximum number of pictures to retrieve
            mission_id: Mission ID to filter by (0 = all pictures)
            view_type: View type - 'missions' or 'photoRoll'
            
        Returns:
            dict: Pictures response with picture list
        """
        if not self.is_authenticated:
            raise Exception("Not authenticated. Call login() first.")
        
        self._log('debug', "Getting pictures (first={0}, max={1}, mission={2}, viewType={3})...".format(
            first, max_count, mission_id, view_type))
        
        request_data = {
            'sloohSessionToken': self.session_token,
            'at': self.user_data.get('at'),
            'cid': self.user_data.get('cid'),
            'token': self.user_data.get('token'),
            'productId': 'ee26fb6d-3351-11eb-83b9-0655cc43ca95',
            'locale': 'en',
            'scheduledMissionId': mission_id,
            'maxImageCount': max_count,
            'firstImageNumber': first,
            'viewType': view_type
        }
        
        self._log('info', "API request: scheduledMissionId={0}, firstImageNumber={1}, maxImageCount={2}".format(
            mission_id, first, max_count))
        
        response = self._post_json('/api/images/getMyPictures', request_data)
        
        # Log basic response info only (avoid logging large objects)
        image_list = response.get('imageList', [])
        self._log('debug', "Response: totalCount={0}, imageCount={1}, received={2}".format(
            response.get('totalCount', 'N/A'),
            response.get('imageCount', 'N/A'),
            len(image_list)))
        
        # Don't parse timestamps here - do it only when needed to avoid stack overflow
        return response
    
    def _extract_picture_data(self, picture, photoroll_position):
        """
        Extract essential data from API picture object into simple dictionary.
        Avoids circular references and .NET object issues.
        """
        # Get string values safely
        def safe_get(obj, key, default=''):
            try:
                val = obj.get(key, default)
                return str(val) if val is not None else default
            except:
                return default
        
        # Parse timestamp from displayDate and displayTime
        timestamp = None
        display_date = safe_get(picture, 'displayDate')
        display_time = safe_get(picture, 'displayTime').replace(' UTC', '')
        
        if display_date and display_time:
            from datetime import datetime
            try:
                # Try multiple date formats
                dt = None
                for fmt in ['%b. %d, %Y', '%B %d, %Y', '%Y-%m-%d']:
                    try:
                        dt = datetime.strptime(display_date, fmt)
                        break
                    except:
                        continue
                
                if dt:
                    # Parse time
                    for time_fmt in ['%H:%M:%S', '%H:%M']:
                        try:
                            clock = datetime.strptime(display_time, time_fmt)
                            timestamp = dt.replace(hour=clock.hour, minute=clock.minute, second=clock.second)
                            break
                        except:
                            continue
            except:
                pass
        
        result = {
            'imageId': safe_get(picture, 'imageId'),
            'customerImageId': safe_get(picture, 'customerImageId'),
            'missionId': safe_get(picture, 'missionId'),
            'scheduledMissionId': safe_get(picture, 'scheduledMissionId'),
            'imageTitle': safe_get(picture, 'imageTitle'),
            'imageDownloadURL': safe_get(picture, 'imageDownloadURL'),
            'imageDownloadFilename': safe_get(picture, 'imageDownloadFilename'),
            'imageType': safe_get(picture, 'imageType', 'png'),
            'telescopeName': safe_get(picture, 'telescopeName', 'Unknown'),
            'instrumentName': safe_get(picture, 'instrumentName', 'Unknown'),
            'displayDate': display_date,
            'displayTime': display_time,
            'photoRoll_position': photoroll_position
        }
        
        # Add timestamp if parsed successfully
        if timestamp:
            result['timestamp'] = timestamp.isoformat() + 'Z'
        
        return result
    
    def _parse_picture_timestamps(self, pictures):
        """Parse timestamps for a list of pictures"""
        from datetime import datetime
        
        # Process in small batches to avoid stack overflow
        for i, picture in enumerate(pictures):
            try:
                picture['title'] = picture.get('imageTitle', '').strip()
                
                # Parse display date and time (UTC)
                display_date = picture.get('displayDate', '')
                display_time = picture.get('displayTime', '').replace(' UTC', '')
                
                if display_date and display_time:
                    # Try multiple date formats
                    timestamp = None
                    for fmt in ['%b. %d, %Y', '%B %d, %Y', '%Y-%m-%d']:
                        try:
                            timestamp = datetime.strptime(display_date, fmt)
                            break
                        except:
                            continue
                    
                    if timestamp:
                        # Parse time
                        clock = None
                        for time_fmt in ['%H:%M:%S', '%H:%M']:
                            try:
                                clock = datetime.strptime(display_time, time_fmt)
                                break
                            except:
                                continue
                        
                        if clock:
                            timestamp = timestamp.replace(
                                hour=clock.hour, 
                                minute=clock.minute, 
                                second=clock.second)
                            picture['timestamp'] = timestamp.isoformat() + 'Z'
                
                # Set defaults for missing data
                if not picture.get('telescopeName'):
                    picture['telescopeName'] = 'Unknown'
                if not picture.get('instrumentName'):
                    picture['instrumentName'] = 'Unknown'
            except Exception as e:
                # Skip problematic pictures silently
                continue
    
    def get_all_missions(self, batch_size=50):
        """
        Get all missions by repeatedly calling API until all are retrieved.
        
        Args:
            batch_size: Number of missions per request
            
        Yields:
            dict: Mission data
        """
        if not self.is_authenticated:
            raise Exception("Not authenticated. Call login() first.")
        
        first = 1
        total_count = None
        retrieved = 0
        
        while True:
            response = self.get_missions(first=first, max_count=batch_size)
            
            if total_count is None:
                total_count = response.get('totalCount', 0)
                self._log('info', "Total missions available: {0}".format(total_count))
            
            missions = response.get('imageList', [])
            if not missions:
                break
            
            for mission in missions:
                yield mission
                retrieved += 1
            
            self._log('debug', "Retrieved {0}/{1} missions".format(retrieved, total_count))
            
            if retrieved >= total_count:
                break
            
            first += len(missions)
    
    def get_all_pictures(self, mission_id=0, batch_size=50, view_type=None, max_scan=None, start_image=1):
        """
        Get all pictures by repeatedly calling API until all are retrieved.
        
        Args:
            mission_id: Mission ID to filter by (0 = all pictures)
            batch_size: Number of pictures per request
            view_type: View type - 'missions' or 'photoRoll' (auto-selected if None)
            max_scan: Maximum number of pictures to retrieve (None = all available)
            start_image: Starting image number in photoroll (1-based, default 1 = most recent)
            
        Yields:
            dict: Picture data with added 'photoRoll_position' field
        """
        if not self.is_authenticated:
            raise Exception("Not authenticated. Call login() first.")
        
        # Auto-select viewType: use 'missions' for specific mission, 'photoRoll' for all
        if view_type is None:
            view_type = 'photoRoll' if mission_id == 0 else 'missions'
        
        first = start_image if start_image > 1 else 1
        total_count = None
        retrieved = 0
        photoroll_position = first  # Track absolute position in photoRoll (1-based)
        
        self._log('info', "Starting get_all_pictures: mission_id={0}, batch_size={1}, view_type={2}, max_scan={3}, start_image={4}".format(
            mission_id, batch_size, view_type, max_scan if max_scan else 'unlimited', first))
        
        while True:
            self._log('debug', "Requesting batch: first={0}, max_count={1}".format(first, batch_size))
            
            response = self.get_pictures(first=first, max_count=batch_size, mission_id=mission_id, view_type=view_type)
            
            if total_count is None:
                # totalCount might be a string
                tc = response.get('totalCount', '0')
                total_count = int(tc) if tc else 0
                self._log('info', "Total pictures available: {0}".format(total_count))
                
                if total_count == 0:
                    self._log('warning', "API reported 0 total pictures!")
                    break
            
            pictures = response.get('imageList', [])
            batch_count = len(pictures)
            
            self._log('debug', "Received {0} pictures in this batch".format(batch_count))
            
            if not pictures:
                self._log('debug', "No pictures in response, ending pagination")
                break
            
            for picture in pictures:
                # Extract essential data into a simple dict to avoid .NET object issues
                simple_picture = self._extract_picture_data(picture, photoroll_position)
                yield simple_picture
                retrieved += 1
                photoroll_position += 1
                
                # Check max_scan limit
                if max_scan and retrieved >= max_scan:
                    self._log('info', "Reached max_scan limit: {0}".format(max_scan))
                    return
            
            self._log('info', "Retrieved {0}/{1} pictures so far".format(retrieved, total_count))
            
            if retrieved >= total_count:
                self._log('info', "All pictures retrieved")
                break
            
            # Move to next batch
            first += batch_count
            self._log('debug', "Next batch will start at position {0}".format(first))
    
    def get_mission_fits(self, mission_id):
        """
        Get FITS files for a specific mission.
        
        Args:
            mission_id: Mission ID
            
        Yields:
            dict: FITS file data with instrument grouping
        """
        if not self.is_authenticated:
            raise Exception("Not authenticated. Call login() first.")
        
        if not mission_id or mission_id == 0:
            return  # No FITS for mission_id=0
        
        request_data = {
            'sloohSiteSessionToken': self.session_token,  # Note: sloohSiteSessionToken for FITS
            'at': self.user_data.get('at'),
            'cid': self.user_data.get('cid'),
            'token': self.user_data.get('token'),
            'productId': 'ee26fb6d-3351-11eb-83b9-0655cc43ca95',
            'locale': 'en',
            'scheduledMissionId': mission_id,
            'maxImageCount': 100,  # Request up to 100 FITS files
            'firstImageNumber': 1,
            'viewType': 'missions'
        }
        
        self._log('debug', "Fetching FITS files for mission {0}".format(mission_id))
        self._log('debug', "FITS request data: {0}".format(request_data))
        response = self._post_json('/api/images/getMissionFITS', request_data)
        
        # Log full response for debugging
        self._log('debug', "FITS API full response: {0}".format(response))
        
        groups = response.get('groupList', [])
        
        for group in groups:
            instrument_name = group.get('groupName', 'Unknown')
            images = group.get('groupImageList', [])
            
            for fits_image in images:
                yield {
                    'imageId': str(fits_image.get('imageId', '')),
                    'imageDownloadURL': fits_image.get('imageURL', ''),
                    'imageTitle': fits_image.get('imageTitle', ''),
                    'instrumentName': instrument_name,
                    'imageType': 'FITS',
                    'missionId': str(mission_id)
                }
    
    def test_connection(self):
        """
        Test connection to Slooh API.
        
        Returns:
            bool: True if connection successful
        """
        try:
            self._log('info', "Testing connection to Slooh...")
            self.get_session_token()
            return True
        except Exception as e:
            self._log('error', "Connection test failed: {0}".format(str(e)))
            return False
    
    def close(self):
        """Close HTTP client"""
        if self.client:
            self.client.Dispose()
    
    def __del__(self):
        """Cleanup"""
        self.close()
