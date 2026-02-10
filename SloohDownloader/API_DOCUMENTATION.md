# Slooh API Documentation

## Overview

This document provides comprehensive documentation of the Slooh API based on reverse engineering the original C# application and testing during Python implementation.

**Base URL**: `https://www.slooh.com`

**Authentication**: Session-based with token and user credentials

---

## API Endpoints

### 1. Generate Session Token

**Endpoint**: `POST /api/app/generateSessionToken`

**Purpose**: Obtain a session token required for all subsequent API calls

**Request**:
```json
POST /api/app/generateSessionToken
Content-Type: application/json
Body: null (empty POST)
```

**Response**:
```json
{
  "sloohSessionToken": "string",
  "apiError": false,
  "errorMessage": null
}
```

**Notes**:
- Must be called first before any other API operations
- Token must be stored and included in all subsequent requests
- Token should be set as cookie `_sloohsstkn` with domain `.slooh.com`

---

### 2. User Login

**Endpoint**: `POST /api/users/login`

**Purpose**: Authenticate user and obtain user session data

**Request**:
```json
{
  "sloohSessionToken": "string",
  "username": "user@example.com",
  "passwd": "password",
  "productId": "ee26fb6d-3351-11eb-83b9-0655cc43ca95",
  "locale": "en"
}
```

**Response**:
```json
{
  "at": "string",
  "cid": "string", 
  "token": "string",
  "displayName": "string",
  "userId": "string",
  "apiError": false,
  "errorMessage": null
}
```

**Important Fields**:
- `at`, `cid`, `token`: Required for all subsequent authenticated requests
- `displayName`: User's display name on Slooh
- Field names are **camelCase** (not snake_case)
- Password field is `passwd` (NOT `password`)

**Common Errors**:
- Incorrect field names (use `passwd` not `password`)
- Missing session token
- Invalid credentials

---

### 3. Get User Gravity Status

**Endpoint**: `POST /api/newdashboard/getUserGravityStatus`

**Purpose**: Get user account information and membership details

**Request**:
```json
{
  "sloohSessionToken": "string",
  "at": "string",
  "cid": "string",
  "token": "string",
  "productId": "ee26fb6d-3351-11eb-83b9-0655cc43ca95",
  "locale": "en"
}
```

**Response**:
```json
{
  "displayName": "string",
  "memberSince": "string",
  "tier": "string",
  "gravityPoints": 0,
  "progressPoints": 0,
  "neededPoints": 0,
  "nextTier": "string",
  "apiError": false
}
```

---

### 4. Get Missions

**Endpoint**: `POST /api/images/getMissionImages`

**Purpose**: Retrieve list of user's scheduled missions

**Request**:
```json
{
  "sloohSessionToken": "string",
  "at": "string",
  "cid": "string",
  "token": "string",
  "productId": "ee26fb6d-3351-11eb-83b9-0655cc43ca95",
  "locale": "en",
  "maxMissionCount": 50,
  "firstMissionNumber": 1
}
```

**Response**:
```json
{
  "maxMissionCount": 50,
  "firstMissionNumber": 1,
  "missionCount": 25,
  "totalCount": 150,
  "imageList": [
    {
      "missionId": 123456,
      "imageTitle": "Orion Nebula",
      "telescopeName": "Canary Four",
      "instrumentName": "CCD Camera",
      "displayDate": "Feb. 7, 2026",
      "displayTime": "20:15:30 UTC",
      "imageCount": 5,
      "owner": "username"
    }
  ],
  "apiError": false
}
```

**Pagination**:
- `firstMissionNumber`: 1-based starting position
- `maxMissionCount`: Maximum missions to return (default: 18)
- `totalCount`: Total missions available
- Increment `firstMissionNumber` by `missionCount` for next page

---

### 5. Get My Pictures

**Endpoint**: `POST /api/images/getMyPictures`

**Purpose**: Retrieve user's pictures/images

**Request**:
```json
{
  "sloohSessionToken": "string",
  "at": "string",
  "cid": "string",
  "token": "string",
  "productId": "ee26fb6d-3351-11eb-83b9-0655cc43ca95",
  "locale": "en",
  "scheduledMissionId": 0,
  "maxImageCount": 50,
  "firstImageNumber": 1,
  "viewType": "photoRoll"
}
```

