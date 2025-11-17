# Utility Scripts

This directory contains utility scripts and standalone tools.

## Files

- Various Python scripts for specific tasks and utilities

## Usage

Scripts in this directory can be run directly or imported as modules depending on their purpose.

## Notes

These scripts are utility tools and may not be part of the core ORM system.

## Slack User Offboarding

For user offboarding in Slack, use the **manual approach** via Slack Admin UI:

### Steps to Deactivate a User

1. Go to: **https://bit-safe.slack.com/admin/people**
2. Find the user (e.g., Addie Tackman)
3. Click the **"⋮"** menu next to their name
4. Click **"Deactivate account"**
5. Confirm deactivation

### What Happens Automatically

When you deactivate a user, Slack automatically:
- Logs them out of all sessions
- Removes them from all channels
- Removes them from all user groups
- Prevents future logins

### Notes

- **No API Required**: Slack's UI handles everything automatically
- **Audit Trail**: Deactivation is logged in Slack's audit logs
- **Reversible**: Accounts can be reactivated if needed
- **Enterprise Grid**: For org-level deactivation, contact your Org Admin

## Telegram User Delete Script

The `telegram_user_delete.py` script provides complete user offboarding functionality for Telegram.

### Setup Requirements

**Required Telegram API Credentials:**
1. **API ID** and **API Hash** from https://my.telegram.org/apps
   - Log in with your phone number
   - Go to "API development tools"
   - Create an application to get your credentials

2. **Phone Number** - Your Telegram phone number (must have admin rights in the groups)

### Environment Configuration

Add these to your `.env` file in the project root:

```bash
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_PHONE=+1234567890
TARGET_USERNAME=nftaddie
```

### First-Time Setup

The first time you run the script, you'll need to authenticate:

```bash
# This will prompt for a verification code sent to your phone
python3 scripts/telegram_user_delete.py --dry-run --username=nftaddie
```

Enter the code when prompted. A session file will be created for future use.

### Usage

```bash
# Set target username
export TARGET_USERNAME=nftaddie

# First, test in dry-run mode (recommended):
python3 scripts/telegram_user_delete.py --dry-run --username=nftaddie

# Then, run the actual offboarding:
python3 scripts/telegram_user_delete.py --username=nftaddie
```

### What It Does

The script performs a complete Telegram offboarding sequence:

1. **Find User**: Locates the user by username (@nftaddie)
2. **Scan All Chats**: Finds all groups, supergroups, and channels
3. **Check Permissions**: Verifies admin rights in each chat
4. **Remove User**: Kicks user from each chat where you have admin permissions

### Requirements

Install required Python packages:

```bash
pip install telethon python-dotenv
```

### Limitations

- **Admin Rights Required**: You must be an admin in each group/channel to remove users
- **Regular Groups**: Can remove any user if you're admin
- **Supergroups/Channels**: Can remove regular users, but not other admins
- **Private Groups**: Only accessible if you're already a member
- **Rate Limits**: Built-in delays to respect Telegram's rate limits

### Notes

- **Authentication**: Uses Telegram Client API (not Bot API) for full access
- **Session Storage**: Creates `telegram_session.session` file for authentication
- **Error Handling**: Continues even if individual removals fail, logging each attempt
- **Audit Trail**: All actions logged to `logs/telegram_offboarding.log`
- **Dry Run**: Always test with `--dry-run` first to see what would happen

## Telegram Admin Messaging Script

The `telegram_message_admins.py` script messages group admins requesting user removal from groups where you lack admin permissions.

### Use Case

After running `telegram_user_delete.py`, you may have groups where you don't have admin rights. This script:
1. Reads the CSV output from the delete script
2. Identifies all unique admins across those groups
3. Sends each admin ONE consolidated message listing all their groups
4. Requests they remove the user from their groups

### Setup Requirements

Same as the Telegram User Delete Script above (API ID, Hash, Phone Number in `.env`).

### Usage

```bash
# First, run the user delete script to generate the CSV:
python3 scripts/telegram_user_delete.py --username=nftaddie

# This creates: logs/telegram_no_admin_access_YYYYMMDD_HHMMSS.csv

# Test messaging in dry-run mode:
python3 scripts/telegram_message_admins.py --csv=logs/telegram_no_admin_access_20251031_223304.csv --dry-run

# Send the actual messages:
python3 scripts/telegram_message_admins.py --csv=logs/telegram_no_admin_access_20251031_223304.csv
```

### What It Does

1. **Parse CSV**: Reads group names and admin usernames from the CSV
2. **Consolidate**: Groups all chats by admin (avoids duplicate messages)
3. **Message Preview**: Shows who will be messaged and how many groups each admin manages
4. **Send Messages**: Sends personalized requests to each admin

### Message Format

**For single-group admins:**
```
Hi! Addie is no longer with BitSafe - could you please remove @nftaddie from "BitSafe Product"? Thanks! -Aki
```

**For multi-group admins:**
```
Hi! Addie is no longer with BitSafe - could you please remove @nftaddie from these groups:

• BitSafe Product
• Verichains <> BitSafe (CBTC)

Thanks! -Aki
```

### Features

- **Deduplication**: Each admin gets exactly ONE message, even if they manage multiple groups
- **Rate Limiting**: 2-second delay between messages to respect Telegram limits
- **Error Handling**: Gracefully handles blocked users, privacy restrictions, and invalid usernames
- **Tracking**: Saves list of messaged admins to prevent duplicates on reruns
- **Dry Run**: Preview exactly what will be sent before sending

### Output Files

- `logs/telegram_admin_messages.log` - Detailed execution log
- `logs/telegram_messaged_admins_YYYYMMDD_HHMMSS.txt` - List of admins who were messaged

### Notes

- Uses the same authentication session as the delete script
- Automatically skips the target user if they're listed as an admin
- Respects Telegram's privacy settings (some users may block messages)
- Test with your own account first to verify message formatting
