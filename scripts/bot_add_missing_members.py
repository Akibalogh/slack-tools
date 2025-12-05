#!/usr/bin/env python3
"""
Use the User Offboarding Tool bot to add missing members to channels
Bot must already be in the channels (run bot_channel_coverage.py first)
"""

import json
import os
import sys

import psycopg2
import requests
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_USER_TOKEN = os.getenv("SLACK_USER_TOKEN")  # To get latest audit


def get_latest_audit():
    """Get latest audit with missing members data"""
    database_url = os.getenv("DATABASE_URL")
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, results_json
        FROM audit_runs  
        WHERE status = 'completed'
        AND results_json IS NOT NULL
        ORDER BY completed_at DESC
        LIMIT 1
    """
    )

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return None

    audit_id, results_json = row
    data = json.loads(results_json)

    return {"id": audit_id, "data": data}


def get_all_channels(token):
    """Get all BitSafe channels with IDs"""
    url = "https://slack.com/api/conversations.list"
    headers = {"Authorization": f"Bearer {token}"}

    all_channels = []
    cursor = None

    while True:
        params = {
            "types": "public_channel,private_channel",
            "exclude_archived": "true",
            "limit": 200,
        }
        if cursor:
            params["cursor"] = cursor

        response = requests.get(url, headers=headers, params=params)
        result = response.json()

        if not result.get("ok"):
            return {}

        all_channels.extend(result.get("channels", []))
        cursor = result.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break

    # Map names to IDs
    return {
        ch["name"]: ch["id"]
        for ch in all_channels
        if "bitsafe" in ch.get("name", "").lower()
    }


def invite_to_channel(channel_id, user_ids, token):
    """Invite users to channel using bot token"""
    url = "https://slack.com/api/conversations.invite"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Slack API accepts comma-separated user IDs
    data = {
        "channel": channel_id,
        "users": ",".join(user_ids) if isinstance(user_ids, list) else user_ids,
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()


def main():
    if not SLACK_BOT_TOKEN or not SLACK_USER_TOKEN:
        print("❌ Tokens not configured")
        return 1

    print("=" * 80)
    print("🤖 BOT-BASED MEMBER MANAGEMENT")
    print("=" * 80)

    # Get latest audit
    print("\n🔍 Fetching latest audit...")
    audit = get_latest_audit()

    if not audit:
        print("❌ No completed audit found")
        return 1

    print(f"✅ Using audit #{audit['id']}")

    # Get required members from database
    database_url = os.getenv("DATABASE_URL")
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name, slack_user_id FROM employees WHERE slack_required = TRUE AND slack_user_id IS NOT NULL"
    )
    required_members = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.close()
    conn.close()

    print(f"📇 Required members: {len(required_members)}")

    # Get all channel IDs
    print("\n🔍 Fetching channel IDs...")
    channel_map = get_all_channels(SLACK_USER_TOKEN)
    print(f"✅ Found {len(channel_map)} BitSafe channels")

    # Parse audit to find missing members
    slack_channels = audit["data"].get("slack_channels", [])

    channels_to_fix = []
    for channel_data in slack_channels:
        missing_str = channel_data.get("Required Missing", "")
        if missing_str and missing_str not in ["-", "None", "✓ All Present"]:
            channel_name = channel_data.get("Group Name", "")
            if channel_name in channel_map:
                # Parse missing names and get their IDs
                missing_members = []
                for member_str in missing_str.split(", "):
                    # Extract name without role (e.g., "Sarah Flood (BDR)" -> "Sarah Flood")
                    name_parts = member_str.split(" (")
                    name = name_parts[0].strip()

                    # Try to find this person in required_members
                    for req_name, req_id in required_members.items():
                        if name in req_name or req_name in name:
                            missing_members.append((req_name, req_id))
                            break

                if missing_members:
                    channels_to_fix.append(
                        {
                            "name": channel_name,
                            "id": channel_map[channel_name],
                            "missing": missing_members,
                        }
                    )

    if not channels_to_fix:
        print("\n🎉 All channels have complete membership!")
        return 0

    print(f"\n📋 {len(channels_to_fix)} channels need updates:\n")
    for channel in channels_to_fix:
        names = [name for name, _ in channel["missing"]]
        print(f"  {channel['name']}: {', '.join(names)}")

    total_adds = sum(len(ch["missing"]) for ch in channels_to_fix)
    print(f"\n📝 Add {total_adds} members using bot? (yes/no): ", end="")

    try:
        confirmation = input().strip().lower()
    except EOFError:
        confirmation = "yes"

    if confirmation != "yes":
        print("\n❌ Cancelled")
        return 1

    # Add members using BOT token
    print(f"\n🤖 Adding members via bot...\n")

    success = 0
    errors = 0

    for channel in channels_to_fix:
        print(f"📢 {channel['name']}:")

        for member_name, member_id in channel["missing"]:
            result = invite_to_channel(channel["id"], member_id, SLACK_BOT_TOKEN)

            if result.get("ok"):
                print(f"  ✅ {member_name}")
                success += 1
            else:
                error = result.get("error")
                if error == "already_in_channel":
                    print(f"  ✓  {member_name} (already in)")
                    success += 1
                elif error == "not_in_channel":
                    print(f"  ⚠️  {member_name} - Bot not in channel! Add bot first.")
                    errors += 1
                else:
                    print(f"  ❌ {member_name}: {error}")
                    errors += 1

        print()

    print("=" * 80)
    print(f"✅ Added {success} members")
    if errors > 0:
        print(f"❌ {errors} errors")
    print("=" * 80)

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