**Request Parameters**:
- `scheduledMissionId`: Mission ID (0 = all missions)
- `maxImageCount`: Maximum images per request (default: 18, recommended: 50)
- `firstImageNumber`: 1-based starting position for pagination
- `viewType`: **CRITICAL PARAMETER**
  - `"missions"`: Returns images grouped by mission
    - With `scheduledMissionId=0`: Returns only 1 image (BUG/LIMITATION)
    - With specific mission ID: Returns images for that mission
  - `"photoRoll"`: Returns all user images in reverse chronological order
    - With `scheduledMissionId=0`: Returns ALL images (recommended)
    - Position 1 = newest image, last position = oldest image

**Response**:
```json
{
  "maxImageCount": 50,
  "firstImageNumber": 1,
  "imageCount": 50,
  "totalCount": "1263",
  "viewType": "photoRoll",
  "imageList": [
    {
      "imageId": "string",
      "customerImageId": "string",
      "missionId": 123456,
      "imageTitle": "Orion Nebula (M42)",
      "imageDownloadURL": "https://astroimages.slooh.com/...",
      "imageType": "PNG",
      "telescopeName": "Canary Four",
      "instrumentName": "CCD Camera",
      "displayDate": "Feb. 7, 2026",
      "displayTime": "20:15:30 UTC"
    }
  ],
  "apiError": false
}
```

**Picture Object Fields**:
- `imageId`: Unique Slooh image ID
- `customerImageId`: Customer-specific ID (often same as imageId)
- `missionId`: Associated mission ID
- `imageTitle`: **Object/target name** (e.g., "Horsehead Nebula (IC 434)")
  - ⚠️ This is the ONLY field containing object name - no separate `objectName` field
  - Use this field for object name filtering
- `imageDownloadURL`: Direct download URL for the image file
- `imageType`: File format (FITS, PNG, JPG, JPEG)
- `telescopeName`: Telescope used (e.g., "Canary Four", "Chile Two")
- `instrumentName`: Instrument/camera name
- `displayDate`: Date in format "Feb. 7, 2026" (abbreviated month)
- `displayTime`: Time in format "HH:MM:SS UTC"

**Pagination**:
- `totalCount`: String (not integer!) - total images available
- Increment `firstImageNumber` by `imageCount` for next batch
- Continue until `firstImageNumber >= parseInt(totalCount)`

**CRITICAL DISCOVERY**:
- `viewType="missions"` with `scheduledMissionId=0` returns only 1 image (API limitation)
- `viewType="photoRoll"` with `scheduledMissionId=0` returns ALL images correctly
- For downloading all user images, **always use `viewType="photoRoll"`**

---

### 6. Get Mission FITS

**Endpoint**: `POST /api/images/getMissionFITS`

**Purpose**: Get FITS files for a specific mission, grouped by instrument

**Request**:
```json
{
  "sloohSessionToken": "string",
  "at": "string",
  "cid": "string",
  "token": "string",
  "productId": "ee26fb6d-3351-11eb-83b9-0655cc43ca95",
  "locale": "en",
  "scheduledMissionId": 123456
}
```

**Response**:
```json
{
  "groupList": [
    {
      "groupName": "CCD Imager",
      "groupImageList": [
        {
          "imageURL": "https://astroimages.slooh.com/.../barnard33_l.fits",
          "imageTitle": "barnard33_l.fits"
        },
        {
          "imageURL": "https://astroimages.slooh.com/.../barnard33_r.fits",
          "imageTitle": "barnard33_r.fits"
        },
        {
          "imageURL": "https://astroimages.slooh.com/.../barnard33_g.fits",
          "imageTitle": "barnard33_g.fits"
        },
        {
          "imageURL": "https://astroimages.slooh.com/.../barnard33_b.fits",
          "imageTitle": "barnard33_b.fits"
        }
      ]
    }
  ],
  "apiError": false
}
```

