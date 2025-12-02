#!/usr/bin/env python3
"""
Slack Ingestion Tool for RepSplit

Downloads data from private Slack channels ending with '-bitsafe' to populate the database
for commission analysis.
"""

import asyncio
import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("slack_ingest.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class SlackIngest:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.db_path = "repsplit.db"
        self.base_url = "https://slack.com/api"

        # Load environment variables
        load_dotenv()

        # Get Slack token from environment
        slack_token = os.getenv("SLACK_TOKEN")
        if not slack_token or slack_token == "xoxp-your-slack-token-here":
            raise ValueError(
                "SLACK_TOKEN not found in .env file. Please add your Slack token to .env file"
            )

        self.headers = {
            "Authorization": f"Bearer {slack_token}",
            "Content-Type": "application/json",
        }

    def load_config(self) -> Dict:
        """Load configuration from JSON file"""
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                return json.load(f)
        else:
            raise FileNotFoundError(f"Config file {self.config_file} not found")

    def is_data_fresh(self) -> bool:
        """Check if data is less than 30 days old"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT MAX(timestamp) FROM messages")
        result = cursor.fetchone()
        conn.close()

        if not result or not result[0]:
            return False

        # Check if most recent message is less than 30 days old
        latest_timestamp = result[0]
        if isinstance(latest_timestamp, str):
            latest_timestamp = float(latest_timestamp)

        days_old = (datetime.now().timestamp() - latest_timestamp) / (24 * 3600)
        return days_old < 30

    def init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create tables
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                conv_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                member_count INTEGER,
                creation_date INTEGER,
                is_bitsafe BOOLEAN DEFAULT FALSE
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                display_name TEXT,
                real_name TEXT,
                email TEXT
            )
        """
        )

        cursor.execute(
            """
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
        """
        )

        cursor.execute(
            """
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
        """
        )

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")

    async def get_private_channels(self) -> List[Dict]:
        """Get all private channels from Slack"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/conversations.list"
            params = {"types": "private_channel", "limit": 1000}

            async with session.get(
                url, headers=self.headers, params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("ok"):
                        channels = data.get("channels", [])
                        logger.info(f"Found {len(channels)} private channels")
                        return channels
                    else:
                        logger.error(f"Slack API error: {data.get('error')}")
                        return []
                else:
                    logger.error(f"HTTP error: {response.status}")
                    return []

    async def get_users(self) -> List[Dict]:
        """Get all users from Slack"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/users.list"

            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("ok"):
                        users = data.get("members", [])
                        logger.info(f"Found {len(users)} users")
                        return users
                    else:
                        logger.error(f"Slack API error: {data.get('error')}")
                        return []
                else:
                    logger.error(f"HTTP error: {response.status}")
                    return []

    async def get_channel_history(
        self, channel_id: str, limit: int = 1000
    ) -> List[Dict]:
        """Get message history from a specific channel"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/conversations.history"
            params = {"channel": channel_id, "limit": limit}

            async with session.get(
                url, headers=self.headers, params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("ok"):
                        messages = data.get("messages", [])
                        logger.info(
                            f"Found {len(messages)} messages in channel {channel_id}"
                        )
                        return messages
                    else:
                        logger.error(f"Slack API error: {data.get('error')}")
                        return []
                else:
                    logger.error(f"HTTP error: {response.status}")
                    return []

    def save_conversations(self, channels: List[Dict]):
        """Save conversation data to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for channel in channels:
            name = channel.get("name", "")
            is_bitsafe = name.endswith("-bitsafe")

            cursor.execute(
                """
                INSERT OR REPLACE INTO conversations 
                (conv_id, name, member_count, creation_date, is_bitsafe)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    channel.get("id"),
                    name,
                    channel.get("num_members", 0),
                    channel.get("created", 0),
                    is_bitsafe,
                ),
            )

        conn.commit()
        conn.close()
        logger.info(f"Saved {len(channels)} conversations to database")

    def save_users(self, users: List[Dict]):
        """Save user data to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for user in users:
            if not user.get("is_bot", False) and not user.get("deleted", False):
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO users 
                    (id, display_name, real_name, email)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        user.get("id"),
                        user.get("profile", {}).get("display_name", ""),
                        user.get("profile", {}).get("real_name", ""),
                        user.get("profile", {}).get("email", ""),
                    ),
                )

        conn.commit()
        conn.close()
        logger.info(f"Saved users to database")

    def save_messages(self, channel_id: str, messages: List[Dict]):
        """Save message data to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for message in messages:
            # Skip bot messages and messages without text
            if message.get("bot_id") or not message.get("text"):
                continue

            cursor.execute(
                """
                INSERT OR REPLACE INTO messages 
                (id, conv_id, timestamp, author, text, stage_hits)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    message.get("ts"),
                    channel_id,
                    float(message.get("ts", 0)),
                    message.get("user", ""),
                    message.get("text", ""),
                    "",  # stage_hits will be populated by RepSplit analysis
                ),
            )

        conn.commit()
        conn.close()
        logger.info(f"Saved {len(messages)} messages for channel {channel_id}")

    async def ingest_data(self, test_mode: bool = True, force_refresh: bool = False):
        """Main ingestion function"""
        logger.info("Starting Slack data ingestion...")

        # Initialize database
        self.init_database()

        # Check data freshness
        if not force_refresh and self.is_data_fresh():
            logger.info("✅ Data is fresh! Using existing data.")
            print("📊 Data is up-to-date (less than 30 days old)")
            print("💡 Use --force-refresh to re-download anyway")
            return

        if not force_refresh:
            print("🔄 Data is older than 30 days, downloading fresh logs...")
        else:
            print("🔄 Force refreshing data...")

        # Get private channels
        channels = await self.get_private_channels()
        if not channels:
            logger.error("No channels found")
            return

        # Filter for customer bitsafe channels only (XYZCo-bitsafe format)
        customer_channels = []
        for c in channels:
            name = c.get("name", "")
            if name.endswith("-bitsafe"):
                # Check if it's a customer channel (not internal like "gsf-app-dev")
                if not name.startswith("gsf-") and not name.startswith("internal-"):
                    customer_channels.append(c)

        logger.info(f"Found {len(customer_channels)} customer bitsafe channels")

        # List all customer channels
        print(f"\n📋 Customer Channels Found ({len(customer_channels)}):")
        print("=" * 50)
        for i, channel in enumerate(customer_channels, 1):
            name = channel.get("name", "")
            member_count = channel.get("num_members", 0)
            created = channel.get("created", 0)
            if created:
                created_date = datetime.fromtimestamp(created).strftime("%Y-%m-%d")
            else:
                created_date = "Unknown"
            print(
                f"{i:2d}. {name:<30} | Members: {member_count:2d} | Created: {created_date}"
            )

        print("=" * 50)

        # Remove test mode - process all customer channels
        target_channels = customer_channels

        # Save conversations
        self.save_conversations(channels)

        # Get and save users
        users = await self.get_users()
        self.save_users(users)

        # Get and save messages for target channels
        for channel in target_channels:
            logger.info(f"Downloading messages for {channel['name']}...")
            messages = await self.get_channel_history(channel["id"])
            if messages:
                self.save_messages(channel["id"], messages)

            # Add small delay to avoid rate limiting
            await asyncio.sleep(1)

        logger.info("Data ingestion complete!")

        # Print summary
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT COUNT(*) FROM conversations WHERE is_bitsafe = TRUE OR name = "gsf-app-dev"'
        )
        target_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM messages")
        message_count = cursor.fetchone()[0]

        conn.close()

        print(f"\nIngestion Summary:")
        print(f"Target channels (bitsafe + gsf-app-dev): {target_count}")
        print(f"Users: {user_count}")
        print(f"Messages: {message_count}")


async def main():
    """Main entry point"""
    import sys

    force_refresh = "--force-refresh" in sys.argv
    test_mode = "--test" in sys.argv

    print("Slack Ingestion Tool for RepSplit")
    print("=================================")

    try:
        ingest = SlackIngest()
        await ingest.ingest_data(test_mode=test_mode, force_refresh=force_refresh)
        print("\n✅ Ingestion complete! You can now run RepSplit analysis.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Please check your config.json file and Slack token.")


if __name__ == "__main__":
    asyncio.run(main())
