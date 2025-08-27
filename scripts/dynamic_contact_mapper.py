#!/usr/bin/env python3
"""
Dynamic Contact Mapper
Extracts company contacts from Slack conversations and builds domain mappings for calendar searches
"""

import re
import sqlite3
from typing import Dict, List, Set
from pathlib import Path


class DynamicContactMapper:
    """Dynamically map companies to their contacts and domains"""

    def __init__(self, db_path: str = "data/slack/repsplit.db"):
        self.db_path = db_path
        self.company_contacts = {}
        self.company_domains = {}

    def extract_contacts_from_slack(self):
        """Extract company contacts from Slack conversations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all messages from bitsafe channels
        cursor.execute(
            """
            SELECT m.text, c.name 
            FROM messages m
            JOIN conversations c ON m.conv_id = c.conv_id
            WHERE c.is_bitsafe = 1 AND m.text IS NOT NULL
        """
        )

        messages = cursor.fetchall()
        conn.close()

        # Extract email addresses and build company mappings
        for message_text, channel_name in messages:
            if message_text:
                # Extract company name from channel
                company_name = channel_name.replace("-bitsafe", "")

                # Find email addresses in message
                emails = self._extract_emails(message_text)

                if emails:
                    if company_name not in self.company_contacts:
                        self.company_contacts[company_name] = set()
                    self.company_contacts[company_name].update(emails)

                    # Extract domains
                    domains = self._extract_domains(emails)
                    if domains:
                        if company_name not in self.company_domains:
                            self.company_domains[company_name] = set()
                        self.company_domains[company_name].update(domains)

        print(f"Extracted contacts for {len(self.company_contacts)} companies")

    def _extract_emails(self, text: str) -> Set[str]:
        """Extract email addresses from text"""
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        emails = re.findall(email_pattern, text)
        return set(emails)

    def _extract_domains(self, emails: Set[str]) -> Set[str]:
        """Extract domains from email addresses"""
        domains = set()
        for email in emails:
            if "@" in email:
                domain = email.split("@")[1]
                domains.add(domain)
        return domains

    def get_company_contacts(self, company_name: str) -> List[str]:
        """Get contacts for a specific company"""
        # Try exact match first
        if company_name in self.company_contacts:
            return list(self.company_contacts[company_name])

        # Try partial matches
        for company, contacts in self.company_contacts.items():
            if (
                company_name.lower() in company.lower()
                or company.lower() in company_name.lower()
            ):
                return list(contacts)

        return []

    def get_company_domains(self, company_name: str) -> List[str]:
        """Get domains for a specific company"""
        # Try exact match first
        if company_name in self.company_domains:
            return list(self.company_domains[company_name])

        # Try partial matches
        for company, domains in self.company_domains.items():
            if (
                company_name.lower() in company.lower()
                or company.lower() in company_name.lower()
            ):
                return list(domains)

        return []

    def search_calendar_by_company(
        self, company_name: str, calendar_service
    ) -> List[dict]:
        """Search calendar for meetings with company contacts"""
        meetings = []

        # Get company contacts and domains
        contacts = self.get_company_contacts(company_name)
        domains = self.get_company_domains(company_name)

        if not contacts and not domains:
            # Fallback: search by company name only
            print(
                f"No contacts/domains found for {company_name}, searching by name only"
            )
            return self._search_by_company_name(company_name, calendar_service)

        # Search for meetings with specific contacts
        for contact in contacts:
            contact_meetings = self._search_calendar_for_contact(
                contact, calendar_service
            )
            meetings.extend(contact_meetings)

        # Search for meetings with domain attendees
        for domain in domains:
            domain_meetings = self._search_calendar_for_domain(domain, calendar_service)
            meetings.extend(domain_meetings)

        return meetings

    def _search_by_company_name(
        self, company_name: str, calendar_service
    ) -> List[dict]:
        """Fallback search by company name in meeting titles/descriptions"""
        # This would use the existing company name search logic
        pass

    def _search_calendar_for_contact(
        self, contact: str, calendar_service
    ) -> List[dict]:
        """Search calendar for meetings with a specific contact"""
        # Implementation would depend on calendar service
        pass

    def _search_calendar_for_domain(self, domain: str, calendar_service) -> List[dict]:
        """Search calendar for meetings with attendees from a specific domain"""
        # Implementation would depend on calendar service
        pass

    def print_company_mappings(self):
        """Print all company contact mappings"""
        print("\n=== COMPANY CONTACT MAPPINGS ===")
        for company, contacts in self.company_contacts.items():
            domains = self.company_domains.get(company, set())
            print(f"\n{company}:")
            if contacts:
                print(f"  Contacts: {', '.join(sorted(contacts))}")
            if domains:
                print(f"  Domains: {', '.join(sorted(domains))}")


def main():
    """Test the dynamic contact mapper"""
    mapper = DynamicContactMapper()

    print("Extracting contacts from Slack conversations...")
    mapper.extract_contacts_from_slack()

    print("\nCompany mappings:")
    mapper.print_company_mappings()

    # Test specific companies
    test_companies = ["brikly", "allnodes", "bitgo", "figment"]
    for company in test_companies:
        contacts = mapper.get_company_contacts(company)
        domains = mapper.get_company_domains(company)
        print(f"\n{company}: {len(contacts)} contacts, {len(domains)} domains")


if __name__ == "__main__":
    main()