**Response Structure**:
- `groupList`: Array of instrument groups
  - `groupName`: Instrument/camera name (e.g., "CCD Imager", "Spectrograph")
  - `groupImageList`: Array of FITS files for this instrument
    - `imageURL`: Direct download URL for FITS file
    - `imageTitle`: FITS filename (e.g., "barnard33_l.fits", "barnard33_r.fits")

**FITS File Naming**:
- Individual filter frames: `object_l.fits`, `object_r.fits`, `object_g.fits`, `object_b.fits`
- L = Luminance (clear/unfiltered)
- R, G, B = Red, Green, Blue filters

**Important Notes**:
- Only works with specific mission IDs (not `scheduledMissionId=0`)
- Not all missions have FITS files available
- FITS files are separate from processed images (PNG/JPG/LRGB)
- Each processed image returned by `getMyPictures` may have corresponding FITS files

---

## Response Data Types

### Image Types
- `FITS`: Flexible Image Transport System (astronomy standard)
  - Raw calibrated data from telescope
  - Individual filter frames (L, R, G, B, Ha, OIII, etc.)
  - Retrieved via separate `getMissionFITS` API call
  - Not included in `getMyPictures` response
- `PNG`: Portable Network Graphics (processed/stacked)
- `JPG` / `JPEG`: JPEG image format (processed/stacked)
- `LRGB`: Composite color image (Luminance + RGB channels combined)
- `M` (Monochrome): Single-filter processed image

### Telescope Names
Common values observed:
- "Canary One", "Canary Two", "Canary Three", "Canary Four", "Canary Five"
- "Chile One", "Chile Two", "Chile Three"
- "Australia One"
- "Unknown" (fallback)

### Date/Time Formats

**displayDate**: `"Feb. 7, 2026"` or `"February 7, 2026"`
- Month can be abbreviated with period: "Feb.", "Jan.", "Dec."
- Month can be full: "February", "January", "December"
- Format: "%b. %d, %Y" or "%B %d, %Y"

**displayTime**: `"20:15:30 UTC"` or `"20:15 UTC"`
- Can include seconds or just HH:MM
- Always ends with " UTC"
- Format: "%H:%M:%S" or "%H:%M"

**Parsing Strategy**:
```python
# Try multiple formats
date_formats = ['%b. %d, %Y', '%B %d, %Y', '%Y-%m-%d']
time_formats = ['%H:%M:%S', '%H:%M']

for fmt in date_formats:
    try:
        date = datetime.strptime(display_date, fmt)
        break
    except:
        continue
```

---

## Download URLs

Image download URLs follow this pattern:
```
https://astroimages.slooh.com/{path}/{filename}
```

**Filename Structure**:
```
{telescope}_{object}_{date}_{time}_{sequence}_{id}_{filter}.{ext}
```

Example:
```
teide5-2026-01-09T100627UTC-HQSxaD.png
c-2025r2_20260207_200810_0_4kb82s_m.png
ngc3372_20260207_063727_0_re5tkp_lrgb.png
```

Components:
- Telescope code (teide5, c-2025r2, ngc3372, etc.)
- Date in various formats
- Time (usually HHMMSS or compact format)
- Sequence number
- Unique ID
- Filter/type suffix (_m, _lrgb, _l, _b, etc.)
- Extension (.png, .jpg, .fits)

**Extract Filename**:
```python
url = picture['imageDownloadURL']
filename = url.split('/')[-1].split('?')[0]  # Remove path and query params
```

---

## API Response Object Issues

### .NET Object Circular References

**Problem**: API responses from IronPython contain complex .NET objects with circular references that cause StackOverflowException when:
- Trying to modify the object
- Trying to serialize/log the object
- Passing object through multiple function calls

**Solution**: Extract data into simple Python dictionaries immediately:

```python
def _extract_picture_data(self, picture, photoroll_position):
    """Extract essential data into simple dict"""
    def safe_get(obj, key, default=''):
        try:
            val = obj.get(key, default)
            return str(val) if val is not None else default
        except:
            return default
    
    return {
        'imageId': safe_get(picture, 'imageId'),
        'customerImageId': safe_get(picture, 'customerImageId'),
        'imageTitle': safe_get(picture, 'imageTitle'),
        'imageDownloadURL': safe_get(picture, 'imageDownloadURL'),
        'imageType': safe_get(picture, 'imageType', 'FITS'),
        'telescopeName': safe_get(picture, 'telescopeName', 'Unknown'),
        # ... etc
    }
```

