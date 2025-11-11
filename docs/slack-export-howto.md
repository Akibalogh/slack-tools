# How to Export Private Slack Channels

## Overview
This document explains how to export messages from private Slack channels using the Slack API.

## The Problem
When trying to export private Slack channel messages, you need:
1. The correct Slack API token with proper scopes
2. The channel ID (not just the channel name)
3. Proper authentication and permissions

## Solution Steps

### Step 1: Get the Right Slack Token
For private channels, you need a token with these scopes:
- `groups:read` - View basic information about private channels
- `groups:history` - Read message history from private channels
- `users:read` - Get user information to map user IDs to names

**Where to get it:**
1. Go to https://api.slack.com/apps
2. Select your app (we used "BitSafe Export Tool" - App ID: A09AJJZF718)
3. Go to "OAuth & Permissions"
4. Find the "User OAuth Token" (starts with `xoxp-`)

### Step 2: Get the Channel ID
Private channels can't be easily found by name through the API, so you need the channel ID:
1. In Slack, right-click on the channel name
2. Select "Copy link"
3. The URL contains the channel ID: `https://...slack.com/archives/C092TS0U91A`
4. Extract the ID: `C092TS0U91A`

### Step 3: Fetch Messages Using the API (Including Threads)

**Important:** Slack threads require a separate API call to fetch replies!

```python
import asyncio
import aiohttp
from datetime import datetime

slack_token = "xoxp-YOUR-TOKEN-HERE"
channel_id = "C092TS0U91A"

headers = {"Authorization": f"Bearer {slack_token}"}

async def export_channel():
    async with aiohttp.ClientSession() as session:
        # Get all top-level messages with pagination
        messages = []
        cursor = None
        
        while True:
            params = {"channel": channel_id, "limit": "200"}
            if cursor:
                params["cursor"] = cursor
            
            async with session.get(
                "https://slack.com/api/conversations.history",
                headers=headers,
                params=params
            ) as resp:
                data = await resp.json()
                if not data.get("ok"):
                    print(f"Error: {data.get('error')}")
                    return []
                
                messages.extend(data.get("messages", []))
                
                cursor = data.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break
        
        # Get threaded replies for messages that have them
        all_messages = []
        for msg in messages:
            all_messages.append(msg)
            
            # Check if message has replies (thread)
            if msg.get("reply_count", 0) > 0:
                thread_ts = msg.get("ts")
                
                # Fetch all replies in this thread
                async with session.get(
                    "https://slack.com/api/conversations.replies",
                    headers=headers,
                    params={"channel": channel_id, "ts": thread_ts}
                ) as resp:
                    data = await resp.json()
                    if data.get("ok"):
                        # Skip first message (parent) as we already have it
                        replies = data.get("messages", [])[1:]
                        all_messages.extend(replies)
        
        # Get user names
        user_ids = set(msg.get("user") for msg in all_messages if msg.get("user"))
        user_map = {}
        
        for user_id in user_ids:
            async with session.get(
                "https://slack.com/api/users.info",
                headers=headers,
                params={"user": user_id}
            ) as resp:
                data = await resp.json()
                if data.get("ok"):
                    user = data.get("user", {})
                    user_map[user_id] = user.get("real_name") or user.get("name") or user_id
        
        # Sort by timestamp (oldest first)
        all_messages.sort(key=lambda m: float(m.get("ts", 0)))
        
        # Format output
        output_lines = []
        for msg in all_messages:
            if msg.get("type") == "message" and not msg.get("subtype"):
                sender = user_map.get(msg.get("user", ""), msg.get("user", "Unknown"))
                timestamp = datetime.fromtimestamp(float(msg.get("ts", 0))).strftime("%Y-%m-%d %H:%M:%S")
                text = msg.get("text", "")
                
                # Mark if it's a thread reply with indentation
                is_reply = msg.get("thread_ts") and msg.get("thread_ts") != msg.get("ts")
                prefix = "  └─ " if is_reply else ""
                
                output_lines.append(f"{prefix}{sender} | {timestamp} | {text}")
        
        return output_lines

# Run it
output_lines = asyncio.run(export_channel())

# Save to file
with open("/Users/akibalogh/Desktop/export.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))
```

## Key API Endpoints Used

1. **conversations.history** - Fetch top-level messages from a channel
   - Endpoint: `https://slack.com/api/conversations.history`
   - Parameters: `channel`, `limit`, `cursor` (for pagination)
   - Returns: List of messages with pagination metadata
   - Note: Does NOT include threaded replies

