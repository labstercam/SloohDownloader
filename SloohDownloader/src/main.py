"""
Slooh Image Downloader - Main Entry Point
Command-line interface for downloading Slooh images.
"""

import clr
clr.AddReference('System')
from System import Environment
from System.IO import Path
import sys

# Add src directory to path for imports
script_dir = Path.GetDirectoryName(__file__)
if script_dir not in sys.path:
    sys.path.append(script_dir)

from config_manager import ConfigurationManager, get_config
from logger import Logger, get_logger
from slooh_client import SloohClient
from download_manager import DownloadManager
from file_organizer import FileOrganizer
from batch_manager import BatchManager
from download_tracker import DownloadTracker


def print_banner():
    """Print application banner"""
    print("=" * 60)
    print(" Slooh Image Downloader v2.0 (Stage 2)")
    print(" IronPython Edition")
    print("=" * 60)
    print()
    print("NOTE: Interactive menu works best in PowerShell/Command Prompt")
    print("      If you experience input issues, use command-line options:")
    print("      Example: ipy src/main.py --configure")
    print()


def print_usage():
    """Print usage information"""
    print("Usage:")
    print("  ipy main.py                   Interactive menu mode")
    print("  ipy main.py --configure       Setup or edit configuration")
    print("  ipy main.py --test            Test configuration and authentication")
    print("  ipy main.py --download        Download all new images")
    print("  ipy main.py --download-all    Download ALL images (ignores tracker)")
    print("  ipy main.py --mission <id>    Download specific mission")
    print("  ipy main.py --retry           Retry failed downloads")
    print("  ipy main.py --stats           Show download statistics")
    print("  ipy main.py --help            Show this help")
    print()


def show_menu():
    """Display interactive menu"""
    print()
    print("=" * 60)
    print(" SLOOH DOWNLOADER - MAIN MENU")
    print("=" * 60)
    print()
    print("  1. Configure settings")
    print("  2. Test authentication")
    print("  3. Download new images")
    print("  4. Download ALL images (ignores tracker)")
    print("  5. Download specific mission")
    print("  6. Retry failed downloads")
    print("  7. Show download statistics")
    print("  8. Help")
    print("  0. Exit")
    print()


def interactive_menu(config_manager, logger):
    """Run interactive menu loop"""
    while True:
        show_menu()
        try:
            choice = safe_input("Select option (0-8): ").strip()
            print()
            
            if choice == '0':
                print("Exiting...")
                return 0
            
            elif choice == '1':
                configure_interactive(config_manager)
            
            elif choice == '2':
                test_authentication(config_manager, logger)
            
            elif choice == '3':
                download_new_images(config_manager, logger)
            
            elif choice == '4':
                download_all_images(config_manager, logger)
            
            elif choice == '5':
                mission_id = safe_input("Enter mission ID: ").strip()
                try:
                    mission_id = int(mission_id)
                    download_mission(mission_id, config_manager, logger)
                except ValueError:
                    print("ERROR: Invalid mission ID")
            
            elif choice == '6':
                retry_failed(config_manager, logger)
            
            elif choice == '7':
                show_stats(config_manager)
            
            elif choice == '8':
                print_usage()
            
            else:
                print("Invalid option. Please select 0-8.")
            
            # Pause before showing menu again
            if choice != '0':
                print()
                safe_input("Press Enter to continue...")
        
        except KeyboardInterrupt:
            print("\n\nExiting...")
            return 0
        except Exception as e:
            print("ERROR: {0}".format(str(e)))
            safe_input("Press Enter to continue...")


def safe_input(prompt):
    """Safe input function that works better with IronPython console"""
    import sys
    try:
        sys.stdout.write(prompt)
        sys.stdout.flush()
        result = sys.stdin.readline()
        if result:
            return result.rstrip('\r\n')
        return ''
    except Exception as e:
        # Console input failed - likely PythonConsoleControl issue
        print("\n[ERROR: Console input failed. Use command-line mode instead.]")
        print("Example: ipy src/main.py --configure")
        raise


