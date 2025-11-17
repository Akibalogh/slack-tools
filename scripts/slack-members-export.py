from dotenv import load_dotenv
import os
import asyncio
import aiohttp
import time
import pandas as pd

# Load environment variables from .env
load_dotenv()
SLACK_TOKEN = os.getenv("SLACK_USER_TOKEN") or os.getenv("SLACK_TOKEN")
# List of channels to process: (channel_id, channel_name)
CHANNELS = [
    ("C08PT9P8ERM", "#gsf-outreach"),
    ("C08AP9QR7K4", "#validator-operations"),
    ("C08338ZAL9X", "#utility-ops"),
    ("C08PT9P8ERM", "#gsf-app-dev"),  # Add gsf-app-dev group
]
TEST_MODE = False  # Set to False to fetch all users for production
MAX_CONCURRENT_REQUESTS = 10  # Limit concurrent requests to avoid rate limiting

if not SLACK_TOKEN:
    print("❌ SLACK_USER_TOKEN (or SLACK_TOKEN) not found in .env file.")
    exit(1)

headers = {"Authorization": f"Bearer {SLACK_TOKEN}"}


async def get_channel_members(session, channel_id, channel_name):
    """Get all member IDs from a channel"""
    print(f"\n🔄 Fetching member IDs from channel: {channel_name} ({channel_id})")

    user_ids = []
    cursor = None
    page = 1

    while True:
        print(f"📄 Fetching page {page} of member list...")
        url = f"https://slack.com/api/conversations.members?channel={channel_id}&limit=1000"
        if cursor:
            url += f"&cursor={cursor}"

        async with session.get(url, headers=headers) as resp:
            data = await resp.json()
            user_ids.extend(data.get("members", []))
            cursor = data.get("response_metadata", {}).get("next_cursor", "")
            if not cursor:
                break
            page += 1
            await asyncio.sleep(0.1)  # Reduced delay

    print(f"✅ Found {len(user_ids)} member IDs in {channel_name}.")
    return user_ids


async def get_user_profile(session, user_id, channel_name):
    """Get user profile information"""
    url = f"https://slack.com/api/users.info?user={user_id}"
    async with session.get(url, headers=headers) as resp:
        data = await resp.json()
        if data.get("ok"):
            profile = data["user"]["profile"]
            return {
                "channel": channel_name,
                "id": user_id,
                "name": profile.get("real_name", ""),
                "email": profile.get("email", ""),
            }
        else:
            return {
                "channel": channel_name,
                "id": user_id,
                "name": "ERROR",
                "email": data.get("error", ""),
            }


async def process_users_concurrently(session, user_ids, channel_name):
    """Process users concurrently with rate limiting"""
    if TEST_MODE:
        print("⚠️ TEST MODE ENABLED: Fetching only the first user.\n")
        user_ids = user_ids[:1]

    print(f"🔍 Fetching user details for {len(user_ids)} users...")

    # Create semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async def get_user_with_semaphore(user_id):
        async with semaphore:
            return await get_user_profile(session, user_id, channel_name)

    # Process users concurrently
    tasks = [get_user_with_semaphore(uid) for uid in user_ids]
    results = await asyncio.gather(*tasks)

    return results


async def main():
    """Main async function"""
    all_results = []

    async with aiohttp.ClientSession() as session:
        for channel_id, channel_name in CHANNELS:
            # Get member IDs for this channel
            user_ids = await get_channel_members(session, channel_id, channel_name)

            # Get user profiles concurrently
            channel_results = await process_users_concurrently(
                session, user_ids, channel_name
            )
            all_results.extend(channel_results)

    print("\n💾 Writing to slack_members.xlsx ...")
    df = pd.DataFrame(all_results)
    # Drop duplicates by 'id' (or 'email' if you prefer)
    df = df.drop_duplicates(subset=["id"])
    # Reorder columns to have channel first
    cols = ["channel", "id", "name", "email"]
    df = df[cols]
    df.to_excel("slack_members.xlsx", index=False)
    print("✅ Done. File saved as slack_members.xlsx")


if __name__ == "__main__":
    asyncio.run(main())
