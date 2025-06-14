from dotenv import load_dotenv
import os
import requests
import time
import pandas as pd

# Load SLACK_TOKEN from .env file
load_dotenv()
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
CHANNEL_ID = "C08PT9P8ERM"

if not SLACK_TOKEN:
    print("❌ SLACK_TOKEN not found in .env file.")
    exit(1)

headers = {
    "Authorization": f"Bearer {SLACK_TOKEN}"
}

print("🔄 Fetching member IDs from channel:", CHANNEL_ID)
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

print(f"✅ Found {len(user_ids)} member IDs.\n")

print("🔍 Fetching user details...")
results = []

for i, uid in enumerate(user_ids, 1):
    print(f"   [{i}/{len(user_ids)}] Getting profile for {uid}...")
    url = f"https://slack.com/api/users.info?user={uid}"
    data = requests.get(url, headers=headers).json()
    if data.get("ok"):
        profile = data["user"]["profile"]
        results.append({
            "id": uid,
            "name": profile.get("real_name", ""),
            "email": profile.get("email", "")
        })
    else:
        results.append({
            "id": uid,
            "name": "ERROR",
            "email": data.get("error", "")
        })
    time.sleep(1)

print("\n💾 Writing to slack_members.xlsx ...")
df = pd.DataFrame(results)
df.to_excel("slack_members.xlsx", index=False)

print("✅ Done. File saved as slack_members.xlsx")