def configure_interactive(config_manager):
    """Interactive configuration setup"""
    print("\n--- Configuration Setup ---\n")
    
    # Slooh credentials
    print("Slooh Credentials:")
    username = safe_input("  Username: ").strip()
    password = safe_input("  Password: ").strip()
    
    if username:
        config_manager.set('slooh.username', username)
    if password:
        config_manager.set('slooh.password', password)
    
    # Download folder
    print("\nDownload Settings:")
    root_folder = safe_input("  Root download folder [{0}]: ".format(
        config_manager.get('folders.base_path'))).strip()
    if root_folder:
        config_manager.set('folders.base_path', root_folder)
    
    # Batch size
    batch_input = safe_input("  Batch size [{0}]: ".format(
        config_manager.get('download.batch_size'))).strip()
    if batch_input:
        try:
            batch_size = int(batch_input)
            config_manager.set('download.batch_size', batch_size)
        except:
            print("  Invalid batch size, keeping default")
    
    # Save configuration
    try:
        config_manager.save()
        print("\nConfiguration saved successfully!")
        
        # Ensure directories exist
        config_manager.ensure_directories()
        
    except Exception as e:
        print("Error saving configuration: {0}".format(str(e)))
        return False
    
    return True


def test_authentication(config_manager, logger):
    """Test Slooh authentication"""
    print("\n--- Testing Slooh Authentication ---\n")
    
    # Check credentials configured
    if not config_manager.has_credentials():
        print("ERROR: Slooh credentials not configured.")
        print("Run with --configure to set up credentials.")
        return False
    
    username = config_manager.get('slooh.username')
    base_url = config_manager.get('slooh.base_url')
    
    print("Slooh URL: {0}".format(base_url))
    print("Username: {0}".format(username))
    print()
    
    # Create client
    client = SloohClient(base_url, logger)
    
    try:
        # Test connection
        print("1. Testing connection...")
        if not client.test_connection():
            print("   FAILED: Could not connect to Slooh")
            return False
        print("   SUCCESS: Connected to Slooh")
        
        # Test authentication
        print("\n2. Testing authentication...")
        password = config_manager.get('slooh.password')
        user_data = client.login(username, password)
        
        print("   SUCCESS: Authenticated!")
        print("\n   User Information:")
        print("   - Display Name: {0}".format(user_data.get('displayName')))
        print("   - User ID: {0}".format(user_data.get('userId')))
        print("   - Membership: {0}".format(user_data.get('membershipType')))
        print("   - Member Since: {0}".format(user_data.get('memberSince')))
        
        # Test getting missions
        print("\n3. Testing API access...")
        try:
            response = client.get_missions(first=1, max_count=1)
            total = response.get('totalCount', 0)
            print("   SUCCESS: Found {0} total missions".format(total))
            
            if 'imageList' in response and response['imageList']:
                mission = response['imageList'][0]
                print("   Latest mission: {0}".format(mission.get('imageTitle', 'Untitled')))
        except Exception as e:
            print("   WARNING: Could not get missions: {0}".format(str(e)))
        
        print("\n" + "=" * 60)
        print("All tests passed! Configuration is working correctly.")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print("   FAILED: {0}".format(str(e)))
        return False
    finally:
        client.close()


