#!/usr/bin/env python3
"""
Add Missing Members to Slack Channels (Targeted)

Reads the audit report and adds only the specific missing members to each channel.
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

import aiohttp
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Slack configuration
SLACK_TOKEN = os.getenv("SLACK_USER_TOKEN")
TEAM_ID = "T05FWTX7PMG"  # BitSafe workspace

# Team member mapping (username -> name for lookup)
TEAM_MEMBERS = {
    "Aki Balogh (CEO)": "aki",
    "Gabi Tui (Head of Product)": "gabi",
    "Mayank (Sales Engineer)": "mayank",
    "Kadeem Clarke (Head of Growth)": "kadeem",
    "Amy Wu (BD)": "amy",
    "Kevin Huet": "kevin",
    "Aliya Gordon": "aliya",
    "Jesse Eisenberg (CTO)": "jesse",
    "Anna Matusova (VP Finance & Legal)": "anna",
    "Dae (Sales Advisor)": "dae",
}

# Known user IDs (for faster lookup and reliability)
KNOWN_USER_IDS = {
    "aki": "U05FZBDQ4RJ",
    "gabi": "U09HC7B6YJZ",
    "mayank": "U091F8WHDC3",
    "kadeem": "U08JNLKMH60",
    "amy": "U092DKJ8L4Q",
    "kevin": "U09S1JLS6EN",
    "aliya": "U09RZH933NJ",
    "jesse": "U05G2HFEAQD",
    "anna": "U062FP6KC0P",
    "dae": "U07K2QBN20V",
}


class TargetedMemberAdder:
    def __init__(self, dry_run=True):
        self.slack_token = SLACK_TOKEN
        self.dry_run = dry_run
        self.user_id_cache = {}  # Maps username -> user_id
        self.channel_id_cache = {}  # Maps channel_name -> channel_id
        self.results = []

    async def get_user_id(self, username):
        """Get Slack user ID for a username"""
        if username in self.user_id_cache:
            return self.user_id_cache[username]

        # Check known user IDs first
        if username in KNOWN_USER_IDS:
            user_id = KNOWN_USER_IDS[username]
            self.user_id_cache[username] = user_id
            return user_id

        # Fallback to API lookup
        headers = {"Authorization": f"Bearer {self.slack_token}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://slack.com/api/users.list",
                headers=headers,
                params={"team_id": TEAM_ID},
            ) as resp:
                data = await resp.json()
                if not data.get("ok"):
                    return None

                for member in data.get("members", []):
                    if member.get("deleted") or member.get("is_bot"):
                        continue

                    member_username = member.get("name", "").lower()

                    if member_username == username.lower():
                        user_id = member.get("id")
                        self.user_id_cache[username] = user_id
                        return user_id

        return None

    async def get_channel_id(self, channel_name):
        """Get Slack channel ID for a channel name"""
        if channel_name in self.channel_id_cache:
            return self.channel_id_cache[channel_name]

        headers = {"Authorization": f"Bearer {self.slack_token}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://slack.com/api/conversations.list",
                headers=headers,
                params={"limit": 200, "types": "public_channel,private_channel"},
            ) as resp:
                data = await resp.json()
                if not data.get("ok"):
                    return None

                for channel in data.get("channels", []):
                    if channel.get("name") == channel_name:
                        channel_id = channel.get("id")
                        self.channel_id_cache[channel_name] = channel_id
                        return channel_id

        return None

    async def add_member_to_channel(self, channel_name, channel_id, username, user_id):
        """Add a single member to a channel"""
        headers = {
            "Authorization": f"Bearer {self.slack_token}",
            "Content-Type": "application/json",
        }

        if self.dry_run:
            print(f"   [DRY RUN] Would add {username} ({user_id}) to {channel_name}")
            return {"status": "dry_run", "channel": channel_name, "member": username}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://slack.com/api/conversations.invite",
                headers=headers,
                json={"channel": channel_id, "users": user_id},
            ) as resp:
                data = await resp.json()

                if data.get("ok"):
                    print(f"   ✅ Added {username} to {channel_name}")
                    return {
                        "status": "success",
                        "channel": channel_name,
                        "member": username,
                    }
                elif data.get("error") == "already_in_channel":
                    print(f"   ℹ️  {username} already in {channel_name}")
                    return {
                        "status": "already_member",
                        "channel": channel_name,
                        "member": username,
                    }
                else:
                    error = data.get("error", "unknown")
                    print(f"   ❌ Failed to add {username} to {channel_name}: {error}")
                    return {
                        "status": "error",
                        "channel": channel_name,
                        "member": username,
                        "error": error,
                    }

    async def process_missing_members(self, report_file):
        """Process the missing members report and add members"""
        print(f"📊 Reading report: {report_file}\n")

        # Read the CSV
        df = pd.read_csv(report_file)

        print(f"Found {len(df)} channels with missing members\n")
        print("🔍 Phase 1: Looking up user and channel IDs...")

        # Pre-cache all user IDs
        all_missing = set()
        for missing_str in df["Required Missing"]:
            if pd.notna(missing_str):
                members = [m.strip() for m in missing_str.split(",")]
                for member in members:
                    if member in TEAM_MEMBERS:
                        username = TEAM_MEMBERS[member]
                        all_missing.add(username)

        # Get user IDs
        for username in all_missing:
            user_id = await self.get_user_id(username)
            if user_id:
                print(f"   ✓ Found {username}: {user_id}")
            else:
                print(f"   ❌ Could not find user: {username}")

        print(
            f"\n🔧 Phase 2: {'[DRY RUN] Simulating' if self.dry_run else 'Adding'} missing members..."
        )

        # Process each channel
        for _, row in df.iterrows():
            channel_name = row["Group Name"]
            missing_str = row["Required Missing"]

            if pd.isna(missing_str):
                continue

            print(f"\n📌 {channel_name}:")

            # Get channel ID
            channel_id = await self.get_channel_id(channel_name)
            if not channel_id:
                print(f"   ❌ Could not find channel ID")
                continue

            # Parse missing members
            missing_members = [m.strip() for m in missing_str.split(",")]

            # Add each missing member
            for member_name in missing_members:
                if member_name not in TEAM_MEMBERS:
                    print(f"   ⚠️  Unknown member: {member_name}")
                    continue

                username = TEAM_MEMBERS[member_name]
                user_id = self.user_id_cache.get(username)

                if not user_id:
                    print(f"   ⚠️  No user ID for {username}")
                    continue

                result = await self.add_member_to_channel(
                    channel_name, channel_id, username, user_id
                )
                self.results.append(result)

                # Rate limiting
                await asyncio.sleep(1)

        # Summary
        print(f"\n\n{'='*60}")
        print("📊 SUMMARY")
        print(f"{'='*60}")

        if self.dry_run:
            print(f"Mode: DRY RUN (no changes made)")
        else:
            success = len([r for r in self.results if r["status"] == "success"])
            already = len([r for r in self.results if r["status"] == "already_member"])
            errors = len([r for r in self.results if r["status"] == "error"])

            print(f"✅ Successfully added: {success}")
            print(f"ℹ️  Already members: {already}")
            print(f"❌ Errors: {errors}")

        print(f"Total operations: {len(self.results)}")


async def main():
    # Parse arguments
    dry_run = "--dry-run" in sys.argv or "--yes" not in sys.argv

    # Find the most recent missing members report
    report_file = "output/reports/slack_missing_members_20251125_170324.csv"

    if not os.path.exists(report_file):
        print(f"❌ Report file not found: {report_file}")
        print("Run the audit script first to generate the missing members report.")
        sys.exit(1)

    print("=" * 60)
    print("TARGETED SLACK MEMBER ADDITION")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Report: {report_file}")

    if not dry_run:
        print("\n⚠️  WARNING: This will make LIVE changes to Slack channels!")
        print("Press Ctrl+C to cancel, or wait 3 seconds to continue...")
        await asyncio.sleep(3)

    print("\n")

    adder = TargetedMemberAdder(dry_run=dry_run)
    await adder.process_missing_members(report_file)

    print(f"\n✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())
