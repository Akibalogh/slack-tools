#!/usr/bin/env python3
"""
Verify Slack token has the necessary scopes for customer group audit.
"""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

def test_token():
    """Test if Slack token has necessary scopes"""
    token = os.getenv('SLACK_USER_TOKEN')
    
    if not token:
        print("❌ SLACK_USER_TOKEN not found in .env file")
        return False
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test 1: Token validity
    print("🔍 Testing token validity...")
    resp = requests.get('https://slack.com/api/auth.test', headers=headers)
    data = resp.json()
    
    if not data.get('ok'):
        print(f"❌ Token is invalid: {data.get('error')}")
        return False
    
    print(f"✅ Token is valid")
    print(f"   User: {data.get('user')}")
    print(f"   Team: {data.get('team')}")
    print(f"   Team ID: {data.get('team_id')}")
    
    # Test 2: Access to private channels
    # Use a known BitSafe customer channel ID
    test_channels = [
        ('C094JJMS5N3', 'lightshift-bitsafe'),
        ('C094P6Z76UB', 'copper-bitsafe'),
        ('C094NEL8CBX', 'vigilmarkets-bitsafe')
    ]
    
    print(f"\n🔍 Testing access to private customer channels...")
    success_count = 0
    
    for channel_id, channel_name in test_channels:
        resp = requests.get('https://slack.com/api/conversations.members', 
                           headers=headers,
                           params={'channel': channel_id})
        data = resp.json()
        
        if data.get('ok'):
            print(f"✅ Can access {channel_name}: {len(data.get('members', []))} members")
            success_count += 1
        else:
            error = data.get('error')
            if error == 'missing_scope':
                print(f"❌ {channel_name}: missing_scope")
                print(f"   Need to add groups:read and groups:history scopes")
            elif error == 'channel_not_found':
                print(f"⚠️  {channel_name}: channel not found (might not be a member)")
            else:
                print(f"❌ {channel_name}: {error}")
    
    if success_count == 0:
        print(f"\n❌ Cannot access any channels - scopes not yet added")
        print(f"\n📋 Follow these steps:")
        print(f"   1. Go to: https://api.slack.com/apps/A09AJJZF718/oauth")
        print(f"   2. Add 'groups:read' and 'groups:history' to User Token Scopes")
        print(f"   3. Click 'Reinstall your app' (yellow banner)")
        print(f"   4. Copy the new token and update .env file")
        print(f"   5. Run this script again to verify")
        return False
    elif success_count < len(test_channels):
        print(f"\n⚠️  Partial access: {success_count}/{len(test_channels)} channels")
        print(f"   Some channels may be in different workspace or you're not a member")
        print(f"   This is OK if you can access at least one channel")
        return True
    else:
        print(f"\n✅ SUCCESS! All test channels accessible")
        print(f"\n🎉 Token is ready for full audit")
        print(f"\nRun: python3 scripts/customer_group_audit.py")
        return True

if __name__ == "__main__":
    success = test_token()
    sys.exit(0 if success else 1)