def download_new_images(config_manager, logger):
    """Download new images since last session"""
    print("\n--- Downloading New Images ---\n")
    
    if not config_manager.has_credentials():
        print("ERROR: Slooh credentials not configured.")
        print("Run with --configure to set up credentials.")
        return False
    
    try:
        # Initialize components
        client = SloohClient(config_manager.get('slooh.base_url'), logger)
        downloader = DownloadManager(config_manager.config, logger)
        organizer = FileOrganizer(config_manager.config, logger)
        tracker = DownloadTracker(config_manager.get('tracking.tracker_file'))
        tracker.load()
        
        batch_manager = BatchManager(
            config_manager.config, client, downloader, organizer, tracker, logger)
        
        # Set up progress callback
        def on_progress(progress):
            print("  Progress: {0}/{1} ({2:.1f}%) - {3} active".format(
                progress['completed'], progress['total'], 
                progress['percent'], progress['active']))
        
        batch_manager.on_progress = on_progress
        
        # Authenticate
        print("Authenticating...")
        username = config_manager.get('slooh.username')
        password = config_manager.get('slooh.password')
        client.login(username, password)
        print("Authenticated as: {0}\n".format(username))
        
        # Download new images
        stats = batch_manager.download_new_since_last_session()
        
        # Show results
        print("\n" + "=" * 60)
        print("Download Complete!")
        print("=" * 60)
        print("Total available: {0}".format(stats['total_available']))
        print("Already downloaded: {0}".format(stats['already_downloaded']))
        print("Skipped (existing): {0}".format(stats['skipped_existing']))
        print("Downloaded: {0}".format(stats['downloaded']))
        print("Failed: {0}".format(stats['failed']))
        print("Total size: {0:.2f} MB".format(stats['total_bytes'] / (1024.0 * 1024.0)))
        print("=" * 60)
        
        return stats['failed'] == 0
        
    except Exception as e:
        print("ERROR: {0}".format(str(e)))
        logger.error("Download failed: {0}".format(str(e)))
        return False
    finally:
        if 'client' in locals():
            client.close()
        if 'downloader' in locals():
            downloader.close()


