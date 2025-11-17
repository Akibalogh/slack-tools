# Employee Offboarding Guide

This document outlines the complete process for offboarding employees from BitSafe's communication platforms.

## Overview

When an employee leaves BitSafe, their access needs to be removed from:
1. Slack workspaces
2. Telegram groups/channels
3. External partner communication channels

## Table of Contents

- [Slack Offboarding](#slack-offboarding)
- [Telegram Offboarding](#telegram-offboarding)
- [Telegram Admin Messaging](#telegram-admin-messaging)
- [Timeline & Checklist](#timeline--checklist)

---

## Slack Offboarding

### Method: Slack Admin UI (Recommended)

The simplest and most effective way to offboard users from Slack is through the Admin UI.

#### Steps

1. Navigate to: **https://bit-safe.slack.com/admin/people**
2. Find the user in the list
3. Click the **"⋮"** (three-dot menu) next to their name
4. Select **"Deactivate account"**
5. Confirm the deactivation

#### What Happens Automatically

When you deactivate a user via the Admin UI, Slack automatically:
- ✅ Logs them out of all sessions
- ✅ Removes them from all channels (public and private)
- ✅ Removes them from all user groups
- ✅ Prevents future logins
- ✅ Creates an audit log entry

#### Important Notes

- **No API Required**: The UI handles everything
- **Audit Trail**: All actions are logged
- **Reversible**: Accounts can be reactivated if needed
- **Enterprise Grid**: For org-level deactivation, contact your Org Admin

---

## Telegram Offboarding

### Method: Automated Script

Use the `telegram_user_delete.py` script to remove users from all Telegram groups where you have admin rights.

#### Prerequisites

1. **Telegram API Credentials**
   - Get API ID and Hash from: https://my.telegram.org/apps
   - Log in with your phone number
   - Go to "API development tools"
   - Create an application

2. **Environment Setup**
   
   Add to `.env` file:
   ```bash
   TELEGRAM_API_ID=your_api_id_here
   TELEGRAM_API_HASH=your_api_hash_here
   TELEGRAM_PHONE=+1234567890
   ```

3. **Install Dependencies**
   ```bash
   pip install telethon python-dotenv
   ```

#### First-Time Authentication

The first time you run the script, you'll need to authenticate:

```bash
python3 scripts/telegram_user_delete.py --dry-run --username=employee_username
```

Enter the verification code sent to your phone. A session file will be created for future use.

#### Usage

**Step 1: Dry Run (Always do this first!)**
```bash
python3 scripts/telegram_user_delete.py --dry-run --username=employee_username
```

Review the output to see:
- How many groups they'll be removed from
- Which groups you lack admin access to
- Any potential issues

**Step 2: Execute Removal**
```bash
python3 scripts/telegram_user_delete.py --username=employee_username
```

#### What the Script Does

1. **Find User**: Locates the user by their Telegram username
2. **Scan Chats**: Identifies all groups, supergroups, and channels
3. **Check Permissions**: Verifies your admin rights in each chat
4. **Remove User**: Kicks the user from chats where you have admin permissions
5. **Generate Report**: Creates CSV of groups where you lack admin access

#### Output Files

- `logs/telegram_offboarding.log` - Detailed execution log
- `logs/telegram_no_admin_access_YYYYMMDD_HHMMSS.csv` - Groups where admin access is needed
- Individual task files in `.taskmaster/tasks/`

#### Limitations

- **Admin Rights Required**: You must be an admin to remove users
- **Cannot Remove Admins**: Can only remove regular users from supergroups/channels
- **Private Groups**: Only accessible if you're already a member
- **Rate Limits**: Script includes delays to respect Telegram's limits

---

## Telegram Admin Messaging

### Method: Automated Messaging Script

After running the deletion script, you may have groups where you don't have admin rights. Use the `telegram_message_admins.py` script to contact those admins.

#### Prerequisites

Same as Telegram Offboarding (uses the same authentication session).

#### Usage

**Step 1: Get the CSV from Deletion Script**

The deletion script creates: `logs/telegram_no_admin_access_YYYYMMDD_HHMMSS.csv`

**Step 2: Dry Run (Test the messaging)**
```bash
python3 scripts/telegram_message_admins.py \
  --csv=logs/telegram_no_admin_access_20251031_223304.csv \
  --dry-run
```

This shows you:
- How many admins will be messaged
- Which admins manage multiple groups
- Preview of the actual messages

**Step 3: Send Messages**
```bash
python3 scripts/telegram_message_admins.py \
  --csv=logs/telegram_no_admin_access_20251031_223304.csv
```

#### What the Script Does

1. **Parse CSV**: Reads group names and admin usernames
2. **Consolidate**: Groups all chats by admin (each admin gets ONE message)
3. **Preview**: Shows message distribution before sending
4. **Send**: Delivers personalized requests to each admin
5. **Track**: Saves list of messaged admins to prevent duplicates

#### Message Format

**For single-group admins:**
```
Hi! [Employee] is no longer with BitSafe - could you please remove @username from "Group Name"? Thanks! -Aki
```

**For multi-group admins:**
```
Hi! [Employee] is no longer with BitSafe - could you please remove @username from these groups:

• Group Name 1
• Group Name 2
• Group Name 3

Thanks! -Aki
```

#### Features

- ✅ **Smart Deduplication**: Each admin gets exactly ONE message
- ✅ **Rate Limiting**: 2-second delay between messages
- ✅ **Error Handling**: Gracefully handles blocked users & privacy restrictions
- ✅ **Tracking**: Prevents duplicate messages on reruns
- ✅ **Dry Run**: Always test before sending

#### Output Files

- `logs/telegram_admin_messages.log` - Detailed execution log
- `logs/telegram_messaged_admins_YYYYMMDD_HHMMSS.txt` - List of messaged admins

#### Success Metrics (Example: Addie's Offboarding)

- **Total Groups**: 193 groups in common
- **Direct Removals**: 106 groups removed automatically
- **Admin Messages**: 58 admins contacted successfully
- **Failed Messages**: 2 (privacy restrictions + invalid username)
- **Total Time**: ~2 minutes for messaging campaign

---

## Timeline & Checklist

### Immediate Actions (Within 1 Hour)

- [ ] **Slack Deactivation**
  - [ ] Deactivate user via Admin UI
  - [ ] Verify removal from all channels
  - [ ] Check audit log entry

- [ ] **Telegram Removal (Phase 1)**
  - [ ] Run dry-run: `telegram_user_delete.py --dry-run`
  - [ ] Review output and groups list
  - [ ] Execute removal: `telegram_user_delete.py`
  - [ ] Save CSV of groups needing admin contact

### Follow-Up Actions (Within 24 Hours)

- [ ] **Telegram Removal (Phase 2)**
  - [ ] Run dry-run: `telegram_message_admins.py --dry-run`
  - [ ] Review message preview
  - [ ] Send admin messages: `telegram_message_admins.py`
  - [ ] Save list of contacted admins

### Verification (Within 48 Hours)

- [ ] **Confirm Removals**
  - [ ] Check Telegram common groups count
  - [ ] Follow up with unresponsive admins
  - [ ] Document any remaining access

- [ ] **Documentation**
  - [ ] Update offboarding log
  - [ ] Save all script outputs
  - [ ] Note any special cases or issues

---

## Troubleshooting

### Slack Issues

**Q: User still appears in some channels after deactivation**  
A: This is a UI caching issue. Force-refresh the page or wait a few minutes.

**Q: Need to reactivate a user**  
A: Go to Admin UI → Deactivated Users → Find user → Reactivate

### Telegram Issues

**Q: Script fails with "SessionPasswordNeededError"**  
A: Add `TELEGRAM_PASSWORD` to your `.env` file for 2FA authentication.

**Q: "Database is locked" error**  
A: Kill any orphaned Python processes and delete `telegram_session.session`.

**Q: Can't remove user from a specific group**  
A: You likely aren't an admin in that group. Use the admin messaging script instead.

**Q: Admin messaging fails with privacy errors**  
A: Some users have privacy settings preventing messages from non-contacts. This is expected and logged.

### Rate Limiting

**Q: Getting rate limited by Telegram**  
A: The scripts include built-in delays. If you hit limits, wait 15-30 minutes before retrying.

---

## Security & Privacy

### Best Practices

1. **Credentials**: Never commit API credentials to Git
2. **Session Files**: Keep `telegram_session.session` secure (it's in `.gitignore`)
3. **Audit Logs**: Keep all output logs for compliance
4. **Message Content**: Review message templates before sending
5. **Dry Runs**: Always test with dry-run mode first

### Data Retention

- Keep script output logs for 90 days minimum
- Archive offboarding tickets with all logs attached
- Document any special circumstances or issues

---

## Script Locations

- **Telegram User Delete**: `scripts/telegram_user_delete.py`
- **Telegram Admin Messaging**: `scripts/telegram_message_admins.py`
- **Detailed Script Documentation**: `scripts/README.md`

---

## Support

For issues or questions:
1. Check `scripts/README.md` for detailed script documentation
2. Review script logs in `logs/` directory
3. Check Slack Admin UI for Slack-related issues
4. Contact IT/DevOps for Telegram API credential issues

---

*Last Updated: November 7, 2024*  
*Version: 1.0*

