#!/usr/bin/env python3
"""
Check which BitSafe channels the User Offboarding Tool bot is NOT in yet
Outputs a list for manual bot additions
"""

import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

SLACK_USER_TOKEN = os.getenv("SLACK_USER_TOKEN")  # To see all channels
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
BOT_USER_ID = "U09PM14F1LP"  # user_offboarding_tool bot ID


def get_all_channels(token):
    """Get all BitSafe channels"""
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
            print(f"❌ Error: {result.get('error')}")
            return []

        all_channels.extend(result.get("channels", []))
        cursor = result.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break

    # Filter for BitSafe channels
    bitsafe_channels = [
        ch for ch in all_channels if "bitsafe" in ch.get("name", "").lower()
    ]

    return bitsafe_channels


def get_channel_members(channel_id, token):
    """Get members of a channel"""
    url = "https://slack.com/api/conversations.members"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"channel": channel_id}

    response = requests.get(url, headers=headers, params=params)
    result = response.json()

    if not result.get("ok"):
        return None

    return result.get("members", [])


def main():
    print("=" * 80)
    print("🤖 BOT CHANNEL COVERAGE CHECK")
    print("=" * 80)

    # Get all BitSafe channels
    print("\n🔍 Fetching all BitSafe channels...")
    channels = get_all_channels(SLACK_USER_TOKEN)

    if not channels:
        print("❌ Could not fetch channels")
        return 1

    print(f"✅ Found {len(channels)} BitSafe channels\n")

    # Check which ones the bot is in
    print("🤖 Checking bot membership...")

    bot_in = []
    bot_not_in = []

    for channel in channels:
        channel_id = channel["id"]
        channel_name = channel["name"]

        members = get_channel_members(channel_id, SLACK_USER_TOKEN)

        if members is None:
            print(f"  ⚠️  {channel_name}: Cannot check membership")
            continue

        if BOT_USER_ID in members:
            bot_in.append(channel_name)
        else:
            bot_not_in.append(channel_name)

    print(f"\n📊 Bot Coverage:")
    print(f"  ✅ Bot IS in: {len(bot_in)} channels")
    print(f"  ❌ Bot NOT in: {len(bot_not_in)} channels\n")

    if not bot_not_in:
        print(
            "🎉 Bot is in ALL BitSafe channels! You're ready to use bot-based member management."
        )
        return 0

    print("📋 Bot needs to be added to these channels:\n")
    for i, channel_name in enumerate(bot_not_in, 1):
        print(f"  {i}. {channel_name}")

    # Save to file
    with open("/tmp/bot_missing_channels.txt", "w") as f:
        for channel_name in bot_not_in:
            f.write(f"{channel_name}\n")

    print(f"\n✅ List saved to: /tmp/bot_missing_channels.txt")
    print("\n" + "=" * 80)
    print("📝 NEXT STEPS:")
    print("=" * 80)
    print("\n1. Add the bot to these channels:")
    print("   - In Slack, go to each channel")
    print("   - Click channel name → Integrations → Add apps")
    print("   - Search for 'User Offboarding Tool'")
    print("   - Click 'Add'")
    print("\n2. Run this script again to verify")
    print("\n3. Once bot is in all channels, run:")
    print("   python scripts/bot_add_missing_members.py")
    print("\n" + "=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
