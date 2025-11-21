#!/usr/bin/env python3
"""
Find @nftaddie (former employee) in Telegram groups
and identify which ones you can remove her from.
"""

import asyncio
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

api_id = os.getenv('TELEGRAM_API_ID')
api_hash = os.getenv('TELEGRAM_API_HASH')
phone = os.getenv('TELEGRAM_PHONE')
password = os.getenv('TELEGRAM_PASSWORD')

ADDIE_USERNAME = 'nftaddie'

async def find_addie():
    client = TelegramClient('telegram_session', api_id, api_hash)
    await client.start(phone=phone, password=password)
    
    print('🔍 Searching for @nftaddie in Telegram groups')
    print('='*70)
    
    me = await client.get_me()
    
    groups_with_addie = []
    total_checked = 0
    
    async for dialog in client.iter_dialogs():
        if not isinstance(dialog.entity, (Channel, Chat)):
            continue
        
        total_checked += 1
        
        try:
            participants = await client.get_participants(dialog.entity)
            
            # Check if Addie is present
            addie_present = False
            addie_user = None
            for p in participants:
                if hasattr(p, 'username') and p.username == ADDIE_USERNAME:
                    addie_present = True
                    addie_user = p
                    break
            
            if not addie_present:
                continue
            
            # Addie found - check my permissions
            my_perms = await client.get_permissions(dialog.entity, me)
            
            if my_perms.is_creator:
                status = '✅ Owner'
            elif my_perms.is_admin:
                if hasattr(my_perms, 'ban_users') and my_perms.ban_users:
                    status = '✅ Admin (can remove)'
                else:
                    status = '⚠️ Admin (no ban)'
            else:
                status = '❌ Member'
            
            groups_with_addie.append({
                'Group Name': dialog.title,
                'Your Status': status,
                'Can Remove': 'Owner' in status or 'can remove' in status,
                'Member Count': len(participants)
            })
            
            print(f'{status}: {dialog.title}')
            
        except Exception as e:
            continue
    
    await client.disconnect()
    
    print()
    print('='*70)
    print(f'Total groups checked: {total_checked}')
    print(f'Groups with @nftaddie: {len(groups_with_addie)}')
    print()
    
    can_remove = [g for g in groups_with_addie if g['Can Remove']]
    cannot_remove = [g for g in groups_with_addie if not g['Can Remove']]
    
    print(f'✅ You can remove Addie from: {len(can_remove)} groups')
    print(f'❌ Need ownership transfer for: {len(cannot_remove)} groups')
    print()
    
    if cannot_remove:
        print('GROUPS NEEDING OWNERSHIP TRANSFER:')
        print('-'*70)
        for g in cannot_remove:
            print(f'  ❌ {g["Group Name"]} ({g["Your Status"]})')
        print()
    
    # Save to Excel
    if groups_with_addie:
        df = pd.DataFrame(groups_with_addie)
        df.to_excel('output/nftaddie_removal_plan.xlsx', index=False)
        print(f'📄 Report saved: output/nftaddie_removal_plan.xlsx')

if __name__ == '__main__':
    asyncio.run(find_addie())

