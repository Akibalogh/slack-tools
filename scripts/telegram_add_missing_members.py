#!/usr/bin/env python3
"""
Add missing required members to Telegram customer groups

Bug Fix (2025-12-04):
- Handles audit data where "Required Missing" field contains '-' as a placeholder
  (indicating no missing members). The script now filters out these groups and
  skips dashes/placeholders when parsing the missing members list.
"""

import argparse
import asyncio
import json
import os
import sys

import psycopg2
from dotenv import load_dotenv
from telethon import TelegramClient, functions
from telethon.errors import (
    ChatAdminRequiredError,
    FloodWaitError,
    UserAlreadyParticipantError,
    UserNotMutualContactError,
    UserPrivacyRestrictedError,
)
from telethon.sessions import StringSession
from telethon.tl.types import Channel, Chat

load_dotenv()

INTERNAL_CHANNELS = {
    "Addie <> BitSafe",
    "BitSafe 2025 Offsite",
    "BitSafe BD",
    "BitSafe Community",
    "BitSafe Company",
}


def get_latest_audit():
    """Get latest audit from database"""
    database_url = os.getenv("DATABASE_URL")
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, results_json FROM audit_runs
        WHERE status = 'completed' AND results_json IS NOT NULL
        ORDER BY completed_at DESC LIMIT 1
    """
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "data": json.loads(row[1])}


def get_required_members():
    """Get required members from database"""
    database_url = os.getenv("DATABASE_URL")
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT name, telegram_username FROM employees
        WHERE telegram_required = TRUE AND telegram_username IS NOT NULL
    """
    )
    members = {row[0]: row[1] for row in cursor.fetchall()}
    cursor.close()
    conn.close()
    return members


async def add_user_to_group(client, dialog, username):
    """Add user to group - matches telegram_admin.py approach"""
    try:
        user = await client.get_entity(username)
        entity = dialog.entity

        # Skip basic groups - they have API limitations
        if isinstance(entity, Chat):
            return True, "basic_group_skipped"

        # Only process Channels (supergroups/broadcast channels)
        if not isinstance(entity, Channel):
            return True, "unknown_type_skipped"

        # For supergroups/channels, use InviteToChannelRequest
        # Pass dialog.entity directly like telegram_admin.py does
        await client(
            functions.channels.InviteToChannelRequest(
                channel=entity, users=[user]
            )
        )
        return True, "added"
    except UserAlreadyParticipantError:
        return True, "already_member"
    except (
        ChatAdminRequiredError,
        UserPrivacyRestrictedError,
        UserNotMutualContactError,
    ):
        return False, "no_permission"
    except FloodWaitError as e:
        return False, f"rate_limited_{e.seconds}s"
    except Exception as e:
        error_msg = str(e)
        # Check for specific error types
        if "USER_ALREADY_PARTICIPANT" in error_msg:
            return True, "already_member"
        if "CHAT_ID_INVALID" in error_msg or "chat ID is not a valid" in error_msg:
            # Try to get fresh entity and retry once
            try:
                fresh_entity = await client.get_entity(dialog.title)
                if isinstance(fresh_entity, Channel):
                    await client(
                        functions.channels.InviteToChannelRequest(
                            channel=fresh_entity, users=[user]
                        )
                    )
                    return True, "added"
            except:
                pass
            return False, "invalid_chat_id"
        return False, error_msg[:60]


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-y", "--yes", action="store_true")
    args = parser.parse_args()

    print("=" * 80)
    print("👥 TELEGRAM ADD MISSING MEMBERS")
    print("=" * 80)

    audit = get_latest_audit()
    required_members = get_required_members()
    print(f"\n✅ Audit #{audit['id']}, {len(required_members)} required members\n")

    telegram_groups = audit["data"].get("telegram_groups", [])
    groups_to_fix = []

    for group in telegram_groups:
        name = group.get("Group Name", "")
        category = group.get("Category", "")
        has_bitsafe = group.get("Has BitSafe Name", "")
        missing = group.get("Required Missing", "")
        permission = group.get("Admin Status", "")

        # Filter out dashes and empty values
        missing_clean = missing.strip() if missing else ""
        if (
            has_bitsafe == "✓ YES"
            and name not in INTERNAL_CHANNELS
            and category != "Internal"
            and missing_clean
            and missing_clean != "-"
            and ("Owner" in permission or "Admin" in permission)
        ):
            groups_to_fix.append({"name": name, "missing": missing})

    print(f"📋 {len(groups_to_fix)} groups need updates\n")

    if not args.yes:
        print("Type 'yes' to confirm: ", end="")
        if input().strip().lower() != "yes":
            return 1

    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cursor = conn.cursor()
    cursor.execute("SELECT session_string FROM telegram_audit_status WHERE id = 1")
    session_string = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    await client.connect()

    dialogs = await client.get_dialogs()
    group_dialogs = {d.title: d for d in dialogs}

    print("\n👥 Adding members...\n")
    success = error = 0

    for idx, group in enumerate(groups_to_fix, 1):
        print(f"[{idx}/{len(groups_to_fix)}] {group['name']}:")
        if group["name"] not in group_dialogs:
            print(f"  ⚠️  Not found")
            error += 1
            continue

        for missing_name in group["missing"].split(","):
            missing_name = missing_name.strip()
            # Skip empty values, dashes, or placeholders
            if not missing_name or missing_name == "-" or missing_name.lower() == "none":
                continue
            
            username = None
            for member_name, member_username in required_members.items():
                if (
                    member_name.lower() in missing_name.lower()
                    or missing_name.lower().split()[0] in member_name.lower()
                ):
                    username = member_username
                    break

            if not username:
                print(f"  ⚠️  {missing_name}: No username")
                error += 1
                continue

            ok, result = await add_user_to_group(
                client, group_dialogs[group["name"]], username
            )
            if ok:
                print(f"  ✅ {missing_name.split('(')[0].strip()}")
                success += 1
            else:
                print(f"  ❌ {missing_name.split('(')[0].strip()}: {result}")
                error += 1

            await asyncio.sleep(2.0)

    await client.disconnect()
    print(f"\n{'='*80}\n✅ Added {success} members\n⚠️  {error} errors\n{'='*80}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
