#!/usr/bin/env python3
"""
Update employee data in admin panel database with correct Slack/Telegram info
"""
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent / "webapp"))
from database import Database

# Initialize database
db = Database()
conn = db.get_connection()
cursor = conn.cursor()

# Updated employee data with correct usernames and IDs
updates = [
    {
        "id": 1,  # Aki
        "slack_username": "akibalogh",
        "slack_user_id": "U05FZBDQ4RJ",
        "telegram_username": "akibalogh"
    },
    {
        "id": 2,  # Gabi
        "slack_username": "gabitui",
        "slack_user_id": "U04QGJC7MCU",  # Need to verify
        "telegram_username": None
    },
    {
        "id": 3,  # Mayank
        "slack_username": "mojo_onchain",
        "slack_user_id": "U04PBFZJJ9R",  # Need to verify
        "telegram_username": "mojo_onchain"
    },
    {
        "id": 4,  # Kadeem
        "slack_username": "kadeemclarke",
        "slack_user_id": "U08JNLKMH60",
        "telegram_username": None
    },
    {
        "id": 5,  # Amy
        "slack_username": "NonFungibleAmy",
        "slack_user_id": "U05J9GZJ70E",  # Need to verify
        "telegram_username": None
    },
    {
        "id": 6,  # Kevin
        "slack_username": "kevin",
        "slack_user_id": "U09S1JLS6EN",
        "telegram_username": None
    },
    {
        "id": 7,  # Aliya
        "slack_username": "aliya",
        "slack_user_id": "U09RZH933NJ",
        "telegram_username": None
    },
    {
        "id": 8,  # Dave
        "slack_username": "dave",
        "slack_user_id": "U0997HN7KPE",
        "telegram_username": None
    },
    {
        "id": 9,  # Dae
        "slack_username": "Dae_L",
        "slack_user_id": "U09KR1HKMND",
        "telegram_username": None,
        "status": "active",
        "slack_required": True
    }
]

print("🔄 Updating employee data...\n")

for update in updates:
    emp_id = update.pop("id")
    
    # Build UPDATE query dynamically
    fields = []
    values = []
    for key, value in update.items():
        fields.append(f"{key} = ?")
        values.append(value)
    
    values.append(emp_id)
    
    query = f"UPDATE employees SET {', '.join(fields)} WHERE id = ?"
    cursor.execute(query, values)
    
    # Get employee name
    cursor.execute("SELECT name FROM employees WHERE id = ?", (emp_id,))
    name = cursor.fetchone()[0]
    print(f"✓ Updated {name}")

conn.commit()
conn.close()

print("\n✅ All employees updated!")


