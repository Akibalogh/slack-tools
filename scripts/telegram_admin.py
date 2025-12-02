#!/usr/bin/env python3
"""
Generic Telegram Group Administration Tool

Unified tool for common Telegram group admin tasks:
- Add users to groups
- Search for users across groups
- Remove users from groups
- Check ownership/admin status
- Generate ownership transfer messages
- Rename groups in bulk

Usage:
    # Add users to all groups (dry run)
    python3 telegram_admin.py add-user --usernames kevin,aliya --dry-run

    # Add users to all groups (live)
    python3 telegram_admin.py add-user --usernames kevin,aliya

    # Find a user
    python3 telegram_admin.py find-user --username nftaddie

    # Remove a user from groups
    python3 telegram_admin.py remove-user --username nftaddie

    # Generate ownership transfer messages
    python3 telegram_admin.py request-ownership --groups groups.txt

    # Rename groups from JSON mapping
    python3 telegram_admin.py rename --mapping renames.json

    # Search and replace in group names
    python3 telegram_admin.py rename --pattern "old" --replace "new"
"""

import argparse
import asyncio
import json
import os

import pandas as pd
from dotenv import load_dotenv
from telethon import TelegramClient, functions
from telethon.tl.functions.channels import EditTitleRequest
from telethon.tl.functions.messages import EditChatTitleRequest
from telethon.tl.types import Channel, Chat

load_dotenv()

api_id = os.getenv("TELEGRAM_API_ID")
api_hash = os.getenv("TELEGRAM_API_HASH")
phone = os.getenv("TELEGRAM_PHONE")
password = os.getenv("TELEGRAM_PASSWORD")


