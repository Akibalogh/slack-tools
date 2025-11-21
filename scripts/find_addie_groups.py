#!/usr/bin/env python3
"""
Find Telegram Groups with Addie

Identifies all Telegram groups where Addie is a member,
checks if Aki is the owner, and prepares messages for ownership transfer.
"""

import asyncio
from telethon import TelegramClient
from telethon.tl.functions.channels import GetParticipantsRequest, GetFullChannelRequest
from telethon.tl.functions.messages import GetFullChatRequest
from telethon.tl.types import ChannelParticipantsSearch, Channel, Chat
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

api_id = os.getenv('TELEGRAM_API_ID')
api_hash = os.getenv('TELEGRAM_API_HASH')
phone = os.getenv('TELEGRAM_PHONE')
password = os.getenv('TELEGRAM_PASSWORD')

# Addie's Telegram username (without @)
ADDIE_USERNAME = "NonFungibleAmy"

async def find_addie_groups():
    """Find all groups where Addie is a member and check Aki's ownership status"""
    
    client = TelegramClient('anon', api_id, api_hash)
    await client.start(phone=phone, password=password)
    
    print('🔍 Telegram Group Analysis: Finding Addie')
    print('='*70)
    
    # Get current user (Aki)
    me = await client.get_me()
    print(f'Analyzing groups for: {me.first_name} {me.last_name}')
    print()
    
    groups_with_addie = []
    groups_without_addie = []
    
    # Iterate through all dialogs (groups)
    async for dialog in client.iter_dialogs():
        # Only process groups/channels, not private chats
        if not isinstance(dialog.entity, (Channel, Chat)):
            continue
        
        group_name = dialog.title
        entity = dialog.entity
        
        try:
            # Get all participants
            participants = await client.get_participants(entity)
            
            # Check if Addie is in the group
            addie_present = False
            for p in participants:
                if hasattr(p, 'username') and p.username == ADDIE_USERNAME:
                    addie_present = True
                    break
            
            if not addie_present:
                groups_without_addie.append(group_name)
                continue
            
            # Addie is present - check Aki's permissions
            aki_perms = await client.get_permissions(entity, me)
            
            # Determine ownership/admin status
            if aki_perms.is_creator:
                status = "✅ Owner (can remove)"
            elif aki_perms.is_admin:
                if hasattr(aki_perms, 'ban_users') and aki_perms.ban_users:
                    status = "✅ Admin (can remove)"
                else:
                    status = "⚠️ Admin (cannot remove)"
            else:
                status = "❌ Member (cannot remove)"
            
            # Get group owner info
            owner_info = "Unknown"
            try:
                if isinstance(entity, Channel):
                    full = await client(GetFullChannelRequest(entity))
                    # Get creator from participants
                    all_participants = await client.get_participants(entity, filter=ChannelParticipantsSearch(''))
                    for p in all_participants:
                        perms = await client.get_permissions(entity, p)
                        if perms.is_creator:
                            owner_info = f"@{p.username}" if p.username else f"{p.first_name}"
                            break
                elif isinstance(entity, Chat):
                    full = await client(GetFullChatRequest(entity.id))
                    # For regular groups, check creator_id
                    if hasattr(full.full_chat, 'participants'):
                        for p in full.full_chat.participants.participants:
                            if hasattr(p, 'inviter_id') and p.inviter_id == entity.creator_id:
                                # Get user info
                                user = await client.get_entity(p.user_id)
                                owner_info = f"@{user.username}" if user.username else f"{user.first_name}"
                                break
            except Exception as e:
                owner_info = f"Error: {str(e)[:30]}"
            
            groups_with_addie.append({
                "Group Name": group_name,
                "Aki's Status": status,
                "Group Owner": owner_info,
                "Member Count": len(participants)
            })
            
            print(f'{"✅" if "can remove" in status else "❌"} {group_name}')
            print(f'   Aki: {status}')
            print(f'   Owner: {owner_info}')
            print()
            
        except Exception as e:
            print(f'⚠️  Error checking {group_name}: {str(e)[:50]}')
            continue
    
    await client.disconnect()
    
    # Generate report
    print()
    print('='*70)
    print('📊 SUMMARY')
    print('='*70)
    print(f'Groups WITH Addie: {len(groups_with_addie)}')
    print(f'Groups WITHOUT Addie: {len(groups_without_addie)}')
    print()
    
    if groups_with_addie:
        df = pd.DataFrame(groups_with_addie)
        
        # Count by status
        can_remove = df[df["Aki's Status"].str.contains("can remove")]
        cannot_remove = df[~df["Aki's Status"].str.contains("can remove")]
        
        print(f'✅ Can remove Addie: {len(can_remove)} groups')
        print(f'❌ Cannot remove Addie: {len(cannot_remove)} groups')
        print()
        
        # Save to Excel
        output_file = 'output/addie_groups_analysis.xlsx'
        df.to_excel(output_file, index=False)
        print(f'📄 Full report saved: {output_file}')
        print()
        
        # Generate ownership transfer messages
        if len(cannot_remove) > 0:
            print('='*70)
            print('📨 OWNERSHIP TRANSFER MESSAGES')
            print('='*70)
            print('For groups where you need ownership, send these messages:')
            print()
            
            for _, row in cannot_remove.iterrows():
                if row["Group Owner"] != "Unknown" and row["Group Owner"].startswith("@"):
                    print(f'**{row["Group Name"]}**')
                    print(f'   Message: Hi {row["Group Owner"]} - could you transfer ownership to me?')
                    print()

if __name__ == '__main__':
    asyncio.run(find_addie_groups())

