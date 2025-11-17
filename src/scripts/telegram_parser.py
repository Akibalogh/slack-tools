#!/usr/bin/env python3
"""
Telegram Parser for Commission Analysis

Parses Telegram HTML export files and converts them to a format compatible
with the existing commission calculation system.
"""

import os
import re
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramParser:
    def __init__(self, telegram_export_path: str, db_path: str = "data/slack/repsplit.db"):
        """
        Initialize the Telegram parser
        
        Args:
            telegram_export_path: Path to the Telegram export directory
            db_path: Path to the SQLite database
        """
        self.telegram_export_path = Path(telegram_export_path)
        self.db_path = db_path
        self.chats_index_path = self.telegram_export_path / "lists" / "chats.html"
        
        # User mapping from Telegram to internal team
        self.user_mapping = {
            "Aki Balogh": "Aki",
            "Addie Ann": "Addie", 
            "Amy Wu": "Amy",
            "0xmojo Mayank": "Mayank"
        }
        
        # Internal team Slack IDs (we'll get these from the database)
        self.internal_team_ids = {}
        
    def load_internal_team_ids(self):
        """Load internal team Slack IDs from the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get internal team members from users table
            cursor.execute("SELECT id, display_name, real_name FROM users WHERE display_name IN ('Aki', 'Addie', 'Amy', 'Mayank')")
            participants = cursor.fetchall()
            
            for slack_id, display_name, real_name in participants:
                if display_name:
                    self.internal_team_ids[display_name] = slack_id
                    
            conn.close()
            logger.info(f"Loaded {len(self.internal_team_ids)} internal team IDs: {list(self.internal_team_ids.keys())}")
            
        except Exception as e:
            logger.error(f"Error loading internal team IDs: {e}")
    
    def find_chat_by_company(self, company_name: str) -> Optional[str]:
        """
        Find a Telegram chat directory by company name
        
        Args:
            company_name: Name of the company to search for
            
        Returns:
            Chat directory name if found, None otherwise
        """
        if not self.chats_index_path.exists():
            logger.error(f"Chats index not found at {self.chats_index_path}")
            return None
            
        try:
            with open(self.chats_index_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Look for company name in the chats list
            soup = BeautifulSoup(content, 'html.parser')
            
            for link in soup.find_all('a'):
                if company_name.lower() in link.get_text().lower():
                    # Extract chat directory from href
                    href = link.get('href', '')
                    if 'chat_' in href:
                        # Extract chat_XXXX from path like "../chats/chat_0058/messages.html"
                        chat_dir = href.split('/')[2]  # Extract chat_XXXX
                        logger.info(f"Found chat for {company_name}: {chat_dir}")
                        return chat_dir
                        
            logger.warning(f"No chat found for company: {company_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error searching for company {company_name}: {e}")
            return None
    
    def parse_chat_messages(self, chat_dir: str) -> List[Dict]:
        """
        Parse messages from a specific chat directory
        
        Args:
            chat_dir: Chat directory name (e.g., 'chat_0058')
            
        Returns:
            List of parsed messages
        """
        messages_path = self.telegram_export_path / "chats" / chat_dir / "messages.html"
        
        if not messages_path.exists():
            logger.error(f"Messages file not found: {messages_path}")
            return []
            
        try:
            with open(messages_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            soup = BeautifulSoup(content, 'html.parser')
            messages = []
            
            # Find all message divs
            message_divs = soup.find_all('div', class_='message')
            
            for msg_div in message_divs:
                # Skip service messages
                if 'service' in msg_div.get('class', []):
                    continue
                    
                message = self._parse_single_message(msg_div)
                if message:
                    messages.append(message)
                    
            logger.info(f"Parsed {len(messages)} messages from {chat_dir}")
            return messages
            
        except Exception as e:
            logger.error(f"Error parsing messages from {chat_dir}: {e}")
            return []
    
    def _parse_single_message(self, msg_div) -> Optional[Dict]:
        """Parse a single message div into a message dictionary"""
        try:
            # Get message ID
            msg_id = msg_div.get('id', '').replace('message-', '')
            
            # Get timestamp
            timestamp_elem = msg_div.find('div', class_='date details')
            timestamp = None
            if timestamp_elem:
                title = timestamp_elem.get('title', '')
                if title:
                    # Parse timestamp from title attribute
                    timestamp = self._parse_timestamp(title)
            
            # Get author
            author_elem = msg_div.find('div', class_='from_name')
            author = None
            if author_elem:
                author = author_elem.get_text().strip()
                # Clean up author name (remove date if present)
                author = re.sub(r'<span.*', '', author).strip()
            
            # Get message text
            text_elem = msg_div.find('div', class_='text')
            text = ''
            if text_elem:
                text = text_elem.get_text().strip()
            
            # Skip if no author or text
            if not author or not text:
                return None
                
            # Map author to internal team member if possible
            mapped_author = self.user_mapping.get(author, author)
            
            return {
                'id': msg_id,
                'author': mapped_author,
                'original_author': author,
                'text': text,
                'timestamp': timestamp,
                'source': 'telegram'
            }
            
        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            return None
    
    def _parse_timestamp(self, title: str) -> Optional[str]:
        """Parse timestamp from title attribute"""
        try:
            # Extract date from title like "06.10.2024 12:31:11 UTC-05:00"
            match = re.search(r'(\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}:\d{2})', title)
            if match:
                date_str = match.group(1)
                # Convert to ISO format
                dt = datetime.strptime(date_str, '%d.%m.%Y %H:%M:%S')
                return dt.isoformat()
        except Exception as e:
            logger.error(f"Error parsing timestamp {title}: {e}")
        return None
    
    def save_messages_to_db(self, messages: List[Dict], company_name: str):
        """
        Save parsed Telegram messages to the database
        
        Args:
            messages: List of parsed messages
            company_name: Name of the company for this conversation
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create telegram_messages table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS telegram_messages (
                    id TEXT PRIMARY KEY,
                    author TEXT,
                    original_author TEXT,
                    text TEXT,
                    timestamp TEXT,
                    source TEXT,
                    company_name TEXT,
                    conv_id TEXT
                )
            ''')
            
            # Create conversation entry if it doesn't exist
            conv_id = f"{company_name.lower().replace(' ', '-')}-telegram"
            cursor.execute('''
                INSERT OR IGNORE INTO conversations 
                (conv_id, name, member_count, creation_date, is_bitsafe)
                VALUES (?, ?, 0, ?, 0)
            ''', (conv_id, company_name, int(datetime.now().timestamp())))
            
            # Insert messages
            for msg in messages:
                cursor.execute('''
                    INSERT OR REPLACE INTO telegram_messages 
                    (id, author, original_author, text, timestamp, source, company_name, conv_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (msg['id'], msg['author'], msg['original_author'], 
                      msg['text'], msg['timestamp'], msg['source'], company_name, conv_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved {len(messages)} Telegram messages to database for {company_name}")
            
        except Exception as e:
            logger.error(f"Error saving messages to database: {e}")
    
    def parse_company_chat(self, company_name: str) -> bool:
        """
        Parse Telegram chat for a specific company
        
        Args:
            company_name: Name of the company to parse
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Parsing Telegram chat for company: {company_name}")
        
        # Load internal team IDs
        self.load_internal_team_ids()
        
        # Find chat directory
        chat_dir = self.find_chat_by_company(company_name)
        if not chat_dir:
            return False
            
        # Parse messages
        messages = self.parse_chat_messages(chat_dir)
        if not messages:
            return False
            
        # Save to database
        self.save_messages_to_db(messages, company_name)
        
        return True

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1:
        company_name = sys.argv[1]
    else:
        company_name = "P2P"  # Default
    
    parser = TelegramParser("data/telegram/DataExport_2025-08-19")
    
    success = parser.parse_company_chat(company_name)
    if success:
        print(f"✅ Successfully parsed {company_name} Telegram chat")
    else:
        print(f"❌ Failed to parse {company_name} Telegram chat")

if __name__ == "__main__":
    main()
