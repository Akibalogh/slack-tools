from dotenv import load_dotenv
import os
import requests
import time
import pandas as pd

# Load environment variables from .env
load_dotenv()
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
# List of channels to process: (channel_id, channel_name)
CHANNELS = [
    ("C08PT9P8ERM", "#gsf-outreach"),
    ("C08AP9QR7K4", "#validator-operations"),
    ("C08338ZAL9X", "#utility-ops"),
]
TEST_MODE = False  # Set to False to fetch all users for production

if not SLACK_TOKEN:
    print("❌ SLACK_TOKEN not found in .env file.")
    exit(1)

headers = {
    "Authorization": f"Bearer {SLACK_TOKEN}"
}

all_results = []

for CHANNEL_ID, CHANNEL_NAME in CHANNELS:
    print(f"\n🔄 Fetching member IDs from channel: {CHANNEL_NAME} ({CHANNEL_ID})")
user_ids = []
cursor = None
page = 1

while True:
    print(f"📄 Fetching page {page} of member list...")
    url = f"https://slack.com/api/conversations.members?channel={CHANNEL_ID}&limit=1000"
    if cursor:
        url += f"&cursor={cursor}"
    resp = requests.get(url, headers=headers).json()
    user_ids.extend(resp.get("members", []))
    cursor = resp.get("response_metadata", {}).get("next_cursor", "")
    if not cursor:
        break
    page += 1
    time.sleep(1)

    print(f"✅ Found {len(user_ids)} member IDs in {CHANNEL_NAME}.")

# TEST MODE: limit to 1 user
if TEST_MODE:
    print("⚠️ TEST MODE ENABLED: Fetching only the first user.\n")
    user_ids = user_ids[:1]

print("🔍 Fetching user details...")
for i, uid in enumerate(user_ids, 1):
    print(f"   [{i}/{len(user_ids)}] Getting profile for {uid}...")
    url = f"https://slack.com/api/users.info?user={uid}"
    data = requests.get(url, headers=headers).json()
    if data.get("ok"):
        profile = data["user"]["profile"]
            all_results.append({
                "channel": CHANNEL_NAME,
            "id": uid,
            "name": profile.get("real_name", ""),
            "email": profile.get("email", "")
        })
    else:
            all_results.append({
                "channel": CHANNEL_NAME,
            "id": uid,
            "name": "ERROR",
            "email": data.get("error", "")
        })
    time.sleep(1)

print("\n💾 Writing to slack_members.xlsx ...")
df = pd.DataFrame(all_results)
# Drop duplicates by 'id' (or 'email' if you prefer)
df = df.drop_duplicates(subset=["id"])
# Reorder columns to have channel first
cols = ["channel", "id", "name", "email"]
df = df[cols]
df.to_excel("slack_members.xlsx", index=False)
print("✅ Done. File saved as slack_members.xlsx")
