#!/usr/bin/env python3
"""
RepSplit - Sales Commission Calculator for Slack Deal Channels

Analyzes private Slack channels ending with '-bitsafe' to calculate commission splits
based on deal stage participation for Aki, Addie, Amy, Mayank, Prateek, Will, and Kadeem.
"""

import os
import json
import csv
import re
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('repsplit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class StageConfig:
    """Configuration for deal stages and their commission weights"""
    name: str
    weight: float
    keywords: List[str]
    regex_patterns: List[str]

@dataclass
class Participant:
    """Sales team participant configuration"""
    name: str
    slack_id: str
    display_name: str
    email: str
    founder_cap: bool = False
    closer_bonus: bool = False

def round_to_nearest_25(percentage: float) -> float:
    """Round a percentage to the nearest 25% (25, 50, 75, or 100)"""
    if percentage <= 0:
        return 0.0
    elif percentage <= 12.5:
        return 0.0
    elif percentage <= 37.5:
        return 25.0
    elif percentage <= 62.5:
        return 50.0
    elif percentage <= 87.5:
        return 75.0
    else:
        return 100.0

class RepSplit:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.db_path = "repsplit.db"
        self.output_dir = Path("output")
        self.justifications_dir = self.output_dir / "justifications"
        
        # Create output directories
        self.output_dir.mkdir(exist_ok=True)
        self.justifications_dir.mkdir(exist_ok=True)
        
        # Initialize database
        self.init_database()
        
    def load_config(self) -> Dict:
        """Load configuration from JSON file"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            # Default configuration with all 7 sales reps
            default_config = {
                "slack_token": "",
                "stages": [
                    {
                        "name": "sourcing_intro",
                        "weight": 8.0,
                        "keywords": ["intro", "connect", "loop in", "reached out", "waitlist", "referral"]
                    },
                    {
                        "name": "discovery_qual",
                        "weight": 12.0,
                        "keywords": ["questions", "requirements", "use case", "needs", "challenge", "timeline"]
                    },
                    {
                        "name": "solution_presentation",
                        "weight": 32.0,
                        "keywords": ["credential", "rewards", "CC", "CBTC", "overview", "explain", "how it works"]
                    },
                    {
                        "name": "technical_discussion",
                        "weight": 5.0,
                        "keywords": ["API", "integration", "technical", "architecture", "implementation", "script"]
                    },
                    {
                        "name": "pricing_terms",
                        "weight": 8.0,
                        "keywords": ["$6000", "cost", "payment", "billing", "subscription", "pricing"]
                    },
                    {
                        "name": "contract_legal",
                        "weight": 15.0,
                        "keywords": ["MSA", "contract", "agreement", "terms", "legal", "docusign", "dropbox sign"]
                    },
                    {
                        "name": "scheduling_coordination",
                        "weight": 8.0,
                        "keywords": ["Calendly", "schedule", "meeting", "call", "demo", "follow up"]
                    },
                    {
                        "name": "closing_onboarding",
                        "weight": 12.0,
                        "keywords": ["signed", "accept", "onboard", "credential issued", "go live", "activate"]
                    }
                ],
                "participants": [
                    {"name": "Aki", "slack_id": "", "display_name": "", "email": "", "founder_cap": True, "earns_commission": True},
                    {"name": "Addie", "slack_id": "", "display_name": "", "email": "", "founder_cap": False, "earns_commission": True},
                    {"name": "Amy", "slack_id": "", "display_name": "", "email": "", "founder_cap": False, "earns_commission": True},
                    {"name": "Mayank", "slack_id": "", "display_name": "", "email": "", "founder_cap": False, "earns_commission": True},
                    {"name": "Prateek", "slack_id": "", "display_name": "", "email": "", "founder_cap": False, "earns_commission": False},
                    {"name": "Will", "slack_id": "", "display_name": "", "email": "", "founder_cap": False, "earns_commission": False},
                    {"name": "Kadeem", "slack_id": "", "display_name": "", "email": "", "founder_cap": False, "earns_commission": False}
                ],
                "diminishing_returns": 0.8,
                "presence_floor": 5.0,
                "closer_bonus": 2.0
            }
            
            # Save default config
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            logger.info(f"Created default config file: {self.config_file}")
            logger.info("Please update the config file with your Slack token and participant information")
            return default_config
    
    def init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                conv_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                member_count INTEGER,
                creation_date INTEGER,
                is_bitsafe BOOLEAN DEFAULT FALSE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                display_name TEXT,
                real_name TEXT,
                email TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conv_id TEXT,
                timestamp REAL,
                author TEXT,
                text TEXT,
                stage_hits TEXT,
                FOREIGN KEY (conv_id) REFERENCES conversations (conv_id),
                FOREIGN KEY (author) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stage_detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conv_id TEXT,
                stage_name TEXT,
                message_id TEXT,
                author TEXT,
                timestamp REAL,
                confidence REAL,
                FOREIGN KEY (conv_id) REFERENCES conversations (conv_id),
                FOREIGN KEY (message_id) REFERENCES messages (id),
                FOREIGN KEY (author) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def detect_stages_in_message(self, text: str) -> List[Tuple[str, float]]:
        """Detect deal stages in a message based on keyword patterns"""
        detected_stages = []
        text_lower = text.lower()
        
        for stage_config in self.config["stages"]:
            stage_name = stage_config["name"]
            keywords = stage_config["keywords"]
            
            matches = 0
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    matches += 1
            
            if matches > 0:
                # Calculate confidence based on number of keyword matches
                # Higher base confidence for multiple matches
                confidence = min(1.0, 0.3 + (matches * 0.4))
                detected_stages.append((stage_name, confidence))
        
        return detected_stages
    
    def _increment_stage_contribution(self, participant_stats: Dict, stage: str):
        """Increment stage contribution count for a participant"""
        if stage not in participant_stats["stage_contributions"]:
            participant_stats["stage_contributions"][stage] = 0
        participant_stats["stage_contributions"][stage] += 1
    
    def calculate_commission_splits(self, conv_id: str) -> Dict[str, float]:
        """Calculate commission splits for a specific conversation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get internal team Slack IDs for filtering
        internal_slack_ids = {p['slack_id'] for p in self.config['participants'] if p['slack_id']}
        
        # Get stage detections for internal team members only
        if internal_slack_ids:
            placeholders = ','.join(['?' for _ in internal_slack_ids])
            cursor.execute(f'''
                SELECT stage_name, author, confidence, timestamp
                FROM stage_detections 
                WHERE conv_id = ? AND author IN ({placeholders})
                ORDER BY timestamp
            ''', [conv_id] + list(internal_slack_ids))
        else:
            cursor.execute('''
                SELECT stage_name, author, confidence, timestamp
                FROM stage_detections 
                WHERE conv_id = ?
                ORDER BY timestamp
            ''', [conv_id])
        
        stage_detections = cursor.fetchall()
        
        # Get messages for internal team members only
        if internal_slack_ids:
            placeholders = ','.join(['?' for _ in internal_slack_ids])
            cursor.execute(f'''
                SELECT author, timestamp
                FROM messages 
                WHERE conv_id = ? AND author IN ({placeholders})
                ORDER BY timestamp
            ''', [conv_id] + list(internal_slack_ids))
        else:
            cursor.execute('''
                SELECT author, timestamp
                FROM messages 
                WHERE conv_id = ?
                ORDER BY timestamp
            ''', [conv_id] + list(internal_slack_ids))
        
        messages = cursor.fetchall()
        
        # Get conversation name for calendar lookup
        cursor.execute('SELECT name FROM conversations WHERE conv_id = ?', (conv_id,))
        conv_data = cursor.fetchone()
        conv_name = conv_data[0] if conv_data else "unknown"
        conn.close()
        
        if not stage_detections and not messages:
            return {}
        
        # Calculate participant contributions
        participant_stats = {}
        
        # Process stage detections
        for stage_name, author, confidence, timestamp in stage_detections:
            if author not in participant_stats:
                participant_stats[author] = {
                    "total_confidence": 0,
                    "stage_contributions": {},
                    "message_count": 0,
                    "first_message": timestamp,
                    "last_message": timestamp,
                    "calendar_meetings": 0
                }
            
            # Add stage contribution
            if stage_name not in participant_stats[author]["stage_contributions"]:
                participant_stats[author]["stage_contributions"][stage_name] = 0
            participant_stats[author]["stage_contributions"][stage_name] += confidence
            
            # Update total confidence
            participant_stats[author]["total_confidence"] += confidence
            
            # Update timestamp range
            participant_stats[author]["first_message"] = min(participant_stats[author]["first_message"], timestamp)
            participant_stats[author]["last_message"] = max(participant_stats[author]["last_message"], timestamp)
        
        # Process message counts
        for author, timestamp in messages:
            if author not in participant_stats:
                participant_stats[author] = {
                    "total_confidence": 0,
                    "stage_contributions": {},
                    "message_count": 0,
                    "first_message": timestamp,
                    "last_message": timestamp,
                    "calendar_meetings": 0
                }
            
            participant_stats[author]["message_count"] += 1
            participant_stats[author]["first_message"] = min(participant_stats[author]["first_message"], timestamp)
            participant_stats[author]["last_message"] = max(participant_stats[author]["last_message"], timestamp)
        
        # Add calendar meeting contributions for in-person interactions
        self._add_calendar_contributions(conv_name, participant_stats)
        
        # Calculate commission splits
        commission_splits = {}
        total_contribution = 0
        
        for participant_id, stats in participant_stats.items():
            # Base contribution from stage activity
            stage_contribution = stats["total_confidence"]
            
            # Add message count contribution (weighted less than stage activity)
            message_contribution = stats["message_count"] * 0.1
            
            # Add calendar meeting contribution (weighted higher for in-person interactions)
            calendar_contribution = stats["calendar_meetings"] * 2.0  # 2x weight for in-person meetings
            
            # Add time-based contribution (earlier involvement gets bonus)
            time_bonus = 0
            if stats["first_message"] < stats["last_message"]:
                # Bonus for early involvement
                time_bonus = 0.2
            
            # Total contribution for this participant
            contribution = stage_contribution + message_contribution + calendar_contribution + time_bonus
            
            commission_splits[participant_id] = contribution
            total_contribution += contribution
        
        # Apply stage weights
        weighted_commissions = {p: 0.0 for p in commission_splits.keys()}
        
        for participant_id, stats in participant_stats.items():
            for stage_name, stage_confidence in stats["stage_contributions"].items():
                # Find stage config and weight
                stage_config = next((s for s in self.config["stages"] if s["name"] == stage_name), None)
                if stage_config:
                    stage_weight = stage_config["weight"]
                    weighted_commissions[participant_id] += stage_confidence * stage_weight
        
        # No founder cap - Aki can earn full commission based on actual contribution
        
        # Apply presence floor
        for participant in weighted_commissions:
            if weighted_commissions[participant] < self.config["presence_floor"]:
                weighted_commissions[participant] = self.config["presence_floor"]
        
        # Normalize to 100%
        total = sum(weighted_commissions.values())
        if total > 0:
            normalized_commissions = {p: (v / total) * 100 for p, v in weighted_commissions.items()}
        else:
            # Equal split if no contributions
            normalized_commissions = {p: 100.0 / len(weighted_commissions) for p in weighted_commissions}
        
        # Round to nearest 25% and normalize to ensure sum = 100%
        rounded_commissions = {p: round_to_nearest_25(v) for p, v in normalized_commissions.items()}
        
        # Ensure participants with real contributions don't get rounded down to 0%
        for participant_id, original_pct in normalized_commissions.items():
            if original_pct > 5.0 and rounded_commissions[participant_id] == 0.0:
                # If they had >5% but got rounded to 0%, give them at least 25%
                rounded_commissions[participant_id] = 25.0
        
        # Check if rounding caused total to exceed 100%
        total_rounded = sum(rounded_commissions.values())
        if total_rounded > 100:
            # Find the participant with the highest commission and reduce by 25%
            # This preserves the 25% increments while ensuring sum <= 100%
            max_participant = max(rounded_commissions.keys(), key=lambda k: rounded_commissions[k])
            if rounded_commissions[max_participant] >= 25:
                rounded_commissions[max_participant] -= 25
                # If still over 100%, repeat the process
                while sum(rounded_commissions.values()) > 100:
                    max_participant = max(rounded_commissions.keys(), key=lambda k: rounded_commissions[k])
                    if rounded_commissions[max_participant] >= 25:
                        rounded_commissions[max_participant] -= 25
                    else:
                        break
        
        return rounded_commissions
    
    def _add_calendar_contributions(self, conv_name: str, participant_stats: dict):
        """Add calendar meeting contributions for in-person interactions"""
        try:
            from calendar_commission_analysis import CalendarCommissionAnalysis
            
            # Initialize calendar analysis
            calendar_analysis = CalendarCommissionAnalysis()
            if not calendar_analysis.authenticate():
                logger.warning("Could not authenticate with Google Calendar - skipping calendar contributions")
                return
            
            # Extract company name from conversation name (remove '-bitsafe' suffix)
            company_name = conv_name.replace('-bitsafe', '').replace('_', ' ').title()
            
            # Get meeting data for this company
            meeting_data = calendar_analysis.get_company_meeting_data(company_name, days_back=180)
            
            if not meeting_data or not meeting_data.get('overlapping_meetings'):
                return
            
            # Map team member names to participant IDs
            name_to_id = {}
            for participant in self.config['participants']:
                if participant['display_name']:
                    name_to_id[participant['display_name']] = participant['slack_id']
            
            # Add calendar contributions
            for overlap in meeting_data['overlapping_meetings']:
                meeting = overlap['meeting']
                team_participants = overlap['team_participants']
                
                # Find the participant ID for each team member
                for team_member in team_participants:
                    if team_member in name_to_id:
                        participant_id = name_to_id[team_member]
                        if participant_id in participant_stats:
                            # Add meeting contribution (weighted by duration)
                            duration_hours = meeting.get('duration_minutes', 60) / 60.0
                            participant_stats[participant_id]["calendar_meetings"] += duration_hours
                            
                            logger.info(f"Added {duration_hours:.1f}h calendar contribution for {team_member} in {company_name}")
            
        except ImportError:
            logger.warning("Calendar integration not available - skipping calendar contributions")
        except Exception as e:
            logger.error(f"Error adding calendar contributions: {e}")
    
    def get_calendar_summary(self, deal_id: str) -> str:
        """Get summary of calendar meetings for a deal"""
        try:
            from calendar_commission_analysis import CalendarCommissionAnalysis
            
            calendar_analysis = CalendarCommissionAnalysis()
            if not calendar_analysis.authenticate():
                return "Calendar not accessible"
            
            company_name = deal_id.replace('-bitsafe', '').replace('_', ' ').title()
            meeting_data = calendar_analysis.get_company_meeting_data(company_name, days_back=180)
            
            if not meeting_data or not meeting_data.get('overlapping_meetings'):
                return "No meetings found"
            
            # Summarize meetings
            meeting_summary = []
            for overlap in meeting_data['overlapping_meetings']:
                meeting = overlap['meeting']
                team_participants = overlap['team_participants']
                duration = meeting.get('duration_minutes', 60)
                
                meeting_summary.append(f"{', '.join(team_participants)} ({duration}m)")
            
            return "; ".join(meeting_summary)
            
        except Exception as e:
            return f"Calendar error: {str(e)}"
    
    def generate_justification(self, conv_id: str, conv_name: str):
        """Generate detailed justification for commission splits"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get conversation details
        cursor.execute('SELECT * FROM conversations WHERE conv_id = ?', (conv_id,))
        conv_data = cursor.fetchone()
        
        # Get all stage detections
        cursor.execute('''
            SELECT sd.stage_name, sd.author, sd.timestamp, sd.confidence,
                   u.display_name, m.text
            FROM stage_detections sd
            JOIN users u ON sd.author = u.id
            JOIN messages m ON sd.message_id = m.id
            WHERE sd.conv_id = ?
            ORDER BY sd.timestamp
        ''', (conv_id,))
        
        stage_detections = cursor.fetchall()
        
        # Get commission splits
        commissions = self.calculate_commission_splits(conv_id)
        
        # Round percentages to nearest 25%
        rounded_commissions = {p: round_to_nearest_25(v) for p, v in commissions.items()}
        
        # Generate markdown file
        justification_file = self.justifications_dir / f"{conv_name}_justification.md"
        
        with open(justification_file, 'w') as f:
            f.write(f"# Commission Split Justification: {conv_name}\n\n")
            f.write(f"**Channel ID:** {conv_id}\n")
            f.write(f"**Created:** {datetime.fromtimestamp(conv_data[3]).strftime('%Y-%m-%d %H:%M:%S') if conv_data[3] else 'Unknown'}\n")
            f.write(f"**Members:** {conv_data[2]}\n\n")
            
            f.write("## Commission Splits\n\n")
            for participant_id, percentage in rounded_commissions.items():
                cursor.execute('SELECT display_name FROM users WHERE id = ?', (participant_id,))
                display_name = cursor.fetchone()
                name = display_name[0] if display_name else participant_id
                f.write(f"- **{name}:** {percentage:.1f}%\n")
            
            # Add calendar meeting information
            f.write("\n## Calendar Meetings (In-Person Interactions)\n\n")
            try:
                from calendar_commission_analysis import CalendarCommissionAnalysis
                
                calendar_analysis = CalendarCommissionAnalysis()
                if calendar_analysis.authenticate():
                    company_name = conv_name.replace('-bitsafe', '').replace('_', ' ').title()
                    meeting_data = calendar_analysis.get_company_meeting_data(company_name, days_back=180)
                    
                    if meeting_data and meeting_data.get('overlapping_meetings'):
                        f.write(f"**Company:** {company_name}\n\n")
                        f.write("**Meetings Found:**\n\n")
                        
                        for overlap in meeting_data['overlapping_meetings']:
                            meeting = overlap['meeting']
                            team_participants = overlap['team_participants']
                            
                            f.write(f"- **{meeting.get('summary', 'No Title')}**\n")
                            f.write(f"  - Date: {meeting.get('start_time', 'Unknown')}\n")
                            f.write(f"  - Duration: {meeting.get('duration_minutes', 0)} minutes\n")
                            f.write(f"  - Team Participants: {', '.join(team_participants)}\n")
                            f.write(f"  - Description: {meeting.get('description', 'No description')[:200]}...\n\n")
                    else:
                        f.write("No in-person meetings found in calendar data.\n\n")
                else:
                    f.write("Could not authenticate with Google Calendar.\n\n")
            except Exception as e:
                f.write(f"Calendar integration error: {str(e)}\n\n")
            
            f.write("## Stage Analysis\n\n")
            
            current_stage = None
            for stage_name, author_id, timestamp, confidence, display_name, message_text in stage_detections:
                if stage_name != current_stage:
                    current_stage = stage_name
                    f.write(f"### {stage_name.replace('_', ' ').title()}\n\n")
                
                timestamp_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"- **{timestamp_str}** - {display_name} (confidence: {confidence:.2f})\n")
                f.write(f"  > {message_text[:200]}{'...' if len(message_text) > 200 else ''}\n\n")
        
        conn.close()
        logger.info(f"Generated justification for {conv_name}")
    
    def run_analysis(self):
        """Run the complete commission analysis"""
        logger.info("Starting RepSplit commission analysis...")
        
        # Get all bitsafe conversations
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT conv_id, name FROM conversations 
            WHERE is_bitsafe = TRUE
        ''')
        
        bitsafe_channels = cursor.fetchall()
        conn.close()
        
        if not bitsafe_channels:
            logger.warning("No bitsafe channels found. Please run the Slack ingestion first.")
            return
        
        logger.info(f"Found {len(bitsafe_channels)} bitsafe channels to analyze")
        
        # Calculate commission splits for each channel
        all_splits = []
        person_totals = {"Aki": 0.0, "Addie": 0.0, "Amy": 0.0, "Mayank": 0.0, "Prateek": 0.0, "Will": 0.0, "Kadeem": 0.0}
        
        for conv_id, conv_name in bitsafe_channels:
            logger.info(f"Analyzing {conv_name}...")
            
            # Calculate splits
            commissions = self.calculate_commission_splits(conv_id)
            
            # Round percentages to nearest 25%
            rounded_commissions = {p: round_to_nearest_25(v) for p, v in commissions.items()}
            
            # Map to participant names
            participant_names = {}
            for participant_id, percentage in rounded_commissions.items():
                # participant_id is already the Slack ID (e.g., U092B2GUASF)
                # Try to match with configured participants using Slack ID first, then display name
                matched = False
                for p in self.config["participants"]:
                    # First try Slack ID match (most reliable)
                    if p["slack_id"] and p["slack_id"] == participant_id:
                        participant_names[participant_id] = p["name"]
                        matched = True
                        break
                
                if not matched:
                    # Fallback: get display name from database using Slack ID
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute('SELECT display_name FROM users WHERE id = ?', (participant_id,))
                    display_name = cursor.fetchone()
                    conn.close()
                    
                    if display_name and display_name[0]:
                        participant_names[participant_id] = display_name[0]
                    else:
                        participant_names[participant_id] = participant_id
            
            # Record splits
            split_record = {
                "deal_id": conv_name,
                "Aki": 0.0,
                "Addie": 0.0,
                "Amy": 0.0,
                "Mayank": 0.0,
                "Prateek": 0.0,
                "Will": 0.0,
                "Kadeem": 0.0
            }
            
            for participant_id, percentage in rounded_commissions.items():
                participant_name = participant_names[participant_id]
                if participant_name in split_record:
                    split_record[participant_name] = percentage
                    person_totals[participant_name] += percentage
            
            all_splits.append(split_record)
            
            # Generate justification
            self.generate_justification(conv_id, conv_name)
        
        # Generate output files
        self.generate_output_files(all_splits, person_totals)
        
        logger.info("Analysis complete!")
    
    def generate_rationale_csv(self, all_splits: List[Dict]):
        """Generate rationale CSV with contestation level and reasoning"""
        
        rationale_data = []
        
        for split in all_splits:
            deal_id = split["deal_id"]
            
            # Get commission percentages
            aki_pct = split.get("Aki", 0.0)
            addie_pct = split.get("Addie", 0.0)
            mayank_pct = split.get("Mayank", 0.0)
            amy_pct = split.get("Amy", 0.0)
            
            # Determine contestation level - more aggressive logic
            max_pct = max(aki_pct, addie_pct, mayank_pct, amy_pct)
            total_participants = sum(1 for p in [aki_pct, addie_pct, mayank_pct, amy_pct] if p > 0)
            
            # More aggressive contestation logic
            if max_pct >= 60.0:
                contestation_level = "CLEAR OWNERSHIP"
            elif max_pct >= 40.0 and total_participants <= 2:
                contestation_level = "CLEAR OWNERSHIP"
            elif total_participants >= 3 or (max_pct < 40.0 and total_participants >= 2):
                contestation_level = "HIGH CONTESTATION"
            else:
                contestation_level = "MODERATE CONTESTATION"
            
            # Determine most likely owner - more nuanced logic
            if max_pct >= 40.0:
                # Find the person with the highest percentage
                if aki_pct == max_pct:
                    most_likely_owner = "Aki"
                elif addie_pct == max_pct:
                    most_likely_owner = "Addie"
                elif mayank_pct == max_pct:
                    most_likely_owner = "Mayank"
                elif amy_pct == max_pct:
                    most_likely_owner = "Amy"
                else:
                    most_likely_owner = "Split"
            else:
                most_likely_owner = "Split"
            
            # Get stage-by-stage breakdown
            stage_breakdown = self.get_stage_breakdown(deal_id)
            
            # Get calendar meeting information
            calendar_info = self.get_calendar_summary(deal_id)
            
            # Generate short rationale
            rationale = self.generate_short_rationale(deal_id, split)
            
            rationale_data.append({
                "Company": deal_id,
                "Aki %": f"{aki_pct:.0f}%",
                "Addie %": f"{addie_pct:.0f}%",
                "Mayank %": f"{mayank_pct:.0f}%",
                "Amy %": f"{amy_pct:.0f}%",
                "Contestation Level": contestation_level,
                "Most Likely Owner": most_likely_owner,
                "Calendar Meetings": calendar_info,
                "Sourcing/Intro": stage_breakdown.get("sourcing_intro", "None"),
                "Discovery/Qual": stage_breakdown.get("discovery_qual", "None"),
                "Solution": stage_breakdown.get("solution_presentation", "None"),
                "Objection": stage_breakdown.get("objection_handling", "None"),
                "Technical": stage_breakdown.get("technical_discussion", "None"),
                "Pricing": stage_breakdown.get("pricing_terms", "None"),
                "Contract": stage_breakdown.get("contract_legal", "None"),
                "Scheduling": stage_breakdown.get("scheduling_coordination", "None"),
                "Closing": stage_breakdown.get("closing_onboarding", "None"),
                "Rationale": rationale
            })
        
        # Write rationale CSV
        with open(self.output_dir / "deal_rationale.csv", 'w', newline='') as f:
            fieldnames = ["Company", "Aki %", "Addie %", "Mayank %", "Amy %", "Contestation Level", "Most Likely Owner", 
                         "Calendar Meetings", "Sourcing/Intro", "Discovery/Qual", "Solution", "Objection", "Technical", "Pricing", "Contract", "Scheduling", "Closing", "Rationale"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rationale_data:
                writer.writerow(row)
        
        logger.info("Generated deal_rationale.csv with contestation levels, stage breakdown, calendar meetings, and rationale")
    
    def get_stage_breakdown(self, deal_id: str) -> Dict[str, str]:
        """Get stage-by-stage breakdown showing who handled each stage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get stage detections for internal team members only
        internal_slack_ids = {p["slack_id"] for p in self.config["participants"] if p["slack_id"]}
        
        cursor.execute('''
            SELECT stage_name, author, confidence
            FROM stage_detections 
            WHERE conv_id = (SELECT conv_id FROM conversations WHERE name = ?) 
            AND author IN ({})
            ORDER BY timestamp
        '''.format(','.join(['?' for _ in internal_slack_ids])), [deal_id] + list(internal_slack_ids))
        
        stage_data = cursor.fetchall()
        conn.close()
        
        # Group by stage and find primary participant
        stage_contributions = {}
        for stage_name, author, confidence in stage_data:
            if stage_name not in stage_contributions:
                stage_contributions[stage_name] = {}
            
            if author not in stage_contributions[stage_name]:
                stage_contributions[stage_name][author] = 0
            
            stage_contributions[stage_name][author] += confidence
        
        # Map stage names to display names
        stage_display_names = {
            "sourcing_intro": "Sourcing/Intro",
            "discovery_qual": "Discovery/Qual", 
            "solution_presentation": "Solution",
            "objection_handling": "Objection",
            "technical_discussion": "Technical",
            "pricing_terms": "Pricing",
            "contract_legal": "Contract",
            "scheduling_coordination": "Scheduling",
            "closing_onboarding": "Closing"
        }
        
        # Get participant names for each stage
        stage_breakdown = {}
        for stage_name, contributions in stage_contributions.items():
            if stage_name in stage_display_names:
                # Find the participant with highest contribution
                if contributions:
                    primary_participant = max(contributions.items(), key=lambda x: x[1])[0]
                    # Map to display name
                    participant_name = self.get_participant_display_name(primary_participant)
                    stage_breakdown[stage_name] = participant_name
                else:
                    stage_breakdown[stage_name] = "None"
        
        return stage_breakdown
    
    def get_participant_display_name(self, participant_id: str) -> str:
        """Get display name for a participant ID"""
        # Try to match with configured participants using Slack ID first
        for p in self.config["participants"]:
            if p["slack_id"] and p["slack_id"] == participant_id:
                return p["name"]
        
        # Fallback: get display name from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT display_name FROM users WHERE id = ?', (participant_id,))
        display_name = cursor.fetchone()
        conn.close()
        
        if display_name and display_name[0]:
            return display_name[0]
        else:
            # For unknown users, return a more descriptive label
            return f"External-{participant_id[-4:]}"
    
    def generate_short_rationale(self, deal_id: str, split: Dict) -> str:
        """Generate short rationale based on commission split and stage analysis"""
        
        # Get participant percentages
        participants = []
        for name, pct in split.items():
            if name in ["Aki", "Addie", "Mayank", "Amy"] and pct > 0:
                participants.append((name, pct))
        
        # Sort by percentage (highest first)
        participants.sort(key=lambda x: x[1], reverse=True)
        
        if len(participants) == 0:
            return "No team involvement recorded."
        
        # Get stage-level details for this deal
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get stage detections for this deal
        cursor.execute('''
            SELECT stage_name, author, confidence 
            FROM stage_detections 
            WHERE conv_id = (SELECT conv_id FROM conversations WHERE name = ?)
            ORDER BY stage_name, confidence DESC
        ''', (deal_id,))
        
        stage_data = cursor.fetchall()
        conn.close()
        
        # Group stages by participant
        stage_participation = {}
        for stage_name, author, confidence in stage_data:
            # Map author to participant name
            participant_name = None
            for name, pct in participants:
                if name in ["Aki", "Addie", "Mayank", "Amy"]:
                    # Find the Slack ID for this participant
                    for p in self.config["participants"]:
                        if p["name"] == name:
                            if p["slack_id"] == author:
                                participant_name = name
                                break
                    if participant_name:
                        break
            
            if participant_name:
                if participant_name not in stage_participation:
                    stage_participation[participant_name] = []
                stage_participation[participant_name].append(stage_name)
        
        # Generate rationale with stage details
        if len(participants) == 1:
            name, pct = participants[0]
            stages = stage_participation.get(name, [])
            if stages:
                stage_list = ", ".join(sorted(set(stages)))
                return f"{name} handled {len(set(stages))} sales stages ({stage_list}) with {pct:.0f}% ownership."
            else:
                return f"{name} handled all sales stages with {pct:.0f}% ownership. No other team involvement."
        
        elif len(participants) == 2:
            name1, pct1 = participants[0]
            name2, pct2 = participants[1]
            stages1 = stage_participation.get(name1, [])
            stages2 = stage_participation.get(name2, [])
            
            if pct1 >= 75:
                stage_list1 = ", ".join(sorted(set(stages1))) if stages1 else "multiple stages"
                stage_list2 = ", ".join(sorted(set(stages2))) if stages2 else "supporting stages"
                return f"{name1} owns business relationship ({pct1:.0f}%) handling {stage_list1}. {name2} supported sales process ({pct2:.0f}%) in {stage_list2}."
            else:
                stage_list1 = ", ".join(sorted(set(stages1))) if stages1 else "multiple stages"
                stage_list2 = ", ".join(sorted(set(stages2))) if stages2 else "multiple stages"
                return f"Two-way split. {name1} ({pct1:.0f}%) handled {stage_list1}, {name2} ({pct2:.0f}%) handled {stage_list2}."
        
        else:
            # Multiple participants
            primary = participants[0]
            others = participants[1:]
            
            # Build stage details for primary
            primary_stages = stage_participation.get(primary[0], [])
            primary_stage_list = ", ".join(sorted(set(primary_stages))) if primary_stages else "multiple stages"
            
            # Build stage details for others
            other_details = []
            for name, pct in others:
                stages = stage_participation.get(name, [])
                stage_list = ", ".join(sorted(set(stages))) if stages else "supporting stages"
                other_details.append(f"{name} ({pct:.0f}%) in {stage_list}")
            
            return f"{primary[0]} owns business relationship ({primary[1]:.0f}%) handling {primary_stage_list}. {', '.join(other_details)} supported sales process."
    
    def generate_output_files(self, all_splits: List[Dict], person_totals: Dict[str, float]):
        """Generate output CSV files and summary"""
        
        # Deal splits CSV with all 7 sales reps
        with open(self.output_dir / "deal_splits.csv", 'w', newline='') as f:
            fieldnames = ["deal_id", "Aki", "Addie", "Amy", "Mayank", "Prateek", "Will", "Kadeem"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for split in all_splits:
                writer.writerow(split)
        
        # Person rollup CSV
        with open(self.output_dir / "person_rollup.csv", 'w', newline='') as f:
            fieldnames = ["person", "total_percentage", "deal_count"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for person, total in person_totals.items():
                deal_count = len([s for s in all_splits if s[person] > 0])
                writer.writerow({
                    "person": person,
                    "total_percentage": total,
                    "deal_count": deal_count
                })
        
        # Deal outline summary
        with open(self.output_dir / "deal_outline.txt", 'w') as f:
            f.write("Typical Deal Stage Progression\n")
            f.write("============================\n\n")
            
            for stage in self.config["stages"]:
                f.write(f"{stage['name'].replace('_', ' ').title()}: {stage['weight']}%\n")
                f.write(f"  Keywords: {', '.join(stage['keywords'])}\n\n")
        
        # Generate rationale CSV with contestation level and reasoning
        self.generate_rationale_csv(all_splits)
        
        logger.info(f"Output files generated in {self.output_dir}")

def main():
    """Main entry point"""
    print("RepSplit - Sales Commission Calculator")
    print("=====================================")
    
    # Check if config exists
    if not os.path.exists("config.json"):
        print("\nNo configuration file found. Please create config.json with your Slack token and participant information.")
        print("A default config.json has been created for you to edit.")
        return
    
    # Initialize and run analysis
    repsplit = RepSplit()
    repsplit.run_analysis()
    
    print("\nAnalysis complete! Check the 'output' directory for results.")

if __name__ == "__main__":
    main()
