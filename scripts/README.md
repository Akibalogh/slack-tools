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

---

## Telegram Group Automation & Ownership Transfer (Dec 2025)

### Overview

Suite of scripts for managing Telegram group membership and ownership based on audit results. Addresses gaps in team coverage and ownership structure across 400+ Telegram groups.

### Scripts

#### `telegram_add_missing_members.py`

Automatically adds missing required team members to customer Telegram groups.

**Features:**
- Reads latest audit from Heroku Postgres
- Filters for customer groups with "BitSafe" in name
- Excludes internal/community/marketing groups (including "BitSafe <> Ben W", "Contribution Capital | BitSafe (New)" - VC)
- Excludes hacked/compromised groups (e.g., "Contribution Capital <> BitSafe" - replaced with new group)
- Handles supergroups and channels (skips basic chats due to API limitations)
- Rate limit detection with informative errors
- Non-interactive mode with `--yes` flag

**Usage:**
```bash
python3 scripts/telegram_add_missing_members.py --yes
```

**Known Limitations:**
- **Telegram Rate Limits:** Very aggressive anti-spam
  - First ~30 groups succeed
  - Then 51-minute cooldown
  - Repeated runs: 20+ hour cooldowns
  - **Recommendation:** Run once daily, manual addition for remainder
- **Basic Groups:** Some groups (InputPeerChat type) cannot be modified via API
  - Script skips these to avoid errors
  - Manual addition required through Telegram UI

**Bug Fixes (Dec 7, 2025):**
- ✅ Fixed "No username" errors for groups with placeholder dashes
  - Audit data uses `'-'` as placeholder when no members are missing
  - Script now filters out dashes/placeholders at filtering and processing stages
  - Eliminates false warnings and prevents unnecessary API calls

**Results (Dec 7-8, 2025):**
- ✅ Processing 138 groups (down from 171 - filters out placeholder groups)
- ✅ Added 254 members successfully in first run
- ⏳ 266 operations rate-limited (expected behavior)
- 🔄 Retry script available for automatic retry after cooldown

#### `telegram_add_missing_members_retry.py`

Automated retry script that waits for rate limit cooldown and retries the member addition process.

**Features:**
- Automatically calculates wait time from latest log file
- Progress updates during wait period
- Can run in background for hands-off operation
- Manual wait time override available

**Usage:**
```bash
# Automatic retry (calculates wait time from latest log)
python3 scripts/telegram_add_missing_members_retry.py --auto-wait

# Retry after specific wait time (in seconds)
python3 scripts/telegram_add_missing_members_retry.py --wait 2600

# Run in background with auto-wait
nohup python3 scripts/telegram_add_missing_members_retry.py --auto-wait > /tmp/telegram_retry_$(date +%Y%m%d_%H%M%S).log 2>&1 &
```

**How it works:**
1. Finds the latest `telegram_add_members_*.log` file
2. Extracts maximum rate limit wait time from log
3. Adds 5-minute buffer to ensure cooldown is complete
4. Waits with progress updates
5. Automatically reruns the member addition script

**Monitoring:**
```bash
# Check retry script progress
tail -f /tmp/telegram_retry_*.log

# Check if retry script is running
ps aux | grep telegram_add_missing_members_retry
```

#### `export_telegram_group.py`

Generic script to export messages from any Telegram group for a specified time period.

**Features:**
- Export messages from any Telegram group by name
- Flexible time periods: days, weeks, months, or years
- Auto-generates output filename with timestamp
- Includes sender names, timestamps, and message text
- Marks reply messages for context
- Uses saved Telegram session (no re-authentication needed)

**Usage:**
```bash
# Export last 3 months (default)
python3 scripts/export_telegram_group.py "BitSafe Leadership Team"

# Export last 30 days
python3 scripts/export_telegram_group.py "Group Name" --days 30

# Export last 2 weeks
python3 scripts/export_telegram_group.py "Group Name" --weeks 2

# Export last 6 months
python3 scripts/export_telegram_group.py "Group Name" --months 6

# Export last 1 year
python3 scripts/export_telegram_group.py "Group Name" --years 1

# Custom output file
python3 scripts/export_telegram_group.py "Group Name" --days 30 -o output/custom_export.txt
```

