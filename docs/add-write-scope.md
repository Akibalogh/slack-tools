# Adding Write Permissions to Slack Token

## Problem
The current Slack tokens have **read-only** permissions. To add members to channels, we need **write** permissions.

## Solution: Add Required Scopes

### Step 1: Go to Your Slack App
Visit: https://api.slack.com/apps/A09AJJZF718/oauth

### Step 2: Add User Token Scopes
Under **User Token Scopes**, add these two scopes:
- ✅ `groups:write` - Manage private channels (add/remove members)
- ✅ `channels:write` - Manage public channels (add/remove members)

### Step 3: Save & Reinstall
1. Click **Save Changes** at the bottom
2. Scroll to the top and click **Reinstall to Workspace**
3. Review permissions and click **Allow**

### Step 4: Update Token
1. After reinstalling, copy the new **User OAuth Token** (starts with `xoxp-`)
2. Update your `.env` file:
   ```bash
   SLACK_USER_TOKEN=xoxp-[your-new-token]
   ```

### Step 5: Test
Run the test script:
```bash
python3 scripts/add_members_to_channels.py aliya kevin --dry-run
```

## Current Scopes (Read-Only)
The token currently has:
- `channels:history` - View public channel messages
- `channels:read` - View public channel info
- `groups:history` - View private channel messages
- `groups:read` - View private channel info
- `im:history` - View direct messages
- `im:read` - View direct message info
- `mpim:history` - View group DM messages
- `mpim:read` - View group DM info
- `users:read` - View workspace users

## Required Additional Scopes (Write)
Need to add:
- `groups:write` - **Add/remove members from private channels**
- `channels:write` - **Add/remove members from public channels**

## Alternative: Use Admin API
If you prefer not to modify the app, you can also use Slack's Admin API with a different token that has `admin.conversations.write` scope. However, this requires Slack Enterprise Grid with Organization-level admin permissions.

