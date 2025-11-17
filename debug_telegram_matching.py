#!/usr/bin/env python3
"""
Debug script to analyze Telegram matching issues
"""

import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from etl.utils.company_matcher import CompanyMatcher
from etl.etl_data_ingestion import DataETL

def analyze_telegram_matching():
    """Analyze why Telegram matching is so low"""
    
    # Load company mapping using ETL
    etl = DataETL()
    companies = etl.load_company_mapping()
    
    # Get sample of company names
    company_names = list(companies.keys())[:20]
    print(f"Analyzing matching for {len(company_names)} sample companies...")
    
    # Get sample chat names from Telegram data
    telegram_export_path = "data/telegram/DataExport_2025-08-19/chats"
    if not os.path.exists(telegram_export_path):
        print(f"Telegram export not found: {telegram_export_path}")
        return
    
    # Get first 50 chat directories
    chat_dirs = [d for d in os.listdir(telegram_export_path) if os.path.isdir(os.path.join(telegram_export_path, d))][:50]
    
    print(f"\nSample chat directories:")
    for i, chat_dir in enumerate(chat_dirs[:10]):
        print(f"{i+1:2d}. {chat_dir}")
    
    # Test matching for each company against each chat
    matches_found = 0
    total_tests = 0
    company_matcher = CompanyMatcher()
    
    print(f"\nTesting matches...")
    for company_name in company_names:
        company_info = companies[company_name]
        
        for chat_dir in chat_dirs:
            # Generate chat name (simplified version of the actual logic)
            chat_name = f"{chat_dir}-telegram"
            
            # Test matching
            is_match = company_matcher._match_telegram_chat(company_name, company_info, chat_name)
            total_tests += 1
            
            if is_match:
                matches_found += 1
                print(f"✅ MATCH: {company_name} <-> {chat_name}")
    
    print(f"\nResults:")
    print(f"Total tests: {total_tests}")
    print(f"Matches found: {matches_found}")
    print(f"Match rate: {matches_found/total_tests*100:.1f}%")
    
    # Analyze chat name patterns
    print(f"\nChat name analysis:")
    chat_patterns = {}
    for chat_dir in chat_dirs:
        # Extract potential company names from directory name
        parts = chat_dir.split('_')
        if len(parts) > 1:
            pattern = f"{len(parts)}_parts"
        else:
            pattern = "single_word"
        
        if pattern not in chat_patterns:
            chat_patterns[pattern] = []
        chat_patterns[pattern].append(chat_dir)
    
    for pattern, examples in chat_patterns.items():
        print(f"{pattern}: {len(examples)} chats")
        print(f"  Examples: {examples[:3]}")

if __name__ == "__main__":
    analyze_telegram_matching()
