#!/usr/bin/env python3
"""
Add Sarah Flood to all BitSafe Slack channels
Uses Slack API directly to find and invite
"""

import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_TEAM_ID = "E09HEBXK4J3"  # BitSafe team ID
SARAH_SLACK_ID = "U0A1SQQKD33"  # Sarah Flood's Slack user ID


def get_all_channels():
    """Get all Slack channels"""
    url = "https://slack.com/api/conversations.list"
    headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
    params = {
        "team_id": SLACK_TEAM_ID,
        "exclude_archived": True,
        "limit": 1000,
    }

    response = requests.get(url, headers=headers, params=params)
    result = response.json()

    if not result.get("ok"):
        print(f"❌ Failed to get channels: {result.get('error')}")
        return []

    return result.get("channels", [])


def get_channel_members(channel_id):
    """Get members of a channel"""
    url = "https://slack.com/api/conversations.members"
    headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
    params = {"channel": channel_id}

    response = requests.get(url, headers=headers, params=params)
    result = response.json()

    if not result.get("ok"):
        return []

    return result.get("members", [])


def invite_to_channel(channel_id, user_id):
    """Invite user to channel"""
    url = "https://slack.com/api/conversations.invite"
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {"channel": channel_id, "users": user_id}

    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    return result.get("ok", False), result


def main():
    if not SLACK_BOT_TOKEN:
        print("❌ SLACK_BOT_TOKEN not configured")
        return 1

    print("=" * 80)
    print("👤 ADD SARAH FLOOD TO BITSAFE SLACK CHANNELS")
    print("=" * 80)

    # Get all channels
    print("\n🔍 Fetching Slack channels...")
    all_channels = get_all_channels()

    # Filter for BitSafe channels (contain "bitsafe" in name)
    bitsafe_channels = [
        ch for ch in all_channels if "bitsafe" in ch.get("name", "").lower()
    ]

    print(f"✅ Found {len(bitsafe_channels)} BitSafe channels")

    # Check which ones Sarah is not in
    channels_to_add = []
    print("\n🔍 Checking Sarah's membership...")

    for channel in bitsafe_channels:
        channel_id = channel["id"]
        channel_name = channel["name"]
        members = get_channel_members(channel_id)

        if SARAH_SLACK_ID not in members:
            channels_to_add.append(
                {"id": channel_id, "name": channel_name, "member_count": len(members)}
            )

    if not channels_to_add:
        print("\n✅ Sarah is already in all BitSafe channels!")
        return 0

    print(f"\n📋 Sarah needs to be added to {len(channels_to_add)} channels:\n")
    for ch in channels_to_add[:10]:  # Show first 10
        print(f"  - {ch['name']} ({ch['member_count']} members)")
    if len(channels_to_add) > 10:
        print(f"  ... and {len(channels_to_add) - 10} more")

    # Confirm
    print(f"\n📝 Add Sarah to {len(channels_to_add)} channels? (yes/no): ", end="")
    try:
        confirmation = input().strip().lower()
    except EOFError:
        confirmation = "yes"  # Auto-confirm for non-interactive

    if confirmation != "yes":
        print(f"\n❌ Cancelled")
        return 1

    # Add Sarah to channels
    print(f"\n👤 Adding Sarah to {len(channels_to_add)} channels...\n")

    success = 0
    already_in = 0
    errors = 0

    for channel in channels_to_add:
        ok, result = invite_to_channel(channel["id"], SARAH_SLACK_ID)

        if ok:
            print(f"  ✅ {channel['name']}")
            success += 1
        else:
            error = result.get("error", "unknown")
            if error == "already_in_channel":
                print(f"  ✓  {channel['name']} (already in)")
                already_in += 1
            else:
                print(f"  ❌ {channel['name']}: {error}")
                errors += 1

    print("\n" + "=" * 80)
    print(f"✅ Added to {success} channels")
    if already_in > 0:
        print(f"✓  Already in {already_in} channels")
    if errors > 0:
        print(f"❌ {errors} errors")
    print("=" * 80)

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
