#!/usr/bin/env python3
"""
Company to Billing Mapping Script

Maps Slack channel conversations to actual billing data, showing:
- Company name from Slack channel
- Two separate deals: holder license + minter license
- PartyIDs for billing
- Revenue and ownership structure
"""

import re
import sqlite3
from collections import defaultdict


def map_companies_to_billing():
    """Map Slack channels to billing data"""

    # Connect to database
    db_path = "repsplit.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🔗 Mapping Companies: Slack Channels → Billing Data")
    print("=" * 80)

    # Get all bitsafe channels
    cursor.execute(
        """
        SELECT c.conv_id, c.name, COUNT(*) as msg_count 
        FROM conversations c 
        JOIN messages m ON c.conv_id = m.conv_id 
        WHERE c.is_bitsafe = TRUE 
        GROUP BY c.conv_id, c.name 
        ORDER BY msg_count DESC
    """
    )

    channels = cursor.fetchall()

    # Company mapping data (from the billing spreadsheet)
    company_billing_data = {
        # Format: "slack_channel_name": {
        #     "company_name": "Display Name",
        #     "holder_deal": {"party_id": "...", "revenue": "...", "owner": "..."},
        #     "minter_deal": {"party_id": "...", "revenue": "...", "owner": "..."}
        # }
        "sendit-bitsafe": {
            "company_name": "SendIt",
            "holder_deal": {
                "party_id": "sendit::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "223,630",
                "owner": "Addie",
            },
            "minter_deal": {
                "party_id": "sendit-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "215,137",
                "owner": "Aki",
            },
        },
        "send-cantonwallet-bitsafe": {
            "company_name": "SendIt CantonWallet",
            "holder_deal": {
                "party_id": "send-cantonwallet::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "34,233",
                "owner": "Aki",
            },
            "minter_deal": {
                "party_id": "send-cantonwallet-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "34,233",
                "owner": "Aki",
            },
        },
        "ordinals-foundation-bitsafe": {
            "company_name": "Ordinals Foundation",
            "holder_deal": {
                "party_id": "ordinals-foundation::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "N/A",
                "owner": "N/A",
            },
            "minter_deal": {
                "party_id": "ordinals-foundation-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "N/A",
                "owner": "N/A",
            },
        },
        "igor-gusarov-bitsafe": {
            "company_name": "Igor Gusarov",
            "holder_deal": {
                "party_id": "igor-gusarov::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "182,388",
                "owner": "Aki",
            },
            "minter_deal": {
                "party_id": "igor-gusarov-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "176,146",
                "owner": "Aki",
            },
        },
        "register-labs-bitsafe": {
            "company_name": "Register Labs",
            "holder_deal": {
                "party_id": "register-labs::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "215,855",
                "owner": "Addie",
            },
            "minter_deal": {
                "party_id": "register-labs-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "178,727",
                "owner": "Mayank",
            },
        },
        "obsidian-bitsafe": {
            "company_name": "Obsidian",
            "holder_deal": {
                "party_id": "obsidian::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "239,584",
                "owner": "Addie",
            },
            "minter_deal": {
                "party_id": "obsidian-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "232,575",
                "owner": "Aki",
            },
        },
        "five-north-bitsafe": {
            "company_name": "Five North",
            "holder_deal": {
                "party_id": "five-north::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "201,844",
                "owner": "Aki",
            },
            "minter_deal": {
                "party_id": "five-north-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "195,970",
                "owner": "Aki",
            },
        },
        "modulo-finance-bitsafe": {
            "company_name": "Modulo Finance",
            "holder_deal": {
                "party_id": "modulo-finance::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "179,690",
                "owner": "Aki",
            },
            "minter_deal": {
                "party_id": "modulo-finance-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "174,293",
                "owner": "Aki",
            },
        },
        "foundinals-bitsafe": {
            "company_name": "Foundinals",
            "holder_deal": {
                "party_id": "foundinals::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "229,478",
                "owner": "Addie",
            },
            "minter_deal": {
                "party_id": "foundinals-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "222,389",
                "owner": "Aki",
            },
        },
        "t-rize-bitsafe": {
            "company_name": "T-RIZE",
            "holder_deal": {
                "party_id": "t-rize::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "99,951",
                "owner": "Aki",
            },
            "minter_deal": {
                "party_id": "t-rize-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "95,756",
                "owner": "Aki",
            },
        },
        "komonode-bitsafe": {
            "company_name": "Komonode",
            "holder_deal": {
                "party_id": "komonode::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "242,733",
                "owner": "Aki",
            },
            "minter_deal": {
                "party_id": "komonode-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "37,710",
                "owner": "Aki",
            },
        },
        "launchnodes-bitsafe": {
            "company_name": "Launchnodes",
            "holder_deal": {
                "party_id": "launchnodes::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "156,297",
                "owner": "Aki",
            },
            "minter_deal": {
                "party_id": "launchnodes-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "150,645",
                "owner": "Mayank",
            },
        },
        "nodemonsters-bitsafe": {
            "company_name": "Nodemonsters",
            "holder_deal": {
                "party_id": "nodemonsters::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "181,179",
                "owner": "Mayank",
            },
            "minter_deal": {
                "party_id": "nodemonsters-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "174,840",
                "owner": "Aki",
            },
        },
        "meria-bitsafe": {
            "company_name": "Meria",
            "holder_deal": {
                "party_id": "meria::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "180,208",
                "owner": "Aki",
            },
            "minter_deal": {
                "party_id": "meria-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "173,868",
                "owner": "Aki",
            },
        },
        "mintify-bitsafe": {
            "company_name": "Mintify",
            "holder_deal": {
                "party_id": "mintify::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "178,922",
                "owner": "Aki",
            },
            "minter_deal": {
                "party_id": "mintify-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "173,664",
                "owner": "Aki",
            },
        },
        "nethermind-bitsafe": {
            "company_name": "Nethermind",
            "holder_deal": {
                "party_id": "nethermind::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "206,187",
                "owner": "Aki",
            },
            "minter_deal": {
                "party_id": "nethermind-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "N/A",
                "owner": "N/A",
            },
        },
        "xbto-bitsafe": {
            "company_name": "XBTO",
            "holder_deal": {
                "party_id": "xbto::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "157,115",
                "owner": "Aki",
            },
            "minter_deal": {
                "party_id": "xbto-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "151,250",
                "owner": "Aki",
            },
        },
        "tall-oak-midstream-bitsafe": {
            "company_name": "Tall Oak Midstream",
            "holder_deal": {
                "party_id": "tall-oak-midstream::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "238,807",
                "owner": "Addie",
            },
            "minter_deal": {
                "party_id": "tall-oak-midstream-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "232,834",
                "owner": "Addie",
            },
        },
        "redstone-bitsafe": {
            "company_name": "Redstone",
            "holder_deal": {
                "party_id": "redstone::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "99,940",
                "owner": "Aki",
            },
            "minter_deal": {
                "party_id": "redstone-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "60,568",
                "owner": "Addie",
            },
        },
        "unlock-it-bitsafe": {
            "company_name": "Unlock It",
            "holder_deal": {
                "party_id": "unlock-it::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "99,084",
                "owner": "Addie",
            },
            "minter_deal": {
                "party_id": "unlock-it-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "N/A",
                "owner": "N/A",
            },
        },
        "chainexperts-bitsafe": {
            "company_name": "Chain Experts",
            "holder_deal": {
                "party_id": "chain-experts::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "N/A",
                "owner": "N/A",
            },
            "minter_deal": {
                "party_id": "chain-experts-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "N/A",
                "owner": "N/A",
            },
        },
        "tenkai-bitsafe": {
            "company_name": "Tenkai",
            "holder_deal": {
                "party_id": "tenkai::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "178,656",
                "owner": "Aki",
            },
            "minter_deal": {
                "party_id": "tenkai-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "173,067",
                "owner": "Aki",
            },
        },
        "trakx-bitsafe": {
            "company_name": "Trakx",
            "holder_deal": {
                "party_id": "trakx::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "7,253",
                "owner": "Amy",
            },
            "minter_deal": {
                "party_id": "trakx-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "6,913",
                "owner": "Amy",
            },
        },
        "chainsafe-bitsafe": {
            "company_name": "Chainsafe",
            "holder_deal": {
                "party_id": "chainsafe::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "172,315",
                "owner": "Aki",
            },
            "minter_deal": {
                "party_id": "chainsafe-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "165,376",
                "owner": "Aki",
            },
        },
        "black-manta-bitsafe": {
            "company_name": "Black Manta",
            "holder_deal": {
                "party_id": "black-manta::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "74,866",
                "owner": "Aki",
            },
            "minter_deal": {
                "party_id": "black-manta-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "47,091",
                "owner": "Aki",
            },
        },
        "brikly-bitsafe": {
            "company_name": "Brikly",
            "holder_deal": {
                "party_id": "brikly::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "255,642",
                "owner": "Aki",
            },
            "minter_deal": {
                "party_id": "brikly-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "248,073",
                "owner": "Aki",
            },
        },
        "p2p-bitsafe": {
            "company_name": "P2P",
            "holder_deal": {
                "party_id": "p2p::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "179,664",
                "owner": "Aki",
            },
            "minter_deal": {
                "party_id": "p2p-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "173,799",
                "owner": "Aki",
            },
        },
        "pier-two-bitsafe": {
            "company_name": "Pier Two",
            "holder_deal": {
                "party_id": "pier-two::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "161,236",
                "owner": "Aki",
            },
            "minter_deal": {
                "party_id": "pier-two-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "N/A",
                "owner": "N/A",
            },
        },
        "hashkey-cloud-bitsafe": {
            "company_name": "Hashkey Cloud",
            "holder_deal": {
                "party_id": "hashkey-cloud::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "159,931",
                "owner": "Aki",
            },
            "minter_deal": {
                "party_id": "hashkey-cloud-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "N/A",
                "owner": "N/A",
            },
        },
        "lithium-digital-bitsafe": {
            "company_name": "Lithium Digital",
            "holder_deal": {
                "party_id": "lithium-digital::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "180,551",
                "owner": "Addie",
            },
            "minter_deal": {
                "party_id": "lithium-digital-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "166,526",
                "owner": "Aki",
            },
        },
        "republic-bitsafe": {
            "company_name": "Republic",
            "holder_deal": {
                "party_id": "republic::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "239,003",
                "owner": "Aki",
            },
            "minter_deal": {
                "party_id": "republic-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "N/A",
                "owner": "N/A",
            },
        },
        "round13-bitsafe": {
            "company_name": "Round13",
            "holder_deal": {
                "party_id": "round13::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "170,147",
                "owner": "Aki",
            },
            "minter_deal": {
                "party_id": "round13-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "164,600",
                "owner": "Aki",
            },
        },
        "mpch-bitsafe": {
            "company_name": "MPCH",
            "holder_deal": {
                "party_id": "mpch::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "79,159",
                "owner": "Aki",
            },
            "minter_deal": {
                "party_id": "mpch-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "revenue": "N/A",
                "owner": "N/A",
            },
        },
    }

    print("📊 Company Mapping Results:")
    print("-" * 80)

    total_revenue = 0
    mapped_companies = 0

    for conv_id, channel_name, msg_count in channels:
        # Use the full channel name as the key
        company_key = channel_name

        if company_key in company_billing_data:
            company_data = company_billing_data[company_key]
            mapped_companies += 1

            print(f"\n🏢 {company_data['company_name']} ({channel_name})")
            print(f"   📱 Slack Messages: {msg_count}")
            print(f"   💰 Revenue Structure:")

            # Holder deal
            holder = company_data["holder_deal"]
            if holder["revenue"] != "N/A":
                print(
                    f"     📋 Holder License: ${holder['revenue']} (Owner: {holder['owner']})"
                )
                print(f"        PartyID: {holder['party_id']}")
                total_revenue += float(holder["revenue"].replace(",", ""))

            # Minter deal
            minter = company_data["minter_deal"]
            if minter["revenue"] != "N/A":
                print(
                    f"     🏭 Minter License: ${minter['revenue']} (Owner: {minter['owner']})"
                )
                print(f"        PartyID: {minter['party_id']}")
                total_revenue += float(minter["revenue"].replace(",", ""))

            print(
                f"   🔗 Total Revenue: ${holder['revenue'] if holder['revenue'] != 'N/A' else '0'} + ${minter['revenue'] if minter['revenue'] != 'N/A' else '0'}"
            )

        else:
            print(f"\n❓ {channel_name} - No billing data found")

    print(f"\n📈 Summary:")
    print(f"   Total Companies Mapped: {mapped_companies}")
    print(f"   Total Revenue Tracked: ${total_revenue:,.2f}")
    if mapped_companies > 0:
        print(f"   Average Revenue per Company: ${total_revenue/mapped_companies:,.2f}")
    else:
        print(f"   Average Revenue per Company: $0.00")

    # Show revenue by owner
    print(f"\n👥 Revenue by Owner:")
    owner_revenue = defaultdict(float)

    for company_key, company_data in company_billing_data.items():
        for deal_type in ["holder_deal", "minter_deal"]:
            deal = company_data[deal_type]
            if deal["revenue"] != "N/A":
                owner = deal["owner"]
                revenue = float(deal["revenue"].replace(",", ""))
                owner_revenue[owner] += revenue

    for owner, revenue in sorted(
        owner_revenue.items(), key=lambda x: x[1], reverse=True
    ):
        print(f"   {owner}: ${revenue:,.2f}")

    conn.close()

    return company_billing_data


if __name__ == "__main__":
    results = map_companies_to_billing()
