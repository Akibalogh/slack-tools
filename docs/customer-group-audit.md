# Customer Group Audit Tool

## Overview

The Customer Group Audit Tool automatically audits Slack and Telegram customer groups to verify that required and optional BitSafe team members are present in each group. It generates an Excel report highlighting gaps, categorizing groups, and flagging groups that need renaming.

## Features

- ✅ **Dual Platform Support**: Audits both Slack and Telegram groups
- 📊 **Excel Reports**: Generates comprehensive Excel reports with all audit data
- 🏷️ **Group Categorization**: Automatically categorizes groups (BD Customer, Marketing, Internal, Intro)
- ⚠️ **iBTC Rename Flagging**: Identifies groups containing "iBTC" that need renaming to use current branding
- 👥 **Team Member Tracking**: Tracks 5 required and 4 optional team members
- 🔒 **Privacy Status**: Flags public Slack channels that should be private
- 📈 **Completeness Scoring**: Shows how many required team members are present in each group

## Team Members

### Required Members
- **@akibalogh** - Aki Balogh (CEO)
- **@gabitui** - Gabi Tui (Head of Product) 
- **@mojo_onchain** - Mayank (Sales Engineer)
- **@kadeemclarke** - Kadeem Clarke (Head of Growth)
- **@NonFungibleAmy** - Amy Wu (BD)

### Optional Members
- **@shin_novation** - Shin (Strategy Advisor)
- **@j_eisenberg** - Jesse Eisenberg (CTO)
- **@anmatusova** - Anna Matusova (VP Finance & Legal)
- **@Dae_L** - Dae (Sales Advisor)

## Group Categories

### BD Customer (Requires Full Team)
Standard customer engagement groups where all 5 required team members should be present.

### Marketing (No Full Team Required)
Marketing and promotional groups:
- Party Action People
- Artemis
- Crypto Insights Group

### Internal (No Full Team Required)
Internal BitSafe groups:
- iBTC Offboarding Support Group
- iBTC withdraw
- BitSafe team at Singapore 2025
- Canton Network
- Loop Community
- PMM Interviews
- Gabi <> BitSafe

### Intro (No Full Team Required)
Introduction/referral groups:
- Bron <> SIG

## Usage

### Basic Usage

```bash
cd /Users/akibalogh/apps/slack-tools
python3 scripts/customer_group_audit.py
```

The script will:
1. Map team members from Slack workspace users
2. Load known BitSafe channels from export data (72 channels)
3. Audit each Slack channel for team member presence
4. Connect to Telegram and find all groups shared with @mojo_onchain (401+ groups)
5. Audit each Telegram group for team member presence
6. Generate an Excel report in the output folder

### Output

The tool generates an Excel report: `output/audit_reports/customer_group_audit_YYYYMMDD_HHMMSS.xlsx`

**Report Columns:**
- **Platform**: Slack or Telegram
- **Group Name**: Name of the customer group
- **Category**: BD Customer, Marketing, Internal, or Intro
- **Requires Full Team**: Yes or No
- **Needs Rename (iBTC)**: ⚠️ YES if contains "iBTC", No otherwise
- **Privacy Status**: Private or ⚠️ PUBLIC for Slack channels
- **History Visibility**: For Telegram groups - Visible, ⚠️ HIDDEN, or Unknown. N/A for Slack.
- **Total Members**: Total number of members in the group
- **Required Present**: Names of required members present
- **Required Missing**: Names of required members missing
- **Optional Present**: Names of optional members present
- **Optional Missing**: Names of optional members missing
- **Completeness**: Score like "5/5 required" or "3/5 required"

### Summary Statistics

The script outputs:
```
📈 Summary:
   Total groups audited: 474
   Slack channels: 72
   Telegram groups: 402

📊 By Category:
   BD Customer: 461
   Internal: 8
   Marketing: 3
   Intro: 1

⚠️  Flags:
   Groups needing rename (contains iBTC): 194
   Telegram groups with HIDDEN history (should be visible): [varies]
   BD Customer groups with missing members: 285/461
```

## Configuration

### Environment Variables

Required in `.env` file:

```bash
# Slack - IMPORTANT: Use the BitSafe Export Tool app token
# Get from: https://api.slack.com/apps/A09AJJZF718/oauth
SLACK_USER_TOKEN=xoxp-[COPY-FROM-SLACK-APP-PAGE]

# Telegram
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef...
TELEGRAM_PHONE=+16176820066
```

