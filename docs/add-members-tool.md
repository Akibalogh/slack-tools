# Slack Member Addition Tool

Bulk add team members to all BitSafe customer Slack channels.

## Overview

This tool automates the process of adding team members to multiple Slack channels at once. It's designed specifically for BitSafe customer channels (channels with "bitsafe" in the name).

## Features

- ✅ **Bulk member addition** - Add multiple members to all customer channels at once
- ✅ **Smart detection** - Automatically finds user IDs from usernames
- ✅ **Skip existing** - Won't try to re-add people already in channels
- ✅ **Dry-run mode** - Test before making changes
- ✅ **Detailed logging** - Saves complete operation log to file
- ✅ **Error handling** - Gracefully handles inaccessible/archived channels
- ✅ **Progress tracking** - Shows real-time progress as it adds members

## Prerequisites

### Required Slack Scopes

The Slack token must have these User Token Scopes:
- `groups:write` - Add members to private channels
- `channels:write` - Add members to public channels
- `users:read` - Look up user information
- `groups:read` - View private channel info
- `channels:read` - View public channel info

See [add-write-scope.md](add-write-scope.md) for instructions on adding these scopes.

### Environment Variables

Required in `.env` file:

```bash
SLACK_USER_TOKEN=xoxp-[your-token-with-write-permissions]
```

## Usage

### Basic Command

```bash
python3 scripts/add_members_to_channels.py <username1> <username2> [options]
```

### Options

- `--dry-run` - Preview what would happen without making changes
- `--yes` or `-y` - Skip confirmation prompt (for automation)

### Examples

**Test first (recommended):**
```bash
python3 scripts/add_members_to_channels.py aliya kevin --dry-run
```

**Add members with confirmation:**
```bash
python3 scripts/add_members_to_channels.py aliya kevin
```

**Add members without confirmation (automation):**
```bash
python3 scripts/add_members_to_channels.py aliya kevin --yes
```

**Add different members:**
```bash
python3 scripts/add_members_to_channels.py shin_novation j_eisenberg --yes
```

## How It Works

1. **Look up user IDs** - Converts Slack usernames to user IDs
2. **Load channels** - Reads BitSafe channels from export data
3. **Check current members** - For each channel, checks who's already there
4. **Add missing members** - Invites members who aren't already in the channel
5. **Generate report** - Shows summary of all operations

## Output

The tool provides:

### Console Output
```
============================================================
🚀 Slack Member Addition Tool
============================================================
Members to add: aliya, kevin
Mode: LIVE (will make changes)
============================================================
🔍 Looking up user IDs for: aliya, kevin
   ✓ Found aliya: Aliya Gordon (U09RZH933NJ)
   ✓ Found kevin: Kevin Huet (U09S1JLS6EN)

Adding members to BitSafe channels...
   Found 72 BitSafe channels
   ✅ Added aliya to #mpch-bitsafe-cbtc
   ✅ Added kevin to #mpch-bitsafe-cbtc
   ℹ️  aliya already in #copper-bitsafe
   ⚠️  Couldn't check members in p2p-bitsafe: channel_not_found
   ...

📊 SUMMARY
============================================================
   success: 132
   already_member: 2
   error_checking: 5
   Total operations: 139
```

### Log File
Automatically saves to `output/add_members_YYYYMMDD_HHMMSS.log` with complete operation details.

## Data Sources

The tool loads BitSafe channels from:
```
data/raw/slack_export_20250815_064939/channels/private_channels.json
```

This file contains 72 BitSafe customer channels that match the pattern `*-bitsafe` or `bitsafe-*`.

## Status Codes

- `success` - Member was successfully added to the channel
- `already_member` - Member was already in the channel (skipped)
- `error_checking` - Could not access channel (likely archived/deleted)
- `error` - API error occurred during member addition

## Common Issues

### Missing Scope Error

**Error**: `missing_scope`

**Solution**: Add `groups:write` and `channels:write` scopes to your Slack app. See [add-write-scope.md](add-write-scope.md).

### Channel Not Found

**Error**: `channel_not_found`

**Cause**: Channel has been archived, deleted, or renamed.

**Action**: None needed - tool automatically skips these channels.

### User Not Found

**Error**: Script can't find the user

**Solution**: 
- Verify the username is correct
- Check the user exists in your workspace
- Try the user's display name or real name instead

## Best Practices

1. **Always test first** - Run with `--dry-run` before making changes
2. **Test on one channel** - Manually verify one channel before bulk operation
3. **Keep logs** - Save log files for audit purposes
4. **Rate limiting** - Tool includes 0.5s delays between operations to respect Slack API limits
5. **Update token** - If you change Slack app scopes, update the token in `.env`

## Use Cases

### Onboarding New Team Members
```bash
# Add new BD team member to all customer channels
python3 scripts/add_members_to_channels.py new_bd_person --yes
```

### Reorganizing Teams
```bash
# Add multiple people from different teams
python3 scripts/add_members_to_channels.py sales_eng1 product_manager1 --yes
```

### Backfilling Missing Members
```bash
# After audit identifies missing members, add them
python3 scripts/add_members_to_channels.py aliya kevin --yes
```

## Related Tools

- **[customer_group_audit.py](customer-group-audit.md)** - Audit which members are in which channels
- **[export_slack_channel.py](slack-export-howto.md)** - Export Slack channel messages

## Technical Details

### Rate Limiting
- 0.5 second delay between each API call
- Respects Slack's tier 3 rate limits (50+ requests per minute)

### API Endpoints Used
- `users.list` - Get workspace users
- `conversations.members` - Check current channel members
- `conversations.invite` - Add members to channels

### Error Handling
- Gracefully handles missing channels
- Skips already-added members
- Logs all errors with context
- Continues processing even if individual operations fail

## History

- **2025-01-19**: Initial creation
  - Bulk add members to BitSafe customer channels
  - Dry-run mode for testing
  - Detailed logging and error handling
  - Support for private and public channels

## Support

For issues or questions:
1. Check that your Slack token has the required scopes
2. Run with `--dry-run` to see what would happen
3. Review the log file in `output/` directory
4. Verify usernames are correct in Slack