**Critical Rules**:
1. Never pass raw API response objects through generators
2. Never try to add fields to API response objects
3. Extract data to simple dicts IMMEDIATELY after API call
4. Use safe_get() to handle None/missing values
5. Convert all values to strings to avoid type issues

---

## Pagination Best Practices

### Memory Management

**Problem**: Loading all 1,000+ images at once causes memory issues and stack overflow

**Solution**: Process in batches

```python
batch_size = 50  # API request batch size
process_batch_size = 50  # Download processing batch size

for picture in get_all_pictures(batch_size=batch_size):
    tasks.append(create_task(picture))
    
    # Process every 50 tasks
    if len(tasks) >= process_batch_size:
        download_batch(tasks)
        tasks = []  # Clear for next batch
```

### Efficient Testing with max_scan

**Problem**: Testing filters requires scanning all 1,300+ images (slow)

**Solution**: Limit API retrieval with `max_scan` parameter

```python
def get_all_pictures(mission_id=0, batch_size=50, max_scan=None):
    """
    max_scan: Stop after retrieving this many pictures (None = unlimited)
    """
    retrieved = 0
    
    for picture in fetch_from_api(batch_size):
        yield picture
        retrieved += 1
        
        if max_scan and retrieved >= max_scan:
            break  # Stop early for testing
```

**Usage**:
- Testing filters: `max_scan=50` (scan only newest 50 images)
- Full download: `max_scan=None` (scan all available)

### Pagination Loop

```python
first = 1
total_count = None

while True:
    response = get_pictures(first=first, max_count=50, view_type='photoRoll')
    
    if total_count is None:
        total_count = int(response.get('totalCount', '0'))
    
    pictures = response.get('imageList', [])
    if not pictures:
        break
    
    for picture in pictures:
        yield picture
    
    first += len(pictures)
    if first > total_count:
        break
```

---

## Common Issues & Solutions

### Issue 1: Only 1 Image Returned

**Symptom**: `totalCount=1` when user has hundreds of images

**Cause**: Using `viewType="missions"` with `scheduledMissionId=0`

**Solution**: Use `viewType="photoRoll"` for all missions

### Issue 2: Stack Overflow During Download

**Symptom**: Process crashes with StackOverflowException

**Causes**:
1. Passing raw API objects through code
2. Trying to modify API response objects
3. Loading too many images at once
4. Excessive logging of complex objects

**Solutions**:
1. Extract data to simple dicts immediately
2. Process downloads in batches (50 at a time)
3. Avoid logging entire response objects
4. Use safe_get() for all field access

### Issue 3: Authentication Failures

**Symptom**: Login returns error even with correct credentials

**Causes**:
1. Using `password` instead of `passwd`
2. Using `sloohSiteSessionToken` instead of `sloohSessionToken`
3. Missing session token
4. Token not set as cookie

**Solution**: Use exact field names from API specification

### Issue 4: Filename Truncation

**Symptom**: Files named `{telescope}_image.jpg` instead of full Slooh names

**Cause**: Looking for `imageDownloadFilename` field which doesn't exist

**Solution**: Extract filename from `imageDownloadURL`:
```python
url = picture['imageDownloadURL']
filename = url.split('/')[-1].split('?')[0]
```

### Issue 5: Object Name Filter Returns 0 Results

**Symptom**: Object filter (e.g., "horsehead") finds no matches even though images exist

**Cause**: Filtering on non-existent `objectName` field

**Solution**: Object name is in `imageTitle` field, not `objectName`:
```python
# ❌ WRONG - objectName doesn't exist
if filter_object.lower() in picture.get('objectName', '').lower():
    match = True

# ✅ CORRECT - use imageTitle
if filter_object.lower() in picture.get('imageTitle', '').lower():
    match = True
```

**Examples**:
- `imageTitle`: "Horsehead Nebula (IC 434)"
- `imageTitle`: "Orion Nebula (M42)"
- `imageTitle`: "Andromeda Galaxy (M31)"

---

## API Behavior & Limitations

