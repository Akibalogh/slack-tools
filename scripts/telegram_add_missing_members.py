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
import time
from datetime import datetime, timedelta

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

try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

    # Fallback: simple progress display
    class tqdm:
        def __init__(self, *args, **kwargs):
            self.total = kwargs.get("total", 0)
            self.n = 0

        def update(self, n=1):
            self.n += n

        def set_description(self, desc):
            pass

        def close(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass


load_dotenv()

INTERNAL_CHANNELS = {
    "Addie <> BitSafe",
    "BitSafe 2025 Offsite",
    "BitSafe BD",
    "BitSafe Community",
    "BitSafe Company",
    "🇬🇧 BitSafe <> Ben W",
    "BitSafe <> Ben W",
    "Contribution Capital | BitSafe (New)",
}

# Groups that have been hacked/compromised (should be excluded)
HACKED_GROUPS = {
    "Contribution Capital <> BitSafe",  # Replaced by "Contribution Capital | BitSafe (New)"
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
            functions.channels.InviteToChannelRequest(channel=entity, users=[user])
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
            and name not in HACKED_GROUPS
            and category != "Internal"
            and missing_clean
            and missing_clean != "-"
            and ("Owner" in permission or "Admin" in permission)
        ):
            groups_to_fix.append({"name": name, "missing": missing})

    # Calculate total operations needed
    total_operations = 0
    for group in groups_to_fix:
        missing_list = [
            m.strip()
            for m in group["missing"].split(",")
            if m.strip() and m.strip() != "-"
        ]
        total_operations += len(missing_list)

    print(f"📋 {len(groups_to_fix)} groups need updates")
    print(f"📊 {total_operations} total member additions needed\n")

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

    # Statistics tracking
    stats = {
        "success": 0,
        "errors": 0,
        "rate_limited": 0,
        "no_permission": 0,
        "already_member": 0,
        "skipped": 0,
        "rate_limit_seconds": [],
        "operations_completed": 0,
        "start_time": time.time(),
    }

    # Initialize progress bar
    progress_bar = tqdm(
        total=total_operations,
        desc="Overall Progress",
        unit="ops",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
        disable=not TQDM_AVAILABLE,
    )

    for idx, group in enumerate(groups_to_fix, 1):
        group_name = group["name"]
        missing_list = [
            m.strip()
            for m in group["missing"].split(",")
            if m.strip() and m.strip() != "-"
        ]

        # Update progress bar description with current group
        if TQDM_AVAILABLE:
            group_short = (
                group_name[:35] + "..." if len(group_name) > 35 else group_name
            )
            progress_bar.set_description(
                f"Group {idx}/{len(groups_to_fix)}: {group_short}"
            )
        else:
            print(f"\n[{idx}/{len(groups_to_fix)}] {group_name}:")

        if group_name not in group_dialogs:
            if not TQDM_AVAILABLE:
                print(f"  ⚠️  Group not found")
            stats["errors"] += 1
            stats["operations_completed"] += len(missing_list)
            progress_bar.update(len(missing_list))
            continue

        for missing_name in missing_list:
            # Extract Telegram username from name like "Gabi Tui (Head of Product)"
            username = None
            for member_name, member_username in required_members.items():
                if (
                    member_name.lower() in missing_name.lower()
                    or missing_name.lower().split()[0] in member_name.lower()
                ):
                    username = member_username
                    break

            if not username:
                if not TQDM_AVAILABLE:
                    print(f"  ❌ {missing_name}: No username found")
                stats["errors"] += 1
                stats["operations_completed"] += 1
                progress_bar.update(1)
                continue

            op_start_time = time.time()
            ok, result = await add_user_to_group(
                client, group_dialogs[group_name], username
            )
            op_duration = time.time() - op_start_time

            stats["operations_completed"] += 1

            if ok:
                if result == "already_member":
                    if not TQDM_AVAILABLE:
                        print(
                            f"  ℹ️  {missing_name.split('(')[0].strip()}: Already member"
                        )
                    stats["already_member"] += 1
                elif "skipped" in result:
                    if not TQDM_AVAILABLE:
                        print(f"  ⏭️  {missing_name.split('(')[0].strip()}: {result}")
                    stats["skipped"] += 1
                else:
                    if not TQDM_AVAILABLE:
                        print(f"  ✅ {missing_name.split('(')[0].strip()}")
                    stats["success"] += 1
            else:
                if result.startswith("rate_limited"):
                    rate_seconds = int(result.split("_")[-1].rstrip("s"))
                    stats["rate_limited"] += 1
                    stats["rate_limit_seconds"].append(rate_seconds)
                    if not TQDM_AVAILABLE:
                        print(
                            f"  ⏱️  {missing_name.split('(')[0].strip()}: "
                            f"Rate limited ({rate_seconds}s)"
                        )
                elif result == "no_permission":
                    if not TQDM_AVAILABLE:
                        print(
                            f"  🔒 {missing_name.split('(')[0].strip()}: No permission"
                        )
                    stats["no_permission"] += 1
                else:
                    if not TQDM_AVAILABLE:
                        print(f"  ❌ {missing_name.split('(')[0].strip()}: {result}")
                stats["errors"] += 1

            progress_bar.update(1)

            # Calculate and update ETA
            elapsed = time.time() - stats["start_time"]
            if stats["operations_completed"] > 0:
                ops_per_sec = stats["operations_completed"] / elapsed
                remaining_ops = total_operations - stats["operations_completed"]
                eta_seconds = remaining_ops / ops_per_sec if ops_per_sec > 0 else 0

                # Update progress bar postfix with metrics
                success_rate = (
                    stats["success"] / stats["operations_completed"] * 100
                    if stats["operations_completed"] > 0
                    else 0
                )
                postfix_dict = {
                    "✅": stats["success"],
                    "❌": stats["errors"],
                    "Success": f"{success_rate:.1f}%",
                }
                if stats["rate_limited"] > 0:
                    postfix_dict["⏱️"] = stats["rate_limited"]
                progress_bar.set_postfix(postfix_dict)

            # Dynamic delay based on rate limits
            delay = 2.0
            if stats["rate_limit_seconds"]:
                avg_rate_limit = sum(stats["rate_limit_seconds"]) / len(
                    stats["rate_limit_seconds"]
                )
                if avg_rate_limit > 1000:  # > 16 minutes
                    delay = 5.0
                elif avg_rate_limit > 300:  # > 5 minutes
                    delay = 3.0
            await asyncio.sleep(delay)

    progress_bar.close()
    await client.disconnect()

    # Final statistics
    elapsed_total = time.time() - stats["start_time"]
    avg_rate_limit = (
        sum(stats["rate_limit_seconds"]) / len(stats["rate_limit_seconds"])
        if stats["rate_limit_seconds"]
        else 0
    )

    print("\n" + "=" * 80)
    print("📊 FINAL STATISTICS")
    print("=" * 80)
    print(f"✅ Successfully added: {stats['success']} members")
    print(f"ℹ️  Already members: {stats['already_member']}")
    print(f"⏭️  Skipped: {stats['skipped']}")
    print(f"⚠️  Errors: {stats['errors']}")
    print(f"   - Rate limited: {stats['rate_limited']}")
    print(f"   - No permission: {stats['no_permission']}")
    if avg_rate_limit > 0:
        print(
            f"   - Avg rate limit wait: {int(avg_rate_limit // 60)}m "
            f"{int(avg_rate_limit % 60)}s"
        )
    print(f"⏱️  Total time: {int(elapsed_total // 60)}m {int(elapsed_total % 60)}s")
    ops_per_sec = (
        stats["operations_completed"] / elapsed_total if elapsed_total > 0 else 0
    )
    print(f"📈 Operations/sec: {ops_per_sec:.2f}")
    success_rate = (
        stats["success"] / stats["operations_completed"] * 100
        if stats["operations_completed"] > 0
        else 0
    )
    print(f"📉 Success rate: {success_rate:.1f}%")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