**Note**: The token must be from the **BitSafe Export Tool** app which has these scopes:
- `groups:read` - View private channel info
- `groups:history` - View private channel messages  
- `channels:read` - View public channel info
- `channels:history` - View public channel messages
- `users:read` - View workspace users

### Group Categorization

Edit `config/customer_group_categories.json` to customize group categories:

```json
{
  "marketing_groups": [
    "Party Action People",
    "Artemis",
    "Crypto Insights Group"
  ],
  "internal_groups": [
    "iBTC Offboarding Support Group",
    "iBTC withdraw",
    "BitSafe team at Singapore 2025",
    "Canton Network"
  ],
  "intro_groups": [
    "Bron <> SIG"
  ]
}
```

## Data Sources

### Slack Channels

The tool loads known BitSafe customer channels from:
- `data/raw/slack_export_20250815_064939/channels/private_channels.json`

This file contains 72 BitSafe customer channels that match the pattern `*-bitsafe` or `bitsafe-*`.

**Note**: The Slack API `conversations.list` doesn't return these channels (likely Slack Connect external channels), so we load them from the export data file instead.

### Telegram Groups

The tool queries the Telegram API to find all groups shared between you and @mojo_onchain (Sales Engineer). This represents all customer-related Telegram groups (401+ groups).

#### Telegram History Visibility

For each Telegram group, the tool checks the **history visibility** setting:

- **Visible**: New members can see the full chat history when they join
- **⚠️ HIDDEN**: New members cannot see messages sent before they joined
- **Unknown**: Could not determine the setting (permissions issue)

**Best Practice**: Customer groups should have history set to **Visible** so new team members can review past conversations and context when they join.

**How to Fix**: In Telegram group settings:
1. Open the group
2. Click the group name at the top
3. Click "Edit"
4. Under "Chat history for new members", select "Visible"
5. Save changes

## Slack Token Scopes

The Slack user token must have these scopes:
- `groups:read` - View basic information about private channels
- `groups:history` - View messages and other content in private channels
- `users:read` - View people in workspace
- `channels:read` - View basic information about public channels
- `channels:history` - View messages in public channels

## Telegram Authentication

The tool uses the Telethon library with your Telegram API credentials. On first run, it will:
1. Prompt for your phone number
2. Send a verification code to your Telegram app
3. Save the session for future runs

Session file: `telegram_session.session`

## Common Issues

### "missing_scope" Error - MOST COMMON
**Cause**: Wrong token in `.env` file  
**Solution**: Make sure you're using the token from the **BitSafe Export Tool** app (A09AJJZF718), not a different Slack app.

Get the correct token from the BitSafe Export Tool app.

If you accidentally used a token from a different app:
1. Go to https://api.slack.com/apps/A09AJJZF718/oauth
2. Copy the "User OAuth Token" 
3. Update your `.env` file
4. Run `python3 scripts/verify_slack_token.py` to verify

### "team_access_not_granted" Error
**Solution**: Use a user token instead of a bot token. Bot tokens may not have access to all private channels.

### No Slack Channels Found
**Solution**: Ensure `data/raw/slack_export_20250815_064939/channels/private_channels.json` exists and contains the channel data.

### Telegram Not Finding Groups
**Solution**: Verify that @mojo_onchain's username is correct and that you share groups with this user.

## Next Steps

### Programmatic Member Management (Future)

Once gaps are identified, a future tool will allow:
- Bulk adding missing required members to groups
- Automated invitations to new customer groups
- Template-based group setup

### Exclusions Management (Future)

Some groups may have legitimate reasons for missing certain team members. Future enhancements:
- Exclusion list for specific group/member combinations
- Justification notes for exceptions
- Review and approval workflow

## Files

- `scripts/customer_group_audit.py` - Main audit script
- `config/customer_group_categories.json` - Group category definitions
- `data/raw/slack_export_20250815_064939/channels/private_channels.json` - Slack channel data
- `telegram_session.session` - Telegram authentication session

## Related Documentation

- [Slack Export How-To](slack-export-howto.md) - Details on exporting Slack channel data
- [Slack API Documentation](https://api.slack.com/) - Official Slack API reference
- [Telethon Documentation](https://docs.telethon.dev/) - Telegram API library reference

