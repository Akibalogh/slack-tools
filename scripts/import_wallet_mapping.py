#!/usr/bin/env python3
"""
Import Wallet Mapping Data

This script parses the company wallet mapping table and imports it into the database
using the new ORM models for wallet tracking.
"""

import re
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional


def parse_wallet_mapping_data(data_text: str) -> List[Dict]:
    """Parse the wallet mapping table data into structured records."""
    records = []
    seen_wallets = set()

    # Split into lines and process each company entry
    lines = data_text.strip().split("\n")

    for line in lines:
        if not line.strip() or "Status" in line or "---" in line:
            continue

        # Parse company data
        parts = line.split("\t")
        if len(parts) >= 5:
            status = parts[0].strip()
            company_name = parts[1].strip()
            fund_ownership = parts[2].strip()
            billing_wallet = parts[3].strip()
            external_customer_id = parts[4].strip() if len(parts) > 4 else None
            current_deposit = parts[5].strip() if len(parts) > 5 else "0"
            total_paid = parts[6].strip() if len(parts) > 6 else "0"

            # Handle missing status (default to "Outstanding")
            if not status:
                status = "Outstanding"

            # Clean up company name
            company_name = re.sub(r"\s+", " ", company_name).strip()

            # Skip empty entries
            if not company_name or not billing_wallet:
                continue

            # Skip duplicate wallet addresses (keep the first occurrence)
            if billing_wallet in seen_wallets:
                print(
                    f"⚠️  Skipping duplicate wallet: {billing_wallet} for {company_name}"
                )
                continue
            seen_wallets.add(billing_wallet)

            records.append(
                {
                    "status": status,
                    "company_name": company_name,
                    "fund_ownership": fund_ownership,
                    "billing_wallet": billing_wallet,
                    "external_customer_id": external_customer_id,
                    "current_deposit": current_deposit,
                    "total_paid": total_paid,
                }
            )

    return records


