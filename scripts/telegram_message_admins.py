#!/usr/bin/env python3
"""
Telegram Admin Messaging Script

Send messages to group admins requesting user removal.

Usage:
    python3 scripts/telegram_message_admins.py --csv=logs/telegram_no_admin_access_[timestamp].csv --dry-run
    python3 scripts/telegram_message_admins.py --csv=logs/telegram_no_admin_access_[timestamp].csv
"""

import argparse
import asyncio
import csv
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

try:
    from telethon import TelegramClient
    from telethon.errors import (FloodWaitError, UserIsBlockedError,
                                 UserPrivacyRestrictedError)
    from telethon.tl.types import User
except ImportError:
    print("❌ Error: telethon not installed")
    print("Install with: pip install telethon")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ Error: python-dotenv not installed")
    print("Install with: pip install python-dotenv")
    sys.exit(1)

# Load environment variables from .env file in project root
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
load_dotenv(env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/telegram_admin_messages.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class TelegramAdminMessenger:
    """Send messages to group admins requesting user removal"""

    def __init__(self, csv_file: str, username_to_remove: str, dry_run: bool = False):
        """
        Initialize the messenger

        Args:
            csv_file: Path to CSV file with group names and admins
            username_to_remove: Username of user to remove (e.g., nftaddie)
            dry_run: If True, don't actually send messages
        """
        self.csv_file = csv_file
        self.username_to_remove = username_to_remove.lstrip("@")
        self.dry_run = dry_run

        self.api_id = os.getenv("TELEGRAM_API_ID")
        self.api_hash = os.getenv("TELEGRAM_API_HASH")
        self.phone = os.getenv("TELEGRAM_PHONE")

        if not all([self.api_id, self.api_hash, self.phone]):
            raise ValueError(
                "Missing required environment variables: "
                "TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE"
            )

        # Initialize client
        self.client = TelegramClient("telegram_session", self.api_id, self.api_hash)

        # Stats tracking
        self.stats = {
            "messages_sent": 0,
            "already_messaged": 0,
            "failed_sends": 0,
            "blocked_by_user": 0,
            "privacy_restricted": 0,
            "user_not_found": 0,
        }

        # Track who we've messaged (to avoid duplicates)
        self.messaged_usernames: Set[str] = set()

    async def connect(self):
        """Connect to Telegram and authenticate"""
        await self.client.connect()

        if not await self.client.is_user_authorized():
            logger.info("📱 Authentication required. Sending code to phone...")
            await self.client.send_code_request(self.phone)

            # Check for code in environment variable first
            code = os.getenv("TELEGRAM_CODE")
            if not code:
                code = input("Enter the code you received: ")
            else:
                logger.info("📱 Using code from TELEGRAM_CODE environment variable")

            try:
                await self.client.sign_in(self.phone, code)
            except Exception as e:
                if "SessionPasswordNeededError" in str(type(e).__name__):
                    logger.info(
                        "🔐 Two-factor authentication detected. Password required..."
                    )
                    password = os.getenv("TELEGRAM_PASSWORD")
                    if not password:
                        password = input("Enter your 2FA password: ")
                    else:
                        logger.info(
                            "🔐 Using password from TELEGRAM_PASSWORD environment variable"
                        )

                    await self.client.sign_in(password=password)
                else:
                    raise

        logger.info("✅ Connected to Telegram successfully")

    def parse_csv(self) -> List[Dict]:
        """
        Parse CSV file to get groups and admins

        Returns:
            List of dicts with group_name and admin_usernames
        """
        groups_data = []

        with open(self.csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                group_name = row["Group Name"]
                admins_str = row["Admins"]

                # Extract usernames from admin string
                # Format: "Name (@username), Name2 (@username2)"
                usernames = re.findall(r"@(\w+)", admins_str)

                if usernames:
                    groups_data.append(
                        {"group_name": group_name, "admin_usernames": usernames}
                    )

        return groups_data

    def create_message(self, group_names: List[str]) -> str:
        """
        Create personalized message for admin

        Args:
            group_names: List of group names

        Returns:
            Message text
        """
        if len(group_names) == 1:
            return f"""Hi! Addie is no longer with BitSafe - could you please remove @{self.username_to_remove} from "{group_names[0]}"? Thanks! -Aki"""
        else:
            groups_list = "\n".join([f"• {name}" for name in group_names])
            return f"""Hi! Addie is no longer with BitSafe - could you please remove @{self.username_to_remove} from these groups:\n\n{groups_list}\n\nThanks! -Aki"""

    async def send_message_to_admin(
        self, username: str, group_names: List[str]
    ) -> bool:
        """
        Send message to a specific admin

        Args:
            username: Admin's username (without @)
            group_names: List of group names they admin

        Returns:
            True if successful, False otherwise
        """
        # Skip if already messaged
        if username in self.messaged_usernames:
            logger.info(f"ℹ️  Already messaged @{username} - skipping")
            self.stats["already_messaged"] += 1
            return True

        # Skip if it's the user we're trying to remove
        if username == self.username_to_remove:
            logger.info(f"ℹ️  Skipping @{username} (user being removed)")
            return True

        try:
            # Find the user
            user = await self.client.get_entity(username)

            if not isinstance(user, User):
                logger.warning(f"⚠️  @{username} is not a user")
                self.stats["user_not_found"] += 1
                return False

            message = self.create_message(group_names)

            if self.dry_run:
                groups_desc = (
                    f"{len(group_names)} group{'s' if len(group_names) > 1 else ''}"
                )
                logger.info(
                    f"🔍 [DRY RUN] Would message @{username} about: {groups_desc}"
                )
                logger.info(f"   Message preview:")
                for line in message.split("\n"):
                    logger.info(f"   {line}")
                logger.info("")
                self.messaged_usernames.add(username)
                return True

            # Send the message
            await self.client.send_message(user, message)
            groups_desc = (
                f"{len(group_names)} group{'s' if len(group_names) > 1 else ''}"
            )
            logger.info(f"✅ Sent message to @{username} about: {groups_desc}")

            self.messaged_usernames.add(username)
            self.stats["messages_sent"] += 1

            # Small delay to respect rate limits
            await asyncio.sleep(2)
            return True

        except UserIsBlockedError:
            logger.warning(f"⚠️  @{username} has blocked us")
            self.stats["blocked_by_user"] += 1
            self.messaged_usernames.add(username)  # Don't try again
            return False

        except UserPrivacyRestrictedError:
            logger.warning(f"⚠️  @{username} has privacy settings preventing messages")
            self.stats["privacy_restricted"] += 1
            self.messaged_usernames.add(username)  # Don't try again
            return False

        except FloodWaitError as e:
            logger.warning(f"⚠️  Rate limit hit. Waiting {e.seconds} seconds...")
            await asyncio.sleep(e.seconds)
            return await self.send_message_to_admin(username, group_names)

        except Exception as e:
            logger.error(f"❌ Error messaging @{username}: {e}")
            self.stats["failed_sends"] += 1
            return False

    async def message_all_admins(self):
        """Message all admins from the CSV file"""
        logger.info("=" * 70)
        logger.info(f"🚀 Starting Admin Messaging Campaign")
        logger.info(f"   Target: @{self.username_to_remove}")
        logger.info(f"   Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        logger.info(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 70)

        # Connect
        await self.connect()

        # Parse CSV
        logger.info(f"\n📋 Reading admin list from: {self.csv_file}")
        groups_data = self.parse_csv()
        logger.info(f"   Found {len(groups_data)} groups")

        # Collect all unique admins
        all_admins = {}  # username -> list of groups
        for group in groups_data:
            for username in group["admin_usernames"]:
                if username not in all_admins:
                    all_admins[username] = []
                all_admins[username].append(group["group_name"])

        # Remove the target user from the list if present
        if self.username_to_remove in all_admins:
            del all_admins[self.username_to_remove]

        logger.info(f"   Total unique admins to message: {len(all_admins)}")
        logger.info("-" * 70)

        # Show preview of who gets messages
        logger.info("\n📊 MESSAGE PREVIEW:")
        logger.info("-" * 70)

        # Sort by number of groups (descending) for easier review
        sorted_admins = sorted(
            all_admins.items(), key=lambda x: len(x[1]), reverse=True
        )

        for username, groups in sorted_admins:
            group_count = len(groups)
            logger.info(
                f"@{username:20} → {group_count} group{'s' if group_count > 1 else ''}"
            )
            if group_count <= 3:
                for group in groups:
                    logger.info(f"  • {group}")

        logger.info("-" * 70)
        logger.info(f"\n📨 Messaging {len(all_admins)} admins...\n")

        # Message each admin (only once, mentioning all their groups)
        for i, (username, groups) in enumerate(all_admins.items(), 1):
            logger.info(
                f"[{i}/{len(all_admins)}] @{username} ({len(groups)} group{'s' if len(groups) > 1 else ''})"
            )

            # Send one message mentioning all their groups
            await self.send_message_to_admin(username, groups)

        # Print summary
        self.print_summary()

        # Save results
        self.save_results()

    def print_summary(self):
        """Print messaging summary"""
        logger.info("\n" + "=" * 70)
        logger.info("📊 MESSAGING SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Messages sent:       {self.stats['messages_sent']}")
        logger.info(f"Already messaged:    {self.stats['already_messaged']}")
        logger.info(f"Blocked by user:     {self.stats['blocked_by_user']}")
        logger.info(f"Privacy restricted:  {self.stats['privacy_restricted']}")
        logger.info(f"User not found:      {self.stats['user_not_found']}")
        logger.info(f"Failed sends:        {self.stats['failed_sends']}")
        logger.info("=" * 70)

        if self.dry_run:
            logger.info("\n✅ Dry run completed. No actual messages were sent.")
        elif self.stats["messages_sent"] > 0:
            logger.info(
                f"\n✅ Successfully messaged {self.stats['messages_sent']} admins"
            )
        else:
            logger.info("\n⚠️  No messages were sent")

    def save_results(self):
        """Save list of messaged admins"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs/telegram_messaged_admins_{timestamp}.txt"

        try:
            with open(filename, "w") as f:
                f.write(f"Telegram Admin Messaging Results\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}\n")
                f.write(f"Total messaged: {len(self.messaged_usernames)}\n")
                f.write("=" * 70 + "\n\n")

                for i, username in enumerate(sorted(self.messaged_usernames), 1):
                    f.write(f"{i}. @{username}\n")

            logger.info(f"\n💾 Saved results to: {filename}")
        except Exception as e:
            logger.error(f"❌ Error saving results: {e}")

    async def cleanup(self):
        """Disconnect from Telegram"""
        if self.client:
            await self.client.disconnect()
            logger.info("🔌 Disconnected from Telegram")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Send messages to Telegram group admins",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--csv",
        type=str,
        required=True,
        help="Path to CSV file with group names and admins",
    )

    parser.add_argument(
        "--username",
        type=str,
        default="nftaddie",
        help="Username to remove (default: nftaddie)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate messages without actually sending",
    )

    args = parser.parse_args()

    # Verify CSV file exists
    if not Path(args.csv).exists():
        parser.error(f"CSV file not found: {args.csv}")

    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)

    # Run messaging campaign
    messenger = TelegramAdminMessenger(
        csv_file=args.csv, username_to_remove=args.username, dry_run=args.dry_run
    )

    try:
        await messenger.message_all_admins()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Messaging interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise
    finally:
        await messenger.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
