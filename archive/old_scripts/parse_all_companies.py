#!/usr/bin/env python3
"""
Script to parse all companies from the user's list into the database
"""

import subprocess
import sys
from pathlib import Path

# Companies to parse (main companies without -minter variants)
COMPANIES_TO_PARSE = [
    "allnodes",
    "alum-labs",
    "Artichoke Capital",
    "b2c2",
    "bitgo",
    "black-manta",
    "brikly",
    "chainsafe",
    "digik",
    "Distributed Lab",
    "everstake",
    "falconx",
    "figment",
    "finoa",
    "five-north",
    "foundinals",
    "gomaestro",
    "Hashkey Cloud",
    "igor-gusarov",
    "incyt",
    "komonode",
    "launchnodes",
    "linkpool",
    "lithium-digital",
    "meria",
    "mintify",
    "modulo-finance",
    "mpch",
    "nansen",
    "nethermind",
    "nodemonsters",
    "notabene",
    "obsidian",
    "p2p",
    "pier-two",
    "redstone",
    "register-labs",
    "republic",
    "round13",
    "sendit",
    "tall-oak-midstream",
    "tenkai",
    "trakx",
    "t-rize",
    "unlock-it",
    "xbto",
    "xlabs",
]


def parse_company(company_name):
    """Parse a single company using telegram_parser.py"""
    try:
        result = subprocess.run(
            ["python3", "telegram_parser.py", company_name],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print(f"✅ Successfully parsed {company_name}")
            return True
        else:
            print(f"❌ Failed to parse {company_name}: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout parsing {company_name}")
        return False
    except Exception as e:
        print(f"💥 Error parsing {company_name}: {e}")
        return False


def main():
    """Parse all companies"""
    print("🚀 Starting to parse all companies...")
    print(f"📋 Total companies to parse: {len(COMPANIES_TO_PARSE)}")
    print("=" * 50)

    success_count = 0
    failed_count = 0

    for i, company in enumerate(COMPANIES_TO_PARSE, 1):
        print(f"\n[{i}/{len(COMPANIES_TO_PARSE)}] Parsing: {company}")

        if parse_company(company):
            success_count += 1
        else:
            failed_count += 1

    print("\n" + "=" * 50)
    print(f"🎯 Parsing complete!")
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📊 Success rate: {(success_count/len(COMPANIES_TO_PARSE)*100):.1f}%")


if __name__ == "__main__":
    main()