def create_wallet_tables(db_path: str):
    """Create the wallet mapping tables if they don't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create company_wallets table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS company_wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            status TEXT NOT NULL,
            fund_ownership TEXT NOT NULL,
            billing_wallet TEXT NOT NULL UNIQUE,
            external_customer_id TEXT,
            current_deposit TEXT,
            total_paid TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Create indexes
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_company_wallets_company_name ON company_wallets(company_name)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_company_wallets_status ON company_wallets(status)"
    )

    conn.commit()
    conn.close()


def import_wallet_data(db_path: str, records: List[Dict]):
    """Import wallet data into the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Clear existing data
    cursor.execute("DELETE FROM company_wallets")

    # Insert new records
    for record in records:
        cursor.execute(
            """
            INSERT INTO company_wallets 
            (company_name, status, fund_ownership, billing_wallet, external_customer_id, current_deposit, total_paid)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                record["company_name"],
                record["status"],
                record["fund_ownership"],
                record["billing_wallet"],
                record["external_customer_id"],
                record["current_deposit"],
                record["total_paid"],
            ),
        )

    conn.commit()
    conn.close()


def main():
    """Main function to import wallet mapping data."""
    print("🔍 Importing Wallet Mapping Data")
    print("=" * 50)

    # Real data from the billing table
    real_data = """Status	Company Name	Fund our PartyID or Theirs?	"Wallet (PartyID) - customer sends money here"	External Customer ID	Current Deposit from Billing tab before clicking revoke/cancel on credentials tab (user should pay this much into wallet)	Total Paid when revoke/cancel
Signed	SendIt CantonWallet	Theirs	send-cantonwallet::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	sendmainnet1::12203726c4d6a2041bc700b91effb7baea3fa3af720edabb5dd3e6e8b56867f9b016		
Signed	Redstone	Theirs	redstone-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	Redstone-validator-1::1220a6f7c2315ed7ba230397a459b036bfe9f36763a0e848dad741c4e9d20d85687c		
Outstanding	Meria	Theirs	meria-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	meria-validator-1::1220bc9f39ab737c8149cae05ee83244983bb5ce8256f6dbaf016897baff1a625978	0	0
Signed	Komonode	Theirs	komonode-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	komonode-validator-1::12205e08c563371194e273ba23d2f1c00d3bf12389f46dbe6e787292a6bddb2c701a	0	0
Signed	T-RIZE	Theirs	t-rize-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	TRIZEGroup-cantonMainnetValidator-1::12206ab3bf15b14410220357d6a6375eb1015f2e7fade1deb449463c2f2a25304889		
Signed	Launchnodes	Theirs	launchnodes-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	auth0_007c686e1c6dc8c01fd351c58ddb::12208e16c5e119691882590e9b121285f5689aa2d739ad09a203fd20b871fef10520		
Outstanding	Nodemonsters	Theirs	nodemonsters-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	nodeMonster-wallet-1::1220787f5ca878cf6cb9680639e5940231207dc57b7ee8546f92325a2f979d4c9901		
Signed	Igor Gusarov	Theirs	igor-gusarov-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	IgorGusarov-myWallet-1::12201eff0a762b51ef3188e50ea8b34b65c135defff401e450a89b8b133812aa8f96	0	0
Outstanding	Five North	Theirs	five-north-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	16::12207ebc4da4e824f5249a17b6559a9e7d3817d45bcde71c871c10a34d9ac9e8b9ba	0	0
Exempt	BitSafe	Theirs	bitsafe-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2		0	0
Signed	Send.It	Theirs	sendit-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	sendmainnet1::12203726c4d6a2041bc700b91effb7baea3fa3af720edabb5dd3e6e8b56867f9b016	0	0
Signed	Tall Oak Midstream	Theirs	tall-oak-midstream-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	MJMBC-cybergy-1::122054dcb4643dbb986352ad7bae3f466222231adf13956445ba7ed6f6165cd2b7ca	199,923.89 CC	76.11 CC
Outstanding	XBTO	Theirs	xbto-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	xbto-validator-1::12209b9741b4de98a57f93948b5f4a2911aa13a789b822eb215ef4c4b54060b0e0d3	198,470.17 CC	1,529.83 CC
Signed	Obsidian	Theirs	obsidian-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	ObsidianSystems-validator-2::122096fe076cc065af0cb38f94caa60e8ddfecbe8f0cfe10655ae7aa06fab99c66b7	198,888.78 CC	1,111.22 CC
Signed	Mintify	Theirs	mintify::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	mintify-mainnet-1::122008e5b5243baf52fcb8790bee596c5272cfdf0b4015302f6c8279330ef19a4e3b		
Signed	Meria	Theirs	meria::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	meria-validator-1::1220bc9f39ab737c8149cae05ee83244983bb5ce8256f6dbaf016897baff1a625978	0	0
Exempt	BitSafe	Theirs	bitsafe::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2		0	0
Outstanding	GoMaestro	Theirs	gomaestro::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2		118,104.83 CC	1,895.17 CC
Signed	Tall Oak Midstream	Theirs	tall-oak-midstream::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	MJMBC-cybergy-1::122054dcb4643dbb986352ad7bae3f466222231adf13956445ba7ed6f6165cd2b7ca	119,899.53 CC	100.47 CC
Outstanding	Nethermind	Theirs	nethermind::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	nethermind-angkor-1::12201d94ec4ba973ab5c51e3b769a6aca54f061afc963619a4d6109044eaccafc7ba	119,625.53 CC	374.47 CC
Signed	Hashkey Cloud	Theirs	hashkey-cloud::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	HashKeyCloud-Canton-1::1220b99f0697cb2485934480b53f3a42255741e544b4134b8984555e5c65cace11e9	118,700.78 CC	1,299.22 CC
Signed	Pier Two	Theirs	pier-two::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	auth0_007c6850583f988e2e748492ff21::1220c8e303505ff29575e34990bf1c7da51369f556e40ddcec5c0e218042f750c5e2	118,593.47 CC	1,406.53 CC
Signed	Nodemonsters	Theirs	nodemonsters::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	nodeMonster-wallet-1::1220787f5ca878cf6cb9680639e5940231207dc57b7ee8546f92325a2f979d4c9901	117,148.12 CC	2,851.88 CC
Signed	Launchnodes	Theirs	launchnodes::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	auth0_007c686e1c6dc8c01fd351c58ddb::12208e16c5e119691882590e9b121285f5689aa2d739ad09a203fd20b871fef10520	116,766.80 CC	1,510.81 CC
Signed	XBTO	Theirs	xbto::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	xbto-validator-1::12209b9741b4de98a57f93948b5f4a2911aa13a789b822eb215ef4c4b54060b0e0d3	116,693.73 CC	3,306.27 CC
Signed	Send.It	Theirs	sendit::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	sendmainnet1::12203726c4d6a2041bc700b91effb7baea3fa3af720edabb5dd3e6e8b56867f9b016	117,196.07 CC	2,803.93 CC
Outstanding	Unlock It	Theirs	unlock-it::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	UnlockIt-validator-1::1220671ca485c7bb9b4b45e8596dd71a6916a912899fe56fedf687a78cdbfa5e0624	115,344.28 CC	4,655.72 CC
Signed	Redstone	Theirs	redstone::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	Redstone-validator-1::1220a6f7c2315ed7ba230397a459b036bfe9f36763a0e848dad741c4e9d20d85687c	115,296.33 CC	4,703.67 CC
Signed	T-RIZE	Theirs	t-rize::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	TRIZEGroup-cantonMainnetValidator-1::12206ab3bf15b14410220357d6a6375eb1015f2e7fade1deb449463c2f2a25304889	115,091.39 CC	4,908.61 CC
Signed	Obsidian	Theirs	obsidian::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	ObsidianSystems-validator-2::122096fe076cc065af0cb38f94caa60e8ddfecbe8f0cfe10655ae7aa06fab99c66b7	117,027.10 CC	2,972.90 CC
Signed	Five North	Theirs	five-north::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	16::12207ebc4da4e824f5249a17b6559a9e7d3817d45bcde71c871c10a34d9ac9e8b9ba	116,412.50 CC	3,587.50 CC
Signed	Igor Gusarov	Theirs	igor-gusarov::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	IgorGusarov-myWallet-1::12201eff0a762b51ef3188e50ea8b34b65c135defff401e450a89b8b133812aa8f96	115,713.22 CC	4,286.78 CC
Outstanding	Foundinals	Theirs	foundinals-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	foundinalsunthy-mainnet-1::12201004202ad4f2ba69d160e148899596aa294db698917f3aaef063afcb0a412c83	117,065.92 CC	2,934.08 CC
Signed	Komonode	Theirs	komonode::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	komonode-validator-1::12205e08c563371194e273ba23d2f1c00d3bf12389f46dbe6e787292a6bddb2c701a	115,699.56 CC	4,300.44 CC
Signed	Register Labs	Ours	register-labs-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	RegisterLabs-validator-1::122096ef466fec3c3b64857a022024f127d395437732081bbb3d55f3fd3f57223f17		
Signed	Foundinals	Ours	foundinals::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	foundinalsunthy-mainnet-1::12201004202ad4f2ba69d160e148899596aa294db698917f3aaef063afcb0a412c83	49,158.97 CC	841.03 CC
Outstanding	Republic	Ours	republic::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	Republic-validator-1::1220cf5c0358766265d8b67b3269d0ab15eba018449585fa9810481842f6ceeffc44	27,721.23 CC	2,278.77 CC
Signed	Register Labs	Ours	register-labs::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	RegisterLabs-validator-1::122096ef466fec3c3b64857a022024f127d395437732081bbb3d55f3fd3f57223f17	27,492.90 CC	2,507.10 CC
Signed	Brikly	Ours	brikly-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2		16,096.78 CC	563.22 CC
Signed	MPCH	Ours	mpch::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2		117,075.05 CC	2,924.95 CC
Signed	Chainsafe	Ours	chainsafe::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2			
Signed	Tenkai	Ours	tenkai::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2			
Signed	Nansen	Ours	nansen::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2			
Signed	Finoa	Theirs	finoa::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2			
Signed	Modulo Finance	Ours	modulo-finance::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2			
Signed	Linkpool	Ours	linkpool::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2			
Signed	Lithium Digital	Ours	lithium-digital::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	lithiumdigital-validator-1::1220e852a0cb4372f91dd2b7b93c71d4580600b0f2c045e6cbebd9f510e88c0ba29b		
Signed	Brikly	Ours	brikly::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2		9,527.35 CC	474.93 CC
Signed	Chainsafe	Ours	chainsafe-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2			
Signed	Brikly	Ours	brikly-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2			
Signed	Incyt	Ours	incyt-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2			
Signed	Nansen	Ours	nansen-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2			
Signed	Modulo Finance	Ours	modulo-finance-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2			
Signed	Kiln	No Rewards	kiln::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2			
Signed	Path Rock	No Rewards	path-rock::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2			
Signed	Proof	No Rewards	proof::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2			
Signed	Thetanuts	No Rewards	thetanuts::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2			
Signed	Trakx	No Rewards	trakx::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2			
Signed	Temple		temple::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	temple-mainnet-1::1220f238bb79df3efbbac2ea964c3cd501003971a2cb59043e2dac50b06e85b8620f		
Signed	POPS		pops::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	POPSTeam-validator-1::1220960f1e2b644b70943f52234d0da1ae992d9baa0b1c744ae936fbe9c535a79a60		
Signed	Amber		amber::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	AmberTrading-Validator-1::12209d63883fd0e0900bf83618ad55dce3fccd8d47768cdffffebba672c722235fdd		
Outstanding	Binance		binance-us::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2			
Outstanding	OpenVector (Cypherock)		openvector-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2			
Outstanding	SenseiNode		sensei-node-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2			
Outstanding	Barg Systems	No Rewards	barg-systems-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	"""

    # Parse the data
    records = parse_wallet_mapping_data(real_data)
    print(f"📊 Parsed {len(records)} wallet records")

    # Create tables
    db_path = "repsplit.db"
    create_wallet_tables(db_path)
    print("✅ Wallet tables created")

    # Import data
    import_wallet_data(db_path, records)
    print("✅ Wallet data imported")

    # Show summary
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM company_wallets")
    total_count = cursor.fetchone()[0]

    cursor.execute("SELECT status, COUNT(*) FROM company_wallets GROUP BY status")
    status_counts = cursor.fetchall()

    cursor.execute(
        "SELECT fund_ownership, COUNT(*) FROM company_wallets GROUP BY fund_ownership"
    )
    ownership_counts = cursor.fetchall()

    conn.close()

    print(f"\n📈 Import Summary:")
    print(f"   Total companies: {total_count}")
    print(f"   Status breakdown:")
    for status, count in status_counts:
        print(f"     {status}: {count}")
    print(f"   Fund ownership:")
    for ownership, count in ownership_counts:
        print(f"     {ownership}: {count}")


if __name__ == "__main__":
    main()
