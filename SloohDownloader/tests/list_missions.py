"""
Quick script to list your Slooh missions and get valid mission IDs
Run this to find mission IDs for testing
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config_manager import get_config
from logger import get_logger
from slooh_client import SloohClient


def main():
    """List missions and their IDs"""
    print("=" * 70)
    print("Slooh Mission Lister")
    print("=" * 70)
    
    # Get credentials
    config = get_config()
    logger = get_logger()
    
    username = config.get('credentials.username')
    password = config.get('credentials.password')
    
    if not username or not password:
        print("\nNo saved credentials found.")
        username = input("Enter username/email: ")
        password = input("Enter password: ")
    else:
        print("\nUsing saved credentials: {0}".format(username))
    
    # Login
    print("\nLogging in...")
    try:
        client = SloohClient('https://app.slooh.com', logger)
        client.get_session_token()
        user_data = client.login(username, password)
        
        if user_data:
            print("Logged in as: {0}".format(user_data.get('displayName', username)))
        else:
            print("Login failed!")
            return
            
    except Exception as e:
        print("Login error: {0}".format(str(e)))
        return
    
    # Get missions
    print("\nFetching your missions...")
    print("-" * 70)
    
    try:
        # Get first batch of missions
        response = client.get_missions(first=1, max_count=20)
        
        total = response.get('totalCount', 0)
        missions = response.get('imageList', [])
        
        print("\nYou have {0} total missions".format(total))
        print("\nShowing first {0} missions:\n".format(len(missions)))
        
        for i, mission in enumerate(missions, 1):
            mission_id = mission.get('missionId', 'N/A')
            title = mission.get('title', 'Untitled')
            timestamp = mission.get('timestamp', 'N/A')
            telescope = mission.get('telescope', 'N/A')
            
            print("{0:2d}. Mission ID: {1:8s} - {2}".format(i, str(mission_id), title))
            print("    Date: {0}, Telescope: {1}".format(timestamp, telescope))
            print()
        
        if len(missions) > 0:
            first_mission = missions[0].get('missionId')
            print("=" * 70)
            print("TIP: Use Mission ID {0} for testing in GUI".format(first_mission))
            print("=" * 70)
        
    except Exception as e:
        print("Error fetching missions: {0}".format(str(e)))
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
