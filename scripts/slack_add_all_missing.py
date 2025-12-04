#!/usr/bin/env python3
"""
Add ALL missing required members to Slack channels
Uses latest audit to find who's missing from which channels
"""

import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

SLACK_TOKEN = os.getenv("SLACK_USER_TOKEN")

# Required members and their Slack IDs (from database)
REQUIRED_MEMBERS = {
    "Aki Balogh": "U05FZBDQ4RJ",
    "Aliya Gordon": "U09RZH933NJ",
    "Amy Wu": "U05J9GZJ70E",
    "Dae Lee": "U09KR1HKMND",
    "Dave Shin": "U0997HN7KPE",
    "Gabi Tuinaite": "U04QGJC7MCU",
    "Kadeem Clarke": "U08JNLKMH60",
    "Kevin Huet": "U09S1JLS6EN",
    "Mayank Sachdev": "U091F8WHDC3",
    "Sarah Flood": "U0A1SQQKD33",
}


def get_channel_by_name(channel_name):
    """Get channel ID by name"""
    url = "https://slack.com/api/conversations.list"
    headers = {"Authorization": f"Bearer {SLACK_TOKEN}"}

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
            break

        for ch in result.get("channels", []):
            if ch.get("name") == channel_name:
                return ch.get("id")

        cursor = result.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break

    return None


def invite_to_channel(channel_id, user_id):
    """Invite user to channel"""
    url = "https://slack.com/api/conversations.invite"
    headers = {
        "Authorization": f"Bearer {SLACK_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {"channel": channel_id, "users": user_id}

    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    return result.get("ok", False), result


def main():
    if not SLACK_TOKEN:
        print("❌ SLACK_USER_TOKEN not configured")
        return 1

    print("=" * 80)
    print("👥 ADD ALL MISSING REQUIRED MEMBERS TO SLACK CHANNELS")
    print("=" * 80)

    # Channels with missing members from audit #102
    missing_data = {
        "blockandbones-bitsafe": ["Dae Lee"],
        "incyt-bitsafe": ["Aki Balogh"],
        "nethermind-canton-bitsafe": ["Dae Lee"],
        "canton-launchnodes-bitsafe": ["Dae Lee"],
        "luganodes-bitsafe": ["Dae Lee"],
        "x-bitsafe": ["Gabi Tuinaite", "Dae Lee", "Sarah Flood"],
        "loxor-finance-bitsafe": ["Dae Lee", "Sarah Flood"],
    }

    print(f"\n📋 {len(missing_data)} channels need updates:")
    total_additions = sum(len(members) for members in missing_data.values())
    print(f"   {total_additions} total member additions needed\n")

    for channel_name, members in missing_data.items():
        print(f"  {channel_name}: {', '.join(members)}")

    print(
        f"\n📝 Add {total_additions} members to {len(missing_data)} channels? (yes/no): ",
        end="",
    )
    try:
        confirmation = input().strip().lower()
    except EOFError:
        confirmation = "yes"

    if confirmation != "yes":
        print(f"\n❌ Cancelled")
        return 1

    # Perform additions
    print(f"\n👥 Adding members...\n")

    success = 0
    already_in = 0
    errors = 0

    for channel_name, members in missing_data.items():
        print(f"📢 {channel_name}:")

        # Get channel ID
        channel_id = get_channel_by_name(channel_name)
        if not channel_id:
            print(f"  ❌ Channel not found")
            errors += len(members)
            continue

        for member_name in members:
            # Get member name without role
            name_only = (
                member_name.split(" (")[0] if "(" in member_name else member_name
            )
            user_id = REQUIRED_MEMBERS.get(name_only)

            if not user_id:
                print(f"  ❌ {member_name}: No Slack ID")
                errors += 1
                continue

            ok, result = invite_to_channel(channel_id, user_id)

            if ok:
                print(f"  ✅ {member_name}")
                success += 1
            else:
                error = result.get("error", "unknown")
                if error == "already_in_channel":
                    print(f"  ✓  {member_name} (already in)")
                    already_in += 1
                else:
                    print(f"  ❌ {member_name}: {error}")
                    errors += 1

        print()

    print("=" * 80)
    print(f"✅ Added {success} members")
    if already_in > 0:
        print(f"✓  {already_in} already in channels")
    if errors > 0:
        print(f"❌ {errors} errors")
    print("=" * 80)

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
