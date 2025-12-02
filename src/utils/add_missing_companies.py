#!/usr/bin/env python3
"""
Add missing companies from the user's list to the company mapping table.
"""

import csv
import os


def get_existing_companies():
    """Get existing companies from the mapping table."""
    existing = set()
    if os.path.exists("output/company_mapping_table.csv"):
        with open("output/company_mapping_table.csv", "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                company_name = row["Company Name"].strip().lower()
                existing.add(company_name)
    return existing


def get_target_companies():
    """Get the target companies from the user's list."""
    return {
        "allnodes": "allnodes",
        "alum-labs": "alumlabs-bitsafe",  # We have this one
        "artichoke-capital": "artichoke-capital",
        "b2c2": "b2c2",
        "bitgo": "bitgo",  # We have this one
        "bitsafe": "bitsafe",
        "black-manta": "blackmanta-bitsafe",  # We have this one
        "brikly": "brikly",
        "chainsafe": "chainsafe-bitsafe",  # We have this one
        "digik": "digik-bitsafe",  # We have this one
        "distributed-lab": "distributed-lab",
        "everstake": "everstake",
        "falconx": "falconx",
        "figment": "figment",
        "finoa": "finoa",
        "five-north": "five-north-bitsafe",  # We have this one
        "foundinals": "foundinals",
        "gomaestro": "gomaestro",
        "hashkey-cloud": "hashkey-cloud",
        "igor-gusarov": "igor-gusarov-bitsafe",  # We have this one
        "incyt": "incyt",
        "komonode": "komonode-bitsafe",  # We have this one
        "launchnodes": "launchnodes-bitsafe",  # We have this one
        "linkpool": "linkpool",
        "lithium-digital": "lithiumdigital-bitsafe",  # We have this one
        "meria": "meria",
        "mintify": "mintify-bitsafe",  # We have this one
        "modulo-finance": "modulo-finance-bitsafe",  # We have this one
        "mpch": "mpch-bitsafe-cbtc",  # We have this one
        "nansen": "nansen",
        "nethermind": "nethermind-canton-bitsafe",  # We have this one
        "nodemonsters": "nodemonster-bitsafe",  # We have this one
        "notabene": "notabene-bitsafe",  # We have this one
        "obsidian": "obsidian-bitsafe",  # We have this one
        "p2p": "p2p-bitsafe",  # We have this one
        "pier-two": "pier-two",
        "redstone": "redstone-bitsafe",  # We have this one
        "register-labs": "register-labs-bitsafe",  # We have this one
        "republic": "republic",
        "round13": "round13",
        "sendit": "sendit-bitsafe",  # We have this one
        "tall-oak-midstream": "tall-oak-midstream-bitsafe",  # We have this one
        "tenkai": "tenkai-bitsafe",  # We have this one
        "trakx": "trakx-bitsafe",  # We have this one
        "t-rize": "t-rize-bitsafe",  # We have this one
        "unlock-it": "unlock-it",
        "xbto": "xbto",
        "xlabs": "xlabs-bitsafe",  # We have this one
    }


def add_missing_companies():
    """Add missing companies to the mapping table."""
    existing = get_existing_companies()
    target_companies = get_target_companies()

    # Find missing companies
    missing = {}
    for target_name, slack_name in target_companies.items():
        if target_name.lower() not in existing and slack_name.lower() not in existing:
            missing[target_name] = slack_name

    print(f"🔍 Found {len(missing)} missing companies:")
    for company in missing:
        print(f"  - {company}")

    # Read existing mapping table
    rows = []
    if os.path.exists("output/company_mapping_table.csv"):
        with open("output/company_mapping_table.csv", "r") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                rows.append(row)

    # Add missing companies
    for company_name, slack_name in missing.items():
        new_row = {
            "Company Name": company_name,
            "Slack Channel": (
                slack_name if not slack_name.endswith("-bitsafe") else slack_name
            ),
            "Telegram Group": "",
            "Calendar Entries": "",
            "Wallet Status": "No",
            "Platform Overlap": "Slack",
        }
        rows.append(new_row)

    # Write updated mapping table
    with open("output/company_mapping_table_updated.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"\n✅ Added {len(missing)} companies to company_mapping_table_updated.csv")
    print(f"📊 Total companies now: {len(rows)}")

    return missing


def main():
    print("🔍 Adding Missing Companies to Mapping Table")
    print("=" * 50)

    missing = add_missing_companies()

    if missing:
        print(f"\n📋 Next steps:")
        print(f"  1. Review company_mapping_table_updated.csv")
        print(f"  2. Import Slack/Telegram data for missing companies")
        print(f"  3. Run commission analysis for all companies")
    else:
        print(f"\n✅ All companies are already in the mapping table!")


if __name__ == "__main__":
    main()
