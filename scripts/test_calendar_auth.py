#!/usr/bin/env python3
"""
Test Google Calendar Authentication
Simple script to test if Google Calendar credentials are working
"""

import os
import sys
from pathlib import Path


def check_credentials_file():
    """Check if credentials file exists and has real values"""
    creds_file = Path("credentials/calendar_credentials.json")

    if not creds_file.exists():
        print("❌ Credentials file not found: credentials/calendar_credentials.json")
        return False

    try:
        import json

        with open(creds_file, "r") as f:
            creds = json.load(f)

        client_id = creds.get("installed", {}).get("client_id", "")
        client_secret = creds.get("installed", {}).get("client_secret", "")

        if "YOUR_CLIENT_ID" in client_id or "YOUR_CLIENT_SECRET" in client_secret:
            print("❌ Credentials file contains placeholder values")
            print("   Please replace with real Google Cloud Console credentials")
            return False

        if not client_id or not client_secret:
            print("❌ Credentials file is missing required fields")
            return False

        print("✅ Credentials file looks valid")
        return True

    except Exception as e:
        print(f"❌ Error reading credentials file: {e}")
        return False


def test_authentication():
    """Test Google Calendar authentication"""
    try:
        from src.etl.integrations.google_calendar_integration import (
            GoogleCalendarIntegration,
        )

        print("🔐 Testing Google Calendar authentication...")
        calendar = GoogleCalendarIntegration()

        if calendar.authenticate():
            print("✅ Authentication successful!")
            return True
        else:
            print("❌ Authentication failed")
            return False

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're running from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False


def test_calendar_access():
    """Test access to calendar data"""
    try:
        from datetime import datetime, timedelta

        from src.etl.integrations.google_calendar_integration import (
            GoogleCalendarIntegration,
        )

        print("📅 Testing calendar data access...")
        calendar = GoogleCalendarIntegration()

        if calendar.authenticate():
            # Test getting calendar list
            calendars = calendar.get_calendar_list()
            print(f"✅ Found {len(calendars)} calendars")

            # Test getting recent meetings
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            meetings = calendar.get_meetings(start_date, end_date)
            print(f"✅ Retrieved {len(meetings)} meetings from last 7 days")

            if meetings:
                print("\n📋 Sample meetings:")
                for i, meeting in enumerate(meetings[:3], 1):
                    print(f"  {i}. {meeting['summary']}")
                    print(f"     Time: {meeting['start_time']}")
                    print(f"     Attendees: {len(meeting['attendees'])}")

            return True
        else:
            print("❌ Cannot access calendar data")
            return False

    except Exception as e:
        print(f"❌ Calendar access error: {e}")
        return False


def main():
    """Main test function"""
    print("🚀 Google Calendar Integration Test")
    print("=" * 50)

    # Check credentials file
    if not check_credentials_file():
        print("\n📖 Please follow the setup guide in GOOGLE_CALENDAR_SETUP.md")
        return False

    # Test authentication
    if not test_authentication():
        print("\n📖 Please check your credentials and try again")
        return False

    # Test calendar access
    if not test_calendar_access():
        print("\n📖 Please check your calendar permissions")
        return False

    print("\n🎉 All tests passed! Google Calendar integration is working!")
    print("You can now run the ETL with real calendar data.")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
