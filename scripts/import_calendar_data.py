#!/usr/bin/env python3
"""
Import Calendar Data from Justification Files

This script parses the commission analysis justification files to extract
calendar meeting data and loads it into the repsplit.db database.

The justification files contain actual calendar meeting data that was captured
during the commission analysis process, including dates, times, participants,
and meeting details.
"""

import os
import re
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import glob

def parse_justification_file(file_path):
    """Parse a justification file to extract calendar meeting data"""
    meetings = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for the Calendar Meetings section
        calendar_section = re.search(
            r'## Calendar Meetings.*?(?=##|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        
        if not calendar_section:
            return meetings
        
        calendar_content = calendar_section.group(0)
        
        # Extract company name from the file content
        company_match = re.search(r'\*\*Company:\*\*\s*([^\n]+)', content)
        company_name = company_match.group(1).strip() if company_match else "Unknown"
        
        # Look for individual meetings with email domain extraction
        meeting_pattern = r'- \*\*([^*]+)\*\*\s*\n\s*- Date:\s*([^\n]+)\s*\n\s*- Duration:\s*([^\n]+)\s*\n\s*- Team Participants:\s*([^\n]+)'
        meeting_matches = re.findall(meeting_pattern, calendar_content, re.MULTILINE)
        
        # Also look for email addresses in the calendar section to determine company domains
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        email_matches = re.findall(email_pattern, calendar_content)
        
        # Extract company domain from email addresses
        company_domains = set()
        for email in email_matches:
            domain = email.split('@')[1].lower()
            # Filter out internal domains (dlc.link, bitsafe.finance, etc.)
            if domain not in ['dlc.link', 'bitsafe.finance', 'gmail.com', 'outlook.com', 'yahoo.com']:
                company_domains.add(domain)
        
        for match in meeting_matches:
            participants, date_str, duration, team_participants = match
            
            # Clean up the data
            participants = participants.strip()
            date_str = date_str.strip()
            duration = duration.strip()
            team_participants = team_participants.strip()
            
            # Parse the date
            try:
                # Handle different date formats
                if 'T' in date_str:
                    # ISO format: 2025-07-14T16:30:00-04:00
                    parsed_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    meeting_date = parsed_date.strftime('%Y-%m-%d')
                    start_time = parsed_date.strftime('%H:%M:%S')
                    end_time = (parsed_date + timedelta(minutes=25)).strftime('%H:%M:%S')  # Default 25 min
                else:
                    # Fallback format
                    meeting_date = date_str
                    start_time = "00:00:00"
                    end_time = "00:00:00"
            except:
                meeting_date = date_str
                start_time = "00:00:00"
                end_time = "00:00:00"
            
            # Parse duration
            duration_minutes = 25  # Default
            duration_match = re.search(r'(\d+)', duration)
            if duration_match:
                duration_minutes = int(duration_match.group(1))
            
            # Filter out generic industry events that aren't company-specific
            generic_events = [
                'geekstap', 'bitcoin', 'consensus', 'token2049', 'dna house', 
                'crypto', 'defi', 'blockchain', 'web3', 'nft', 'dao',
                'marketing committee', 'networking', 'happy hour', 'cocktail',
                'conference', 'summit', 'workshop', 'meetup', 'event'
            ]
            
            # Check if this is a generic event
            meeting_lower = participants.lower()
            is_generic = any(generic in meeting_lower for generic in generic_events)
            
            # Only include company-specific meetings or meetings with company names
            if not is_generic or company_name.lower() in meeting_lower:
                meeting = {
                    'company_name': company_name,
                    'meeting_title': participants,
                    'start_time': start_time,
                    'end_time': end_time,
                    'participants': team_participants,
                    'duration_minutes': duration_minutes,
                    'meeting_date': meeting_date
                }
                meetings.append(meeting)
            
    except Exception as e:
        print(f"   ⚠️  Error parsing {file_path}: {e}")
    
    return meetings

def load_calendar_data_to_db(meetings):
    """Load calendar meeting data into the database"""
    try:
        conn = sqlite3.connect("repsplit.db")
        cursor = conn.cursor()
        
        # Clear existing calendar data
        cursor.execute("DELETE FROM calendar_meetings")
        print(f"   🗑️  Cleared existing calendar data")
        
        # Insert new calendar data
        for meeting in meetings:
            cursor.execute("""
                INSERT INTO calendar_meetings 
                (company_name, meeting_title, start_time, end_time, participants, duration_minutes, meeting_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                meeting['company_name'],
                meeting['meeting_title'],
                meeting['start_time'],
                meeting['end_time'],
                meeting['participants'],
                meeting['duration_minutes'],
                meeting['meeting_date']
            ))
        
        conn.commit()
        print(f"   💾 Loaded {len(meetings)} calendar meetings into database")
        
        # Verify the data
        cursor.execute("SELECT COUNT(*) FROM calendar_meetings")
        count = cursor.fetchone()[0]
        print(f"   ✅ Database now contains {count} calendar meetings")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return False

def main():
    """Main function to import calendar data"""
    print("🔍 Importing Calendar Data from Justification Files")
    print("=" * 60)
    
    # Find all justification files
    justification_dir = "output/justifications"
    if not os.path.exists(justification_dir):
        print(f"   ❌ Justification directory not found: {justification_dir}")
        return
    
    justification_files = glob.glob(f"{justification_dir}/*.md")
    print(f"   📁 Found {len(justification_files)} justification files")
    
    if not justification_files:
        print("   ⚠️  No justification files found")
        return
    
    # Parse all justification files
    all_meetings = []
    for file_path in justification_files:
        print(f"   📖 Parsing {os.path.basename(file_path)}...")
        meetings = parse_justification_file(file_path)
        all_meetings.extend(meetings)
        if meetings:
            print(f"      Found {len(meetings)} meetings")
    
    print(f"\n📊 Summary:")
    print(f"   Total meetings found: {len(all_meetings)}")
    
    if all_meetings:
        # Group by company
        companies = {}
        for meeting in all_meetings:
            company = meeting['company_name']
            if company not in companies:
                companies[company] = []
            companies[company].append(meeting)
        
        print(f"   Companies with meetings: {len(companies)}")
        for company, company_meetings in companies.items():
            print(f"      {company}: {len(company_meetings)} meetings")
        
        # Load data into database
        print(f"\n💾 Loading data into database...")
        if load_calendar_data_to_db(all_meetings):
            print(f"   ✅ Calendar data import completed successfully!")
        else:
            print(f"   ❌ Calendar data import failed!")
    else:
        print("   ⚠️  No calendar meetings found in justification files")

if __name__ == "__main__":
    main()
