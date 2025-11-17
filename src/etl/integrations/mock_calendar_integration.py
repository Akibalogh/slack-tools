#!/usr/bin/env python3
"""
Mock Google Calendar Integration
Provides sample calendar data for testing when real Google Calendar API is not available
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MockCalendarIntegration:
    """Mock Google Calendar integration for testing"""
    
    def __init__(self):
        self.service = None
        self.creds = None
    
    def authenticate(self) -> bool:
        """Mock authentication - always succeeds"""
        logger.info("Mock Google Calendar authentication successful")
        return True
    
    def get_meetings(self, start_date: datetime, end_date: datetime, 
                    calendar_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Generate mock meetings for testing"""
        meetings = []
        
        # Sample company names from our mapping
        sample_companies = [
            "Allnodes", "BitGo", "Copper", "HexTrust", "ChainSafe", "BitSafe",
            "Custody", "Institutional", "P2P", "Bitcoin", "BTC", "CBTC"
        ]
        
        # Generate meetings for the past 180 days
        current_date = start_date
        while current_date <= end_date:
            # Randomly generate 0-3 meetings per day
            num_meetings = random.randint(0, 3)
            
            for _ in range(num_meetings):
                company = random.choice(sample_companies)
                meeting_time = current_date + timedelta(
                    hours=random.randint(9, 17),
                    minutes=random.choice([0, 15, 30, 45])
                )
                
                meeting = {
                    'id': f"mock_meeting_{random.randint(1000, 9999)}",
                    'summary': f"{company} - {self._generate_meeting_title()}",
                    'description': self._generate_meeting_description(company),
                    'start_time': meeting_time.isoformat(),
                    'end_time': (meeting_time + timedelta(hours=random.randint(1, 3))).isoformat(),
                    'location': random.choice([
                        "Zoom Meeting", "Google Meet", "Microsoft Teams", 
                        "In-person", "Conference Room A", "Virtual"
                    ]),
                    'attendees': self._generate_attendees(company),
                    'meeting_url': f"https://meet.google.com/{random.randint(100000000, 999999999)}",
                    'calendar_id': f"mock_calendar_{random.randint(1, 5)}",
                    'created': (meeting_time - timedelta(days=random.randint(1, 30))).isoformat(),
                    'updated': (meeting_time - timedelta(days=random.randint(1, 7))).isoformat(),
                    'status': random.choice(['confirmed', 'tentative', 'cancelled']),
                    'html_link': f"https://calendar.google.com/event?eid={random.randint(100000000, 999999999)}"
                }
                
                meetings.append(meeting)
            
            current_date += timedelta(days=1)
        
        logger.info(f"Generated {len(meetings)} mock meetings")
        return meetings
    
    def _generate_meeting_title(self) -> str:
        """Generate random meeting titles"""
        titles = [
            "Strategy Discussion", "Technical Review", "Partnership Meeting",
            "Product Demo", "Sales Call", "Implementation Planning",
            "Quarterly Review", "Integration Discussion", "Security Audit",
            "Compliance Check", "Performance Review", "Roadmap Planning"
        ]
        return random.choice(titles)
    
    def _generate_meeting_description(self, company: str) -> str:
        """Generate random meeting descriptions"""
        descriptions = [
            f"Meeting with {company} team to discuss upcoming initiatives",
            f"Technical integration planning session with {company}",
            f"Partnership discussion and next steps with {company}",
            f"Product demonstration for {company} stakeholders",
            f"Sales call to explore opportunities with {company}",
            f"Implementation planning meeting with {company}",
            f"Quarterly business review with {company}",
            f"Security and compliance discussion with {company}",
            f"Performance metrics review with {company}",
            f"Strategic planning session with {company}"
        ]
        return random.choice(descriptions)
    
    def _generate_attendees(self, company: str) -> List[Dict[str, str]]:
        """Generate random attendees"""
        attendees = []
        
        # Always include a company representative
        attendees.append({
            'email': f"contact@{company.lower().replace(' ', '')}.com",
            'name': f"{company} Representative",
            'response_status': 'accepted'
        })
        
        # Add 1-3 internal attendees
        internal_attendees = [
            {'email': 'aki@bitsafe.com', 'name': 'Aki Balogh', 'response_status': 'accepted'},
            {'email': 'sales@bitsafe.com', 'name': 'Sales Team', 'response_status': 'accepted'},
            {'email': 'tech@bitsafe.com', 'name': 'Technical Team', 'response_status': 'tentative'},
            {'email': 'product@bitsafe.com', 'name': 'Product Team', 'response_status': 'accepted'},
            {'email': 'partnerships@bitsafe.com', 'name': 'Partnerships Team', 'response_status': 'accepted'}
        ]
        
        num_internal = random.randint(1, 3)
        selected_internal = random.sample(internal_attendees, num_internal)
        attendees.extend(selected_internal)
        
        return attendees
    
    def get_calendar_list(self) -> List[Dict[str, Any]]:
        """Generate mock calendar list"""
        calendars = [
            {
                'id': 'primary',
                'summary': 'Primary Calendar',
                'description': 'Main work calendar',
                'primary': True,
                'access_role': 'owner',
                'time_zone': 'America/New_York',
                'selected': True
            },
            {
                'id': 'mock_calendar_1',
                'summary': 'Business Meetings',
                'description': 'Client and partner meetings',
                'primary': False,
                'access_role': 'writer',
                'time_zone': 'America/New_York',
                'selected': True
            },
            {
                'id': 'mock_calendar_2',
                'summary': 'Internal Meetings',
                'description': 'Internal team meetings',
                'primary': False,
                'access_role': 'writer',
                'time_zone': 'America/New_York',
                'selected': True
            }
        ]
        
        return calendars
    
    def test_connection(self) -> bool:
        """Test mock connection"""
        logger.info("Testing mock Google Calendar connection...")
        return True


def main():
    """Test the mock calendar integration"""
    logging.basicConfig(level=logging.INFO)
    
    calendar = MockCalendarIntegration()
    
    if calendar.test_connection():
        print("✅ Mock Google Calendar integration working!")
        
        # Test getting recent meetings
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        meetings = calendar.get_meetings(start_date, end_date)
        print(f"📅 Generated {len(meetings)} mock meetings in the last 7 days")
        
        if meetings:
            print("\nSample meetings:")
            for meeting in meetings[:5]:  # Show first 5
                print(f"  - {meeting['summary']} ({meeting['start_time']})")
    else:
        print("❌ Mock Google Calendar integration failed")


if __name__ == '__main__':
    main()