**Output:**
- Text file in `output/` directory with format: `telegram_export_{group_name}_{timestamp}.txt`
- Includes header with export metadata (group name, time range, message count)
- Chronologically sorted messages (oldest first)
- Reply messages marked with "↳" prefix

**Examples:**
```bash
# Export leadership team chat for last 3 months
python3 scripts/export_telegram_group.py "BitSafe Leadership Team"

# Export customer group for last week
python3 scripts/export_telegram_group.py "Customer <> BitSafe (CBTC)" --weeks 1
```

#### `telegram_make_history_visible.py`

Makes message history visible to new members for groups with hidden history.

**Usage:**
```bash
# All groups where we have permission
python3 scripts/telegram_make_history_visible.py --yes

# Only BitSafe customer groups
python3 scripts/telegram_make_history_visible.py --yes --bitsafe-only
```

**Results:**
- ✅ Updated 9 BitSafe groups to visible history
- Works only on supergroups/channels (basic chats don't support this)

### Ownership Transfer Workflow

**Problem:** In 163 Telegram groups, we're only "Member" (not Owner/Admin). Need ownership to:
- Add/remove team members
- Manage group settings
- Transfer ownership to others

**Solution:** Manual ownership transfer requests with clear instructions.

**Process:**

1. **Identify Groups Needing Transfer:**
   ```bash
   python3 scripts/show_member_only_groups.py
   ```
   Generates:
   - `output/member_only_groups.csv` - Full list (163 groups)
   - `output/ownership_transfer_message.txt` - Message template

2. **Find Current Owners:**
   ```bash
   python3 scripts/find_group_owners.py
   ```
   Identifies owner username for each group

3. **Send Transfer Requests:**
   Manually message owners with template, or use batch script:
   ```bash
   python3 scripts/send_ownership_requests_batch1.py
   ```

**Message Template Includes:**
- Friendly explanation of why ownership is needed
- **Critical detail:** Must enable "Add new admins" permission first
- Step-by-step instructions for mobile and desktop
- Note that 2FA password may be required

**Transfer Requirements (from Telegram):**
1. Recipient must first be added as admin
2. Admin must have "Add new admins" permission enabled
3. "Transfer Group Ownership" button only appears after step 2
4. Owner may need 2FA password to confirm
5. Transfer is irreversible (unless new owner transfers back)

**Test Results (Dec 4, 2025):**
- ✅ Sent requests to 3 owners (4 groups total)
- ✅ @ThePhunky1 responded positively: "super helpful, didn't know how to do this"
- ✅ Transferring GlobalStake group ownership
- ⏳ Waiting on @Dae_L (2 groups - internal team member)
- ⏳ Waiting on @kaskitrix (1 group)

### Helper Scripts

#### `show_bitsafe_customer_gaps.py`

Generates CSV report of customer groups missing team members.

```bash
python3 scripts/show_bitsafe_customer_gaps.py
```

Output: `output/bitsafe_customer_gaps.csv`

#### `show_member_only_groups.py`

Lists groups where we're only members (not owner/admin).

```bash
python3 scripts/show_member_only_groups.py
```

Outputs:
- `output/member_only_groups.csv`
- `output/ownership_transfer_message.txt`

#### `update_group_categories.py`

Updates group categories in database audit results.

**Usage:**
1. Edit `CATEGORY_UPDATES` dictionary in script
2. Run: `python3 scripts/update_group_categories.py`

**Example:**
```python
CATEGORY_UPDATES = {
    "BitSafe Marketing": "Internal",
    "BitSafe Community": "Community",
    "7Ridge <> BitSafe (CBTC)": "Investor",
}
```

**Results:** Reclassified 8 groups in audit #103

### Recommendations

**For Member Addition:**
- **Automated:** Good for first 30 groups, then hit rate limits
- **Manual:** More reliable for remaining groups
- **Hybrid:** Use automation for initial batch, manual for remainder

**For Ownership Transfer:**
- **Manual only:** No API support in Telegram
- Use provided message template
- Focus on 98 BitSafe customer groups first
- Track progress manually via audits

**For Group Management:**
- Prioritize supergroups/channels over basic groups
- Basic groups have API limitations
- Consider converting basic groups to supergroups for better API access
