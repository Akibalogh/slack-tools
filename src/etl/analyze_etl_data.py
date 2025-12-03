#!/usr/bin/env python3
"""
ETL Data Analysis Script
Reads and analyzes the machine-readable ETL output
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ETLDataAnalyzer:
    def __init__(self, etl_file: str = "data/etl_output.json"):
        self.etl_file = etl_file
        self.data = None

    def load_data(self) -> bool:
        """Load ETL data from JSON file"""
        if not os.path.exists(self.etl_file):
            logger.error(f"ETL file not found: {self.etl_file}")
            return False

        try:
            with open(self.etl_file, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            logger.info(f"Loaded ETL data from {self.etl_file}")
            return True
        except Exception as e:
            logger.error(f"Error loading ETL data: {e}")
            return False

    def get_data_coverage_summary(self) -> Dict[str, Any]:
        """Get data coverage summary"""
        if not self.data:
            return {}

        stats = self.data.get("statistics", {})

        summary = {
            "total_companies": stats.get("total_companies", 0),
            "companies_with_slack": stats.get("companies_with_slack", 0),
            "companies_with_telegram": stats.get("companies_with_telegram", 0),
            "companies_with_calendar": stats.get("companies_with_calendar", 0),
            "companies_with_hubspot": stats.get("companies_with_hubspot", 0),
            "total_slack_channels": stats.get("total_slack_channels", 0),
            "total_telegram_chats": stats.get("total_telegram_chats", 0),
            "total_calendar_meetings": stats.get("total_calendar_meetings", 0),
            "total_hubspot_deals": stats.get("total_hubspot_deals", 0),
        }

        # Calculate coverage percentages
        total = summary["total_companies"]
        if total > 0:
            summary["slack_coverage_pct"] = (
                summary["companies_with_slack"] / total
            ) * 100
            summary["telegram_coverage_pct"] = (
                summary["companies_with_telegram"] / total
            ) * 100
            summary["calendar_coverage_pct"] = (
                summary["companies_with_calendar"] / total
            ) * 100
            summary["hubspot_coverage_pct"] = (
                summary["companies_with_hubspot"] / total
            ) * 100

        return summary

    def get_companies_by_data_source(self, source: str) -> List[str]:
        """Get companies that have data from a specific source"""
        if not self.data:
            return []

        companies = []
        for company_name, company_data in self.data.get("companies", {}).items():
            if source == "slack" and company_data.get("slack_channels"):
                companies.append(company_name)
            elif source == "telegram" and company_data.get("telegram_chats"):
                companies.append(company_name)
            elif source == "calendar" and company_data.get("calendar_meetings"):
                companies.append(company_name)
            elif source == "hubspot" and company_data.get("hubspot_deals"):
                companies.append(company_name)

        return companies

    def get_companies_with_multiple_sources(
        self, min_sources: int = 2
    ) -> List[Dict[str, Any]]:
        """Get companies with data from multiple sources"""
        if not self.data:
            return []

        companies = []
        for company_name, company_data in self.data.get("companies", {}).items():
            sources = []
            if company_data.get("slack_channels"):
                sources.append("slack")
            if company_data.get("telegram_chats"):
                sources.append("telegram")
            if company_data.get("calendar_meetings"):
                sources.append("calendar")
            if company_data.get("hubspot_deals"):
                sources.append("hubspot")

            if len(sources) >= min_sources:
                companies.append(
                    {
                        "company_name": company_name,
                        "sources": sources,
                        "source_count": len(sources),
                        "data": company_data,
                    }
                )

        return sorted(companies, key=lambda x: x["source_count"], reverse=True)

    def get_company_details(self, company_name: str) -> Dict[str, Any]:
        """Get detailed data for a specific company"""
        if not self.data:
            return {}

        return self.data.get("companies", {}).get(company_name, {})

    def search_companies(self, query: str) -> List[str]:
        """Search for companies by name"""
        if not self.data:
            return []

        query_lower = query.lower()
        matches = []

        for company_name in self.data.get("companies", {}).keys():
            if query_lower in company_name.lower():
                matches.append(company_name)

        return matches

    def get_data_quality_metrics(self) -> Dict[str, Any]:
        """Get data quality metrics"""
        if not self.data:
            return {}

        metrics = {
            "companies_with_no_data": 0,
            "companies_with_single_source": 0,
            "companies_with_multiple_sources": 0,
            "average_sources_per_company": 0,
            "data_completeness_score": 0,
        }

        total_companies = 0
        total_sources = 0

        for company_name, company_data in self.data.get("companies", {}).items():
            total_companies += 1
            source_count = 0

            if company_data.get("slack_channels"):
                source_count += 1
            if company_data.get("telegram_chats"):
                source_count += 1
            if company_data.get("calendar_meetings"):
                source_count += 1
            if company_data.get("hubspot_deals"):
                source_count += 1

            total_sources += source_count

            if source_count == 0:
                metrics["companies_with_no_data"] += 1
            elif source_count == 1:
                metrics["companies_with_single_source"] += 1
            else:
                metrics["companies_with_multiple_sources"] += 1

        if total_companies > 0:
            metrics["average_sources_per_company"] = total_sources / total_companies
            metrics["data_completeness_score"] = (
                total_sources / (total_companies * 4)
            ) * 100  # 4 possible sources

        return metrics

    def export_company_list(
        self, output_file: str = "data/company_data_summary.csv"
    ) -> None:
        """Export company data summary to CSV"""
        if not self.data:
            logger.error("No data loaded")
            return

        import csv

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Company Name",
                    "Base Company",
                    "Slack Channels",
                    "Telegram Chats",
                    "Calendar Meetings",
                    "HubSpot Deals",
                    "Total Sources",
                    "Data Quality",
                ]
            )

            for company_name, company_data in self.data.get("companies", {}).items():
                company_info = company_data.get("company_info", {})
                base_company = company_info.get("base_company", "")

                slack_count = len(company_data.get("slack_channels", []))
                telegram_count = len(company_data.get("telegram_chats", []))
                calendar_count = len(company_data.get("calendar_meetings", []))
                hubspot_count = len(company_data.get("hubspot_deals", []))

                total_sources = sum(
                    [slack_count, telegram_count, calendar_count, hubspot_count]
                )

                data_quality = (
                    "High"
                    if total_sources >= 3
                    else (
                        "Medium"
                        if total_sources >= 2
                        else "Low"
                        if total_sources >= 1
                        else "None"
                    )
                )

                writer.writerow(
                    [
                        company_name,
                        base_company,
                        slack_count,
                        telegram_count,
                        calendar_count,
                        hubspot_count,
                        total_sources,
                        data_quality,
                    ]
                )

        logger.info(f"Company summary exported to {output_file}")

    def print_summary_report(self) -> None:
        """Print a summary report"""
        if not self.data:
            logger.error("No data loaded")
            return

        print("\n" + "=" * 60)
        print("ETL DATA ANALYSIS REPORT")
        print("=" * 60)

        # Basic statistics
        coverage = self.get_data_coverage_summary()
        print(f"\n📊 DATA COVERAGE SUMMARY")
        print(f"Total Companies: {coverage['total_companies']}")
        print(
            f"Slack Coverage: {coverage['companies_with_slack']} ({coverage.get('slack_coverage_pct', 0):.1f}%)"
        )
        print(
            f"Telegram Coverage: {coverage['companies_with_telegram']} ({coverage.get('telegram_coverage_pct', 0):.1f}%)"
        )
        print(
            f"Calendar Coverage: {coverage['companies_with_calendar']} ({coverage.get('calendar_coverage_pct', 0):.1f}%)"
        )
        print(
            f"HubSpot Coverage: {coverage['companies_with_hubspot']} ({coverage.get('hubspot_coverage_pct', 0):.1f}%)"
        )

        # Data quality metrics
        quality = self.get_data_quality_metrics()
        print(f"\n📈 DATA QUALITY METRICS")
        print(f"Companies with No Data: {quality['companies_with_no_data']}")
        print(
            f"Companies with Single Source: {quality['companies_with_single_source']}"
        )
        print(
            f"Companies with Multiple Sources: {quality['companies_with_multiple_sources']}"
        )
        print(
            f"Average Sources per Company: {quality['average_sources_per_company']:.2f}"
        )
        print(f"Data Completeness Score: {quality['data_completeness_score']:.1f}%")

        # Top companies with multiple sources
        multi_source = self.get_companies_with_multiple_sources(min_sources=2)
        if multi_source:
            print(f"\n🏆 TOP COMPANIES WITH MULTIPLE DATA SOURCES")
            for i, company in enumerate(multi_source[:10], 1):
                print(
                    f"{i:2d}. {company['company_name']} ({company['source_count']} sources: {', '.join(company['sources'])})"
                )

        print("\n" + "=" * 60)


def main():
    """Main function"""
    analyzer = ETLDataAnalyzer()

    if not analyzer.load_data():
        return

    analyzer.print_summary_report()
    analyzer.export_company_list()


if __name__ == "__main__":
    main()
