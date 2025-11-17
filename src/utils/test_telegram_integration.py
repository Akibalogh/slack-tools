#!/usr/bin/env python3
"""
Test script to verify Telegram integration with commission analysis
"""

import sqlite3
from repsplit import RepSplit

def test_p2p_analysis():
    """Test commission analysis for P2P with both Slack and Telegram data"""
    
    print("🔍 Testing P2P Commission Analysis (Slack + Telegram)")
    print("=" * 60)
    
    # Initialize RepSplit
    repsplit = RepSplit()
    
    # Check Slack data
    conn = sqlite3.connect("data/slack/repsplit.db")
    cursor = conn.cursor()
    
    print("\n📱 SLACK DATA:")
    cursor.execute("""
        SELECT author, COUNT(*) as message_count
        FROM messages 
        WHERE conv_id = 'C0957JB9Q65'
        GROUP BY author
        ORDER BY message_count DESC
    """)
    slack_messages = cursor.fetchall()
    
    for author, count in slack_messages:
        print(f"  {author}: {count} messages")
    
    print("\n📱 TELEGRAM DATA:")
    cursor.execute("""
        SELECT author, COUNT(*) as message_count
        FROM telegram_messages 
        WHERE conv_id = 'p2p-telegram'
        GROUP BY author
        ORDER BY message_count DESC
    """)
    telegram_messages = cursor.fetchall()
    
    for author, count in telegram_messages:
        print(f"  {author}: {count} messages")
    
    conn.close()
    
    print("\n💰 COMMISSION CALCULATION:")
    
    # Test Slack-only analysis
    print("\n  Slack Only (p2p-bitsafe):")
    slack_splits = repsplit.calculate_commission_splits('C0957JB9Q65')
    for participant, commission in slack_splits.items():
        print(f"    {participant}: {commission}%")
    
    # Test Telegram-only analysis  
    print("\n  Telegram Only (P2P):")
    telegram_splits = repsplit.calculate_commission_splits('p2p-telegram')
    for participant, commission in telegram_splits.items():
        print(f"    {participant}: {commission}%")

if __name__ == "__main__":
    test_p2p_analysis()
