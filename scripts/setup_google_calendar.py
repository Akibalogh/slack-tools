#!/usr/bin/env python3
"""
Google Calendar Setup Script
Helps configure Google Calendar API credentials for ETL integration
"""

import json
import os
import sys
from pathlib import Path


def create_credentials_directory():
    """Create credentials directory if it doesn't exist"""
    creds_dir = Path("credentials")
    creds_dir.mkdir(exist_ok=True)
    print(f"✅ Created credentials directory: {creds_dir}")
    return creds_dir


def create_credentials_template():
    """Create a template for Google Calendar credentials"""
    template = {
        "installed": {
            "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
            "project_id": "your-project-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "YOUR_CLIENT_SECRET",
            "redirect_uris": ["http://localhost"],
        }
    }

    creds_file = Path("credentials/calendar_credentials.json")
    with open(creds_file, "w") as f:
        json.dump(template, f, indent=2)

    print(f"✅ Created credentials template: {creds_file}")
    return creds_file


def print_setup_instructions():
    """Print setup instructions for Google Calendar API"""
    print("\n" + "=" * 80)
    print("GOOGLE CALENDAR API SETUP INSTRUCTIONS")
    print("=" * 80)
    print()
    print("1. Go to Google Cloud Console:")
    print("   https://console.cloud.google.com/")
    print()
    print("2. Create a new project or select an existing one")
    print()
    print("3. Enable the Google Calendar API:")
    print("   - Go to 'APIs & Services' > 'Library'")
    print("   - Search for 'Google Calendar API'")
    print("   - Click 'Enable'")
    print()
    print("4. Create credentials:")
    print("   - Go to 'APIs & Services' > 'Credentials'")
    print("   - Click 'Create Credentials' > 'OAuth client ID'")
    print("   - Choose 'Desktop application'")
    print("   - Download the JSON file")
    print()
    print("5. Replace the template file:")
    print("   - Rename the downloaded file to 'calendar_credentials.json'")
    print("   - Place it in the 'credentials/' directory")
    print("   - Replace the template values in the file")
    print()
    print("6. Test the integration:")
    print(
        "   python3 -c \"from src.etl.integrations.google_calendar_integration import GoogleCalendarIntegration; calendar = GoogleCalendarIntegration(); print('Success!' if calendar.test_connection() else 'Failed')\""
    )
    print()
    print("=" * 80)


def create_gitignore_entry():
    """Add credentials to .gitignore if not already present"""
    gitignore_file = Path(".gitignore")

    if gitignore_file.exists():
        with open(gitignore_file, "r") as f:
            content = f.read()

        if "credentials/" not in content:
            with open(gitignore_file, "a") as f:
                f.write("\n# Google Calendar credentials\ncredentials/\n")
            print("✅ Added credentials/ to .gitignore")
        else:
            print("✅ credentials/ already in .gitignore")
    else:
        with open(gitignore_file, "w") as f:
            f.write("# Google Calendar credentials\ncredentials/\n")
        print("✅ Created .gitignore with credentials/ entry")


def install_required_packages():
    """Install required Python packages"""
    packages = [
        "google-auth",
        "google-auth-oauthlib",
        "google-auth-httplib2",
        "google-api-python-client",
    ]

    print("\nInstalling required packages...")
    for package in packages:
        print(f"Installing {package}...")
        os.system(f"pip3 install {package}")


def main():
    """Main setup function"""
    print("🚀 Setting up Google Calendar integration...")

    # Create credentials directory
    create_credentials_directory()

    # Create credentials template
    create_credentials_template()

    # Add to gitignore
    create_gitignore_entry()

    # Install packages
    install_required_packages()

    # Print instructions
    print_setup_instructions()

    print("\n✅ Google Calendar setup complete!")
    print("Follow the instructions above to configure your credentials.")


if __name__ == "__main__":
    main()
