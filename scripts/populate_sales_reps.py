#!/usr/bin/env python3
"""
Script to populate the sales_reps table with current team members.

This script ensures that only authorized sales representatives can move deals forward
and earn commission in the system.
"""

import os
import sqlite3
from pathlib import Path


def get_db_path():
    """Get the database path."""
    # Look for the database in common locations
    possible_paths = [
        "repsplit.db",
        "data/repsplit.db",
        "src/orm/repsplit.db",
        ".taskmaster/repsplit.db",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    # If not found, create in current directory
    return "repsplit.db"


def create_sales_reps_table(db_path: str):
    """Create the sales_reps table if it doesn't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create sales_reps table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sales_reps (
            user_id TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            real_name TEXT,
            email TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            role TEXT DEFAULT 'sales_rep',
            commission_rate REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Add is_sales_rep column to users table if it doesn't exist
    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN is_sales_rep BOOLEAN DEFAULT FALSE"
        )
    except sqlite3.OperationalError:
        # Column already exists
        pass

    # Add author_is_sales_rep column to stage_detections table if it doesn't exist
    try:
        cursor.execute(
            "ALTER TABLE stage_detections ADD COLUMN author_is_sales_rep BOOLEAN DEFAULT FALSE"
        )
    except sqlite3.OperationalError:
        # Column already exists
        pass

    # Add author_is_sales_rep column to messages table if it doesn't exist
    try:
        cursor.execute(
            "ALTER TABLE messages ADD COLUMN author_is_sales_rep BOOLEAN DEFAULT FALSE"
        )
    except sqlite3.OperationalError:
        # Column already exists
        pass

    conn.commit()
    conn.close()


def populate_sales_reps(db_path: str):
    """Populate the sales_reps table with current team members."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Clear existing sales reps to ensure clean state
    cursor.execute("DELETE FROM sales_reps")

    # Current sales team members
    # NOTE: Kadeem, Prateek, and Will are NOT sales reps - they are support/operations staff
    sales_reps = [
        ("aki", "Aki", "Aki Balogh", "aki@bitsafe.com", "sales_rep", None),
        ("addie", "Addie", "Addie Tackman", "addie@bitsafe.com", "sales_rep", None),
        ("amy", "Amy", "Amy", "amy@bitsafe.com", "sales_rep", None),
        ("mayank", "Mayank", "Mayank", "mayank@bitsafe.com", "sales_rep", None),
        # Excluded: Kadeem, Prateek, Will - they are NOT sales representatives
    ]

    # Insert or update sales reps
    for user_id, display_name, real_name, email, role, commission_rate in sales_reps:
        cursor.execute(
            """
            INSERT OR REPLACE INTO sales_reps
            (user_id, display_name, real_name, email, role, commission_rate)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (user_id, display_name, real_name, email, role, commission_rate),
        )

        # Also update the users table to mark them as sales reps
        cursor.execute(
            """
            INSERT OR REPLACE INTO users (id, display_name, real_name, email, is_sales_rep)
            VALUES (?, ?, ?, ?, TRUE)
        """,
            (user_id, display_name, real_name, email),
        )

    # Update existing users in the database to mark known sales reps
    known_sales_reps = [rep[0] for rep in sales_reps]

    # First, clear all sales rep flags to ensure clean state
    cursor.execute("UPDATE users SET is_sales_rep = FALSE")

    # Update by display name matches
    # NOTE: Only update actual sales reps - Kadeem, Prateek, Will are excluded
    for display_name in ["Aki", "Addie", "Amy", "Mayank"]:
        cursor.execute(
            """
            UPDATE users SET is_sales_rep = TRUE
            WHERE display_name LIKE ? OR real_name LIKE ?
        """,
            (f"%{display_name}%", f"%{display_name}%"),
        )

    conn.commit()
    conn.close()


def update_existing_data(db_path: str):
    """Update existing stage detections and messages to mark sales rep authors."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # First, clear all authorization flags to ensure clean state
    cursor.execute("UPDATE stage_detections SET author_is_sales_rep = FALSE")
    cursor.execute("UPDATE messages SET author_is_sales_rep = FALSE")

    # Get all sales rep user IDs
    cursor.execute("SELECT user_id FROM sales_reps WHERE is_active = TRUE")
    sales_rep_ids = [row[0] for row in cursor.fetchall()]

    # Update stage_detections table
    for user_id in sales_rep_ids:
        cursor.execute(
            """
            UPDATE stage_detections
            SET author_is_sales_rep = TRUE
            WHERE author = ? OR author LIKE ?
        """,
            (user_id, f"%{user_id}%"),
        )

    # Update messages table
    for user_id in sales_rep_ids:
        cursor.execute(
            """
            UPDATE messages
            SET author_is_sales_rep = TRUE
            WHERE author = ? OR author LIKE ?
        """,
            (user_id, f"%{user_id}%"),
        )

    # Also update by display name patterns
    # NOTE: Only update actual sales reps - Kadeem, Prateek, Will are excluded
    sales_rep_names = ["Aki", "Addie", "Amy", "Mayank"]
    for name in sales_rep_names:
        cursor.execute(
            """
            UPDATE stage_detections
            SET author_is_sales_rep = TRUE
            WHERE author LIKE ?
        """,
            (f"%{name}%",),
        )

        cursor.execute(
            """
            UPDATE messages
            SET author_is_sales_rep = TRUE
            WHERE author LIKE ?
        """,
            (f"%{name}%",),
        )

    conn.commit()
    conn.close()


def verify_sales_reps(db_path: str):
    """Verify that sales reps are properly configured."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=== Sales Representatives Configuration ===")

    # Check sales_reps table
    cursor.execute(
        "SELECT user_id, display_name, real_name, role, is_active FROM sales_reps"
    )
    sales_reps = cursor.fetchall()

    print(f"\nTotal Sales Reps: {len(sales_reps)}")
    for user_id, display_name, real_name, role, is_active in sales_reps:
        status = "ACTIVE" if is_active else "INACTIVE"
        print(f"  - {display_name} ({user_id}): {role} - {status}")

    # Check users table
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_sales_rep = TRUE")
    sales_rep_users = cursor.fetchone()[0]
    print(f"\nUsers marked as Sales Reps: {sales_rep_users}")

    # Check stage detections
    cursor.execute(
        "SELECT COUNT(*) FROM stage_detections WHERE author_is_sales_rep = TRUE"
    )
    authorized_stages = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM stage_detections WHERE author_is_sales_rep = FALSE"
    )
    unauthorized_stages = cursor.fetchone()[0]

    print(f"\nStage Detections:")
    print(f"  - Authorized Sales Reps: {authorized_stages}")
    print(f"  - Unauthorized Users: {unauthorized_stages}")

    # Check messages
    cursor.execute("SELECT COUNT(*) FROM messages WHERE author_is_sales_rep = TRUE")
    authorized_messages = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM messages WHERE author_is_sales_rep = FALSE")
    unauthorized_messages = cursor.fetchone()[0]

    print(f"\nMessages:")
    print(f"  - Authorized Sales Reps: {authorized_messages}")
    print(f"  - Unauthorized Users: {unauthorized_messages}")

    conn.close()


def main():
    """Main function to populate sales reps."""
    db_path = get_db_path()

    print(f"Using database: {db_path}")

    # Create tables and columns
    print("Creating sales rep tables and columns...")
    create_sales_reps_table(db_path)

    # Populate with current team
    print("Populating sales reps table...")
    populate_sales_reps(db_path)

    # Update existing data
    print("Updating existing data with sales rep flags...")
    update_existing_data(db_path)

    # Verify configuration
    print("Verifying configuration...")
    verify_sales_reps(db_path)

    print("\n✅ Sales reps configuration complete!")
    print("\nKey Changes:")
    print("  - Only authorized sales reps can move deals forward")
    print("  - Non-sales rep contributions are weighted at 50%")
    print("  - Commission calculations respect sales rep authorization")
    print("  - U_____ users (non-sales reps) cannot earn commission")


if __name__ == "__main__":
    main()
