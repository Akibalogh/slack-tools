#!/usr/bin/env python3
"""
Find potential calendar matches that are being missed
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from etl.utils.company_matcher import CompanyMatcher
from etl.etl_data_ingestion import DataETL

def find_potential_matches():
    """Find meetings that might match companies but aren't being matched"""
    
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
            
            # Get all company names and their variants
            company_matcher = CompanyMatcher()
            all_company_terms = set()
            
            for company_name, company_info in companies.items():
                # Add company name variants
                variants = company_matcher.generate_name_variants(company_name)
                all_company_terms.update(variants)
                
                # Add base company variants
                if company_info.get('base_company'):
                    base_variants = company_matcher.generate_name_variants(company_info['base_company'])
                    all_company_terms.update(base_variants)
                
                # Add calendar domain variants
                if company_info.get('calendar_domain'):
                    domain_variants = company_matcher.generate_name_variants(company_info['calendar_domain'])
                    all_company_terms.update(domain_variants)
            
            print(f"Generated {len(all_company_terms)} company terms to search for")
            
            # Search for meetings that contain company terms
            potential_matches = []
            
            for meeting in meetings[:100]:  # Check first 100 meetings
                summary = meeting.get('summary', '')
                description = meeting.get('description', '')
                attendees = meeting.get('attendees', [])
                
                # Extract attendee emails
                attendee_emails = []
                for attendee in attendees:
                    if isinstance(attendee, dict) and 'email' in attendee:
                        attendee_emails.append(attendee['email'])
                
                meeting_text = f"{summary} {description} {' '.join(attendee_emails)}".lower()
                
                # Check if any company terms appear in the meeting text
                found_terms = []
                for term in all_company_terms:
                    if term.lower() in meeting_text:
                        found_terms.append(term)
                
                if found_terms:
                    potential_matches.append({
                        'meeting': meeting,
                        'found_terms': found_terms,
                        'meeting_text': meeting_text[:200]
                    })
            
            print(f"\\nFound {len(potential_matches)} meetings with potential company terms:")
            
            for i, match in enumerate(potential_matches[:20]):  # Show first 20
                meeting = match['meeting']
                print(f"\\n{i+1}. {meeting.get('summary', '')}")
                print(f"   Found terms: {match['found_terms']}")
                print(f"   Text: {match['meeting_text']}...")
                
        else:
            print("Could not authenticate with Google Calendar")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    find_potential_matches()