### Server-Side Filtering

**NOT Supported**:
- ❌ Filter by telescope name
- ❌ Filter by object name
- ❌ Filter by date range
- ❌ Filter by image type

**Supported**:
- ✅ Filter by mission ID (`scheduledMissionId`)
- ✅ Pagination (`firstImageNumber`, `maxImageCount`)

**Implication**: All filtering must be done client-side after fetching images

### Session Timeout

**Behavior**: Slooh automatically logs out sessions after period of inactivity (typically 15-30 minutes)

**Symptoms**:
- API returns `totalCount=0` for requests that previously worked
- Same request pattern that returned 1,300 images now returns 0
- No explicit error message - just empty results

**Detection**:
```python
if total_count == 0 and previously_had_images:
    # Session likely expired - need to re-authenticate
    pass
```

**Solutions**:
1. **Manual**: Close application and log in again
2. **Automatic** (future): Detect and re-authenticate automatically
3. **Preventive**: Complete downloads in one session without long pauses

**Note**: This matches Slooh website behavior - consistent with their web platform

### Rate Limiting

- No documented rate limits observed
- Batch size of 50 works reliably
- API timeout ~17 seconds for 50 images

### PhotoRoll Ordering

- **Position 1 = Newest image** (reverse chronological)
- **Last position = Oldest image**
- Order is consistent across requests
- Position tracking useful for incremental updates

### FITS File Retrieval Pattern

**Problem**: Processed images (PNG/LRGB) and FITS files are retrieved separately

**Pattern**:
1. Call `getMyPictures` → Returns processed images (PNG, LRGB, JPG)
2. Each image has a `missionId` field
3. For images with `missionId`, call `getMissionFITS(missionId)` → Returns raw FITS files
4. FITS files share the same object/target but are individual filter frames

**Implementation Strategy**:
```python
# Track missions already fetched to avoid duplicate API calls
fits_missions_fetched = set()

for picture in get_all_pictures():
    # Queue processed image (PNG/LRGB)
    queue_download(picture)
    
    # Also fetch FITS files for this mission
    mission_id = picture.get('missionId')
    if mission_id and mission_id not in fits_missions_fetched:
        fits_missions_fetched.add(mission_id)
        
        for fits_file in get_mission_fits(mission_id):
            # Queue FITS file
            queue_download(fits_file)
```