class TelegramAdmin:
    def __init__(self):
        self.client = None
        self.me = None

    async def connect(self):
        """Establish Telegram connection"""
        self.client = TelegramClient("telegram_session", api_id, api_hash)
        await self.client.connect()

        if not await self.client.is_user_authorized():
            # Need to authenticate
            await self.client.send_code_request(phone)

            code = os.getenv("TELEGRAM_CODE")
            if not code:
                code = input("Enter the code you received: ")
            else:
                print(f"📱 Using code from TELEGRAM_CODE environment variable")

            try:
                await self.client.sign_in(phone, code)
            except Exception as e:
                if "SessionPasswordNeededError" in str(type(e).__name__):
                    pwd = os.getenv("TELEGRAM_PASSWORD")
                    if not pwd:
                        pwd = input("Enter your 2FA password: ")
                    else:
                        print(
                            f"🔐 Using password from TELEGRAM_PASSWORD environment variable"
                        )
                    await self.client.sign_in(password=pwd)
                else:
                    raise

        self.me = await self.client.get_me()
        print(f"✅ Connected as: {self.me.first_name} {self.me.last_name}")

    async def disconnect(self):
        """Close Telegram connection"""
        if self.client:
            await self.client.disconnect()

    async def find_user(self, username):
        """Find all groups where a user is present"""
        print(f"🔍 Searching for @{username} in all groups...")
        print()

        groups = []
        checked = 0

        async for dialog in self.client.iter_dialogs():
            if not isinstance(dialog.entity, (Channel, Chat)):
                continue

            checked += 1

            try:
                participants = await self.client.get_participants(dialog.entity)

                user_found = any(
                    hasattr(p, "username") and p.username == username
                    for p in participants
                )

                if user_found:
                    perms = await self.client.get_permissions(dialog.entity, self.me)

                    if perms.is_creator:
                        status = "✅ Owner"
                    elif (
                        perms.is_admin
                        and hasattr(perms, "ban_users")
                        and perms.ban_users
                    ):
                        status = "✅ Admin (can remove)"
                    else:
                        status = "❌ Member (need ownership)"

                    groups.append(
                        {
                            "name": dialog.title,
                            "status": status,
                            "can_remove": "✅" in status,
                        }
                    )
                    print(f"{status}: {dialog.title}")
            except:
                pass

        print()
        print("=" * 70)
        print(f"Checked {checked} groups")
        print(f"Found @{username} in: {len(groups)} groups")

        can_remove = [g for g in groups if g["can_remove"]]
        cannot_remove = [g for g in groups if not g["can_remove"]]

        print(f"✅ You can remove from: {len(can_remove)} groups")
        print(f"❌ Need ownership: {len(cannot_remove)} groups")

        # Save report
        if groups:
            df = pd.DataFrame(groups)
            output_file = f"output/user_search_{username}.xlsx"
            df.to_excel(output_file, index=False)
            print(f"\n📄 Report saved: {output_file}")

        return groups

    async def add_users(self, usernames, dry_run=False):
        """Add users to all groups where you have admin permission"""
        print(
            f'🔄 {"[DRY RUN] " if dry_run else ""}Adding users: {", ".join(usernames)}...'
        )
        print()

        # Resolve usernames to user entities
        users_to_add = []
        for username in usernames:
            try:
                user = await self.client.get_entity(username)
                users_to_add.append((username, user))
                print(f"✅ Found @{username}")
            except Exception as e:
                print(f"❌ Could not find @{username}: {e}")

        if not users_to_add:
            print("❌ No valid users to add")
            return [], []

        print()
        print("=" * 70)
        print(f"Processing groups...")
        print()

        success = []
        already_member = []
        failed = []
        no_permission = []

        checked = 0
        async for dialog in self.client.iter_dialogs():
            if not isinstance(dialog.entity, (Channel, Chat)):
                continue

            checked += 1
            if checked % 50 == 0:
                print(f"   Processed {checked} groups...")

            # Check if we have permission
            try:
                my_perms = await self.client.get_permissions(dialog.entity, self.me)
                if not (
                    my_perms.is_creator
                    or (
                        my_perms.is_admin
                        and hasattr(my_perms, "invite_users")
                        and my_perms.invite_users
                    )
                ):
                    no_permission.append(dialog.title)
                    continue

                # Get current participants to check membership
                participants = await self.client.get_participants(dialog.entity)
                participant_ids = {p.id for p in participants}

                # Try to add each user
                for username, user in users_to_add:
                    try:
                        if user.id in participant_ids:
                            already_member.append((dialog.title, username))
                            continue

                        if dry_run:
                            print(
                                f"   [DRY RUN] Would add @{username} to {dialog.title}"
                            )
                            success.append((dialog.title, username))
                        else:
                            await self.client(
                                functions.channels.InviteToChannelRequest(
                                    channel=dialog.entity, users=[user]
                                )
                            )
                            success.append((dialog.title, username))
                            print(f"   ✅ Added @{username} to {dialog.title}")
                            await asyncio.sleep(1)  # Rate limiting

                    except Exception as e:
                        error_msg = str(e)[:60]
                        if "USER_ALREADY_PARTICIPANT" in error_msg:
                            already_member.append((dialog.title, username))
                        else:
                            failed.append((dialog.title, username, error_msg))
                            if not dry_run:
                                print(
                                    f"   ❌ Failed to add @{username} to {dialog.title}: {error_msg}"
                                )

            except Exception as e:
                # Skip groups where we can't check permissions
                continue

        print()
        print("=" * 70)
        print("📊 SUMMARY")
        print("=" * 70)
        print(f"Total groups checked: {checked}")
        print(f"✅ Successfully added: {len(success)}")
        print(f"ℹ️  Already members: {len(already_member)}")
        print(f"❌ Failed: {len(failed)}")
        print(f"🔒 No permission: {len(no_permission)}")

        # Save detailed results
        if not dry_run:
            with open("output/telegram_member_addition.txt", "w") as f:
                f.write("TELEGRAM MEMBER ADDITION RESULTS\n")
                f.write("=" * 70 + "\n\n")
                f.write(f"Successfully Added ({len(success)}):\n")
                for group, user in success:
                    f.write(f"  {group} - @{user}\n")
                f.write(f"\nAlready Members ({len(already_member)}):\n")
                for group, user in already_member:
                    f.write(f"  {group} - @{user}\n")
                f.write(f"\nFailed ({len(failed)}):\n")
                for group, user, error in failed:
                    f.write(f"  {group} - @{user}: {error}\n")
                f.write(f"\nNo Permission ({len(no_permission)}):\n")
                for group in no_permission:
                    f.write(f"  {group}\n")
            print(f"\n📄 Detailed results saved: output/telegram_member_addition.txt")

        return success, failed

    async def remove_user(self, username, groups=None):
        """Remove a user from specified groups or all groups where you have permission"""
        print(f"🔄 Removing @{username}...")
        print()

        success = []
        failed = []

        async for dialog in self.client.iter_dialogs():
            if groups and dialog.title not in groups:
                continue

            if not isinstance(dialog.entity, (Channel, Chat)):
                continue

            try:
                # Find the user
                participants = await self.client.get_participants(dialog.entity)
                user = None
                for p in participants:
                    if hasattr(p, "username") and p.username == username:
                        user = p
                        break

                if not user:
                    continue

                # Check if we have permission
                my_perms = await self.client.get_permissions(dialog.entity, self.me)
                if not (
                    my_perms.is_creator
                    or (
                        my_perms.is_admin
                        and hasattr(my_perms, "ban_users")
                        and my_perms.ban_users
                    )
                ):
                    failed.append((dialog.title, "No permission"))
                    continue

                # Remove user
                await self.client.kick_participant(dialog.entity, user)
                success.append(dialog.title)
                print(f"✅ Removed from: {dialog.title}")

            except Exception as e:
                failed.append((dialog.title, str(e)[:60]))
                print(f"❌ Failed: {dialog.title} - {str(e)[:60]}")

        print()
        print("=" * 70)
        print(f"✅ Removed from: {len(success)} groups")
        print(f"❌ Failed: {len(failed)} groups")

        return success, failed

    async def get_group_owners(self, group_names):
        """Get owner info for specified groups"""
        print(f"🔍 Finding owners for {len(group_names)} groups...")
        print()

        messages = []

        async for dialog in self.client.iter_dialogs():
            if dialog.title not in group_names:
                continue

            try:
                participants = await self.client.get_participants(dialog.entity)

                owner = None
                for p in participants:
                    perms = await self.client.get_permissions(dialog.entity, p)
                    if perms.is_creator:
                        owner = p
                        break

                if owner:
                    owner_handle = (
                        f"@{owner.username}" if owner.username else owner.first_name
                    )
                    messages.append(
                        {
                            "group": dialog.title,
                            "owner": owner_handle,
                            "message": f"Hi {owner_handle} - could you transfer ownership to me?",
                        }
                    )
                    print(f"✅ {dialog.title} → {owner_handle}")
                else:
                    print(f"⚠️  {dialog.title}: Owner not found")
            except Exception as e:
                print(f"❌ {dialog.title}: {str(e)[:50]}")

        print()
        print("=" * 70)
        print("📨 OWNERSHIP TRANSFER MESSAGES:")
        print("=" * 70)
        for m in messages:
            print(f'\n**{m["group"]}**')
            print(f'   {m["message"]}')

        # Save to file
        with open("output/ownership_requests.txt", "w") as f:
            for m in messages:
                f.write(f'{m["group"]}\n')
                f.write(f'  {m["message"]}\n\n')

        return messages

    async def rename_groups(self, rename_map=None, pattern=None, replace=None):
        """Rename groups based on mapping or pattern replacement"""
        if pattern and replace:
            # Search and replace mode
            print(f'🔄 Replacing "{pattern}" with "{replace}" in group names...')
            rename_map = {}

            async for dialog in self.client.iter_dialogs():
                if pattern in dialog.title:
                    new_name = dialog.title.replace(pattern, replace)
                    rename_map[dialog.title] = new_name

        if not rename_map:
            print("❌ No rename mapping provided")
            return

        print(f"🔄 Renaming {len(rename_map)} groups...")
        print()

        success = []
        failed = []
        not_found = []

        async for dialog in self.client.iter_dialogs():
            if dialog.title not in rename_map:
                continue

            old_name = dialog.title
            new_name = rename_map[old_name]

            try:
                if isinstance(dialog.entity, Channel):
                    await self.client(
                        EditTitleRequest(channel=dialog.entity, title=new_name)
                    )
                elif isinstance(dialog.entity, Chat):
                    await self.client(
                        EditChatTitleRequest(chat_id=dialog.entity.id, title=new_name)
                    )
                else:
                    failed.append((old_name, "Unsupported chat type"))
                    continue

                success.append((old_name, new_name))
                print(f"✅ {old_name} → {new_name}")

                await asyncio.sleep(1)  # Rate limiting

            except Exception as e:
                error_msg = str(e)
                if "wait" in error_msg.lower():
                    print(f"⏸️  Rate limited: {old_name}")
                    failed.append((old_name, "Rate limited"))
                else:
                    print(f"❌ Failed: {old_name} - {error_msg[:60]}")
                    failed.append((old_name, error_msg[:60]))

        print()
        print("=" * 70)
        print(f"✅ Renamed: {len(success)} groups")
        print(f"❌ Failed: {len(failed)} groups")

        return success, failed


