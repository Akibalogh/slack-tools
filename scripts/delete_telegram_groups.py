#!/usr/bin/env python3
"""
Delete specific Telegram groups permanently
⚠️ REQUIRES EXPLICIT CONFIRMATION - CANNOT BE UNDONE
"""

import asyncio
import os

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

load_dotenv()

# Groups to delete (EXPLICIT LIST - EXTRA CONFIRMATION REQUIRED)
GROUPS_TO_DELETE = [
    "Aki / Mayank",
    "PMM Interviews",
]


async def main():
    # Get Telegram credentials
    api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
    api_hash = os.getenv("TELEGRAM_API_HASH", "")
    phone = os.getenv("TELEGRAM_PHONE", "")

    if not all([api_id, api_hash, phone]):
        print("❌ Telegram credentials not configured")
        return

    # Use saved session from database (same as audits)
    import psycopg2

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        cursor.execute("SELECT session_string FROM telegram_audit_status WHERE id = 1")
        row = cursor.fetchone()
        session_string = row[0] if row else None
        cursor.close()
        conn.close()
    else:
        session_string = None

    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    await client.start(phone=phone)

    print("=" * 80)
    print("⚠️  TELEGRAM GROUP DELETION TOOL")
    print("=" * 80)
    print(f"\n🎯 Groups marked for deletion: {len(GROUPS_TO_DELETE)}")
    for group in GROUPS_TO_DELETE:
        print(f"   - {group}")

    # Find @mojo_onchain to get common chats
    try:
        mojo_user = await client.get_entity("mojo_onchain")
    except Exception as e:
        print(f"❌ Couldn't find @mojo_onchain: {e}")
        await client.disconnect()
        return

    # Get all dialogs (groups)
    print(f"\n🔍 Searching for groups...")
    found_groups = []

    async for dialog in client.iter_dialogs():
        if dialog.is_group or dialog.is_channel:
            group_name = dialog.title
            if group_name in GROUPS_TO_DELETE:
                # Get more details
                participants_count = getattr(
                    dialog.entity, "participants_count", "Unknown"
                )

                # Check our permissions
                try:
                    me = await client.get_me()
                    perms = await client.get_permissions(dialog.entity, me)
                    if perms.is_creator:
                        admin_status = "Owner"
                        can_delete = True
                    elif perms.is_admin:
                        admin_status = "Admin"
                        can_delete = False  # Admins can't delete groups, only owners
                    else:
                        admin_status = "Member"
                        can_delete = False
                except:
                    admin_status = "Unknown"
                    can_delete = False

                found_groups.append(
                    {
                        "name": group_name,
                        "entity": dialog.entity,
                        "members": participants_count,
                        "admin_status": admin_status,
                        "can_delete": can_delete,
                    }
                )

    print(f"\n📋 Found {len(found_groups)}/{len(GROUPS_TO_DELETE)} groups:\n")

    if not found_groups:
        print("❌ No groups found to delete!")
        await client.disconnect()
        return

    for group in found_groups:
        print(f"Group: {group['name']}")
        print(f"  Members: {group['members']}")
        print(f"  Your role: {group['admin_status']}")
        print(
            f"  Can delete: {'✅ YES' if group['can_delete'] else '❌ NO (need Owner)'}"
        )
        print()

    print("=" * 80)
    print("⚠️  CONFIRMATION REQUIRED")
    print("=" * 80)
    print("\n🚨 This will PERMANENTLY DELETE these Telegram groups!")
    print("🚨 This action CANNOT BE UNDONE!")
    print("🚨 All messages and history will be lost!")
    print(f"\n📝 To confirm, type: DELETE {len(found_groups)} GROUPS")
    print()

    confirmation = input("Confirmation: ").strip()

    if confirmation != f"DELETE {len(found_groups)} GROUPS":
        print("\n❌ Deletion cancelled (confirmation didn't match)")
        await client.disconnect()
        return

    print(f"\n⚠️  Final confirmation: Type 'I UNDERSTAND THIS IS PERMANENT'")
    final = input("Final confirmation: ").strip()

    if final != "I UNDERSTAND THIS IS PERMANENT":
        print("\n❌ Deletion cancelled (final confirmation didn't match)")
        await client.disconnect()
        return

    # Perform deletions
    print(f"\n🗑️  Deleting {len(found_groups)} groups...\n")

    for group in found_groups:
        if not group["can_delete"]:
            print(f"⚠️  Skipping {group['name']} (not Owner)")
            continue

        try:
            await client.delete_dialog(group["entity"])
            print(f"✅ Deleted: {group['name']}")
        except Exception as e:
            print(f"❌ Failed to delete {group['name']}: {e}")

    print(f"\n✅ Deletion process complete!")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