**Why Separate Calls?**:
- Different users have different access levels (some can't download FITS)
- FITS files are larger and not always needed
- Allows API to optimize bandwidth for different use cases

---

## Code Examples

### Complete Authentication Flow

```python
# 1. Get session token
response = client.PostAsync(BASE_URL + '/api/app/generateSessionToken', None).Result
data = json.loads(response.Content.ReadAsStringAsync().Result)
session_token = data['sloohSessionToken']

# 2. Set cookie
cookie = Cookie('_sloohsstkn', session_token)
cookie.Domain = '.slooh.com'
cookie.Path = '/'
cookie_container.Add(Uri(BASE_URL), cookie)

# 3. Login
login_data = {
    'sloohSessionToken': session_token,
    'username': 'user@example.com',
    'passwd': 'password',  # Note: passwd not password!
    'productId': 'ee26fb6d-3351-11eb-83b9-0655cc43ca95',
    'locale': 'en'
}
response = client.PostAsJsonAsync(BASE_URL + '/api/users/login', login_data).Result
user_data = json.loads(response.Content.ReadAsStringAsync().Result)

# Store for subsequent requests
at = user_data['at']
cid = user_data['cid']
token = user_data['token']
```

### Get All Pictures with Pagination

```python
def get_all_pictures(mission_id=0, batch_size=50, max_scan=None):
    """
    Get all pictures with pagination and optional scan limit.
    
    Args:
        mission_id: Mission ID (0 = all missions)
        batch_size: Images per API request
        max_scan: Stop after retrieving this many (None = unlimited)
    """
    first = 1
    total_count = None
    photoroll_position = 1
    retrieved = 0
    
    while True:
        request = {
            'sloohSessionToken': session_token,
            'at': at,
            'cid': cid,
            'token': token,
            'productId': 'ee26fb6d-3351-11eb-83b9-0655cc43ca95',
            'locale': 'en',
            'scheduledMissionId': mission_id,
            'maxImageCount': batch_size,
            'firstImageNumber': first,
            'viewType': 'photoRoll'  # CRITICAL for all missions
        }
        
        response = post_json('/api/images/getMyPictures', request)
        
        if total_count is None:
            total_count = int(response.get('totalCount', '0'))
            if total_count == 0:
                # Session may be expired
                break
        
        pictures = response.get('imageList', [])
        if not pictures:
            break
        
        for picture in pictures:
            # Extract to simple dict to avoid .NET object issues
            simple_picture = extract_picture_data(picture, photoroll_position)
            yield simple_picture
            photoroll_position += 1
            retrieved += 1
            
            # Check max_scan limit
            if max_scan and retrieved >= max_scan:
                return  # Stop early
        
        first += len(pictures)
        if first > total_count:
            break
```

### Get FITS Files for Missions

```python
def get_mission_fits(mission_id):
    """
    Get FITS files for a specific mission.
    
    Args:
        mission_id: Mission ID (must be > 0)
        
    Yields:
        dict: FITS file data
    """
    if not mission_id or mission_id == 0:
        return  # No FITS for mission_id=0
    
    request = {
        'sloohSessionToken': session_token,
        'at': at,
        'cid': cid,
        'token': token,
        'productId': 'ee26fb6d-3351-11eb-83b9-0655cc43ca95',
        'locale': 'en',
        'scheduledMissionId': mission_id
    }
    
    response = post_json('/api/images/getMissionFITS', request)
    
    groups = response.get('groupList', [])
    
    for group in groups:
        instrument_name = group.get('groupName', 'Unknown')
        images = group.get('groupImageList', [])
        
        for fits_image in images:
            yield {
                'imageDownloadURL': fits_image.get('imageURL', ''),
                'imageTitle': fits_image.get('imageTitle', ''),
                'instrumentName': instrument_name,
                'imageType': 'FITS',
                'missionId': str(mission_id)
            }
```

### Download Both Processed and FITS Files

```python
def download_all_with_fits(mission_id=0, max_scan=None):
    """
    Download both processed images and FITS files.
    """
    fits_missions_fetched = set()  # Track to avoid duplicates
    
    for picture in get_all_pictures(mission_id, max_scan=max_scan):
        # Download processed image (PNG/LRGB/JPG)
        download(picture)
        
        # Also fetch FITS files for this mission
        mission_id_str = picture.get('missionId', '')
        if mission_id_str and mission_id_str != '0':
            if mission_id_str not in fits_missions_fetched:
                fits_missions_fetched.add(mission_id_str)
                
                try:
                    for fits_file in get_mission_fits(int(mission_id_str)):
                        # Copy metadata from parent image
                        fits_file['imageTitle'] = picture.get('imageTitle')
                        fits_file['telescopeName'] = picture.get('telescopeName')
                        
                        download(fits_file)
                except Exception as e:
                    logger.warning(f"Failed to fetch FITS: {e}")
```

---

## Version History

- **v1.2** (2026-02-10): FITS file support
  - Expanded `getMissionFITS` endpoint documentation with complete response structure
  - Added FITS File Retrieval Pattern section
  - Documented FITS file grouping by instrument
  - Added code examples for fetching both processed images and FITS files
  - Clarified that FITS files are separate from processed images
  - Updated Image Types section with FITS details

- **v1.1** (2026-02-10): Testing phase updates
  - Added `max_scan` parameter for efficient filter testing
  - Documented that object name is in `imageTitle` field (no separate `objectName`)
  - Added session timeout behavior documentation
  - Added Issue 5: Object name filter troubleshooting
  - Updated code examples with max_scan and session detection

- **v1.0** (2026-02-10): Initial documentation
  - Documented all endpoints
  - Identified viewType photoRoll issue
  - Documented .NET object circular reference problems
  - Added pagination best practices
  - Documented common issues and solutions

---

## References

- Original C# implementation: `src/Slooh.Explorer/`
- Python implementation: `SloohDownloader/src/slooh_client.py`
- Bug fixes log: `SloohDownloader/BUGFIXES.md`
