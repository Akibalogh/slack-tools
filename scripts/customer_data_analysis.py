#!/usr/bin/env python3
"""
Comprehensive analysis of customer data availability for commission calculations
"""

# Customer list from user (consolidating -minter variants)
customers = [
    "allnodes",
    "alum-labs",
    "artichoke-capital",
    "b2c2",
    "bitgo",
    "bitsafe",
    "black-manta",
    "brikly",
    "chainsafe",
    "digik",
    "distributed-lab",
    "everstake",
    "falconx",
    "figment",
    "finoa",
    "five-north",
    "foundinals",
    "gomaestro",
    "hashkey-cloud",
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
    "send-cantonwallet",
    "sendit",
    "tall-oak-midstream",
    "tenkai",
    "trakx",
    "t-rize",
    "unlock-it",
    "xbto",
    "xlabs",
]

# Available Slack channels (from database query)
slack_channels = [
    "7ridge-bitsafe",
    "alumlabs-bitsafe",
    "anchorpoint-bitsafe",
    "bargsystems-bitsafe",
    "bcw-bitsafe",
    "blackmanta-bitsafe",
    "blacksand-bitsafe",
    "blockandbones-bitsafe",
    "blockdaemon-bitsafe",
    "brale-bitsafe",
    "canton-launchnodes-bitsafe",
    "cense-bitsafe",
    "chainexperts-bitsafe",
    "chainsafe-bitsafe",
    "chata-ai-bitsafe",
    "copper-bitsafe",
    "cygnet-bitsafe",
    "digik-bitsafe",
    "entropydigital-bitsafe",
    "five-north-bitsafe",
    "g20-bitsafe",
    "gateway-bitsafe",
    "hashrupt-bitsafe",
    "hlt-bitsafe",
    "igor-gusarov-bitsafe",
    "integraate-bitsafe",
    "ipblock-bitsafe",
    "kaiko-bitsafe",
    "kaleido-bitsafe",
    "komonode-bitsafe",
    "launchnodes-bitsafe",
    "levl-bitsafe",
    "lightshift-bitsafe",
    "lithiumdigital-bitsafe",
    "luganodes-bitsafe",
    "maestro-bitsafe",
    "matrixedlink-bitsafe",
    "mintify-bitsafe",
    "mlabs-bitsafe",
    "modulo-finance-bitsafe",
    "mse-bitsafe",
    "neogenesis-bitsafe",
    "nethermind-canton-bitsafe",
    "nodemonster-bitsafe",
    "noders-bitsafe",
    "notabene-bitsafe",
    "novaprime-bitsafe",
    "obsidian-bitsafe",
    "openblock-bitsafe",
    "ordinals-foundation-bitsafe",
    "p2p-bitsafe",
    "palladium-bitsafe",
    "pathrock-bitsafe",
    "proof-bitsafe",
    "redstone-bitsafe",
    "register-labs-bitsafe",
    "rwaxyz-bitsafe",
    "sbc-bitsafe",
    "sendit-bitsafe",
    "t-rize-bitsafe",
    "tall-oak-midstream-bitsafe",
    "temple-bitsafe",
    "tenkai-bitsafe",
    "thetanuts-bitsafe",
    "trakx-bitsafe",
    "ubyx-bitsafe",
    "vigilmarkets-bitsafe",
    "xlabs-bitsafe",
    "zeconomy-bitsafe",
]

# Available Telegram conversations (from export analysis)
telegram_companies = [
    "ChainSafe",
    "Copper",
    "P2P",
    "Allnodes",
    "BitGo",
    "B2C2",
    "Figment",
    "Finoa",
    "Nansen",
    "Nethermind",
    "Everstake",
    "FalconX",
    "Incyt",
    "LinkPool",
    "Meria",
    "Republic",
    "Round13",
    "Pier Two",
    "XBTO",
    "Brikly",
    "Distributed Lab",
    "Hashkey Cloud",
    "Gomaestro",
    "Foundinals",
    "Unlock-it",
    "Send-cantonwallet",
    "Nodemonsters",
    "Artichoke Capital",
]

# Additional Slack channels found
additional_slack = ["mpch-bitsafe-cbtc"]

# Update slack_channels list
slack_channels.extend(additional_slack)

print("=== COMPREHENSIVE CUSTOMER DATA ANALYSIS ===\n")

# Check each customer
found_slack = []
found_telegram = []
found_both = []
missing_data = []

for customer in customers:
    has_slack = False
    has_telegram = False

    # Check Slack (various naming patterns)
    slack_patterns = [
        f"{customer}-bitsafe",
        f"{customer.replace('-', '')}-bitsafe",
        f"{customer.replace('-', '')}labs-bitsafe" if "labs" in customer else None,
        (
            f"black{customer.split('-')[1]}-bitsafe"
            if customer.startswith("black-")
            else None
        ),
        f"{customer}-bitsafe-cbtc" if customer == "mpch" else None,
    ]

    for pattern in slack_patterns:
        if pattern and pattern in slack_channels:
            has_slack = True
            break

    # Check Telegram (case-insensitive, various formats)
    for tg_company in telegram_companies:
        if customer.lower().replace("-", "").replace(
            "_", ""
        ) == tg_company.lower().replace("-", "").replace("_", "").replace(" ", ""):
            has_telegram = True
            break

    # Categorize
    if has_slack and has_telegram:
        found_both.append(customer)
    elif has_slack:
        found_slack.append(customer)
    elif has_telegram:
        found_telegram.append(customer)
    else:
        missing_data.append(customer)

print("✅ CUSTOMERS WITH BOTH SLACK + TELEGRAM DATA:")
for item in found_both:
    print(f"  - {item}")

print(f"\n✅ CUSTOMERS WITH SLACK DATA ONLY:")
for item in found_slack:
    print(f"  - {item}")

print(f"\n✅ CUSTOMERS WITH TELEGRAM DATA ONLY:")
for item in found_telegram:
    print(f"  - {item}")

print(f"\n❌ CUSTOMERS WITH NO DATA SOURCES:")
for item in missing_data:
    print(f"  - {item}")

print(f"\n📊 SUMMARY:")
print(f"  - Total customers: {len(customers)}")
print(f"  - With Slack data: {len(found_slack) + len(found_both)}")
print(f"  - With Telegram data: {len(found_telegram) + len(found_both)}")
print(f"  - With both: {len(found_both)}")
print(f"  - Missing data: {len(missing_data)}")

print(f"\n🚀 READY FOR COMMISSION ANALYSIS:")
ready_customers = found_slack + found_telegram + found_both
print(f"  - {len(ready_customers)} customers have sufficient data")
print(f"  - {len(missing_data)} customers need additional data sources")

if missing_data:
    print(f"\n🔍 COMPANIES THAT NEED ATTENTION:")
    print("  - Check if they have Telegram chats we missed")
    print("  - Look for Google Calendar meetings")
    print("  - Verify HubSpot company name variations")
    for company in missing_data:
        print(f"    * {company}")

print(f"\n💡 RECOMMENDATIONS:")
print("  1. Process commissions for the 47 customers with data")
print("  2. Add missing Telegram data for remaining companies")
print("  3. Check Google Calendar for meeting data")
print("  4. Verify HubSpot company name mappings")
