# Slack Token Scope Fix

## Problem

The `.env` file was using the wrong Slack token. The BitSafe Export Tool app already has all the necessary scopes, but the `.env` was pointing to a different token.

**Root Cause:**
- ✅ The app has the right scopes (`groups:read`, `groups:history`)
- ❌ The `.env` file had the wrong token (from a different app/workspace)

## Solution (FIXED)

### Quick Fix: Use the Correct Token

The BitSafe Export Tool app (App ID: A09AJJZF718) already has all required scopes. Get the token from:

**https://api.slack.com/apps/A09AJJZF718/oauth**

Copy the "User OAuth Token" and add to `.env`:

```bash
SLACK_USER_TOKEN=xoxp-[COPY-FROM-SLACK-APP-PAGE]
```

This token has:
- ✅ `groups:read`
- ✅ `groups:history`
- ✅ `channels:read`
- ✅ `channels:history`
- ✅ `users:read`

### If You Need to Add Scopes to a Different App

### Step 1: Add OAuth Scopes

1. Go to: https://api.slack.com/apps/A09AJJZF718/oauth
2. Scroll to **"User Token Scopes"** section
3. Click **"Add an OAuth Scope"**
4. Add these scopes:
   - `groups:read` - View basic information about private channels
   - `groups:history` - View messages and other content in private channels
   - `users:read` - View people in workspace (already have)
   - `channels:read` - View basic information about public channels (already have)
   - `channels:history` - View messages in public channels (already have)

### Step 2: Reinstall the App

After adding scopes, you'll see a yellow banner at the top:

> **"Your app's scopes have changed"**  
> **Reinstall your app for these changes to take effect**

Click **"reinstall your app"**

### Step 3: Update Token in .env

After reinstalling, you'll get a new token. Update your `.env` file:

```bash
SLACK_USER_TOKEN=xoxp-NEW-TOKEN-HERE
```

### Step 4: Verify Token Works

Run the verification script:

```bash
python3 scripts/verify_slack_token.py
```

You should see:
```
✅ Token is valid
✅ Has groups:read scope
✅ Has groups:history scope
✅ Can access test channel
```

### Step 5: Run Full Audit

```bash
python3 scripts/customer_group_audit.py
```

Expected output:
```
Total groups audited: 474
   Slack channels: 72
   Telegram groups: 402
```

## Why This is Needed

The 72 BitSafe customer channels are **private channels** (aka "groups" in Slack API terminology). Private channels require special scopes:

- Without `groups:read`: Can't see private channel info
- Without `groups:history`: Can't see private channel messages  
- Without `groups:members`: Can't see who's in the channel

These are **different** from public channel scopes (`channels:*`).

## Verification

Once fixed, the audit will show:
- ✅ 72 Slack channels with team member presence
- ✅ 402 Telegram groups (already working)
- ✅ Combined report with 474 total groups

## Troubleshooting

### "Channel not found" error
- The channel ID might be wrong
- You might not be a member of the channel
- Try with a channel you know you're in

### "Team access not granted" error  
- You're on Enterprise Grid
- Some channels might be in different teams
- Use team_id parameter in API calls

### Still getting "missing_scope"
- Make sure you clicked "Reinstall app" after adding scopes
- Get the NEW token from the OAuth page
- Update your .env file with the new token
- Restart your terminal to reload environment variables

## Alternative: Use Different Slack App

If the above doesn't work, create a new Slack app with the right scopes from the start:

1. Go to: https://api.slack.com/apps
2. Create new app → "From scratch"
3. Name: "BitSafe Audit Tool"
4. Add OAuth scopes (User Token):
   - `channels:read`
   - `channels:history`
   - `groups:read`
   - `groups:history`
   - `users:read`
5. Install to workspace
6. Copy the User OAuth Token
7. Update `.env` with new token

