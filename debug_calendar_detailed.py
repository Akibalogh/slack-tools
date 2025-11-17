#!/usr/bin/env python3
"""
Detailed debug script for Calendar matching
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from etl.utils.company_matcher import CompanyMatcher
from etl.etl_data_ingestion import DataETL

def debug_calendar_matching():
    """Debug calendar matching in detail"""
    
    # Load company mapping
    etl = DataETL()
    companies = etl.load_company_mapping()
    
    # Load calendar data using the integration directly
    try:
        from etl.integrations.google_calendar_integration import GoogleCalendarIntegration
        calendar = GoogleCalendarIntegration()
        
        if calendar.authenticate():
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)
            
            meetings = calendar.get_meetings(start_date, end_date)
            print(f"Retrieved {len(meetings)} meetings from Google Calendar")
            
            # Test matching for first 10 meetings
            company_matcher = CompanyMatcher()
            
            for i, meeting in enumerate(meetings[:10]):
                summary = meeting.get('summary', '')
                description = meeting.get('description', '')
                attendees = meeting.get('attendees', [])
                
                # Extract attendee emails
                attendee_emails = []
                for attendee in attendees:
                    if isinstance(attendee, dict) and 'email' in attendee:
                        attendee_emails.append(attendee['email'])
                
                meeting_text = f"{summary} {description} {' '.join(attendee_emails)}".lower()
                
                print(f"\nMeeting {i+1}: {summary}")
                print(f"  Description: {description[:100]}...")
                print(f"  Attendees: {attendee_emails}")
                print(f"  Meeting text: {meeting_text[:200]}...")
                
                # Test against sample companies
                sample_companies = list(companies.keys())[:5]
                matches = []
                
                for company_name in sample_companies:
                    company_info = companies[company_name]
                    if company_matcher._match_calendar_meeting(company_name, company_info, meeting_text):
                        matches.append(company_name)
                
                if matches:
                    print(f"  ✅ Matches: {matches}")
                else:
                    print(f"  ❌ No matches")
        else:
            print("Could not authenticate with Google Calendar")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_calendar_matching()
