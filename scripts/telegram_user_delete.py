#!/usr/bin/env python3
"""
Telegram User Offboarding Script

Complete offboarding automation for removing users from all Telegram chats.
Uses Telegram Client API (telethon) for full access to groups, channels, and supergroups.

Requirements:
    pip install telethon python-dotenv

Environment Variables (add to .env):
    TELEGRAM_API_ID=your_api_id
    TELEGRAM_API_HASH=your_api_hash
    TELEGRAM_PHONE=your_phone_number
    TARGET_USERNAME=nftaddie

Setup:
    1. Get API credentials from https://my.telegram.org/apps
    2. Add credentials to .env file
    3. First run will require phone verification

Usage:
    # Dry run (recommended first)
    python3 scripts/telegram_user_delete.py --dry-run --username=nftaddie

    # Actual removal
    python3 scripts/telegram_user_delete.py --username=nftaddie
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    from telethon import TelegramClient
    from telethon.errors import (ChatAdminRequiredError, FloodWaitError,
                                 UserAdminInvalidError,
                                 UserNotParticipantError)
    from telethon.tl.types import (Channel, ChannelParticipantAdmin,
                                   ChannelParticipantCreator,
                                   ChannelParticipantsAdmins, Chat,
                                   ChatParticipantAdmin,
                                   ChatParticipantCreator, User)
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
import sys
from pathlib import Path

# Get project root (parent of scripts directory)
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"

load_dotenv(env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/telegram_offboarding.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class TelegramOffboarding:
    """Handle complete Telegram user offboarding"""

    def __init__(self, dry_run: bool = False):
        """
        Initialize Telegram offboarding client

        Args:
            dry_run: If True, only simulate actions without making changes
        """
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
            "groups_removed": 0,
            "channels_removed": 0,
            "supergroups_removed": 0,
            "failed_removals": 0,
            "access_denied": 0,
            "not_participant": 0,
        }

        # Track groups where we don't have admin access
        self.no_admin_access_groups = []
        self.no_admin_access_details = []  # Store detailed info including owners

    async def connect(self):
        """Connect to Telegram and authenticate"""
        await self.client.connect()

        if not await self.client.is_user_authorized():
            logger.info("📱 Authentication required. Sending code to phone...")
            await self.client.send_code_request(self.phone)

            # Check for code in environment variable first (for non-interactive use)
            code = os.getenv("TELEGRAM_CODE")
            if not code:
                code = input("Enter the code you received: ")
            else:
                logger.info(f"📱 Using code from TELEGRAM_CODE environment variable")

            try:
                await self.client.sign_in(self.phone, code)
            except Exception as e:
                # Check if 2FA password is required
                if "SessionPasswordNeededError" in str(type(e).__name__):
                    logger.info(
                        "🔐 Two-factor authentication detected. Password required..."
                    )
                    password = os.getenv("TELEGRAM_PASSWORD")
                    if not password:
                        password = input("Enter your 2FA password: ")
                    else:
                        logger.info(
                            f"🔐 Using password from TELEGRAM_PASSWORD environment variable"
                        )

                    await self.client.sign_in(password=password)
                else:
                    raise

        logger.info("✅ Connected to Telegram successfully")

    async def find_user(self, username: str) -> Optional[User]:
        """
        Find user by username

        Args:
            username: Username to find (with or without @)

        Returns:
            User object if found, None otherwise
        """
        # Remove @ if present
        username = username.lstrip("@")

        try:
            user = await self.client.get_entity(username)
            if isinstance(user, User):
                logger.info(
                    f"✅ Found user: {user.first_name} {user.last_name or ''} (@{user.username})"
                )
                logger.info(f"   User ID: {user.id}")
                return user
            else:
                logger.error(f"❌ Entity is not a user: {type(user)}")
                return None
        except Exception as e:
            logger.error(f"❌ Error finding user @{username}: {e}")
            return None

    async def get_all_chats(self) -> List:
        """
        Get all chats/groups/channels the authenticated user is in

        Returns:
            List of chat entities
        """
        logger.info("🔍 Fetching all chats, groups, and channels...")

        chats = []
        async for dialog in self.client.iter_dialogs():
            # Skip private chats (DMs)
            if isinstance(dialog.entity, User):
                continue

            chats.append(dialog.entity)

        logger.info(f"📊 Found {len(chats)} group chats/channels")
        return chats

    async def get_chat_admins(self, chat) -> List[str]:
        """
        Get list of admin names for a chat

        Args:
            chat: Chat entity

        Returns:
            List of admin names/usernames
        """
        admins = []
        try:
            if isinstance(chat, Channel):
                # For channels/supergroups
                async for participant in self.client.iter_participants(
                    chat, filter=ChannelParticipantsAdmins
                ):
                    name = participant.first_name or ""
                    if participant.last_name:
                        name += f" {participant.last_name}"
                    if participant.username:
                        name += f" (@{participant.username})"
                    admins.append(name)
            elif isinstance(chat, Chat):
                # For regular groups
                try:
                    full_chat = await self.client.get_entity(chat)
                    participants = await self.client.get_participants(chat)
                    for p in participants:
                        perms = await self.client.get_permissions(chat, p.id)
                        if perms.is_admin or perms.is_creator:
                            name = p.first_name or ""
                            if p.last_name:
                                name += f" {p.last_name}"
                            if p.username:
                                name += f" (@{p.username})"
                            admins.append(name)
                except:
                    pass
        except Exception as e:
            logger.debug(
                f"Could not get admins for {getattr(chat, 'title', 'Unknown')}: {e}"
            )

        return admins if admins else ["Unknown"]

    async def check_admin_permissions(self, chat) -> bool:
        """
        Check if we have admin permissions to remove users

        Args:
            chat: Chat entity to check

        Returns:
            True if we have admin permissions, False if unknown or denied
        """
        try:
            me = await self.client.get_me()

            if isinstance(chat, Chat):
                # Regular group - use get_permissions which is more reliable
                try:
                    permissions = await self.client.get_permissions(chat, me.id)
                    return permissions.is_admin or permissions.is_creator
                except Exception as perm_error:
                    # If we can't get permissions, we likely don't have access
                    logger.debug(
                        f"   Cannot check permissions in {chat.title}: {type(perm_error).__name__}"
                    )
                    return False

            elif isinstance(chat, Channel):
                # Channel or supergroup
                permissions = await self.client.get_permissions(chat, me.id)
                return permissions.is_admin or permissions.is_creator

            return False

        except Exception as e:
            # Catch any other permission errors
            logger.debug(
                f"   Could not check permissions for {getattr(chat, 'title', 'Unknown')}: {type(e).__name__}"
            )
            return False

    async def remove_user_from_chat(self, chat, user: User) -> bool:
        """
        Remove user from a specific chat

        Args:
            chat: Chat entity to remove user from
            user: User to remove

        Returns:
            True if successful, False otherwise
        """
        chat_name = getattr(chat, "title", "Unknown")

        try:
            # Check if user is actually in the chat
            try:
                await self.client.get_permissions(chat, user)
            except UserNotParticipantError:
                logger.info(f"ℹ️  User not in {chat_name} - skipping")
                self.stats["not_participant"] += 1
                return True
            except Exception as check_error:
                # If we can't check participation (permission denied, etc.), skip
                logger.info(f"ℹ️  Cannot verify participation in {chat_name} - skipping")
                self.stats["not_participant"] += 1
                return True

            # Check if we have admin permissions
            if not await self.check_admin_permissions(chat):
                logger.warning(f"⚠️  No admin permissions in {chat_name} - skipping")
                self.stats["access_denied"] += 1
                self.no_admin_access_groups.append(chat_name)

                # Get admin info for this group
                admins = await self.get_chat_admins(chat)
                self.no_admin_access_details.append(
                    {"name": chat_name, "admins": admins}
                )
                return False

            if self.dry_run:
                logger.info(
                    f"🔍 [DRY RUN] Would remove @{user.username} from: {chat_name}"
                )
                return True

            # Perform actual removal
            if isinstance(chat, Chat):
                # Regular group
                await self.client.kick_participant(chat, user)
                logger.info(f"✅ Removed from group: {chat_name}")
                self.stats["groups_removed"] += 1

            elif isinstance(chat, Channel):
                # Channel or supergroup
                await self.client.kick_participant(chat, user)

                if chat.megagroup:
                    logger.info(f"✅ Removed from supergroup: {chat_name}")
                    self.stats["supergroups_removed"] += 1
                else:
                    logger.info(f"✅ Removed from channel: {chat_name}")
                    self.stats["channels_removed"] += 1

            # Small delay to respect rate limits
            await asyncio.sleep(0.5)
            return True

        except ChatAdminRequiredError:
            logger.warning(f"⚠️  Admin rights required for {chat_name}")
            self.stats["access_denied"] += 1
            self.no_admin_access_groups.append(chat_name)

            # Get admin info for this group
            admins = await self.get_chat_admins(chat)
            self.no_admin_access_details.append({"name": chat_name, "admins": admins})
            return False

        except UserAdminInvalidError:
            logger.warning(f"⚠️  Cannot remove admin from {chat_name}")
            self.stats["access_denied"] += 1
            self.no_admin_access_groups.append(chat_name)

            # Get admin info for this group
            admins = await self.get_chat_admins(chat)
            self.no_admin_access_details.append({"name": chat_name, "admins": admins})
            return False

        except FloodWaitError as e:
            logger.warning(f"⚠️  Rate limit hit. Waiting {e.seconds} seconds...")
            await asyncio.sleep(e.seconds)
            return await self.remove_user_from_chat(chat, user)

        except Exception as e:
            logger.error(f"❌ Error removing from {chat_name}: {e}")
            self.stats["failed_removals"] += 1
            return False

    async def offboard_user(self, username: str, limit: int = None):
        """
        Complete offboarding process for a user

        Args:
            username: Username to offboard (with or without @)
            limit: Optional limit on number of chats to process (for testing)
        """
        logger.info("=" * 70)
        logger.info(f"🚀 Starting Telegram Offboarding for @{username.lstrip('@')}")
        logger.info(f"   Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        logger.info(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 70)

        # Connect to Telegram
        await self.connect()

        # Find the user
        user = await self.find_user(username)
        if not user:
            logger.error(f"❌ Could not find user @{username}")
            return

        # Get all chats
        chats = await self.get_all_chats()

        if not chats:
            logger.warning("⚠️  No group chats or channels found")
            return

        # Limit chats if specified (for testing)
        if limit and limit < len(chats):
            logger.info(f"\n⚠️  LIMITING to first {limit} chats for testing")
            chats = chats[:limit]

        # Remove user from each chat
        logger.info(f"\n🔧 Processing {len(chats)} chats...")
        logger.info("-" * 70)

        for i, chat in enumerate(chats, 1):
            chat_name = getattr(chat, "title", "Unknown")
            logger.info(f"\n[{i}/{len(chats)}] Processing: {chat_name}")
            await self.remove_user_from_chat(chat, user)

        # Print summary
        self.print_summary()

        # Save groups without admin access to file
        if self.no_admin_access_groups:
            self.save_no_admin_groups()

    def print_summary(self):
        """Print offboarding summary"""
        logger.info("\n" + "=" * 70)
        logger.info("📊 OFFBOARDING SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Groups removed:      {self.stats['groups_removed']}")
        logger.info(f"Channels removed:    {self.stats['channels_removed']}")
        logger.info(f"Supergroups removed: {self.stats['supergroups_removed']}")
        logger.info(f"Not participant:     {self.stats['not_participant']}")
        logger.info(f"Access denied:       {self.stats['access_denied']}")
        logger.info(f"Failed removals:     {self.stats['failed_removals']}")
        logger.info("=" * 70)

        total_removed = (
            self.stats["groups_removed"]
            + self.stats["channels_removed"]
            + self.stats["supergroups_removed"]
        )

        if self.dry_run:
            logger.info("\n✅ Dry run completed. No actual changes were made.")
        elif total_removed > 0:
            logger.info(f"\n✅ Successfully removed user from {total_removed} chats")
        else:
            logger.info("\n⚠️  No removals were made")

        # Print list of groups without admin access
        if self.no_admin_access_groups:
            logger.info("\n" + "=" * 70)
            logger.info(
                f"⚠️  GROUPS WITHOUT ADMIN ACCESS ({len(self.no_admin_access_groups)})"
            )
            logger.info("=" * 70)
            for i, group_name in enumerate(self.no_admin_access_groups, 1):
                logger.info(f"{i}. {group_name}")
            logger.info("=" * 70)

    def save_no_admin_groups(self):
        """Save list of groups without admin access to file with admin info"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs/telegram_no_admin_access_{timestamp}.txt"

        try:
            with open(filename, "w") as f:
                f.write(f"Groups Where Admin Access is Required\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total: {len(self.no_admin_access_groups)} groups\n")
                f.write("=" * 70 + "\n\n")

                if self.no_admin_access_details:
                    # Write with admin details
                    for i, group_info in enumerate(self.no_admin_access_details, 1):
                        f.write(f"{i}. {group_info['name']}\n")
                        f.write(f"   Admins: {', '.join(group_info['admins'])}\n\n")
                else:
                    # Fallback to simple list
                    for i, group_name in enumerate(self.no_admin_access_groups, 1):
                        f.write(f"{i}. {group_name}\n")

            logger.info(f"\n💾 Saved groups without admin access to: {filename}")
        except Exception as e:
            logger.error(f"❌ Error saving groups to file: {e}")

    async def cleanup(self):
        """Disconnect from Telegram"""
        if self.client:
            await self.client.disconnect()
            logger.info("🔌 Disconnected from Telegram")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Telegram User Offboarding Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Dry run (recommended first)
    python3 scripts/telegram_user_delete.py --dry-run --username=nftaddie
    
    # Actual removal
    python3 scripts/telegram_user_delete.py --username=nftaddie
    
    # Using environment variable
    export TARGET_USERNAME=nftaddie
    python3 scripts/telegram_user_delete.py --dry-run
        """,
    )

    parser.add_argument(
        "--username",
        type=str,
        default=os.getenv("TARGET_USERNAME"),
        help="Telegram username to offboard (with or without @)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate actions without making actual changes",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of chats to process (for testing)",
    )

    args = parser.parse_args()

    if not args.username:
        parser.error(
            "Username is required. Use --username=USERNAME or set TARGET_USERNAME env var"
        )

    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)

    # Run offboarding
    offboarding = TelegramOffboarding(dry_run=args.dry_run)

    try:
        await offboarding.offboard_user(args.username, limit=args.limit)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Offboarding interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise
    finally:
        await offboarding.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
