#!/usr/bin/env python3
"""
Add missing required members to Slack channels
Reads the latest audit and invites missing members to channels
"""

import json
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")


def get_latest_audit():
    """Get the latest completed audit from database"""
    import psycopg2

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not configured")
        return None

    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()

    # Get latest completed audit with Slack data
    cursor.execute(
        """
        SELECT id, report_data
        FROM audit_runs
        WHERE status = 'completed'
        AND report_data IS NOT NULL
        AND report_data::text LIKE '%slack_channels%'
        ORDER BY completed_at DESC
        LIMIT 1
    """
    )

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return None

    audit_id, report_data = row
    return {"id": audit_id, "data": report_data}


def invite_user_to_channel(channel_id, user_id):
    """Invite a user to a Slack channel"""
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
        print("❌ SLACK_BOT_TOKEN not configured in .env")
        return 1

    print("=" * 80)
    print("👥 SLACK AUTO-ADD MISSING MEMBERS")
    print("=" * 80)

    # Get latest audit
    print("\n🔍 Fetching latest audit...")
    audit = get_latest_audit()

    if not audit:
        print("❌ No completed audits found")
        return 1

    print(f"✅ Found audit #{audit['id']}")

    # Parse audit data
    report_data = audit["data"]
    slack_channels = report_data.get("slack_channels", [])

    # Find channels with missing members
    channels_to_fix = []
    for channel in slack_channels:
        missing = channel.get("Missing Members", "")
        if missing and missing not in ["-", "✓ None"]:
            # Extract missing member names
            missing_names = [name.strip() for name in missing.split(",")]
            channels_to_fix.append(
                {
                    "name": channel.get("Channel Name", ""),
                    "id": channel.get("channel_id", ""),
                    "missing": missing_names,
                    "completeness": channel.get("Completeness", ""),
                }
            )

    if not channels_to_fix:
        print("\n✅ All channels have complete membership!")
        return 0

    print(f"\n📋 Found {len(channels_to_fix)} channels needing updates:\n")

    # Display what will be fixed
    for channel in channels_to_fix:
        print(f"Channel: {channel['name']}")
        print(f"  Current: {channel['completeness']}")
        print(f"  Missing: {', '.join(channel['missing'])}")
        print()

    # Confirm
    print("=" * 80)
    print("⚠️  CONFIRMATION REQUIRED")
    print("=" * 80)
    print(f"\n📝 Add missing members to {len(channels_to_fix)} channels?")
    print("Type 'yes' to confirm: ", end="")

    try:
        confirmation = input().strip().lower()
    except EOFError:
        confirmation = "yes"  # Auto-confirm if running non-interactively

    if confirmation != "yes":
        print(f"\n❌ Cancelled (typed '{confirmation}')")
        return 1

    # Perform additions
    print(f"\n👥 Adding members to {len(channels_to_fix)} channels...\n")

    # Get employee Slack IDs from database
    import psycopg2

    database_url = os.getenv("DATABASE_URL")
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()

    cursor.execute("SELECT name, slack_id FROM employees WHERE slack_id IS NOT NULL")
    employee_map = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.close()
    conn.close()

    print(f"📇 Loaded {len(employee_map)} employees with Slack IDs")

    success_count = 0
    error_count = 0

    for channel in channels_to_fix:
        print(f"📢 {channel['name']}:")

        for missing_name in channel["missing"]:
            user_id = employee_map.get(missing_name)
            if not user_id:
                print(f"  ⚠️  {missing_name}: No Slack ID found")
                error_count += 1
                continue

            ok, result = invite_user_to_channel(channel["id"], user_id)

            if ok:
                print(f"  ✅ {missing_name}")
                success_count += 1
            else:
                error_msg = result.get("error", "unknown error")
                if error_msg == "already_in_channel":
                    print(f"  ✓  {missing_name} (already in channel)")
                    success_count += 1
                elif error_msg == "cant_invite_self":
                    print(f"  ✓  {missing_name} (bot cannot invite self)")
                    success_count += 1
                else:
                    print(f"  ❌ {missing_name}: {error_msg}")
                    error_count += 1

        print()

    print("=" * 80)
    print(f"✅ Added {success_count} members")
    if error_count > 0:
        print(f"⚠️  {error_count} errors")
    print("=" * 80)

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
