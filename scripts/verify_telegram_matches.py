#!/usr/bin/env python3
"""
Verify Telegram Matches

Extract actual Telegram group names and create a table for manual verification
of which companies truly have Telegram data vs. false positives.
"""

import csv
import re
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple


class TelegramMatchVerifier:
    def __init__(self, hubspot_file: str, telegram_export_path: str):
        self.hubspot_file = Path(hubspot_file)
        self.telegram_export_path = Path(telegram_export_path)
        self.chats_index_path = self.telegram_export_path / "lists" / "chats.html"

    def load_hubspot_companies(self) -> List[str]:
        """Load all company names from HubSpot CRM export"""
        companies = []

        try:
            with open(self.hubspot_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["Deal Name"] and row["Deal Name"].strip():
                        # Clean company name (remove - Minter Upsell, etc.)
                        company = re.sub(
                            r" - Minter Upsell$| — Minter Upsell$| Minter upsell$",
                            "",
                            row["Deal Name"].strip(),
                        )
                        companies.append(company)

            print(f"Loaded {len(companies)} companies from HubSpot CRM")
            return companies

        except Exception as e:
            print(f"Error loading HubSpot companies: {e}")
            return []

    def extract_telegram_groups(self) -> Dict[str, str]:
        """Extract all Telegram group names and their chat directories"""
        groups = {}

        if not self.chats_index_path.exists():
            print(f"Chats index not found at {self.chats_index_path}")
            return groups

        try:
            with open(self.chats_index_path, "r", encoding="utf-8") as f:
                content = f.read()

            soup = BeautifulSoup(content, "html.parser")

            for link in soup.find_all("a"):
                href = link.get("href", "")
                if "chat_" in href:
                    # Extract chat directory
                    chat_dir = href.split("/")[2]

                    # Get group name
                    group_name = link.get_text().strip()

                    groups[chat_dir] = group_name

            print(f"Extracted {len(groups)} Telegram groups")
            return groups

        except Exception as e:
            print(f"Error extracting Telegram groups: {e}")
            return groups

    def find_matches(
        self, companies: List[str], groups: Dict[str, str]
    ) -> List[Tuple[str, str, str, str]]:
        """
        Find matches between companies and Telegram groups

        Returns:
            List of (company, chat_dir, group_name, match_quality)
        """
        matches = []

        for company in companies:
            best_match = None
            best_quality = "none"

            for chat_dir, group_name in groups.items():
                quality = self._assess_match_quality(company, group_name)

                if quality != "none" and (
                    best_match is None or self._is_better_match(quality, best_quality)
                ):
                    best_match = (chat_dir, group_name, quality)
                    best_quality = quality

            if best_match:
                chat_dir, group_name, quality = best_match
                matches.append((company, chat_dir, group_name, quality))
            else:
                matches.append((company, "", "", "none"))

        return matches

    def _assess_match_quality(self, company: str, group_name: str) -> str:
        """Assess the quality of a match between company and group name"""
        company_lower = company.lower()
        group_lower = group_name.lower()

        # Exact match
        if company_lower == group_lower:
            return "exact"

        # Company name is contained in group name
        if company_lower in group_lower:
            return "company_in_group"

        # Group name is contained in company name
        if group_lower in company_lower:
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

    def _is_better_match(self, quality1: str, quality2: str) -> bool:
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

    def generate_verification_table(
        self, matches: List[Tuple[str, str, str, str]]
    ) -> str:
        """Generate a verification table"""
        table = []
        table.append("# Telegram Match Verification Table")
        table.append("")
        table.append(
            "| Company | Chat Dir | Telegram Group Name | Match Quality | Notes |"
        )
        table.append(
            "|---------|----------|-------------------|---------------|-------|"
        )

        for company, chat_dir, group_name, quality in matches:
            if quality != "none":
                table.append(
                    f"| {company} | `{chat_dir}` | {group_name} | {quality} | |"
                )
            else:
                table.append(f"| {company} | | | | No match found |")

        return "\n".join(table)

    def save_verification_table(
        self, table: str, output_file: str = "telegram_match_verification.md"
    ):
        """Save the verification table to a file"""
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(table)
            print(f"Verification table saved to {output_file}")
        except Exception as e:
            print(f"Error saving verification table: {e}")

    def run_verification(self):
        """Run the complete verification process"""
        print("🔍 Starting Telegram match verification...")

        # Load HubSpot companies
        companies = self.load_hubspot_companies()
        if not companies:
            print("❌ No companies loaded from HubSpot")
            return

        # Extract Telegram groups
        groups = self.extract_telegram_groups()
        if not groups:
            print("❌ No Telegram groups extracted")
            return

        # Find matches
        print("🔍 Finding matches...")
        matches = self.find_matches(companies, groups)

        # Generate verification table
        table = self.generate_verification_table(matches)
        self.save_verification_table(table)

        # Print summary
        print(f"\n📊 Verification Results:")
        print(f"   HubSpot companies: {len(companies)}")
        print(f"   Telegram groups: {len(groups)}")

        quality_counts = {}
        for _, _, _, quality in matches:
            quality_counts[quality] = quality_counts.get(quality, 0) + 1

        print(f"   Match quality breakdown:")
        for quality, count in sorted(quality_counts.items()):
            if quality != "none":
                print(f"     {quality}: {count}")
        print(f"     No match: {quality_counts.get('none', 0)}")

        print(f"\n📄 Verification table saved to: telegram_match_verification.md")
        print(f"🔍 Please review the table to identify false positives!")


def main():
    verifier = TelegramMatchVerifier(
        hubspot_file="data/hubspot/hubspot-crm-exports-all-deals-2025-08-11-1.csv",
        telegram_export_path="data/telegram/DataExport_2025-08-19",
    )

    verifier.run_verification()


if __name__ == "__main__":
    main()
