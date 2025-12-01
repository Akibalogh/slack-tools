#!/usr/bin/env python3
"""
Customer Group Audit Tool

Audits Slack and Telegram customer groups to verify required and optional
team members are present.
"""

import asyncio
import aiohttp
import os
import json
from telethon import TelegramClient
from telethon.tl.functions.messages import GetCommonChatsRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import GetFullChatRequest
from telethon.tl.types import Channel, Chat
from datetime import datetime
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load group categorization
CATEGORIES_FILE = "config/customer_group_categories.json"
try:
    with open(CATEGORIES_FILE, 'r') as f:
        GROUP_CATEGORIES = json.load(f)
except FileNotFoundError:
    GROUP_CATEGORIES = {
        "marketing_groups": [],
        "internal_groups": [],
        "special_groups": {}
    }

# Slack configuration
SLACK_TOKEN = os.getenv("SLACK_USER_TOKEN")  # Use user token with groups:read/history scopes
BD_CHANNEL_ID = "C094Q9TUVUL"  # #business-development

if not SLACK_TOKEN:
    print("❌ SLACK_USER_TOKEN not found in .env file")
    exit(1)

# Telegram configuration (optional - script will skip Telegram audit if not provided)
try:
    TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
    TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
    TELEGRAM_ENABLED = TELEGRAM_API_ID > 0 and TELEGRAM_API_HASH
except (ValueError, TypeError):
    TELEGRAM_API_ID = 0
    TELEGRAM_API_HASH = ""
    TELEGRAM_ENABLED = False

# Team members for SLACK (all should be in Slack channels)
REQUIRED_SLACK_MEMBERS = {
    "akibalogh": "Aki Balogh (CEO)",
    "gabitui": "Gabi Tui (Head of Product)",
    "mojo_onchain": "Mayank (Sales Engineer)",
    "kadeemclarke": "Kadeem Clarke (Head of Growth)",
    "NonFungibleAmy": "Amy Wu (BD)",
    "kevin": "Kevin Huet",
    "aliya": "Aliya Gordon",
    "dave": "Dave Shin",
    "Dae_L": "Dae Lee (Sales Advisor)"
}

# Team members for TELEGRAM (core team only, not all members required)
REQUIRED_TELEGRAM_MEMBERS = {
    "akibalogh": "Aki Balogh (CEO)",
    "gabitui": "Gabi Tui (Head of Product)",
    "mojo_onchain": "Mayank (Sales Engineer)",
    "kadeemclarke": "Kadeem Clarke (Head of Growth)",
    "NonFungibleAmy": "Amy Wu (BD)"
}

# For backward compatibility
REQUIRED_MEMBERS = REQUIRED_SLACK_MEMBERS

OPTIONAL_MEMBERS = {
    "shin_novation": "Shin (Strategy Advisor)",
    "j_eisenberg": "Jesse Eisenberg (CTO)",
    "anmatusova": "Anna Matusova (VP Finance & Legal)",
    "Dae_L": "Dae (Sales Advisor)"
}

# Known Slack username mappings (from workspace)
SLACK_USERNAME_MAP = {
    "aki": "akibalogh",
    "gabi": "gabitui",
    "mayank": "mojo_onchain",
    "kadeem": "kadeemclarke",
    "amy": "NonFungibleAmy",
    "kevin": "kevin",
    "aliya": "aliya",
    "jesse": "j_eisenberg",
    "anna": "anmatusova",
    "dae": "Dae_L"
}

def categorize_group(group_name):
    """Determine group category and if it requires full team"""
    # Check marketing groups
    if any(mg.lower() in group_name.lower() for mg in GROUP_CATEGORIES.get("marketing_groups", [])):
        return "Marketing", False
    
    # Check internal groups
    if any(ig.lower() in group_name.lower() for ig in GROUP_CATEGORIES.get("internal_groups", [])):
        return "Internal", False
    
    # Check intro groups
    if any(intro.lower() in group_name.lower() for intro in GROUP_CATEGORIES.get("intro_groups", [])):
        return "Intro", False
    
    # Check special groups
    for special, note in GROUP_CATEGORIES.get("special_groups", {}).items():
        if special.lower() in group_name.lower():
            return f"Special ({note})", False
    
    # Default: BD Customer group requiring full team
    return "BD Customer", True

