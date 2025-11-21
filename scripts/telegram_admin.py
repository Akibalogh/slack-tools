#!/usr/bin/env python3
"""
Generic Telegram Group Administration Tool

Unified tool for common Telegram group admin tasks:
- Search for users across groups
- Remove users from groups
- Check ownership/admin status
- Generate ownership transfer messages
- Rename groups in bulk

Usage:
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

import asyncio
import argparse
import json
from telethon import TelegramClient
from telethon.tl.functions.channels import EditTitleRequest
from telethon.tl.functions.messages import EditChatTitleRequest
from telethon.tl.types import Channel, Chat
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

api_id = os.getenv('TELEGRAM_API_ID')
api_hash = os.getenv('TELEGRAM_API_HASH')
phone = os.getenv('TELEGRAM_PHONE')
password = os.getenv('TELEGRAM_PASSWORD')


class TelegramAdmin:
    def __init__(self):
        self.client = None
        self.me = None
    
    async def connect(self):
        """Establish Telegram connection"""
        self.client = TelegramClient('telegram_session', api_id, api_hash)
        await self.client.start(phone=phone, password=password)
        self.me = await self.client.get_me()
        print(f'✅ Connected as: {self.me.first_name} {self.me.last_name}')
    
    async def disconnect(self):
        """Close Telegram connection"""
        if self.client:
            await self.client.disconnect()
    
    async def find_user(self, username):
        """Find all groups where a user is present"""
        print(f'🔍 Searching for @{username} in all groups...')
        print()
        
        groups = []
        checked = 0
        
        async for dialog in self.client.iter_dialogs():
            if not isinstance(dialog.entity, (Channel, Chat)):
                continue
            
            checked += 1
            
            try:
                participants = await self.client.get_participants(dialog.entity)
                
                user_found = any(hasattr(p, 'username') and p.username == username for p in participants)
                
                if user_found:
                    perms = await self.client.get_permissions(dialog.entity, self.me)
                    
                    if perms.is_creator:
                        status = '✅ Owner'
                    elif perms.is_admin and hasattr(perms, 'ban_users') and perms.ban_users:
                        status = '✅ Admin (can remove)'
                    else:
                        status = '❌ Member (need ownership)'
                    
                    groups.append({
                        'name': dialog.title,
                        'status': status,
                        'can_remove': '✅' in status
                    })
                    print(f'{status}: {dialog.title}')
            except:
                pass
        
        print()
        print('='*70)
        print(f'Checked {checked} groups')
        print(f'Found @{username} in: {len(groups)} groups')
        
        can_remove = [g for g in groups if g['can_remove']]
        cannot_remove = [g for g in groups if not g['can_remove']]
        
        print(f'✅ You can remove from: {len(can_remove)} groups')
        print(f'❌ Need ownership: {len(cannot_remove)} groups')
        
        # Save report
        if groups:
            df = pd.DataFrame(groups)
            output_file = f'output/user_search_{username}.xlsx'
            df.to_excel(output_file, index=False)
            print(f'\n📄 Report saved: {output_file}')
        
        return groups
    
    async def remove_user(self, username, groups=None):
        """Remove a user from specified groups or all groups where you have permission"""
        print(f'🔄 Removing @{username}...')
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
                    if hasattr(p, 'username') and p.username == username:
                        user = p
                        break
                
                if not user:
                    continue
                
                # Check if we have permission
                my_perms = await self.client.get_permissions(dialog.entity, self.me)
                if not (my_perms.is_creator or (my_perms.is_admin and hasattr(my_perms, 'ban_users') and my_perms.ban_users)):
                    failed.append((dialog.title, 'No permission'))
                    continue
                
                # Remove user
                await self.client.kick_participant(dialog.entity, user)
                success.append(dialog.title)
                print(f'✅ Removed from: {dialog.title}')
                
            except Exception as e:
                failed.append((dialog.title, str(e)[:60]))
                print(f'❌ Failed: {dialog.title} - {str(e)[:60]}')
        
        print()
        print('='*70)
        print(f'✅ Removed from: {len(success)} groups')
        print(f'❌ Failed: {len(failed)} groups')
        
        return success, failed
    
    async def get_group_owners(self, group_names):
        """Get owner info for specified groups"""
        print(f'🔍 Finding owners for {len(group_names)} groups...')
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
                    owner_handle = f'@{owner.username}' if owner.username else owner.first_name
                    messages.append({
                        'group': dialog.title,
                        'owner': owner_handle,
                        'message': f'Hi {owner_handle} - could you transfer ownership to me?'
                    })
                    print(f'✅ {dialog.title} → {owner_handle}')
                else:
                    print(f'⚠️  {dialog.title}: Owner not found')
            except Exception as e:
                print(f'❌ {dialog.title}: {str(e)[:50]}')
        
        print()
        print('='*70)
        print('📨 OWNERSHIP TRANSFER MESSAGES:')
        print('='*70)
        for m in messages:
            print(f'\n**{m["group"]}**')
            print(f'   {m["message"]}')
        
        # Save to file
        with open('output/ownership_requests.txt', 'w') as f:
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
            print('❌ No rename mapping provided')
            return
        
        print(f'🔄 Renaming {len(rename_map)} groups...')
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
                    await self.client(EditTitleRequest(channel=dialog.entity, title=new_name))
                elif isinstance(dialog.entity, Chat):
                    await self.client(EditChatTitleRequest(chat_id=dialog.entity.id, title=new_name))
                else:
                    failed.append((old_name, "Unsupported chat type"))
                    continue
                
                success.append((old_name, new_name))
                print(f'✅ {old_name} → {new_name}')
                
                await asyncio.sleep(1)  # Rate limiting
                
            except Exception as e:
                error_msg = str(e)
                if 'wait' in error_msg.lower():
                    print(f'⏸️  Rate limited: {old_name}')
                    failed.append((old_name, 'Rate limited'))
                else:
                    print(f'❌ Failed: {old_name} - {error_msg[:60]}')
                    failed.append((old_name, error_msg[:60]))
        
        print()
        print('='*70)
        print(f'✅ Renamed: {len(success)} groups')
        print(f'❌ Failed: {len(failed)} groups')
        
        return success, failed


async def main():
    parser = argparse.ArgumentParser(description='Telegram Group Administration Tool')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Find user command
    find_parser = subparsers.add_parser('find-user', help='Find a user across groups')
    find_parser.add_argument('--username', required=True, help='Telegram username (without @)')
    
    # Remove user command
    remove_parser = subparsers.add_parser('remove-user', help='Remove a user from groups')
    remove_parser.add_argument('--username', required=True, help='Telegram username (without @)')
    remove_parser.add_argument('--groups', help='File with group names (one per line)')
    
    # Request ownership command
    owner_parser = subparsers.add_parser('request-ownership', help='Generate ownership transfer messages')
    owner_parser.add_argument('--groups', required=True, help='File with group names (one per line)')
    
    # Rename command
    rename_parser = subparsers.add_parser('rename', help='Rename groups')
    rename_group = rename_parser.add_mutually_exclusive_group(required=True)
    rename_group.add_argument('--mapping', help='JSON file with old_name: new_name mapping')
    rename_group.add_argument('--pattern', help='Pattern to search for (use with --replace)')
    rename_parser.add_argument('--replace', help='Replacement string (use with --pattern)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    admin = TelegramAdmin()
    
    try:
        await admin.connect()
        
        if args.command == 'find-user':
            await admin.find_user(args.username)
        
        elif args.command == 'remove-user':
            groups = None
            if args.groups:
                with open(args.groups, 'r') as f:
                    groups = [line.strip() for line in f if line.strip()]
            await admin.remove_user(args.username, groups)
        
        elif args.command == 'request-ownership':
            with open(args.groups, 'r') as f:
                group_names = [line.strip() for line in f if line.strip()]
            await admin.get_group_owners(group_names)
        
        elif args.command == 'rename':
            if args.mapping:
                with open(args.mapping, 'r') as f:
                    rename_map = json.load(f)
                await admin.rename_groups(rename_map=rename_map)
            elif args.pattern and args.replace:
                await admin.rename_groups(pattern=args.pattern, replace=args.replace)
        
    finally:
        await admin.disconnect()


if __name__ == '__main__':
    asyncio.run(main())