def download_all_images(config_manager, logger):
    """Download ALL images (ignoring tracker)"""
    print("\n--- Downloading ALL Images ---\n")
    print("WARNING: This will download all images, even if already downloaded.")
    response = safe_input("Continue? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("Cancelled.")
        return True
    
    # Temporarily disable tracker checking
    original_check = config_manager.get('download.check_tracker')
    config_manager.set('download.check_tracker', False)
    
    try:
        return download_new_images(config_manager, logger)
    finally:
        config_manager.set('download.check_tracker', original_check)


def download_mission(mission_id, config_manager, logger):
    """Download specific mission"""
    print("\n--- Downloading Mission {0} ---\n".format(mission_id))
    
    if not config_manager.has_credentials():
        print("ERROR: Slooh credentials not configured.")
        return False
    
    try:
        # Initialize components
        client = SloohClient(config_manager.get('slooh.base_url'), logger)
        downloader = DownloadManager(config_manager.config, logger)
        organizer = FileOrganizer(config_manager.config, logger)
        tracker = DownloadTracker(config_manager.get('tracking.tracker_file'))
        tracker.load()
        
        batch_manager = BatchManager(
            config_manager.config, client, downloader, organizer, tracker, logger)
        
        # Authenticate
        print("Authenticating...")
        username = config_manager.get('slooh.username')
        password = config_manager.get('slooh.password')
        client.login(username, password)
        
        # Download mission
        stats = batch_manager.download_mission(mission_id)
        
        # Show results
        print("\n" + "=" * 60)
        print("Download Complete!")
        print("=" * 60)
        print("Downloaded: {0}".format(stats['downloaded']))
        print("Failed: {0}".format(stats['failed']))
        print("=" * 60)
        
        return stats['failed'] == 0
        
    except Exception as e:
        print("ERROR: {0}".format(str(e)))
        return False
    finally:
        if 'client' in locals():
            client.close()


def retry_failed(config_manager, logger):
    """Retry failed downloads"""
    print("\n--- Retrying Failed Downloads ---\n")
    
    try:
        tracker = DownloadTracker(config_manager.get('tracking.tracker_file'))
        tracker.load()
        
        failed = tracker.get_failed_downloads()
        if not failed:
            print("No failed downloads to retry.")
            return True
        
        print("Found {0} failed downloads\n".format(len(failed)))
        
        # Initialize components
        client = SloohClient(config_manager.get('slooh.base_url'), logger)
        downloader = DownloadManager(config_manager.config, logger)
        organizer = FileOrganizer(config_manager.config, logger)
        
        batch_manager = BatchManager(
            config_manager.config, client, downloader, organizer, tracker, logger)
        
        # Authenticate
        username = config_manager.get('slooh.username')
        password = config_manager.get('slooh.password')
        client.login(username, password)
        
        # Retry
        stats = batch_manager.resume_failed_downloads()
        
        print("\n" + "=" * 60)
        print("Retry Complete!")
        print("=" * 60)
        print("Downloaded: {0}".format(stats.get('completed', 0)))
        print("Failed: {0}".format(stats.get('failed', 0)))
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print("ERROR: {0}".format(str(e)))
        return False
    finally:
        if 'client' in locals():
            client.close()


def show_stats(config_manager):
    """Show download statistics"""
    print("\n--- Download Statistics ---\n")
    
    try:
        tracker = DownloadTracker(config_manager.get('tracking.tracker_file'))
        tracker.load()
        
        stats = tracker.get_statistics()
        
        print("Images:")
        print("  Total downloaded: {0}".format(stats['total_images']))
        print("  Failed: {0}".format(stats['failed_downloads']))
        print("  Success rate: {0:.1f}%".format(stats['success_rate']))
        
        print("\nSessions:")
        print("  Total sessions: {0}".format(stats['total_sessions']))
        print("  Successful: {0}".format(stats['successful_sessions']))
        
        print("\nData:")
        print("  Total size: {0:.2f} MB".format(stats['total_size_mb']))
        
        if stats['last_download']:
            print("\nLast Download:")
            print("  Date: {0}".format(stats['last_download']))
        
        # Show folder stats
        organizer = FileOrganizer(config_manager.config)
        folder_stats = organizer.get_folder_stats()
        
        print("\nFolders:")
        print("  Base path: {0}".format(folder_stats['base_path']))
        print("  Total files: {0}".format(folder_stats['total_files']))
        print("  Total size: {0:.2f} MB".format(folder_stats['total_size_mb']))
        
        print()
        
    except Exception as e:
        print("ERROR: {0}".format(str(e)))


def main():
    """Main entry point"""
    print_banner()
    
    # Parse command line arguments
    args = Environment.GetCommandLineArgs()
    
    # Check for help or no arguments - show interactive menu
    if len(args) < 2:
        # No arguments - run interactive menu
        try:
            config_manager = ConfigurationManager()
            config_manager.load()
            logger = get_logger('SloohDownloader', config_manager)
            logger.info("Slooh Downloader started in interactive mode")
            return interactive_menu(config_manager, logger)
        except Exception as e:
            print("ERROR: Failed to initialize: {0}".format(str(e)))
            return 1
    
    if '--help' in args:
        print_usage()
        return 0
    
    # Initialize configuration
    try:
        config_manager = ConfigurationManager()
        config_manager.load()
        
        # Initialize logger
        logger = get_logger('SloohDownloader', config_manager)
        logger.info("Slooh Downloader started")
        
    except Exception as e:
        print("ERROR: Failed to initialize: {0}".format(str(e)))
        return 1
    
    # Handle commands
    if '--configure' in args:
        if configure_interactive(config_manager):
            return 0
        else:
            return 1
    
    elif '--test' in args:
        if test_authentication(config_manager, logger):
            return 0
        else:
            return 1
    
    elif '--download' in args:
        if download_new_images(config_manager, logger):
            return 0
        else:
            return 1
    
    elif '--download-all' in args:
        if download_all_images(config_manager, logger):
            return 0
        else:
            return 1
    
    elif '--mission' in args:
        try:
            mission_idx = args.index('--mission')
            if mission_idx + 1 < len(args):
                mission_id = int(args[mission_idx + 1])
                if download_mission(mission_id, config_manager, logger):
                    return 0
                else:
                    return 1
            else:
                print("ERROR: --mission requires mission ID")
                return 1
        except ValueError:
            print("ERROR: Invalid mission ID")
            return 1
    
    elif '--retry' in args:
        if retry_failed(config_manager, logger):
            return 0
        else:
            return 1
    
    elif '--stats' in args:
        show_stats(config_manager)
        return 0
    
    else:
        print("ERROR: Unknown command")
        print_usage()
        return 1


if __name__ == '__main__':
    exit_code = 0
    try:
        exit_code = main()
    except (SystemExit, KeyboardInterrupt):
        pass
    except Exception as e:
        print("\nFATAL ERROR: {0}".format(str(e)))
        import traceback
        traceback.print_exc()
        exit_code = 1
    
    # Use os._exit to avoid SystemExit exception traceback in IronPython
    import os
    os._exit(exit_code)