async def main():
    parser = argparse.ArgumentParser(description="Telegram Group Administration Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Add user command
    add_parser = subparsers.add_parser(
        "add-user", help="Add users to all groups where you have admin access"
    )
    add_parser.add_argument(
        "--usernames",
        required=True,
        help="Comma-separated list of Telegram usernames (without @)",
    )
    add_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    # Find user command
    find_parser = subparsers.add_parser("find-user", help="Find a user across groups")
    find_parser.add_argument(
        "--username", required=True, help="Telegram username (without @)"
    )

    # Remove user command
    remove_parser = subparsers.add_parser(
        "remove-user", help="Remove a user from groups"
    )
    remove_parser.add_argument(
        "--username", required=True, help="Telegram username (without @)"
    )
    remove_parser.add_argument("--groups", help="File with group names (one per line)")

    # Request ownership command
    owner_parser = subparsers.add_parser(
        "request-ownership", help="Generate ownership transfer messages"
    )
    owner_parser.add_argument(
        "--groups", required=True, help="File with group names (one per line)"
    )

    # Rename command
    rename_parser = subparsers.add_parser("rename", help="Rename groups")
    rename_group = rename_parser.add_mutually_exclusive_group(required=True)
    rename_group.add_argument(
        "--mapping", help="JSON file with old_name: new_name mapping"
    )
    rename_group.add_argument(
        "--pattern", help="Pattern to search for (use with --replace)"
    )
    rename_parser.add_argument(
        "--replace", help="Replacement string (use with --pattern)"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    admin = TelegramAdmin()

    try:
        await admin.connect()

        if args.command == "add-user":
            usernames = [u.strip() for u in args.usernames.split(",")]
            await admin.add_users(usernames, dry_run=args.dry_run)

        elif args.command == "find-user":
            await admin.find_user(args.username)

        elif args.command == "remove-user":
            groups = None
            if args.groups:
                with open(args.groups, "r") as f:
                    groups = [line.strip() for line in f if line.strip()]
            await admin.remove_user(args.username, groups)

        elif args.command == "request-ownership":
            with open(args.groups, "r") as f:
                group_names = [line.strip() for line in f if line.strip()]
            await admin.get_group_owners(group_names)

        elif args.command == "rename":
            if args.mapping:
                with open(args.mapping, "r") as f:
                    rename_map = json.load(f)
                await admin.rename_groups(rename_map=rename_map)
            elif args.pattern and args.replace:
                await admin.rename_groups(pattern=args.pattern, replace=args.replace)

    finally:
        await admin.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
