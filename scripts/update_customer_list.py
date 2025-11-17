#!/usr/bin/env python3
"""
Update Customer List Script

This script updates the company mapping to only include actual customer companies
based on the provided customer list.
"""

import csv
import re
from typing import Set, List

def parse_customer_list(customer_list: str) -> Set[str]:
    """Parse the customer list and extract company names."""
    customers = set()
    
    for line in customer_list.strip().split('\n'):
        if '::' in line:
            # Extract company name before the ::
            company_name = line.split('::')[0].strip()
            customers.add(company_name)
    
    return customers

def update_company_mapping(customers: Set[str], mapping_file: str = "data/company_mapping.csv"):
    """Update the company mapping file to only include actual customers."""
    
    # Read existing mapping
    existing_companies = set()
    rows_to_keep = []
    
    with open(mapping_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        for row in reader:
            existing_companies.add(row['Company Name'])
            rows_to_keep.append(row)
    
    # Filter to only include customers
    filtered_rows = []
    customers_found = set()
    customers_missing = set()
    
    for row in rows_to_keep:
        company_name = row['Company Name']
        
        # Check if this company is in our customer list
        if company_name in customers:
            filtered_rows.append(row)
            customers_found.add(company_name)
        else:
            # Check if it's a variant of a customer company
            base_name = company_name.replace('-minter', '').replace('-mainnet-1', '').replace('-validator-1', '').replace('-validator-2', '').replace('-wallet-1', '')
            if base_name in customers:
                filtered_rows.append(row)
                customers_found.add(company_name)
    
    # Check for customers not in mapping
    for customer in customers:
        if customer not in customers_found:
            # Check variants
            found_variant = False
            for existing in existing_companies:
                if existing.startswith(customer) or customer in existing:
                    found_variant = True
                    break
            if not found_variant:
                customers_missing.add(customer)
    
    # Write filtered mapping
    with open(mapping_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filtered_rows)
    
    return {
        'total_customers': len(customers),
        'customers_in_mapping': len(customers_found),
        'customers_missing': customers_missing,
        'companies_removed': len(existing_companies) - len(filtered_rows),
        'final_company_count': len(filtered_rows)
    }

def main():
    # Your customer list
    customer_list = """allnodes::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
alum-labs::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
alum-labs-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
artichoke-capital::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
artichoke-capital-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
b2c2::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
b2c2-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
bitgo::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
bitgo-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
bitsafe::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
bitsafe-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
black-manta::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
black-manta-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
brikly::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
brikly-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
brikly-mainnet-1::122007725fa01ff8d201e87afc2a3c04b8dd67fd65660e9acb68a72ca54a59b5f610
chainsafe::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
chainsafe-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
digik::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
digik-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
distributed-lab::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
distributed-lab-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
everstake::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
everstake-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
falconx::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
falconx-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
figment::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
figment-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
finoa::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
finoa-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
five-north::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
five-north-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
16::12207ebc4da4e824f5249a17b6559a9e7d3817d45bcde71c871c10a34d9ac9e8b9ba
fivenorth-mainnet1-1::12208a2c7404062865085b75b9e8a3cbca56f272c0103bc55b0e65ca7c2dd855294a
Maestro-mainnet-1::1220265a4c49d3c7cfa97273cf6533cad1918f04eee60d774366593b737b12882702
foundinals::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
foundinals-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
foundinalsunthy-mainnet-1::12201004202ad4f2ba69d160e148899596aa294db698917f3aaef063afcb0a412c83
gomaestro::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
gomaestro-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
hashkey-cloud::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
HashKeyCloud-Canton-1::1220b99f0697cb2485934480b53f3a42255741e544b4134b8984555e5c65cace11e9
igor-gusarov::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
igor-gusarov-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
IgorGusarov-myWallet-1::12201eff0a762b51ef3188e50ea8b34b65c135defff401e450a89b8b133812aa8f96
incyt::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
incyt-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
komonode::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
komonode-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
komonode-validator-1::12205e08c563371194e273ba23d2f1c00d3bf12389f46dbe6e787292a6bddb2c701a
launchnodes::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
launchnodes-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
auth0_007c686e1c6dc8c01fd351c58ddb::12208e16c5e119691882590e9b121285f5689aa2d739ad09a203fd20b871fef10520
linkpool::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
linkpool-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
lithium-digital::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
lithium-digital-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
meria::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
meria-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
mintify::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
mintify-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
modulo-finance::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
modulo-finance-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
mpch::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
auth0_007c68010d49d99132535c385e3d::12208cf414eff7a7d4949e659511edb25c82e652be0898864f2fa0d055c3b9abe06d
nansen::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
nansen-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
nethermind::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
nethermind-angkor-1::12201d94ec4ba973ab5c51e3b769a6aca54f061afc963619a4d6109044eaccafc7ba
nodemonsters::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
nodemonsters-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
nodeMonster-wallet-1::1220787f5ca878cf6cb9680639e5940231207dc57b7ee8546f92325a2f979d4c9901
notabene::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
notabene-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
obsidian::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
obsidian-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
ObsidianSystems-validator-2::122096fe076cc065af0cb38f94caa60e8ddfecbe8f0cfe10655ae7aa06fab99c66b7
p2p::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
p2p-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
pier-two::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
auth0_007c6850583f988e2e748492ff21::1220c8e303505ff29575e34990bf1c7da51369f556e40ddcec5c0e218042f750c5e2
redstone::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
redstone-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
red-stone-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
Redstone-validator-1::1220a6f7c2315ed7ba230397a459b036bfe9f36763a0e848dad741c4e9d20d85687c
register-labs::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
register-labs-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
RegisterLabs-validator-1::122096ef466fec3c3b64857a022024f127d395437732081bbb3d55f3fd3f57223f17
republic::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
Republic-validator-1::1220cf5c0358766265d8b67b3269d0ab15eba018449585fa9810481842f6ceeffc44
round13::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
round13-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
send-cantonwallet::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
sendit::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
sendit-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
sendmainnet1::12203726c4d6a2041bc700b91effb7baea3fa3af720edabb5dd3e6e8b56867f9b016
tall-oak-midstream::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
tall-oak-midstream-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
MJMBC-cybergy-1::122054dcb4643dbb986352ad7bae3f466222231adf13956445ba7ed6f6165cd2b7ca
tenkai::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
tenkai-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
trakx::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
trakx-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
t-rize::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
t-rize-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
TRIZEGroup-cantonMainnetValidator-1::12206ab3bf15b14410220357d6a6375eb1015f2e7fade1deb449463c2f2a25304889
unlock-it::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
UnlockIt-validator-1::1220671ca485c7bb9b4b45e8596dd71a6916a912899fe56fedf687a78cdbfa5e0624
xbto::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
xbto-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
xbto-validator-1::12209b9741b4de98a57f93948b5f4a2911aa13a789b822eb215ef4c4b54060b0e0d3
xlabs::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
xlabs-minter::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2"""
    
    print("🔍 Updating Company Mapping to Only Include Actual Customers")
    print("=" * 60)
    
    # Parse customer list
    customers = parse_customer_list(customer_list)
    print(f"📋 Found {len(customers)} unique customer companies")
    
    # Update mapping
    results = update_company_mapping(customers)
    
    print(f"✅ Company mapping updated:")
    print(f"   • Total customers: {results['total_customers']}")
    print(f"   • Customers in mapping: {results['customers_in_mapping']}")
    print(f"   • Companies removed: {results['companies_removed']}")
    print(f"   • Final company count: {results['final_company_count']}")
    
    if results['customers_missing']:
        print(f"\n⚠️  Customers not found in mapping ({len(results['customers_missing'])}):")
        for customer in sorted(results['customers_missing']):
            print(f"   • {customer}")
    
    print(f"\n🎯 Next step: Run ETL again to generate filtered output")
    print(f"   python src/etl/run_etl.py --workers 2 --batch-size 50")

if __name__ == "__main__":
    main()
