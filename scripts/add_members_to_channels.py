#!/usr/bin/env python3
"""
Add Members to Slack Channels Tool

Bulk adds specified team members to all BitSafe customer Slack channels.
"""

import asyncio
import aiohttp
import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Slack configuration
SLACK_TOKEN = os.getenv("SLACK_USER_TOKEN")  # Must have groups:write and channels:write scopes
TEAM_ID = "T05FWTX7PMG"  # BitSafe workspace

class SlackMemberAdder:
    def __init__(self, member_usernames):
        self.slack_token = SLACK_TOKEN
        self.member_usernames = member_usernames  # List of Slack usernames (e.g., ['shin_novation', 'kdclarke'])
        self.member_ids = {}  # Will map username -> user_id
        self.results = []
        
    async def get_user_ids(self):
        """Map usernames to Slack user IDs"""
        print(f"🔍 Looking up user IDs for: {', '.join(self.member_usernames)}")
        
        headers = {
            "Authorization": f"Bearer {self.slack_token}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://slack.com/api/users.list",
                headers=headers,
                params={"team_id": TEAM_ID}
            ) as resp:
                data = await resp.json()
                if not data.get("ok"):
                    print(f"❌ Error fetching users: {data.get('error')}")
                    return False
                
                members = data.get("members", [])
                
                for member in members:
                    profile = member.get("profile", {})
                    username = member.get("name", "")
                    display_name = profile.get("display_name", "")
                    real_name = profile.get("real_name", "")
                    user_id = member.get("id", "")
                    
                    # Check if this user matches any of our target usernames
                    for target_username in self.member_usernames:
                        target_lower = target_username.lower().replace("@", "")
                        if (username.lower() == target_lower or 
                            display_name.lower() == target_lower or
                            real_name.lower().replace(" ", "") == target_lower):
                            self.member_ids[target_username] = user_id
                            print(f"   ✓ Found {target_username}: {real_name} ({user_id})")
                            break
        
        # Check if we found all users
        missing = set(self.member_usernames) - set(self.member_ids.keys())
        if missing:
            print(f"❌ Could not find users: {', '.join(missing)}")
            return False
        
        return True
    
    async def add_members_to_channels(self, dry_run=False):
        """Add members to all BitSafe customer channels - always uses live API"""
        print(f"\n{'[DRY RUN] ' if dry_run else ''}Adding members to BitSafe channels...")
        
        # Always fetch channels from live API to ensure we have the latest channels
        print(f"   Fetching channels from Slack API...")
        
        headers = {
            "Authorization": f"Bearer {self.slack_token}",
            "Content-Type": "application/json"
        }
        
        bitsafe_channels = []
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://slack.com/api/conversations.list",
                headers=headers,
                params={"limit": 200, "exclude_archived": "false", "types": "public_channel,private_channel"}
            ) as resp:
                data = await resp.json()
                if data.get("ok"):
                    all_channels = data.get("channels", [])
                    bitsafe_channels = [
                        ch for ch in all_channels 
                        if "bitsafe" in ch.get("name", "").lower()
                    ]
                else:
                    print(f"❌ Error fetching channels: {data.get('error')}")
                    return
        
        print(f"   Found {len(bitsafe_channels)} BitSafe channels")
        
        async with aiohttp.ClientSession() as session:
            for channel in bitsafe_channels:
                channel_id = channel["id"]
                channel_name = channel["name"]
                
                # Check current members first
                async with session.get(
                    "https://slack.com/api/conversations.members",
                    headers=headers,
                    params={"channel": channel_id}
                ) as resp:
                    data = await resp.json()
                    if not data.get("ok"):
                        print(f"   ⚠️  Couldn't check members in {channel_name}: {data.get('error')}")
                        self.results.append({
                            "channel": channel_name,
                            "status": "error_checking",
                            "message": data.get('error')
                        })
                        continue
                    
                    current_members = set(data.get("members", []))
                
                # Add each member
                for username, user_id in self.member_ids.items():
                    if user_id in current_members:
                        print(f"   ℹ️  {username} already in #{channel_name}")
                        self.results.append({
                            "channel": channel_name,
                            "user": username,
                            "status": "already_member"
                        })
                        continue
                    
                    if dry_run:
                        print(f"   [DRY RUN] Would add {username} to #{channel_name}")
                        self.results.append({
                            "channel": channel_name,
                            "user": username,
                            "status": "would_add"
                        })
                        continue
                    
                    # Actually add the member
                    async with session.post(
                        "https://slack.com/api/conversations.invite",
                        headers=headers,
                        json={
                            "channel": channel_id,
                            "users": user_id
                        }
                    ) as resp:
                        data = await resp.json()
                        if data.get("ok"):
                            print(f"   ✅ Added {username} to #{channel_name}")
                            self.results.append({
                                "channel": channel_name,
                                "user": username,
                                "status": "success"
                            })
                        else:
                            error = data.get('error')
                            print(f"   ❌ Failed to add {username} to #{channel_name}: {error}")
                            self.results.append({
                                "channel": channel_name,
                                "user": username,
                                "status": "error",
                                "message": error
                            })
                
                # Small delay to avoid rate limits
                await asyncio.sleep(0.5)
    
    def print_summary(self, dry_run=False):
        """Print summary of operations"""
        if dry_run:
            print(f"\n📊 DRY RUN SUMMARY")
        else:
            print(f"\n📊 SUMMARY")
        print("="*60)
        
        by_status = {}
        for result in self.results:
            status = result['status']
            by_status[status] = by_status.get(status, 0) + 1
        
        for status, count in sorted(by_status.items()):
            print(f"   {status}: {count}")
        
        print(f"\n   Total operations: {len(self.results)}")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 add_members_to_channels.py <username1> <username2> [--dry-run] [--yes]")
        print("\nExample:")
        print("  python3 add_members_to_channels.py shin_novation kdclarke --dry-run")
        print("  python3 add_members_to_channels.py aliya kevin --yes")
        sys.exit(1)
    
    # Parse arguments
    dry_run = "--dry-run" in sys.argv
    skip_confirm = "--yes" in sys.argv or "-y" in sys.argv
    usernames = [arg for arg in sys.argv[1:] if not arg.startswith("--") and not arg.startswith("-")]
    
    print("="*60)
    print("🚀 Slack Member Addition Tool")
    print("="*60)
    print(f"Members to add: {', '.join(usernames)}")
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE (will make changes)'}")
    print("="*60)
    
    if not dry_run and not skip_confirm:
        confirm = input("\n⚠️  This will add members to ALL BitSafe channels. Continue? (yes/no): ")
        if confirm.lower() != "yes":
            print("Cancelled.")
            sys.exit(0)
    
    adder = SlackMemberAdder(usernames)
    
    # Get user IDs
    if not await adder.get_user_ids():
        sys.exit(1)
    
    # Add members to channels
    await adder.add_members_to_channels(dry_run=dry_run)
    
    # Print summary
    adder.print_summary(dry_run=dry_run)
    
    if dry_run:
        print("\n💡 Remove --dry-run flag to actually add members")

if __name__ == "__main__":
    asyncio.run(main())

