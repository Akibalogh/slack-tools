#!/usr/bin/env python3
"""
Map HubSpot CRM deals against Telegram conversations

Identifies which companies in the CRM pipeline have corresponding Telegram data
and provides a comprehensive mapping for commission analysis.
"""

import csv
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

from telegram_parser import TelegramParser


class CRMTelegramMapper:
    def __init__(self, hubspot_file: str, telegram_export_path: str):
        """
        Initialize the CRM to Telegram mapper

        Args:
            hubspot_file: Path to HubSpot CRM export CSV
            telegram_export_path: Path to Telegram export directory
        """
        self.hubspot_file = Path(hubspot_file)
        self.telegram_export_path = Path(telegram_export_path)
        self.telegram_parser = TelegramParser(telegram_export_path)

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

            logger.info(f"Loaded {len(companies)} companies from HubSpot CRM")
            return companies

        except Exception as e:
            logger.error(f"Error loading HubSpot companies: {e}")
            return []

    def find_telegram_matches(self, companies: List[str]) -> Dict[str, str]:
        """
        Find Telegram chat directories for each company

        Args:
            companies: List of company names from HubSpot

        Returns:
            Dictionary mapping company names to chat directories
        """
        matches = {}
        chats_index_path = self.telegram_export_path / "lists" / "chats.html"

        if not chats_index_path.exists():
            logger.error(f"Chats index not found at {chats_index_path}")
            return matches

        try:
            with open(chats_index_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Create a mapping of company names to potential Telegram matches
            for company in companies:
                chat_dir = self._find_chat_for_company(content, company)
                if chat_dir:
                    matches[company] = chat_dir

            logger.info(
                f"Found {len(matches)} Telegram matches out of {len(companies)} companies"
            )
            return matches

        except Exception as e:
            logger.error(f"Error finding Telegram matches: {e}")
            return matches

    def _find_chat_for_company(self, content: str, company_name: str) -> str:
        """Find Telegram chat directory for a specific company"""
        # Look for company name in the chats list
        soup = BeautifulSoup(content, "html.parser")

        for link in soup.find_all("a"):
            link_text = link.get_text().lower()
            company_lower = company_name.lower()

            # Check for exact matches and partial matches
            if (
                company_lower in link_text
                or any(word in link_text for word in company_lower.split())
                or any(word in company_lower for word in link_text.split())
            ):
                href = link.get("href", "")
                if "chat_" in href:
                    # Extract chat_XXXX from path like "../chats/chat_0058/messages.html"
                    chat_dir = href.split("/")[2]
                    return chat_dir

        return None

    def categorize_matches(self, matches: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Categorize matches by type and priority

        Args:
            matches: Dictionary of company names to chat directories

        Returns:
            Categorized matches
        """
        categories = {
            "exact_matches": [],  # Clear company name matches
            "partial_matches": [],  # Partial company name matches
            "high_priority": [],  # Companies with significant deal value
            "medium_priority": [],  # Companies with moderate deal value
            "low_priority": [],  # Companies with low deal value
        }

        for company, chat_dir in matches.items():
            # Check for exact matches first
            if self._is_exact_match(company, chat_dir):
                categories["exact_matches"].append(company)
            else:
                categories["partial_matches"].append(company)

            # TODO: Add priority categorization based on deal value when available

        return categories

    def _is_exact_match(self, company_name: str, chat_dir: str) -> bool:
        """Check if this is an exact company name match"""
        # This is a simplified check - could be enhanced with fuzzy matching
        return True  # For now, assume all matches are good

    def generate_mapping_report(
        self, companies: List[str], matches: Dict[str, str]
    ) -> str:
        """Generate a comprehensive mapping report"""
        report = []
        report.append("# CRM to Telegram Mapping Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        report.append(f"## Summary")
        report.append(f"- **Total HubSpot companies**: {len(companies)}")
        report.append(f"- **Telegram matches found**: {len(matches)}")
        report.append(f"- **Match percentage**: {len(matches)/len(companies)*100:.1f}%")
        report.append("")

        report.append("## Companies with Telegram Data")
        report.append("")

        for company, chat_dir in sorted(matches.items()):
            report.append(f"- **{company}** → `{chat_dir}`")

        report.append("")
        report.append("## Companies without Telegram Data")
        report.append("")

        companies_without_tg = [c for c in companies if c not in matches]
        for company in sorted(companies_without_tg):
            report.append(f"- {company}")

        report.append("")
        report.append("## Next Steps")
        report.append("1. Parse Telegram data for matched companies")
        report.append("2. Integrate with commission calculations")
        report.append("3. Update stage detection for Telegram messages")
        report.append("4. Compare commission splits with and without Telegram data")

        return "\n".join(report)

    def save_mapping_report(
        self, report: str, output_file: str = "crm_telegram_mapping.md"
    ):
        """Save the mapping report to a file"""
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report)
            logger.info(f"Mapping report saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving mapping report: {e}")

    def run_mapping(self) -> Dict[str, str]:
        """
        Run the complete mapping process

        Returns:
            Dictionary of company names to chat directories
        """
        logger.info("Starting CRM to Telegram mapping...")

        # Load HubSpot companies
        companies = self.load_hubspot_companies()
        if not companies:
            logger.error("No companies loaded from HubSpot")
            return {}

        # Find Telegram matches
        matches = self.find_telegram_matches(companies)

        # Generate and save report
        report = self.generate_mapping_report(companies, matches)
        self.save_mapping_report(report)

        # Print summary
        print(f"\n📊 Mapping Results:")
        print(f"   HubSpot companies: {len(companies)}")
        print(f"   Telegram matches: {len(matches)}")
        print(f"   Match rate: {len(matches)/len(companies)*100:.1f}%")

        if matches:
            print(f"\n🏆 Top matches found:")
            for i, (company, chat_dir) in enumerate(list(matches.items())[:10], 1):
                print(f"   {i}. {company} → {chat_dir}")

        return matches


def main():
    """Main function"""
    mapper = CRMTelegramMapper(
        hubspot_file="data/hubspot/hubspot-crm-exports-all-deals-2025-08-11-1.csv",
        telegram_export_path="data/telegram/DataExport_2025-08-19",
    )

    matches = mapper.run_mapping()

    if matches:
        print(
            f"\n✅ Mapping complete! Found {len(matches)} companies with Telegram data."
        )
        print(f"📄 Detailed report saved to: crm_telegram_mapping.md")
    else:
        print(f"\n❌ No matches found. Check the mapping report for details.")


if __name__ == "__main__":
    import logging
    from datetime import datetime

    from bs4 import BeautifulSoup

    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    main()