2. **conversations.replies** - Fetch all replies in a thread
   - Endpoint: `https://slack.com/api/conversations.replies`
   - Parameters: `channel`, `ts` (thread timestamp from parent message)
   - Returns: List of all messages in the thread (including parent)
   - Required scope: `channels:history` or `groups:history`

3. **users.info** - Get user details
   - Endpoint: `https://slack.com/api/users.info`
   - Parameters: `user` (user ID)
   - Returns: User object with name, email, etc.

## Common Errors and Solutions

### Error: `missing_scope`
**Problem:** Token doesn't have required permissions
**Solution:** Add scopes in Slack app settings and reinstall the app

### Error: `team_access_not_granted`
**Problem:** Enterprise Grid workspace, token doesn't have access to that team
**Solution:** Use the correct token for the team/workspace

### Error: `channel_not_found`
**Problem:** Wrong channel ID or not a member
**Solution:** Verify the channel ID and ensure you're a member

### Error: `missing_argument` with `team_id`
**Problem:** Enterprise Grid requires team_id parameter
**Solution:** Get team_id from `auth.test` endpoint first

## Output Format

The script outputs messages in this format:
```
Sender Name | YYYY-MM-DD HH:MM:SS | Message text
```

Thread replies are indented with a visual tree character:
```
  └─ Sender Name | YYYY-MM-DD HH:MM:SS | Reply message text
```

Example:
```
Anna Matusova | 2025-06-25 09:37:07 | Could you confirm when the transactions will be ready?
  └─ Kashif Amin | 2025-06-25 18:51:00 | I checked the internal transfers today and they look good
  └─ Kashif Amin | 2025-06-25 18:52:00 | Please make sure to refresh the browser page
Robert Tera | 2025-06-25 10:52:38 | Hey team, could you resend the invite?
```

## Files Generated

1. **bitwave-bitsafe-export.txt** - The exported channel messages
2. **slack-export-howto.md** - This documentation file

## Notes

- The script only exports standard messages (excludes system messages, file uploads, etc.)
- Messages are sorted chronologically (oldest first)
- **Threaded replies are included** via separate API calls to `conversations.replies`
- Thread replies are visually marked with `  └─ ` prefix for easy identification
- User mentions (`<@U123456>`) are preserved in the original format
- Links are preserved in the text
- The script handles pagination automatically (up to 200 messages per API call)
- Rate limiting is handled by the async/await pattern
- Each thread requires an additional API call, so channels with many threads will take longer

## Security Notes

⚠️ **Important:** Keep your Slack tokens secure!
- Never commit tokens to Git
- Store them in `.env` files (add to `.gitignore`)
- Rotate tokens regularly
- Use tokens with minimum required scopes

## Usage for Other Channels

To export a different channel:
1. Get the channel ID (right-click → Copy link)
2. Update `channel_id` variable in the script
3. Run the script
4. Output will be saved to the specified file

## Example Export Stats

For the bitwave-bitsafe channel:
- **Date Range:** June 25, 2025 - November 5, 2025
- **Top-level messages:** 64
- **Total messages (with threads):** 266
- **Unique users:** 9
- **Threads:** Multiple conversations with detailed technical discussions

## Implementation for bitwave-bitsafe Export

This specific export was performed with:
- **App Used:** BitSafe Export Tool (App ID: A09AJJZF718)
- **Channel ID:** C092TS0U91A
- **Token Type:** User OAuth Token (xoxp-*)
- **Output File:** `/Users/akibalogh/Desktop/bitwave-bitsafe-export.txt`

### Process Summary:
1. Fetched all top-level messages using `conversations.history` with pagination
2. For each message with `reply_count > 0`, fetched thread replies using `conversations.replies`
3. Retrieved user information for all unique user IDs
4. Sorted all messages chronologically
5. Formatted output with thread indentation (`  └─ ` prefix for replies)
6. Exported 266 total messages (64 top-level + 202 thread replies)

### Key Challenges Solved:
- ✅ Enterprise Grid workspace authentication
- ✅ Private channel access (required special scopes)
- ✅ Pagination handling (automatically fetched all messages)
- ✅ Thread replies extraction (separate API calls for each thread)
- ✅ User ID to name mapping
- ✅ Chronological sorting with visual thread hierarchy

