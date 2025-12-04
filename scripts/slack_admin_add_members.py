#!/usr/bin/env python3
"""
Add missing members to Slack channels using Enterprise Grid Admin API
Requires Primary Org Owner admin token
"""

import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

SLACK_ADMIN_TOKEN = os.getenv("SLACK_ADMIN_TOKEN")
TEAM_ID = "E09HEBXK4J3"

# Members and channels that need fixing (from audit #102)
FIXES_NEEDED = {
    "incyt-bitsafe": ["U05FZBDQ4RJ"],  # Aki Balogh
    "x-bitsafe": ["U04QGJC7MCU", "U09KR1HKMND", "U0A1SQQKD33"],  # Gabi, Dae, Sarah
    "loxor-finance-bitsafe": ["U09KR1HKMND", "U0A1SQQKD33"],  # Dae, Sarah
}

MEMBER_NAMES = {
    "U05FZBDQ4RJ": "Aki Balogh",
    "U04QGJC7MCU": "Gabi Tuinaite",
    "U09KR1HKMND": "Dae Lee",
    "U0A1SQQKD33": "Sarah Flood",
}


def get_all_channels():
    """Get all Slack channels using admin token"""
    url = "https://slack.com/api/conversations.list"
    headers = {"Authorization": f"Bearer {SLACK_ADMIN_TOKEN}"}

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
            print(f"❌ Failed to list channels: {result.get('error')}")
            return {}

        channels = result.get("channels", [])
        all_channels.extend(channels)

        cursor = result.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break

    # Map names to IDs
    channel_map = {ch["name"]: ch["id"] for ch in all_channels}
    return channel_map


def admin_invite(channel_id, user_ids):
    """Invite users to channel using Enterprise Grid Admin API"""
    url = "https://slack.com/api/admin.conversations.invite"
    headers = {
        "Authorization": f"Bearer {SLACK_ADMIN_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {"channel_id": channel_id, "user_ids": user_ids}

    response = requests.post(url, headers=headers, json=data)
    return response.json()


def main():
    if not SLACK_ADMIN_TOKEN:
        print("❌ SLACK_ADMIN_TOKEN not configured")
        print("\nGenerate token at: https://api.slack.com/apps/A09PW015AV9/oauth")
        print("Copy the User OAuth Token (must be from Primary Org Owner)")
        return 1

    print("=" * 80)
    print("👑 ENTERPRISE GRID ADMIN - ADD MISSING MEMBERS")
    print("=" * 80)

    # Get all channels
    print("\n🔍 Fetching all channels...")
    channel_map = get_all_channels()

    if not channel_map:
        return 1

    print(f"✅ Found {len(channel_map)} total channels\n")

    # Verify we can find the target channels
    missing_channels = [ch for ch in FIXES_NEEDED.keys() if ch not in channel_map]

    if missing_channels:
        print(f"⚠️  Could not find {len(missing_channels)} channels:")
        for ch in missing_channels:
            print(f"  - {ch}")
        print()

    # Display what will be done
    total_additions = sum(len(users) for users in FIXES_NEEDED.values())
    print(
        f"📋 {len(FIXES_NEEDED)} channels need updates ({total_additions} additions):\n"
    )

    for channel_name, user_ids in FIXES_NEEDED.items():
        if channel_name not in channel_map:
            print(f"  {channel_name}: NOT FOUND")
            continue

        names = [MEMBER_NAMES.get(uid, uid) for uid in user_ids]
        print(f"  {channel_name}: {', '.join(names)}")

    print(f"\n📝 Add {total_additions} members to channels? (yes/no): ", end="")

    try:
        confirmation = input().strip().lower()
    except EOFError:
        confirmation = "yes"

    if confirmation != "yes":
        print("\n❌ Cancelled")
        return 1

    # Perform additions using Admin API
    print(f"\n👑 Adding members using Admin API...\n")

    success = 0
    errors = 0

    for channel_name, user_ids in FIXES_NEEDED.items():
        if channel_name not in channel_map:
            print(f"❌ {channel_name}: Channel not found")
            errors += len(user_ids)
            continue

        channel_id = channel_map[channel_name]
        print(f"📢 {channel_name}:")

        # Admin API can add multiple users at once
        result = admin_invite(channel_id, user_ids)

        if result.get("ok"):
            print(f"  ✅ Added {len(user_ids)} members")
            success += len(user_ids)
        else:
            error = result.get("error")
            print(f"  ❌ Error: {error}")
            errors += len(user_ids)

        print()

    print("=" * 80)
    print(f"✅ Successfully added {success} members")
    if errors > 0:
        print(f"❌ {errors} errors")
    print("=" * 80)

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
