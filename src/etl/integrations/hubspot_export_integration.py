#!/usr/bin/env python3
"""
HubSpot Export Integration

Reads HubSpot data from CSV/Excel export files instead of using the API.
This is simpler and doesn't require API credentials.
"""

import csv
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class HubSpotExportIntegration:
    """Integration for reading HubSpot data from export files"""

    def __init__(self, export_directory: str = "data/hubspot"):
        self.export_directory = export_directory
        self.deals_data = []
        self.contacts_data = []
        self.companies_data = []

    def load_export_files(self) -> bool:
        """Load all available export files from the directory"""
        if not os.path.exists(self.export_directory):
            logger.warning(
                f"HubSpot export directory not found: {self.export_directory}"
            )
            return False

        try:
            # Look for CSV and Excel files
            files = []
            for file in os.listdir(self.export_directory):
                if file.endswith((".csv", ".xlsx", ".xls")) and not file.startswith(
                    "."
                ):
                    files.append(file)

            if not files:
                logger.warning(
                    f"No HubSpot export files found in {self.export_directory}"
                )
                return False

            logger.info(f"Found {len(files)} HubSpot export files: {files}")

            # Load each file
            for file in files:
                file_path = os.path.join(self.export_directory, file)
                self._load_file(file_path)

            return True

        except Exception as e:
            logger.error(f"Error loading HubSpot export files: {e}")
            return False

    def _load_file(self, file_path: str):
        """Load a single export file"""
        try:
            if file_path.endswith(".csv"):
                df = pd.read_csv(file_path)
            elif file_path.endswith((".xlsx", ".xls")):
                df = pd.read_excel(file_path)
            else:
                logger.warning(f"Unsupported file format: {file_path}")
                return

            # Determine file type based on filename or columns
            filename = os.path.basename(file_path).lower()

            if "deal" in filename:
                self.deals_data.extend(self._process_deals(df))
                logger.info(f"Loaded {len(self.deals_data)} deals from {file_path}")
            elif "contact" in filename:
                self.contacts_data.extend(self._process_contacts(df))
                logger.info(
                    f"Loaded {len(self.contacts_data)} contacts from {file_path}"
                )
            elif "compan" in filename:
                self.companies_data.extend(self._process_companies(df))
                logger.info(
                    f"Loaded {len(self.companies_data)} companies from {file_path}"
                )
            else:
                # Try to auto-detect based on columns
                if self._is_deals_data(df):
                    self.deals_data.extend(self._process_deals(df))
                    logger.info(
                        f"Auto-detected and loaded {len(self.deals_data)} deals from {file_path}"
                    )
                elif self._is_contacts_data(df):
                    self.contacts_data.extend(self._process_contacts(df))
                    logger.info(
                        f"Auto-detected and loaded {len(self.contacts_data)} contacts from {file_path}"
                    )
                elif self._is_companies_data(df):
                    self.companies_data.extend(self._process_companies(df))
                    logger.info(
                        f"Auto-detected and loaded {len(self.companies_data)} companies from {file_path}"
                    )
                else:
                    logger.warning(f"Could not determine file type for {file_path}")

        except Exception as e:
            logger.error(f"Error loading file {file_path}: {e}")

    def _is_deals_data(self, df: pd.DataFrame) -> bool:
        """Check if DataFrame contains deal data"""
        deal_columns = ["deal", "opportunity", "amount", "stage", "close", "pipeline"]
        return any(col.lower() in " ".join(df.columns).lower() for col in deal_columns)

    def _is_contacts_data(self, df: pd.DataFrame) -> bool:
        """Check if DataFrame contains contact data"""
        contact_columns = ["contact", "email", "phone", "first", "last", "name"]
        return any(
            col.lower() in " ".join(df.columns).lower() for col in contact_columns
        )

    def _is_companies_data(self, df: pd.DataFrame) -> bool:
        """Check if DataFrame contains company data"""
        company_columns = ["company", "domain", "industry", "city", "state"]
        return any(
            col.lower() in " ".join(df.columns).lower() for col in company_columns
        )

    def _process_deals(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Process deals DataFrame into standardized format, filtering for commit/closed won deals only"""
        deals = []

        for _, row in df.iterrows():
            deal = {
                "deal_name": self._get_value(
                    row, ["Deal Name", "deal name", "deal_name", "name", "title"]
                ),
                "company_name": self._get_value(
                    row,
                    [
                        "Company Name",
                        "company",
                        "company_name",
                        "account",
                        "account_name",
                    ],
                ),
                "deal_stage": self._get_value(
                    row,
                    ["Deal Stage", "stage", "deal_stage", "pipeline_stage", "status"],
                ),
                "deal_value": self._get_value(
                    row, ["Amount", "amount", "deal_value", "value", "revenue"]
                ),
                "close_date": self._get_value(
                    row,
                    [
                        "Close Date",
                        "close date",
                        "close_date",
                        "expected_close",
                        "close",
                    ],
                ),
                "deal_owner": self._get_value(
                    row,
                    [
                        "Deal owner",
                        "owner",
                        "deal_owner",
                        "assigned_to",
                        "user",
                        "deal owner",
                    ],
                ),
                "description": self._get_value(
                    row, ["Use case", "description", "notes", "comments", "use case"]
                ),
                "source": self._get_value(
                    row, ["Sourced by", "source", "lead_source", "origin", "sourced by"]
                ),
                "created_date": self._get_value(
                    row, ["created", "created_date", "date_created"]
                ),
                "last_modified": self._get_value(
                    row, ["modified", "last_modified", "updated"]
                ),
                "priority": self._get_value(row, ["Priority", "priority"]),
                "estimated_fees": self._get_value(
                    row, ["Estimated Fees ($)", "estimated fees ($)", "estimated_fees"]
                ),
                "btc_fund_size": self._get_value(
                    row, ["BTC Fund Size ($Mn)", "btc fund size ($mn)", "btc_fund_size"]
                ),
            }

            # For this specific export, deal_name contains the company name
            # If no separate company_name field, use deal_name as company_name
            if not deal["company_name"] and deal["deal_name"]:
                deal["company_name"] = deal["deal_name"]

            # Only include deals with at least a name and company
            if not deal["deal_name"] or not deal["company_name"]:
                continue

            # Filter for commit or closed won deals only
            deal_stage = deal["deal_stage"]
            if deal_stage:
                deal_stage_lower = deal_stage.lower().strip()
                # Check for commit or closed won status
                if not (
                    deal_stage_lower
                    in ["commit", "closed won", "closed-won", "closedwon"]
                    or "commit" in deal_stage_lower
                    or "closed won" in deal_stage_lower
                ):
                    continue

            deals.append(deal)

        return deals

    def _process_contacts(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Process contacts DataFrame into standardized format"""
        contacts = []

        for _, row in df.iterrows():
            contact = {
                "first_name": self._get_value(
                    row, ["first name", "first_name", "first"]
                ),
                "last_name": self._get_value(row, ["last name", "last_name", "last"]),
                "email": self._get_value(row, ["email", "email_address", "e_mail"]),
                "company": self._get_value(row, ["company", "company_name", "account"]),
                "job_title": self._get_value(
                    row, ["title", "job_title", "position", "role"]
                ),
                "phone": self._get_value(row, ["phone", "phone_number", "telephone"]),
                "city": self._get_value(row, ["city", "location"]),
                "state": self._get_value(row, ["state", "province", "region"]),
                "country": self._get_value(row, ["country", "nation"]),
                "created_date": self._get_value(
                    row, ["created", "created_date", "date_created"]
                ),
                "last_modified": self._get_value(
                    row, ["modified", "last_modified", "updated"]
                ),
            }

            # Only include contacts with at least an email
            if contact["email"]:
                contacts.append(contact)

        return contacts

    def _process_companies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Process companies DataFrame into standardized format"""
        companies = []

        for _, row in df.iterrows():
            company = {
                "company_name": self._get_value(
                    row, ["company name", "company_name", "name", "account"]
                ),
                "domain": self._get_value(row, ["domain", "website", "url"]),
                "industry": self._get_value(row, ["industry", "sector", "vertical"]),
                "city": self._get_value(row, ["city", "location"]),
                "state": self._get_value(row, ["state", "province", "region"]),
                "country": self._get_value(row, ["country", "nation"]),
                "employee_count": self._get_value(
                    row, ["employees", "employee_count", "size"]
                ),
                "annual_revenue": self._get_value(
                    row, ["revenue", "annual_revenue", "sales"]
                ),
                "created_date": self._get_value(
                    row, ["created", "created_date", "date_created"]
                ),
                "last_modified": self._get_value(
                    row, ["modified", "last_modified", "updated"]
                ),
            }

            # Only include companies with at least a name
            if company["company_name"]:
                companies.append(company)

        return companies

    def _get_value(self, row: pd.Series, possible_keys: List[str]) -> Optional[str]:
        """Get value from row using possible column names"""
        for key in possible_keys:
            if key in row.index and pd.notna(row[key]):
                return str(row[key]).strip()
        return None

    def get_deals(self) -> List[Dict[str, Any]]:
        """Get all deals data"""
        return self.deals_data

    def get_contacts(self) -> List[Dict[str, Any]]:
        """Get all contacts data"""
        return self.contacts_data

    def get_companies(self) -> List[Dict[str, Any]]:
        """Get all companies data"""
        return self.companies_data

    def get_deals_by_company(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get deals grouped by company name"""
        company_deals = {}

        for deal in self.deals_data:
            company = deal.get("company_name", "").strip()
            if company:
                if company not in company_deals:
                    company_deals[company] = []
                company_deals[company].append(deal)

        return company_deals

    def get_contacts_by_company(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get contacts grouped by company name"""
        company_contacts = {}

        for contact in self.contacts_data:
            company = contact.get("company", "").strip()
            if company:
                if company not in company_contacts:
                    company_contacts[company] = []
                company_contacts[company].append(contact)

        return company_contacts

    def test_connection(self) -> bool:
        """Test if export files can be loaded"""
        return self.load_export_files()


def main():
    """Test the HubSpot export integration"""
    integration = HubSpotExportIntegration()

    if integration.test_connection():
        print("✅ HubSpot export integration working!")
        print(f"Deals: {len(integration.get_deals())}")
        print(f"Contacts: {len(integration.get_contacts())}")
        print(f"Companies: {len(integration.get_companies())}")

        # Show sample data
        deals = integration.get_deals()
        if deals:
            print(f"\nSample deal: {deals[0]}")
    else:
        print("❌ HubSpot export integration failed")


if __name__ == "__main__":
    main()
