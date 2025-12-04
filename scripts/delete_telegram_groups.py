#!/usr/bin/env python3
"""
Leave specific Telegram groups
- If Owner: Deletes the group permanently (cannot be undone)
- If Member/Admin: Leaves the group (group continues for others)
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

    # Connect without prompting for auth (use saved session only)
    await client.connect()
    if not await client.is_user_authorized():
        print(
            "❌ Telegram session expired! Please run an audit first to refresh session."
        )
        await client.disconnect()
        return

    print("=" * 80)
    print("📤 TELEGRAM GROUP LEAVE TOOL")
    print("=" * 80)
    print(f"\n🎯 Groups to leave: {len(GROUPS_TO_DELETE)}")
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
                        can_delete = True  # Owner can delete
                    elif perms.is_admin:
                        admin_status = "Admin"
                        can_delete = True  # Admin can leave
                    else:
                        admin_status = "Member"
                        can_delete = True  # Member can leave
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
        if group["admin_status"] == "Owner":
            print(f"  Action: ⚠️  DELETE group (permanent)")
        else:
            print(f"  Action: 📤 LEAVE group (group stays for others)")
        print()

    print("=" * 80)
    print("⚠️  CONFIRMATION REQUIRED")
    print("=" * 80)
    print("\n📤 You will LEAVE these groups:")
    for group in found_groups:
        action = (
            "DELETE (permanent)"
            if group["admin_status"] == "Owner"
            else "LEAVE (continues for others)"
        )
        print(f"   - {group['name']} → {action}")
    print(f"\n📝 To confirm, type: yes")
    print()

    confirmation = input("Confirmation: ").strip().lower()

    if confirmation != "yes":
        print(f"\n❌ Cancelled (you typed '{confirmation}', expected 'yes')")
        await client.disconnect()
        return

    # Perform leave/delete actions
    print(f"\n📤 Leaving {len(found_groups)} groups...\n")

    for group in found_groups:
        action = "Deleting" if group["admin_status"] == "Owner" else "Leaving"
        try:
            await client.delete_dialog(group["entity"])
            emoji = "🗑️" if group["admin_status"] == "Owner" else "📤"
            print(f"{emoji} {action}: {group['name']}")
        except Exception as e:
            print(f"❌ Failed to {action.lower()} {group['name']}: {e}")

    print(f"\n✅ Process complete!")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
