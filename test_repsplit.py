#!/usr/bin/env python3
"""
Test script for RepSplit commission calculation logic
"""

import sqlite3
from datetime import datetime
import os

def create_test_data():
    """Create test data in the database"""
    db_path = "repsplit.db"
    
    # Remove existing database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE conversations (
            conv_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            member_count INTEGER,
            creation_date INTEGER,
            is_bitsafe BOOLEAN DEFAULT FALSE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            display_name TEXT,
            real_name TEXT,
            email TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE messages (
            id TEXT PRIMARY KEY,
            conv_id TEXT,
            timestamp REAL,
            author TEXT,
            text TEXT,
            stage_hits TEXT,
            FOREIGN KEY (conv_id) REFERENCES conversations (conv_id),
            FOREIGN KEY (author) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE stage_detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conv_id TEXT,
            stage_name TEXT,
            message_id TEXT,
            author TEXT,
            timestamp REAL,
            confidence REAL,
            FOREIGN KEY (conv_id) REFERENCES conversations (conv_id),
            FOREIGN KEY (message_id) REFERENCES messages (id),
            FOREIGN KEY (author) REFERENCES users (id)
        )
    ''')
    
    # Insert test data
    cursor.execute('''
        INSERT INTO conversations (conv_id, name, member_count, creation_date, is_bitsafe)
        VALUES (?, ?, ?, ?, ?)
    ''', ("C123", "test-bitsafe", 5, int(datetime.now().timestamp()), True))
    
    # Insert test users
    test_users = [
        ("U001", "Aki", "Aki Test", "aki@test.com"),
        ("U002", "Addie", "Addie Test", "addie@test.com"),
        ("U003", "Amy", "Amy Test", "amy@test.com"),
        ("U004", "Mayank", "Mayank Test", "mayank@test.com"),
    ]
    
    for user in test_users:
        cursor.execute('''
            INSERT INTO users (id, display_name, real_name, email)
            VALUES (?, ?, ?, ?)
        ''', user)
    
    # Insert test messages with stage signals
    test_messages = [
        ("M001", "C123", datetime.now().timestamp(), "U001", "Hi, let me introduce our solution", ""),
        ("M002", "C123", datetime.now().timestamp(), "U002", "What are your use case requirements?", ""),
        ("M003", "C123", datetime.now().timestamp(), "U003", "Here's our proposal and deck", ""),
        ("M004", "C123", datetime.now().timestamp(), "U001", "Let's discuss pricing and terms", ""),
        ("M005", "C123", datetime.now().timestamp(), "U004", "Schedule a follow-up meeting", ""),
        ("M006", "C123", datetime.now().timestamp(), "U002", "Great! Deal is signed and closed", ""),
    ]
    
    for msg in test_messages:
        cursor.execute('''
            INSERT INTO messages (id, conv_id, timestamp, author, text, stage_hits)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', msg)
    
    # Insert stage detections
    stage_detections = [
        ("C123", "first_touch", "M001", "U001", datetime.now().timestamp(), 0.8),
        ("C123", "discovery", "M002", "U002", datetime.now().timestamp(), 0.9),
        ("C123", "solutioning", "M003", "U003", datetime.now().timestamp(), 0.8),
        ("C123", "negotiation", "M004", "U001", datetime.now().timestamp(), 0.9),
        ("C123", "scheduling_ops", "M005", "U004", datetime.now().timestamp(), 0.7),
        ("C123", "closing", "M006", "U002", datetime.now().timestamp(), 0.9),
    ]
    
    for stage in stage_detections:
        cursor.execute('''
            INSERT INTO stage_detections (conv_id, stage_name, message_id, author, timestamp, confidence)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', stage)
    
    conn.commit()
    conn.close()
    
    print("✅ Test data created successfully!")
    print("Database contains:")
    print("- 1 bitsafe channel: test-bitsafe")
    print("- 4 users: Aki, Addie, Amy, Mayank")
    print("- 6 messages with stage signals")
    print("- 6 stage detections across all stages")

if __name__ == "__main__":
    create_test_data()
