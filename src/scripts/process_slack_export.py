#!/usr/bin/env python3
"""
Process Slack Export Data for ETL Pipeline

This script processes Slack export JSON files and populates the database
for the ETL pipeline to use.
"""

import os
import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/slack_export_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SlackExportProcessor:
    def __init__(self, export_path: str, db_path: str):
        self.export_path = Path(export_path)
        self.db_path = db_path
        self.conn = None
        
    def setup_database(self):
        """Setup the database with required tables"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Create conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                conv_id TEXT PRIMARY KEY,
                name TEXT,
                type TEXT,
                created REAL,
                purpose TEXT,
                topic TEXT
            )
        ''')
        
        # Create messages table
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
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT,
                real_name TEXT,
                email TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_conv_id ON messages (conv_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_author ON messages (author)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages (timestamp)')
        
        self.conn.commit()
        logger.info("Database setup complete")
    
    def load_users(self):
        """Load user data from Slack export"""
        users_file = self.export_path / "users" / "users.json"
        if not users_file.exists():
            logger.warning(f"Users file not found: {users_file}")
            return
        
        with open(users_file, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
        
        cursor = self.conn.cursor()
        for user in users_data:
            cursor.execute('''
                INSERT OR REPLACE INTO users (id, name, real_name, email)
                VALUES (?, ?, ?, ?)
            ''', (
                user.get('id', ''),
                user.get('name', ''),
                user.get('real_name', ''),
                user.get('profile', {}).get('email', '')
            ))
        
        self.conn.commit()
        logger.info(f"Loaded {len(users_data)} users")
    
    def process_channel(self, channel_file: Path, channel_info: Dict[str, Any]):
        """Process a single channel's messages"""
        channel_id = channel_info.get('id', '')
        channel_name = channel_info.get('name', '')
        channel_type = channel_info.get('type', '')
        created = channel_info.get('created', 0)
        purpose = channel_info.get('purpose', {}).get('value', '')
        topic = channel_info.get('topic', {}).get('value', '')
        
        # Insert conversation record
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO conversations (conv_id, name, type, created, purpose, topic)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (channel_id, channel_name, channel_type, created, purpose, topic))
        
        # Process messages
        if channel_file.exists():
            with open(channel_file, 'r', encoding='utf-8') as f:
                messages_data = json.load(f)
            
            message_count = 0
            for message in messages_data:
                if message.get('type') == 'message' and not message.get('subtype'):
                    message_id = message.get('ts', '')
                    timestamp = float(message.get('ts', 0))
                    author = message.get('user', '')
                    text = message.get('text', '')
                    
                    # Insert message
                    cursor.execute('''
                        INSERT OR REPLACE INTO messages (id, conv_id, timestamp, author, text, stage_hits)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (message_id, channel_id, timestamp, author, text, ''))
                    
                    message_count += 1
            
            logger.info(f"Processed {message_count} messages from {channel_name}")
        else:
            logger.warning(f"Messages file not found: {channel_file}")
    
    def process_channels(self):
        """Process all channels from the export"""
        channels_dir = self.export_path / "channels"
        if not channels_dir.exists():
            logger.error(f"Channels directory not found: {channels_dir}")
            return
        
        # Load channel metadata
        private_channels_file = channels_dir / "private_channels.json"
        public_channels_file = channels_dir / "public_channels.json"
        
        channels_info = []
        
        if private_channels_file.exists():
            with open(private_channels_file, 'r', encoding='utf-8') as f:
                private_channels = json.load(f)
                channels_info.extend(private_channels)
        
        if public_channels_file.exists():
            with open(public_channels_file, 'r', encoding='utf-8') as f:
                public_channels = json.load(f)
                channels_info.extend(public_channels)
        
        logger.info(f"Found {len(channels_info)} channels to process")
        
        # Process each channel
        for channel_info in channels_info:
            channel_name = channel_info.get('name', '')
            channel_file = channels_dir / f"{channel_name}_messages.json"
            
            # Only process channels ending with -bitsafe
            if channel_name.endswith('-bitsafe'):
                self.process_channel(channel_file, channel_info)
            else:
                logger.debug(f"Skipping channel {channel_name} (not a -bitsafe channel)")
        
        self.conn.commit()
        logger.info("Channel processing complete")
    
    def process_dms(self):
        """Process DM conversations"""
        dms_dir = self.export_path / "dms"
        if not dms_dir.exists():
            logger.info("No DMs directory found")
            return
        
        # List all DM directories
        dm_dirs = [d for d in dms_dir.iterdir() if d.is_dir()]
        logger.info(f"Found {len(dm_dirs)} DM conversations")
        
        for dm_dir in dm_dirs:
            # Create a conversation ID from the directory name
            conv_id = f"dm_{dm_dir.name}"
            
            # Insert conversation record
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO conversations (conv_id, name, type, created, purpose, topic)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (conv_id, f"DM {dm_dir.name}", "dm", 0, "", ""))
            
            # Process messages in this DM
            messages_file = dm_dir / "messages.json"
            if messages_file.exists():
                with open(messages_file, 'r', encoding='utf-8') as f:
                    messages_data = json.load(f)
                
                message_count = 0
                for message in messages_data:
                    if message.get('type') == 'message' and not message.get('subtype'):
                        message_id = message.get('ts', '')
                        timestamp = float(message.get('ts', 0))
                        author = message.get('user', '')
                        text = message.get('text', '')
                        
                        # Insert message
                        cursor.execute('''
                            INSERT OR REPLACE INTO messages (id, conv_id, timestamp, author, text, stage_hits)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (message_id, conv_id, timestamp, author, text, ''))
                        
                        message_count += 1
                
                logger.info(f"Processed {message_count} messages from DM {dm_dir.name}")
        
        self.conn.commit()
        logger.info("DM processing complete")
    
    def process_export(self):
        """Process the entire Slack export"""
        logger.info(f"Processing Slack export from {self.export_path}")
        
        # Setup database
        self.setup_database()
        
        # Load users
        self.load_users()
        
        # Process channels
        self.process_channels()
        
        # Process DMs
        self.process_dms()
        
        # Get final statistics
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM conversations")
        conv_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM messages")
        msg_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        logger.info(f"Processing complete:")
        logger.info(f"  Conversations: {conv_count}")
        logger.info(f"  Messages: {msg_count}")
        logger.info(f"  Users: {user_count}")
        
        self.conn.close()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process Slack export data')
    parser.add_argument('--export-path', default='data/raw/slack_export_20250815_064939',
                       help='Path to Slack export directory')
    parser.add_argument('--db-path', default='data/slack/repsplit.db',
                       help='Path to output database')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(args.db_path), exist_ok=True)
    
    # Process the export
    processor = SlackExportProcessor(args.export_path, args.db_path)
    processor.process_export()

if __name__ == '__main__':
    main()

