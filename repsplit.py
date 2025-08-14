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
            
            # Check for keyword matches
            matches = 0
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    matches += 1
            
            if matches > 0:
                # Calculate confidence based on number of keyword matches
                confidence = min(1.0, matches / len(keywords) + 0.3)
                detected_stages.append((stage_name, confidence))
        
        return detected_stages
    
    def calculate_commission_splits(self, conv_id: str) -> Dict[str, float]:
        """Calculate commission splits for a specific conversation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all stage detections for this conversation
        cursor.execute('''
            SELECT stage_name, author, confidence
            FROM stage_detections 
            WHERE conv_id = ?
            ORDER BY timestamp
        ''', (conv_id,))
        
        stage_data = cursor.fetchall()
        
        # Get conversation participants
        cursor.execute('''
            SELECT DISTINCT author FROM messages WHERE conv_id = ?
        ''', (conv_id,))
        
        participants = [row[0] for row in cursor.fetchall()]
        
        # Initialize commission tracking
        commissions = {p: 0.0 for p in participants}
        stage_contributions = {}
        
        # Process each stage
        for stage_name, author, confidence in stage_data:
            if stage_name not in stage_contributions:
                stage_contributions[stage_name] = {}
            
            if author not in stage_contributions[stage_name]:
                stage_contributions[stage_name][author] = 0
            
            # Apply diminishing returns
            current_contrib = stage_contributions[stage_name][author]
            diminishing_factor = self.config["diminishing_returns"] ** current_contrib
            contribution = confidence * diminishing_factor
            
            stage_contributions[stage_name][author] += 1
            commissions[author] += contribution
        
        # Apply stage weights
        weighted_commissions = {p: 0.0 for p in participants}
        
        for stage_name, author_contribs in stage_contributions.items():
            # Find stage config
            stage_config = next((s for s in self.config["stages"] if s["name"] == stage_name), None)
            if not stage_config:
                continue
            
            stage_weight = stage_config["weight"]
            total_contrib = sum(author_contribs.values())
            
            if total_contrib > 0:
                for author, contrib in author_contribs.items():
                    share = (contrib / total_contrib) * stage_weight
                    weighted_commissions[author] += share
        
        # Apply founder cap for Aki (unless they appear in negotiation/closing)
        aki_id = next((p["slack_id"] for p in self.config["participants"] if p["name"] == "Aki"), None)
        if aki_id and aki_id in weighted_commissions:
            # Check if Aki appears in negotiation or closing stages
            aki_in_later_stages = False
            for stage_name, author_contribs in stage_contributions.items():
                if stage_name in ["negotiation", "closing"] and aki_id in author_contribs:
                    aki_in_later_stages = True
                    break
            
            if not aki_in_later_stages:
                # Apply founder cap
                max_aki_share = 30.0  # Cap Aki at 30% unless in later stages
                if weighted_commissions[aki_id] > max_aki_share:
                    excess = weighted_commissions[aki_id] - max_aki_share
                    weighted_commissions[aki_id] = max_aki_share
                    
                    # Redistribute excess to other participants
                    other_participants = [p for p in participants if p != aki_id]
                    if other_participants:
                        excess_per_participant = excess / len(other_participants)
                        for p in other_participants:
                            weighted_commissions[p] += excess_per_participant
        
        # Apply presence floor
        for participant in participants:
            if weighted_commissions[participant] < self.config["presence_floor"]:
                weighted_commissions[participant] = self.config["presence_floor"]
        
        # Normalize to 100%
        total = sum(weighted_commissions.values())
        if total > 0:
            normalized_commissions = {p: (v / total) * 100 for p, v in weighted_commissions.items()}
        else:
            # Equal split if no contributions
            normalized_commissions = {p: 100.0 / len(participants) for p in participants}
        
        conn.close()
        return normalized_commissions
    
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
        
        # Generate markdown file
        justification_file = self.justifications_dir / f"{conv_name}_justification.md"
        
        with open(justification_file, 'w') as f:
            f.write(f"# Commission Split Justification: {conv_name}\n\n")
            f.write(f"**Channel ID:** {conv_id}\n")
            f.write(f"**Created:** {datetime.fromtimestamp(conv_data[3]).strftime('%Y-%m-%d %H:%M:%S') if conv_data[3] else 'Unknown'}\n")
            f.write(f"**Members:** {conv_data[2]}\n\n")
            
            f.write("## Commission Splits\n\n")
            for participant_id, percentage in commissions.items():
                cursor.execute('SELECT display_name FROM users WHERE id = ?', (participant_id,))
                display_name = cursor.fetchone()
                name = display_name[0] if display_name else participant_id
                f.write(f"- **{name}:** {percentage:.1f}%\n")
            
            f.write("\n## Stage Analysis\n\n")
            
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
            
            # Map to participant names
            participant_names = {}
            for participant_id, percentage in commissions.items():
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT display_name FROM users WHERE id = ?', (participant_id,))
                display_name = cursor.fetchone()
                conn.close()
                
                if display_name:
                    # Try to match with configured participants
                    for p in self.config["participants"]:
                        if p["display_name"] and p["display_name"].lower() in display_name[0].lower():
                            participant_names[participant_id] = p["name"]
                            break
                    else:
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
            
            for participant_id, percentage in commissions.items():
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
