#!/usr/bin/env python3
"""
Populate Stage Detections
Processes all existing messages in the database to detect deal stages and populate the stage_detections table.
This script should be run after slack_ingest.py to enable proper commission calculations.
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Tuple, Dict
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stage_detection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StageDetectionPopulator:
    def __init__(self, db_path: str = "repsplit.db", config_file: str = "config.json"):
        self.db_path = db_path
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self) -> Dict:
        """Load configuration from config.json"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file {self.config_file} not found")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return {}
    
    def detect_stages_in_message(self, text: str) -> List[Tuple[str, float]]:
        """Detect deal stages in a message based on keyword patterns"""
        detected_stages = []
        text_lower = text.lower()
        
        for stage_config in self.config.get("stages", []):
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
    
    def populate_stage_detections(self):
        """Process all messages and populate stage_detections table"""
        logger.info("Starting stage detection population...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if stage_detections table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stage_detections'")
        if not cursor.fetchone():
            logger.error("stage_detections table not found. Please run slack_ingest.py first.")
            return
        
        # Check if messages table has data
        cursor.execute("SELECT COUNT(*) FROM messages")
        message_count = cursor.fetchone()[0]
        if message_count == 0:
            logger.error("No messages found in database. Please run slack_ingest.py first.")
            return
        
        logger.info(f"Found {message_count} messages to process")
        
        # Clear existing stage detections
        cursor.execute("DELETE FROM stage_detections")
        logger.info("Cleared existing stage detections")
        
        # Get all messages with conversation and user info
        cursor.execute('''
            SELECT m.id, m.conv_id, m.author, m.timestamp, m.text, u.display_name
            FROM messages m
            LEFT JOIN users u ON m.author = u.id
            ORDER BY m.conv_id, m.timestamp
        ''')
        
        messages = cursor.fetchall()
        logger.info(f"Processing {len(messages)} messages...")
        
        # Process each message
        stage_detections_inserted = 0
        for i, (message_id, conv_id, author, timestamp, text, display_name) in enumerate(messages):
            if i % 100 == 0:
                logger.info(f"Processed {i}/{len(messages)} messages...")
            
            # Skip empty or very short messages
            if not text or len(text.strip()) < 3:
                continue
            
            # Detect stages in this message
            detected_stages = self.detect_stages_in_message(text)
            
            # Insert stage detections
            for stage_name, confidence in detected_stages:
                cursor.execute('''
                    INSERT INTO stage_detections 
                    (conv_id, stage_name, message_id, author, timestamp, confidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (conv_id, stage_name, message_id, author, timestamp, confidence))
                stage_detections_inserted += 1
        
        # Commit changes
        conn.commit()
        conn.close()
        
        logger.info(f"Stage detection population complete!")
        logger.info(f"Inserted {stage_detections_inserted} stage detections from {len(messages)} messages")
        
        # Show summary by stage
        self.show_stage_summary()
    
    def show_stage_summary(self):
        """Show summary of detected stages"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT stage_name, COUNT(*) as count, AVG(confidence) as avg_confidence
            FROM stage_detections
            GROUP BY stage_name
            ORDER BY count DESC
        ''')
        
        results = cursor.fetchall()
        
        if results:
            logger.info("\n📊 Stage Detection Summary:")
            logger.info("=" * 50)
            for stage_name, count, avg_confidence in results:
                logger.info(f"{stage_name:20} | {count:4} detections | {avg_confidence:.2f} avg confidence")
        else:
            logger.warning("No stage detections found!")
        
        conn.close()

def main():
    """Main entry point"""
    print("Stage Detection Populator")
    print("=========================")
    
    # Check if database exists
    if not Path("repsplit.db").exists():
        print("❌ Database not found. Please run slack_ingest.py first.")
        return
    
    # Check if config exists
    if not Path("config.json").exists():
        print("❌ Config file not found. Please create config.json first.")
        return
    
    # Initialize and run
    populator = StageDetectionPopulator()
    populator.populate_stage_detections()
    
    print("\n✅ Stage detection population complete!")
    print("Now you can run repsplit.py to generate proper justifications with stage analysis.")

if __name__ == "__main__":
    main()
