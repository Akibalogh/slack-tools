#!/usr/bin/env python3
"""
Calendar Commission Analysis
Integrates Google Calendar data with commission analysis to show complete team involvement
"""

import json
import datetime
from google_calendar_integration import GoogleCalendarIntegration

class CalendarCommissionAnalysis:
    """Analyze calendar data for commission analysis"""
    
    def __init__(self):
        self.calendar = GoogleCalendarIntegration()
        self.team_emails = {
            'Aki': 'aki@dlc.link',
            'Addie': 'addie@dlc.link', 
            'Mayank': 'mayank@dlc.link',
            'Amy': 'amy@dlc.link',
            'Kadeem': 'kadeem@dlc.link',
            'Anna': 'anna@dlc.link',
            'Robert': 'robert@dlc.link'
        }
        
    def authenticate(self):
        """Authenticate with Google Calendar"""
        return self.calendar.authenticate()
    
    def get_company_meeting_data(self, company_name: str, days_back: int = 180) -> dict:
        """Get comprehensive meeting data for a company"""
        if not self.calendar.service:
            print("Not authenticated")
            return {}
        
        # Get meetings with company name
        company_meetings = self.calendar.search_meetings_for_company(company_name, days_back)
        
        # Get meetings for each team member
        team_meetings = {}
        for name, email in self.team_emails.items():
            user_meetings = self.calendar.search_meetings_for_user(email, days_back)
            team_meetings[name] = user_meetings
        
        # Analyze overlap - find meetings where both company and team members were present
        overlapping_meetings = []
        for company_meeting in company_meetings:
            meeting_attendees = company_meeting.get('attendees', [])
            
            # Find which team members were in this meeting
            team_participants = []
            for name, email in self.team_emails.items():
                if email in meeting_attendees:
                    team_participants.append(name)
            
            if team_participants:
                overlapping_meetings.append({
                    'meeting': company_meeting,
                    'team_participants': team_participants
                })
        
        return {
            'company_name': company_name,
            'company_meetings': company_meetings,
            'team_meetings': team_meetings,
            'overlapping_meetings': overlapping_meetings,
            'total_company_meeting_time': sum(m['duration_minutes'] for m in company_meetings),
            'team_participation': self._calculate_team_participation(overlapping_meetings)
        }
    
    def _calculate_team_participation(self, overlapping_meetings: list) -> dict:
        """Calculate team participation percentages based on meeting time"""
        team_time = {name: 0 for name in self.team_emails.keys()}
        total_time = 0
        
        for overlap in overlapping_meetings:
            meeting = overlap['meeting']
            participants = overlap['team_participants']
            duration = meeting['duration_minutes']
            
            # Split meeting time among participants
            time_per_participant = duration / len(participants)
            for participant in participants:
                team_time[participant] += time_per_participant
            total_time += duration
        
        # Calculate percentages
        if total_time > 0:
            team_percentages = {
                name: (time / total_time) * 100 
                for name, time in team_time.items()
                if time > 0
            }
        else:
            team_percentages = {}
        
        return {
            'total_time_minutes': total_time,
            'team_time_minutes': team_time,
            'team_percentages': team_percentages
        }
    
    def analyze_launchnodes_deal(self) -> dict:
        """Specific analysis for Launchnodes deal"""
        print("🔍 Analyzing Launchnodes deal with calendar data...")
        
        # Get calendar data for Launchnodes
        calendar_data = self.get_company_meeting_data("Launchnodes", days_back=180)
        
        # Get Slack data for comparison
        from commission_analysis import CommissionAnalyzer
        slack_analyzer = CommissionAnalyzer()
        slack_data = slack_analyzer.get_slack_activity("launchnodes")
        
        print(f"\n📅 Calendar Analysis:")
        print(f"  Company meetings found: {len(calendar_data['company_meetings'])}")
        print(f"  Total meeting time: {calendar_data['total_company_meeting_time']} minutes")
        
        if calendar_data['overlapping_meetings']:
            print(f"  Team participation meetings: {len(calendar_data['overlapping_meetings'])}")
            print(f"  Team participation time: {calendar_data['team_participation']['total_time_minutes']} minutes")
            
            print(f"\n👥 Team Participation (Calendar):")
            for name, percentage in calendar_data['team_participation']['team_percentages'].items():
                minutes = calendar_data['team_participation']['team_time_minutes'][name]
                print(f"  {name}: {percentage:.1f}% ({minutes:.0f} min)")
        
        print(f"\n💬 Slack Analysis:")
        if slack_data['total_messages'] > 0:
            print(f"  Total messages: {slack_data['total_messages']}")
            for user, count in slack_data['user_breakdown'].items():
                percentage = (count / slack_data['total_messages']) * 100
                print(f"  {user}: {percentage:.1f}% ({count} messages)")
        
        # Compare calendar vs Slack
        print(f"\n🔍 Comparison Analysis:")
        self._compare_calendar_vs_slack(calendar_data, slack_data)
        
        return calendar_data
    
    def _compare_calendar_vs_slack(self, calendar_data: dict, slack_data: dict):
        """Compare calendar participation vs Slack activity"""
        calendar_participants = set(calendar_data['team_participation']['team_percentages'].keys())
        slack_participants = set(slack_data['user_breakdown'].keys())
        
        print(f"  Calendar participants: {', '.join(calendar_participants) if calendar_participants else 'None'}")
        print(f"  Slack participants: {', '.join(slack_participants) if slack_participants else 'None'}")
        
        # Find discrepancies
        calendar_only = calendar_participants - slack_participants
        slack_only = slack_participants - calendar_participants
        
        if calendar_only:
            print(f"  ⚠️  Only in calendar: {', '.join(calendar_only)}")
        if slack_only:
            print(f"  ⚠️  Only in Slack: {', '.join(slack_only)}")
        
        # Calculate total involvement
        total_calendar_time = calendar_data['team_participation']['total_time_minutes']
        total_slack_messages = slack_data['total_messages']
        
        print(f"\n📊 Total Involvement:")
        print(f"  Calendar: {total_calendar_time} minutes")
        print(f"  Slack: {total_slack_messages} messages")
        
        if total_calendar_time > 0 and total_slack_messages > 0:
            print(f"  📈 Calendar/Slack ratio: {total_calendar_time/total_slack_messages:.1f} min per message")
    
    def get_commission_recommendation(self, company_name: str) -> dict:
        """Get commission recommendation based on calendar + Slack data"""
        calendar_data = self.get_company_meeting_data(company_name, days_back=180)
        
        # Get Slack data
        from commission_analysis import CommissionAnalyzer
        slack_analyzer = CommissionAnalyzer()
        slack_data = slack_analyzer.get_slack_activity(company_name.lower().replace(' ', '-'))
        
        # Combine calendar and Slack data
        combined_analysis = self._combine_calendar_and_slack(calendar_data, slack_data)
        
        return combined_analysis
    
    def _combine_calendar_and_slack(self, calendar_data: dict, slack_data: dict) -> dict:
        """Combine calendar and Slack data for comprehensive analysis"""
        # Weight factors (adjustable)
        CALENDAR_WEIGHT = 0.7  # Calendar meetings are more valuable
        SLACK_WEIGHT = 0.3     # Slack activity is supporting evidence
        
        team_scores = {}
        
        # Calendar scores
        for name, percentage in calendar_data['team_participation']['team_percentages'].items():
            team_scores[name] = percentage * CALENDAR_WEIGHT
        
        # Slack scores
        if slack_data['total_messages'] > 0:
            for user, count in slack_data['user_breakdown'].items():
                slack_percentage = (count / slack_data['total_messages']) * 100
                if user in team_scores:
                    team_scores[user] += slack_percentage * SLACK_WEIGHT
                else:
                    team_scores[user] = slack_percentage * SLACK_WEIGHT
        
        # Normalize to 100%
        total_score = sum(team_scores.values())
        if total_score > 0:
            normalized_scores = {
                name: (score / total_score) * 100 
                for name, score in team_scores.items()
            }
        else:
            normalized_scores = {}
        
        return {
            'calendar_data': calendar_data,
            'slack_data': slack_data,
            'combined_scores': team_scores,
            'final_percentages': normalized_scores,
            'recommendation': self._generate_recommendation(normalized_scores)
        }
    
    def _generate_recommendation(self, percentages: dict) -> str:
        """Generate commission recommendation based on percentages"""
        if not percentages:
            return "No participation data available"
        
        # Find primary participant
        primary_participant = max(percentages.items(), key=lambda x: x[1])
        primary_name, primary_percentage = primary_participant
        
        if primary_percentage >= 80:
            return f"100% to {primary_name} (dominates with {primary_percentage:.1f}% involvement)"
        elif primary_percentage >= 60:
            return f"Primary: {primary_name} ({primary_percentage:.1f}%), others split remaining"
        else:
            return f"Contested deal - {primary_name} leads with {primary_percentage:.1f}%"

def main():
    """Main function to test calendar commission analysis"""
    analyzer = CalendarCommissionAnalysis()
    
    if not analyzer.authenticate():
        print("Failed to authenticate with Google Calendar")
        return
    
    print("✅ Successfully authenticated with Google Calendar")
    
    # Analyze Launchnodes deal
    print("\n" + "="*60)
    launchnodes_analysis = analyzer.analyze_launchnodes_deal()
    
    # Get commission recommendation
    print("\n" + "="*60)
    print("💰 COMMISSION RECOMMENDATION:")
    recommendation = analyzer.get_commission_recommendation("Launchnodes")
    
    print(f"\nFinal Commission Split:")
    for name, percentage in recommendation['final_percentages'].items():
        print(f"  {name}: {percentage:.1f}%")
    
    print(f"\nRecommendation: {recommendation['recommendation']}")
    
    # Save detailed analysis
    with open('launchnodes_calendar_analysis.json', 'w') as f:
        json.dump(recommendation, f, indent=2, default=str)
    
    print(f"\n💾 Detailed analysis saved to 'launchnodes_calendar_analysis.json'")

if __name__ == '__main__':
    main()
