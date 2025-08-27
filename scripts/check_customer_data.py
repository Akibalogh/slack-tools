#!/usr/bin/env python3
"""
Check which customers from the provided list have available data sources
"""

# Customer list from user (removing -minter duplicates and blockchain hashes)
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

# Available Telegram conversations
telegram_companies = ["ChainSafe", "Copper", "P2P"]

print("=== CUSTOMER DATA AVAILABILITY ANALYSIS ===\n")

# Check each customer
found_slack = []
found_telegram = []
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
    ]

    for pattern in slack_patterns:
        if pattern and pattern in slack_channels:
            has_slack = True
            break

    # Check Telegram (case-insensitive, various formats)
    for tg_company in telegram_companies:
        if customer.lower().replace("-", "").replace(
            "_", ""
        ) == tg_company.lower().replace("-", "").replace("_", ""):
            has_telegram = True
            break

    # Categorize
    if has_slack and has_telegram:
        found_slack.append(f"{customer} (Slack + Telegram)")
    elif has_slack:
        found_slack.append(f"{customer} (Slack)")
    elif has_telegram:
        found_telegram.append(f"{customer} (Telegram)")
    else:
        missing_data.append(customer)

print("✅ CUSTOMERS WITH SLACK DATA:")
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
print(f"  - With Slack data: {len([x for x in found_slack if 'Slack' in x])}")
print(
    f"  - With Telegram data: {len([x for x in found_slack if 'Telegram' in x]) + len(found_telegram)}"
)
print(f"  - Missing data: {len(missing_data)}")

if missing_data:
    print(f"\n🔍 NEED TO CHECK FOR THESE COMPANIES:")
    print("  - Do they have Telegram chats?")
    print("  - Do they have Google Calendar meetings?")
    print("  - Are they in HubSpot with different names?")
    for company in missing_data:
        print(f"    * {company}")
