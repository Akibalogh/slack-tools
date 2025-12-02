#!/usr/bin/env python3
"""
Extract Real Telegram Matches

Carefully extract only the Telegram groups that have genuine matches
with HubSpot companies, avoiding false positives.
"""

import csv
import re
from pathlib import Path

from bs4 import BeautifulSoup


def load_hubspot_companies():
    """Load companies from HubSpot CSV"""
    companies = []
    with open("data/hubspot/hubspot-crm-exports-all-deals-2025-08-11-1.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Deal Name"] and row["Deal Name"].strip():
                company = re.sub(
                    r" - Minter Upsell$| — Minter Upsell$| Minter upsell$",
                    "",
                    row["Deal Name"].strip(),
                )
                companies.append(company)
    return companies


def extract_telegram_groups():
    """Extract all Telegram group names and their chat directories, excluding DMs"""
    groups = {}
    all_chats = []

    with open(
        "data/telegram/DataExport_2025-08-19/lists/chats.html", "r", encoding="utf-8"
    ) as f:
        content = f.read()

    soup = BeautifulSoup(content, "html.parser")

    for link in soup.find_all("a"):
        href = link.get("href", "")
        if "chat_" in href:
            # Extract chat directory
            parts = href.split("/")
            if len(parts) >= 3:
                chat_dir = parts[2]
                group_name = link.get_text().strip()
                all_chats.append((chat_dir, group_name))

                # Filter for actual group chats - look for dividers that indicate multiple participants
                # Groups typically have <> separators (most common), or / or - in rare cases
                if (
                    "<>" in group_name
                    or "&lt;&gt;" in group_name  # HTML encoded <>
                    or "/" in group_name
                    or " - "
                    in group_name  # Note: space-dash-space to avoid false positives
                    or any(
                        indicator in group_name.lower()
                        for indicator in ["group", "team", "channel", "community"]
                    )
                ):
                    groups[chat_dir] = group_name

    # Debug: Show some examples
    print(f"   Total chats found: {len(all_chats)}")
    print(f"   Groups after filtering: {len(groups)}")
    print(f"   Sample chats (first 10):")
    for i, (chat_dir, name) in enumerate(all_chats[:10]):
        print(f"     {chat_dir}: {name}")
    print(f"   Sample groups (first 10):")
    for i, (chat_dir, name) in enumerate(list(groups.items())[:10]):
        print(f"     {chat_dir}: {name}")

    return groups


def find_real_matches(companies, groups):
    """Find only real matches with strict criteria"""
    real_matches = []

    # Now do the actual matching for all companies
    for company in companies:
        best_match = None
        best_quality = "none"

        for chat_dir, group_name in groups.items():
            quality = assess_match_quality_strict(company, group_name)
            if quality != "none" and (
                best_match is None or is_better_match(quality, best_quality)
            ):
                best_match = (chat_dir, group_name, quality)
                best_quality = quality

        if best_match and best_quality in ["exact", "company_in_group"]:
            chat_dir, group_name, quality = best_match
            real_matches.append((company, chat_dir, group_name, quality))

    return real_matches


def assess_match_quality_strict(company, group_name):
    """Strict assessment of match quality - only real company group matches"""
    company_lower = company.lower().strip()
    group_lower = group_name.lower().strip()

    # Skip only truly generic groups (not company groups that happen to contain "group")
    # Generic groups are ones that are just named "group", "team", etc. without company names
    generic_only_groups = [
        "group",
        "community",
        "team",
        "channel",
        "chat",
        "general",
        "private",
    ]
    if group_lower.strip() in generic_only_groups:
        return "none"

    # Skip individual names (DMs) - look for group dividers
    if not (
        "<>" in group_name
        or "&lt;&gt;" in group_name
        or "/" in group_name
        or " - " in group_name
    ):
        # If no group divider, it's likely a DM
        return "none"

    # Exact match
    if company_lower == group_lower:
        return "exact"

    # Company name is contained in group name (most reliable)
    if company_lower in group_lower:
        return "company_in_group"

    # Group name is contained in company name
    if group_lower in company_lower:
        return "group_in_company"

    # Word overlap - only if significant
    company_words = set(company_lower.split())
    group_words = set(group_lower.split())
    overlap = company_words.intersection(group_words)

    # Only count if overlap is substantial
    if len(overlap) >= 2 and len(overlap) >= len(company_words) * 0.5:
        return "word_overlap"

    return "none"


def is_better_match(quality1, quality2):
    """Determine if quality1 is better than quality2"""
    quality_order = [
        "exact",
        "company_in_group",
        "group_in_company",
        "word_overlap",
        "single_word",
        "none",
    ]
    return quality_order.index(quality1) < quality_order.index(quality2)


def main():
    print("🔍 Loading HubSpot companies...")
    companies = load_hubspot_companies()
    print(f"   Loaded {len(companies)} companies")

    print("🔍 Extracting Telegram groups...")
    groups = extract_telegram_groups()
    print(f"   Found {len(groups)} Telegram groups")

    print("🔍 Finding REAL matches (strict criteria)...")
    real_matches = find_real_matches(companies, groups)

    # Create clean table
    print("\n📊 REAL TELEGRAM MATCHES (VERIFIED)")
    print("=" * 100)
    print(
        f"{'Company':<30} {'Chat Dir':<12} {'Match Quality':<15} {'Telegram Group Name'}"
    )
    print("-" * 100)

    for company, chat_dir, group_name, quality in real_matches:
        # Truncate long names for display
        company_display = company[:28] + ".." if len(company) > 30 else company
        group_display = group_name[:60] + ".." if len(group_name) > 62 else group_name

        print(f"{company_display:<30} {chat_dir:<12} {quality:<15} {group_display}")

    print(f"\n📊 Summary:")
    print(f"   Total HubSpot companies: {len(companies)}")
    print(f"   Real Telegram matches: {len(real_matches)}")
    print(f"   Real match rate: {len(real_matches)/len(companies)*100:.1f}%")

    # Show specific companies of interest
    print(f"\n🔍 Key Companies Check:")
    key_companies = [
        "P2P",
        "ChainSafe",
        "Copper",
        "Chata AI",
        "T-Rize",
        "Vigil",
        "Igor Gusarov",
    ]

    for key_company in key_companies:
        found = False
        for company, chat_dir, group_name, quality in real_matches:
            if key_company.lower() in company.lower():
                print(f"   ✅ {company} → {chat_dir} ({quality})")
                found = True
                break
        if not found:
            print(f"   ❌ {key_company} - No REAL Telegram match found")

    # Save to file
    with open("real_telegram_matches.txt", "w") as f:
        f.write("REAL TELEGRAM MATCHES (VERIFIED)\n")
        f.write("=" * 50 + "\n\n")
        for company, chat_dir, group_name, quality in real_matches:
            f.write(f"{company} → {chat_dir} ({quality})\n")
            f.write(f"  Group: {group_name}\n\n")

    print(f"\n📄 Detailed list saved to: real_telegram_matches.txt")


if __name__ == "__main__":
    main()
