#!/usr/bin/env python3
"""
Create Clean Telegram Match Table

Generate a simple, clean table showing actual Telegram group names
for companies in the CRM pipeline.
"""

import csv
import re
from pathlib import Path

def load_hubspot_companies():
    """Load companies from HubSpot CSV"""
    companies = []
    with open("data/hubspot/hubspot-crm-exports-all-deals-2025-08-11-1.csv", 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Deal Name'] and row['Deal Name'].strip():
                company = re.sub(r' - Minter Upsell$| — Minter Upsell$| Minter upsell$', '', row['Deal Name'].strip())
                companies.append(company)
    return companies

def extract_telegram_groups():
    """Extract Telegram group names from chats list"""
    groups = {}
    
    with open("data/telegram/DataExport_2025-08-19/lists/chats.html", 'r') as f:
        content = f.read()
    
    # Simple regex to extract chat directories and names
    import re
    pattern = r'href="\.\./chats/(chat_\d+)/messages\.html[^"]*"[^>]*>([^<]+)</a>'
    matches = re.findall(pattern, content)
    
    for chat_dir, group_name in matches:
        groups[chat_dir] = group_name.strip()
    
    return groups

def find_matches(companies, groups):
    """Find matches between companies and Telegram groups"""
    matches = []
    
    for company in companies:
        best_match = None
        best_quality = "none"
        
        for chat_dir, group_name in groups.items():
            quality = assess_match_quality(company, group_name)
            if quality != "none" and (best_match is None or is_better_match(quality, best_quality)):
                best_match = (chat_dir, group_name, quality)
                best_quality = quality
        
        if best_match:
            chat_dir, group_name, quality = best_match
            matches.append((company, chat_dir, group_name, quality))
        else:
            matches.append((company, "", "", "none"))
    
    return matches

def assess_match_quality(company, group_name):
    """Assess match quality"""
    company_lower = company.lower()
    group_lower = group_name.lower()
    
    if company_lower == group_lower:
        return "exact"
    elif company_lower in group_lower:
        return "company_in_group"
    elif group_lower in company_lower:
        return "group_in_company"
    
    # Word overlap
    company_words = set(company_lower.split())
    group_words = set(group_lower.split())
    overlap = company_words.intersection(group_words)
    
    if len(overlap) >= 2:
        return "word_overlap"
    elif len(overlap) == 1:
        return "single_word"
    
    return "none"

def is_better_match(quality1, quality2):
    """Determine if quality1 is better than quality2"""
    quality_order = ["exact", "company_in_group", "group_in_company", "word_overlap", "single_word", "none"]
    return quality_order.index(quality1) < quality_order.index(quality2)

def main():
    print("🔍 Loading HubSpot companies...")
    companies = load_hubspot_companies()
    print(f"   Loaded {len(companies)} companies")
    
    print("🔍 Extracting Telegram groups...")
    groups = extract_telegram_groups()
    print(f"   Found {len(groups)} Telegram groups")
    
    print("🔍 Finding matches...")
    matches = find_matches(companies, groups)
    
    # Create clean table
    print("\n📊 TELEGRAM MATCH VERIFICATION TABLE")
    print("=" * 80)
    print(f"{'Company':<30} {'Chat Dir':<12} {'Match Quality':<15} {'Telegram Group Name'}")
    print("-" * 80)
    
    # Show only companies with matches
    companies_with_matches = [m for m in matches if m[3] != "none"]
    
    for company, chat_dir, group_name, quality in companies_with_matches:
        # Truncate long names for display
        company_display = company[:28] + ".." if len(company) > 30 else company
        group_display = group_name[:50] + ".." if len(group_name) > 52 else group_name
        
        print(f"{company_display:<30} {chat_dir:<12} {quality:<15} {group_display}")
    
    print(f"\n📊 Summary:")
    print(f"   Total companies: {len(companies)}")
    print(f"   Companies with matches: {len(companies_with_matches)}")
    print(f"   Match rate: {len(companies_with_matches)/len(companies)*100:.1f}%")
    
    # Show specific companies of interest
    print(f"\n🔍 Key Companies Check:")
    key_companies = ["P2P", "ChainSafe", "Copper", "Chata AI", "T-Rize", "Vigil", "Igor Gusarov"]
    
    for key_company in key_companies:
        found = False
        for company, chat_dir, group_name, quality in companies_with_matches:
            if key_company.lower() in company.lower():
                print(f"   ✅ {company} → {chat_dir} ({quality})")
                found = True
                break
        if not found:
            print(f"   ❌ {key_company} - No Telegram match found")

if __name__ == "__main__":
    main()
