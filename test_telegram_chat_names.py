#!/usr/bin/env python3
"""
Test script to see what chat names are being generated from Telegram data
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from etl.etl_data_ingestion import process_telegram_chat_worker

def test_chat_names():
    """Test what chat names are generated from Telegram data"""
    
    telegram_export_path = "data/telegram/DataExport_2025-08-19/chats"
    
    # Test first 10 chats
    for i in range(1, 11):
        chat_dir = f"chat_{i:04d}"
        chat_path = os.path.join(telegram_export_path, chat_dir)
        
        if os.path.exists(chat_path):
            result = process_telegram_chat_worker(chat_dir, telegram_export_path)
            if result:
                print(f"{chat_dir}: {result['chat_name']} ({result['message_count']} msgs)")
                print(f"  Participants: {result['participants'][:3]}...")
            else:
                print(f"{chat_dir}: No data")

if __name__ == "__main__":
    test_chat_names()
