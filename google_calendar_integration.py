#!/usr/bin/env python3
"""
Google Calendar Integration for Commission Analysis
Accesses calendars as admin user to find meeting data for deals
"""

import os
import json
import datetime
from typing import Dict, List, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleCalendarIntegration:
    """Google Calendar integration for finding meeting data"""
    
    # If modifying these scopes, delete the file token.json.
    SCOPES = [
        'https://www.googleapis.com/auth/calendar.readonly',
        'https://www.googleapis.com/auth/calendar.events.readonly'
    ]
    
    def __init__(self):
        self.creds = None
        self.service = None
        self.calendar_ids = []
        
    def authenticate(self):
        """Authenticate with Google Calendar API"""
        # The file token.json stores the user's access and refresh tokens
        if os.path.exists('token.json'):
            try:
                self.creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
            except Exception as e:
                print(f"Error loading token: {e}")
                self.creds = None
        
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing token: {e}")
                    self.creds = None
            
            if not self.creds:
                # Check if we have client credentials
                if os.path.exists('credentials.json'):
                    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', self.SCOPES)
                    self.creds = flow.run_local_server(port=0)
                else:
                    print("No credentials.json found. Please set up OAuth credentials.")
                    return False
            
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())
        
        try:
            self.service = build('calendar', 'v3', credentials=self.creds)
            return True
        except Exception as e:
            print(f"Error building service: {e}")
            return False
    
    def get_calendar_list(self):
        """Get list of accessible calendars"""
        try:
            calendar_list = self.service.calendarList().list().execute()
            self.calendar_ids = []
            
            for calendar in calendar_list['items']:
                calendar_id = calendar['id']
                summary = calendar.get('summary', 'Unknown')
                access_role = calendar.get('accessRole', 'unknown')
                
                print(f"Calendar: {summary} ({calendar_id}) - Access: {access_role}")
                self.calendar_ids.append(calendar_id)
                
            return self.calendar_ids
        except HttpError as error:
            print(f'Error getting calendar list: {error}')
            return []
    
    def search_meetings_for_company(self, company_name: str, days_back: int = 90) -> List[Dict]:
        """Search for meetings related to a specific company"""
        if not self.service:
            print("Not authenticated")
            return []
        
        # Calculate time range
        now = datetime.datetime.utcnow()
        time_min = (now - datetime.timedelta(days=days_back)).isoformat() + 'Z'
        time_max = now.isoformat() + 'Z'
        
        meetings = []
        
        for calendar_id in self.calendar_ids:
            try:
                # Search for events with company name in title or description
                events_result = self.service.events().list(
                    calendarId=calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    q=company_name,  # Search query
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                events = events_result.get('items', [])
                
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    end = event['end'].get('dateTime', event['end'].get('date'))
                    title = event.get('summary', 'No Title')
                    description = event.get('description', '')
                    attendees = event.get('attendees', [])
                    
                    # Check if company name appears in title or description
                    if (company_name.lower() in title.lower() or 
                        company_name.lower() in description.lower()):
                        
                        meeting_info = {
                            'calendar_id': calendar_id,
                            'event_id': event['id'],
                            'title': title,
                            'start': start,
                            'end': end,
                            'description': description,
                            'attendees': [a.get('email', '') for a in attendees],
                            'duration_minutes': self._calculate_duration(start, end)
                        }
                        meetings.append(meeting_info)
                        
            except HttpError as error:
                print(f'Error searching calendar {calendar_id}: {error}')
                continue
        
        return meetings
    
    def search_meetings_for_user(self, user_email: str, days_back: int = 90) -> List[Dict]:
        """Search for meetings attended by a specific user"""
        if not self.service:
            print("Not authenticated")
            return []
        
        # Calculate time range
        now = datetime.datetime.utcnow()
        time_min = (now - datetime.timedelta(days=days_back)).isoformat() + 'Z'
        time_max = now.isoformat() + 'Z'
        
        meetings = []
        
        for calendar_id in self.calendar_ids:
            try:
                events_result = self.service.events().list(
                    calendarId=calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                events = events_result.get('items', [])
                
                for event in events:
                    attendees = event.get('attendees', [])
                    attendee_emails = [a.get('email', '') for a in attendees]
                    
                    # Check if user is an attendee
                    if user_email in attendee_emails:
                        start = event['start'].get('dateTime', event['start'].get('date'))
                        end = event['end'].get('dateTime', event['end'].get('date'))
                        title = event.get('summary', 'No Title')
                        description = event.get('description', '')
                        
                        meeting_info = {
                            'calendar_id': calendar_id,
                            'event_id': event['id'],
                            'title': title,
                            'start': start,
                            'end': end,
                            'description': description,
                            'attendees': attendee_emails,
                            'duration_minutes': self._calculate_duration(start, end)
                        }
                        meetings.append(meeting_info)
                        
            except HttpError as error:
                print(f'Error searching calendar {calendar_id}: {error}')
                continue
        
        return meetings
    
    def _calculate_duration(self, start: str, end: str) -> int:
        """Calculate meeting duration in minutes"""
        try:
            if 'T' in start and 'T' in end:  # Has time
                start_dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                end_dt = datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
                duration = end_dt - start_dt
                return int(duration.total_seconds() / 60)
            else:  # All-day event
                return 0
        except:
            return 0
    
    def get_meeting_summary_for_company(self, company_name: str, days_back: int = 90) -> Dict:
        """Get summary of meetings for a company"""
        meetings = self.search_meetings_for_company(company_name, days_back)
        
        if not meetings:
            return {
                'company': company_name,
                'total_meetings': 0,
                'total_duration_minutes': 0,
                'attendees': {},
                'meetings': []
            }
        
        # Calculate totals
        total_duration = sum(m['duration_minutes'] for m in meetings)
        attendees = {}
        
        for meeting in meetings:
            for attendee in meeting['attendees']:
                if attendee:
                    attendees[attendee] = attendees.get(attendee, 0) + meeting['duration_minutes']
        
        return {
            'company': company_name,
            'total_meetings': len(meetings),
            'total_duration_minutes': total_duration,
            'attendees': attendees,
            'meetings': meetings
        }

def main():
    """Main function to test calendar integration"""
    calendar = GoogleCalendarIntegration()
    
    if not calendar.authenticate():
        print("Failed to authenticate")
        return
    
    print("Successfully authenticated with Google Calendar")
    
    # Get list of accessible calendars
    calendar_ids = calendar.get_calendar_list()
    print(f"\nFound {len(calendar_ids)} accessible calendars")
    
    # Test search for Launchnodes meetings
    print("\nSearching for Launchnodes meetings...")
    launchnodes_meetings = calendar.search_meetings_for_company("Launchnodes", days_back=180)
    
    if launchnodes_meetings:
        print(f"Found {len(launchnodes_meetings)} Launchnodes meetings:")
        for meeting in launchnodes_meetings:
            print(f"  - {meeting['title']} ({meeting['start']}) - {meeting['duration_minutes']} min")
    else:
        print("No Launchnodes meetings found")
    
    # Test search for meetings with specific users
    print("\nSearching for meetings with team members...")
    team_emails = [
        "aki@example.com",  # Replace with actual emails
        "addie@example.com",
        "mayank@example.com",
        "amy@example.com"
    ]
    
    for email in team_emails:
        user_meetings = calendar.search_meetings_for_user(email, days_back=30)
        if user_meetings:
            total_duration = sum(m['duration_minutes'] for m in user_meetings)
            print(f"  {email}: {len(user_meetings)} meetings, {total_duration} minutes total")

if __name__ == '__main__':
    main()