def needs_rename(group_name):
    """Check if group name contains iBTC and needs renaming"""
    return "iBTC" in group_name

class CustomerGroupAuditor:
    def __init__(self):
        self.slack_user_map = {}  # Maps Slack username -> user_id
        self.required_slack_ids = {}
        self.optional_slack_ids = {}
        self.audit_results = []
        
    async def get_slack_bd_members(self):
        """Get all workspace users and map team members"""
        print(f"📋 Fetching workspace users to map team members...")
        
        headers = {"Authorization": f"Bearer {SLACK_TOKEN}"}
        team_id = None
        
        async with aiohttp.ClientSession() as session:
            # First get team_id for Enterprise Grid
            async with session.get("https://slack.com/api/auth.test", headers=headers) as resp:
                auth_data = await resp.json()
                if auth_data.get("ok"):
                    team_id = auth_data.get("team_id")
                    print(f"   Team ID: {team_id}")
            
            # Get ALL workspace users
            cursor = None
            user_count = 0
            
            while True:
                params = {"limit": 200}
                if team_id:
                    params["team_id"] = team_id
                if cursor:
                    params["cursor"] = cursor
                
                async with session.get(
                    "https://slack.com/api/users.list",
                    headers=headers,
                    params=params
                ) as resp:
                    data = await resp.json()
                    if not data.get("ok"):
                        print(f"❌ Error getting users: {data.get('error')}")
                        break
                    
                    for user in data.get("members", []):
                        if user.get("deleted") or user.get("is_bot"):
                            continue
                        
                        user_id = user["id"]
                        username = user.get("name", "").lower()
                        real_name = user.get("real_name", "").lower()
                        display_name = user.get("profile", {}).get("display_name", "").lower()
                        
                        self.slack_user_map[user_id] = {
                            "username": user.get("name", ""),
                            "real_name": user.get("real_name", "")
                        }
                        
                        user_count += 1
                        
                        # Check direct username mapping first
                        actual_username = user.get("name", "").lower()
                        if actual_username in SLACK_USERNAME_MAP:
                            mapped_handle = SLACK_USERNAME_MAP[actual_username]
                            
                            # Is it a required member?
                            if mapped_handle in REQUIRED_SLACK_MEMBERS and mapped_handle not in self.required_slack_ids:
                                self.required_slack_ids[mapped_handle] = user_id
                                print(f"   ✓ Found required: {REQUIRED_SLACK_MEMBERS[mapped_handle]} (@{user.get('name')})")
                            
                            # Is it an optional member?
                            elif mapped_handle in OPTIONAL_MEMBERS and mapped_handle not in self.optional_slack_ids:
                                self.optional_slack_ids[mapped_handle] = user_id
                                print(f"   ✓ Found optional: {OPTIONAL_MEMBERS[mapped_handle]} (@{user.get('name')})")
                    
                    cursor = data.get("response_metadata", {}).get("next_cursor")
                    if not cursor:
                        break
        
        print(f"\n   Scanned {user_count} workspace users")
        print(f"   Mapped {len(self.required_slack_ids)}/{len(REQUIRED_SLACK_MEMBERS)} required members")
        print(f"   Mapped {len(self.optional_slack_ids)}/{len(OPTIONAL_MEMBERS)} optional members")
        
        # Show any missing mappings
        missing_required = set(REQUIRED_SLACK_MEMBERS.keys()) - set(self.required_slack_ids.keys())
        missing_optional = set(OPTIONAL_MEMBERS.keys()) - set(self.optional_slack_ids.keys())
        
        if missing_required:
            print(f"   ⚠️  Missing required: {', '.join(missing_required)}")
        if missing_optional:
            print(f"   ℹ️  Missing optional: {', '.join(missing_optional)}")
    
    async def audit_slack_channels(self):
        """Audit all Slack channels with 'bitsafe' in the name - always uses live API"""
        print(f"\n🔍 Auditing Slack channels...")
        
        headers = {"Authorization": f"Bearer {SLACK_TOKEN}"}
        
        # Always use live API to ensure we have the latest channels (including newly created ones)
        bitsafe_channels = []
        
        print(f"   Fetching channels from Slack API...")
        
        async with aiohttp.ClientSession() as session:
            params = {"limit": 200, "exclude_archived": "false", "types": "public_channel,private_channel"}
            async with session.get(
                "https://slack.com/api/conversations.list",
                headers=headers,
                params=params
            ) as resp:
                data = await resp.json()
                if data.get("ok"):
                    all_channels = data.get("channels", [])
                    bitsafe_channels = [
                        ch for ch in all_channels 
                        if "bitsafe" in ch.get("name", "").lower()
                    ]
        
        print(f"   Found {len(bitsafe_channels)} BitSafe channels via API")
        
        # Audit each channel (whether from file or API)
        async with aiohttp.ClientSession() as session:
            for channel in bitsafe_channels:
                channel_id = channel["id"]
                channel_name = channel["name"]
                is_private = channel.get("is_private", True)  # Default to private for safety
                
                # Get channel members
                async with session.get(
                    "https://slack.com/api/conversations.members",
                    headers=headers,
                    params={"channel": channel_id}
                ) as resp:
                    data = await resp.json()
                    if not data.get("ok"):
                        print(f"   ⚠️  Couldn't access {channel_name}: {data.get('error')}")
                        continue
                    
                    members = data.get("members", [])
                
                # Check which required/optional members are present
                required_present = []
                required_missing = []
                optional_present = []
                optional_missing = []
                
                for username, user_id in self.required_slack_ids.items():
                    if user_id in members:
                        required_present.append(REQUIRED_SLACK_MEMBERS[username])
                    else:
                        required_missing.append(REQUIRED_SLACK_MEMBERS[username])
                
                for username, user_id in self.optional_slack_ids.items():
                    if user_id in members:
                        optional_present.append(OPTIONAL_MEMBERS[username])
                    else:
                        optional_missing.append(OPTIONAL_MEMBERS[username])
                
                # Categorize the group
                category, requires_full_team = categorize_group(channel_name)
                rename_flag = "⚠️ YES" if needs_rename(channel_name) else "No"
                
                # Add to results
                self.audit_results.append({
                    "Platform": "Slack",
                    "Group Name": channel_name,
                    "Category": category,
                    "Requires Full Team": "Yes" if requires_full_team else "No",
                    "Needs Rename (iBTC)": rename_flag,
                    "Privacy Status": "Private" if is_private else "⚠️ PUBLIC",
                    "History Visibility": "N/A",  # Slack-specific, not applicable
                    "Admin Status": "N/A",  # Slack channels managed via workspace admin
                    "Total Members": len(members),
                    "Required Present": ", ".join(required_present) if required_present else "NONE",
                    "Required Missing": ", ".join(required_missing) if required_missing else "-",
                    "Optional Present": ", ".join(optional_present) if optional_present else "-",
                    "Optional Missing": ", ".join(optional_missing) if optional_missing else "-",
                    "Completeness": f"{len(required_present)}/{len(REQUIRED_SLACK_MEMBERS)} required"
                })
                
                warning = "" if requires_full_team or len(required_present) >= 3 else " ⚠️"
                print(f"   ✓ {channel_name}: {len(required_present)}/{len(REQUIRED_SLACK_MEMBERS)} required [{category}]{warning}")
    
    async def audit_telegram_groups(self):
        """Audit all Telegram groups shared with @mojo_onchain"""
        print(f"\n🔍 Auditing Telegram groups...")
        
        client = TelegramClient('telegram_session', TELEGRAM_API_ID, TELEGRAM_API_HASH)
        await client.start()
        
        # Find @mojo_onchain
        try:
            mojo_user = await client.get_entity("mojo_onchain")
            print(f"   Found @mojo_onchain: {mojo_user.first_name}")
        except Exception as e:
            print(f"❌ Couldn't find @mojo_onchain: {e}")
            return
        
        # Get ALL common chats with pagination
        try:
            all_common_chats = []
            max_id = 0
            
            while True:
                result = await client(GetCommonChatsRequest(
                    user_id=mojo_user,
                    max_id=max_id,
                    limit=100
                ))
                
                if not result.chats:
                    break
                
                all_common_chats.extend(result.chats)
                
                # Update max_id for next batch (use the last chat's ID)
                if hasattr(result.chats[-1], 'id'):
                    max_id = result.chats[-1].id
                else:
                    break
                
                print(f"   Fetched {len(all_common_chats)} groups so far...")
                
                # If we got less than 100, we're done
                if len(result.chats) < 100:
                    break
            
            common_chat_ids = all_common_chats
            print(f"   Total common groups: {len(common_chat_ids)}")
            
            # Get details for each group
            for chat in common_chat_ids:
                if not hasattr(chat, 'title'):
                    continue
                
                group_name = chat.title
                member_count = getattr(chat, 'participants_count', 0)
                
                # Check history visibility settings
                history_visible = "Unknown"
                try:
                    if isinstance(chat, Channel):
                        full_chat = await client(GetFullChannelRequest(chat))
                        hidden = full_chat.full_chat.hidden_prehistory
                    elif isinstance(chat, Chat):
                        full_chat = await client(GetFullChatRequest(chat.id))
                        hidden = getattr(full_chat.full_chat, 'hidden_prehistory', False)
                    else:
                        hidden = False  # Default for other chat types
                    
                    history_visible = "Hidden" if hidden else "Visible"
                except Exception as e:
                    print(f"      Warning: Couldn't check history settings for {group_name}: {e}")
                    history_visible = "Unknown"
                
                # Check admin status
                admin_status = "Member"
                try:
                    # Get our own permissions in this chat
                    me = await client.get_me()
                    perms = await client.get_permissions(chat, me)
                    
                    if perms.is_creator:
                        admin_status = "✅ Owner"
                    elif perms.is_admin:
                        # Check if we have change_info permission
                        if hasattr(perms, 'change_info') and perms.change_info:
                            admin_status = "✅ Admin (can rename)"
                        else:
                            admin_status = "Admin (no rename)"
                    else:
                        admin_status = "Member"
                except Exception as e:
                    # If permission check fails, assume member
                    admin_status = f"Unknown ({str(e)[:30]}...)" if str(e) else "Unknown"
                
                # Get participants
                try:
                    participants = await client.get_participants(chat)
                    
                    # Map Telegram usernames to our team list
                    required_present = []
                    required_missing = list(REQUIRED_TELEGRAM_MEMBERS.values())
                    optional_present = []
                    optional_missing = list(OPTIONAL_MEMBERS.values())
                    
                    # Check each participant
                    for p in participants:
                        username = getattr(p, 'username', None)
                        if not username:
                            continue
                        
                        # Check required members
                        if username in REQUIRED_TELEGRAM_MEMBERS:
                            required_present.append(REQUIRED_TELEGRAM_MEMBERS[username])
                            if REQUIRED_TELEGRAM_MEMBERS[username] in required_missing:
                                required_missing.remove(REQUIRED_TELEGRAM_MEMBERS[username])
                        
                        # Check optional members
                        if username in OPTIONAL_MEMBERS:
                            optional_present.append(OPTIONAL_MEMBERS[username])
                            if OPTIONAL_MEMBERS[username] in optional_missing:
                                optional_missing.remove(OPTIONAL_MEMBERS[username])
                    
                    # Categorize the group
                    category, requires_full_team = categorize_group(group_name)
                    rename_flag = "⚠️ YES" if needs_rename(group_name) else "No"
                    history_flag = "⚠️ HIDDEN" if history_visible == "Hidden" else history_visible
                    
                    # Add to results
                    self.audit_results.append({
                        "Platform": "Telegram",
                        "Group Name": group_name,
                        "Category": category,
                        "Requires Full Team": "Yes" if requires_full_team else "No",
                        "Needs Rename (iBTC)": rename_flag,
                        "Privacy Status": "Private",  # TG groups in common are always accessible
                        "History Visibility": history_flag,
                        "Admin Status": admin_status,
                        "Total Members": len(participants),
                        "Required Present": ", ".join(required_present) if required_present else "NONE",
                        "Required Missing": ", ".join(required_missing) if required_missing else "-",
                        "Optional Present": ", ".join(optional_present) if optional_present else "-",
                        "Optional Missing": ", ".join(optional_missing) if optional_missing else "-",
                        "Completeness": f"{len(required_present)}/{len(REQUIRED_TELEGRAM_MEMBERS)} required"
                    })
                    
                    warning = "" if requires_full_team or len(required_present) >= 3 else " ⚠️"
                    rename_note = " [RENAME]" if needs_rename(group_name) else ""
                    print(f"   ✓ {group_name}: {len(required_present)}/{len(REQUIRED_TELEGRAM_MEMBERS)} required [{category}]{warning}{rename_note}")
                    
                except Exception as e:
                    print(f"   ⚠️  Couldn't audit {group_name}: {e}")
                    continue
            
        except Exception as e:
            print(f"❌ Error getting common chats: {e}")
        
        await client.disconnect()
    
    def generate_report(self):
        """Generate Excel report"""
        print(f"\n📊 Generating report...")
        
        # Create DataFrame
        df = pd.DataFrame(self.audit_results)
        
        # Sort by platform, then completeness, then group name
        df = df.sort_values(['Platform', 'Completeness', 'Group Name'])
        
        # Save to Excel in output directory
        output_dir = "output/audit_reports"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"{output_dir}/customer_group_audit_{timestamp}.xlsx"
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Audit Results', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Audit Results']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(col)
                )
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
        
        print(f"✅ Report saved to: {output_file}")
        print(f"\n📈 Summary:")
        print(f"   Total groups audited: {len(df)}")
        print(f"   Slack channels: {len(df[df['Platform'] == 'Slack'])}")
        print(f"   Telegram groups: {len(df[df['Platform'] == 'Telegram'])}")
        
        # Category breakdown
        print(f"\n📊 By Category:")
        for category in df['Category'].value_counts().index:
            count = len(df[df['Category'] == category])
            print(f"   {category}: {count}")
        
        # Flags
        print(f"\n⚠️  Flags:")
        public_count = len(df[(df['Platform'] == 'Slack') & (df['Privacy Status'].str.contains('PUBLIC'))])
        if public_count > 0:
            print(f"   PUBLIC Slack channels (should be private): {public_count}")
        
        rename_count = len(df[df['Needs Rename (iBTC)'].str.contains('YES')])
        if rename_count > 0:
            print(f"   Groups needing rename (contains iBTC): {rename_count}")
        
        hidden_history_count = len(df[(df['Platform'] == 'Telegram') & (df['History Visibility'].str.contains('HIDDEN'))])
        if hidden_history_count > 0:
            print(f"   Telegram groups with HIDDEN history (should be visible): {hidden_history_count}")
        
        # Missing members in BD customer groups
        bd_groups = df[df['Requires Full Team'] == 'Yes']
        if len(bd_groups) > 0:
            incomplete = len(bd_groups[~bd_groups['Completeness'].str.startswith('5/')])
            print(f"   BD Customer groups with missing members: {incomplete}/{len(bd_groups)}")

async def main():
    auditor = CustomerGroupAuditor()
    
    # Step 1: Get Slack user IDs
    await auditor.get_slack_bd_members()
    
    # Step 2: Audit Slack channels
    await auditor.audit_slack_channels()
    
    # Step 3: Audit Telegram groups (optional)
    if TELEGRAM_ENABLED:
        await auditor.audit_telegram_groups()
    else:
        print("\n⚠️  Telegram audit skipped (credentials not configured)")
    
    # Step 4: Generate report
    auditor.generate_report()

if __name__ == "__main__":
    asyncio.run(main())

