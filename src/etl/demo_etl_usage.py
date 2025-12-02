#!/usr/bin/env python3
"""
ETL Data Usage Demo
Demonstrates how to use the machine-readable ETL output
"""

import json
import os
from typing import Any, Dict, List


def load_etl_data(file_path: str = "data/etl_output.json") -> Dict[str, Any]:
    """Load ETL data from JSON file"""
    if not os.path.exists(file_path):
        print(f"❌ ETL file not found: {file_path}")
        return {}

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def demo_company_search(data: Dict[str, Any]) -> None:
    """Demo: Search for companies"""
    print("\n🔍 COMPANY SEARCH DEMO")
    print("=" * 40)

    # Search for companies with "bit" in the name
    search_term = "bit"
    matches = [
        name
        for name in data.get("companies", {}).keys()
        if search_term.lower() in name.lower()
    ]

    print(f"Companies with '{search_term}' in name: {len(matches)}")
    for company in matches[:5]:  # Show first 5
        company_data = data["companies"][company]
        slack_count = len(company_data.get("slack_channels", []))
        telegram_count = len(company_data.get("telegram_chats", []))
        calendar_count = len(company_data.get("calendar_meetings", []))
        hubspot_count = len(company_data.get("hubspot_deals", []))

        print(
            f"  • {company}: Slack({slack_count}) Telegram({telegram_count}) Calendar({calendar_count}) HubSpot({hubspot_count})"
        )


def demo_data_analysis(data: Dict[str, Any]) -> None:
    """Demo: Analyze data patterns"""
    print("\n📊 DATA ANALYSIS DEMO")
    print("=" * 40)

    # Find companies with the most Slack activity
    companies_with_slack = []
    for company_name, company_data in data.get("companies", {}).items():
        slack_channels = company_data.get("slack_channels", [])
        if slack_channels:
            total_messages = sum(
                channel.get("message_count", 0) for channel in slack_channels
            )
            companies_with_slack.append((company_name, total_messages))

    # Sort by message count
    companies_with_slack.sort(key=lambda x: x[1], reverse=True)

    print("Top 5 companies by Slack message count:")
    for i, (company, message_count) in enumerate(companies_with_slack[:5], 1):
        print(f"  {i}. {company}: {message_count} messages")


def demo_stage_analysis(data: Dict[str, Any]) -> None:
    """Demo: Analyze stage detections"""
    print("\n🎯 STAGE DETECTION DEMO")
    print("=" * 40)

    # Find companies with stage detections
    companies_with_stages = []
    for company_name, company_data in data.get("companies", {}).items():
        slack_channels = company_data.get("slack_channels", [])
        total_stages = sum(
            channel.get("stage_detection_count", 0) for channel in slack_channels
        )
        if total_stages > 0:
            companies_with_stages.append((company_name, total_stages))

    # Sort by stage count
    companies_with_stages.sort(key=lambda x: x[1], reverse=True)

    print("Top 5 companies by stage detection count:")
    for i, (company, stage_count) in enumerate(companies_with_stages[:5], 1):
        print(f"  {i}. {company}: {stage_count} stage detections")


def demo_meeting_analysis(data: Dict[str, Any]) -> None:
    """Demo: Analyze calendar meetings"""
    print("\n📅 CALENDAR MEETINGS DEMO")
    print("=" * 40)

    # Find companies with calendar meetings
    companies_with_meetings = []
    for company_name, company_data in data.get("companies", {}).items():
        meetings = company_data.get("calendar_meetings", [])
        if meetings:
            companies_with_meetings.append((company_name, len(meetings)))

    # Sort by meeting count
    companies_with_meetings.sort(key=lambda x: x[1], reverse=True)

    print("Companies with calendar meetings:")
    for company, meeting_count in companies_with_meetings:
        print(f"  • {company}: {meeting_count} meetings")


def demo_data_export(data: Dict[str, Any]) -> None:
    """Demo: Export specific data subsets"""
    print("\n📤 DATA EXPORT DEMO")
    print("=" * 40)

    # Export companies with high data quality
    high_quality_companies = []
    for company_name, company_data in data.get("companies", {}).items():
        slack_count = len(company_data.get("slack_channels", []))
        telegram_count = len(company_data.get("telegram_chats", []))
        calendar_count = len(company_data.get("calendar_meetings", []))
        hubspot_count = len(company_data.get("hubspot_deals", []))

        total_sources = slack_count + telegram_count + calendar_count + hubspot_count
        if total_sources >= 2:  # High quality = 2+ sources
            high_quality_companies.append(
                {
                    "company_name": company_name,
                    "slack_channels": slack_count,
                    "telegram_chats": telegram_count,
                    "calendar_meetings": calendar_count,
                    "hubspot_deals": hubspot_count,
                    "total_sources": total_sources,
                }
            )

    # Sort by total sources
    high_quality_companies.sort(key=lambda x: x["total_sources"], reverse=True)

    print(f"Found {len(high_quality_companies)} high-quality companies:")
    for company in high_quality_companies[:5]:
        print(f"  • {company['company_name']}: {company['total_sources']} sources")


def demo_commission_analysis(data: Dict[str, Any]) -> None:
    """Demo: Analyze data for commission calculation"""
    print("\n💰 COMMISSION ANALYSIS DEMO")
    print("=" * 40)

    # Find companies with both Slack and stage detections (good for commission analysis)
    commission_ready_companies = []
    for company_name, company_data in data.get("companies", {}).items():
        slack_channels = company_data.get("slack_channels", [])
        if slack_channels:
            total_messages = sum(
                channel.get("message_count", 0) for channel in slack_channels
            )
            total_stages = sum(
                channel.get("stage_detection_count", 0) for channel in slack_channels
            )

            if total_stages > 0:  # Has stage detections
                commission_ready_companies.append(
                    {
                        "company_name": company_name,
                        "message_count": total_messages,
                        "stage_count": total_stages,
                        "channels": len(slack_channels),
                    }
                )

    # Sort by stage count
    commission_ready_companies.sort(key=lambda x: x["stage_count"], reverse=True)

    print("Companies ready for commission analysis:")
    for company in commission_ready_companies[:5]:
        print(
            f"  • {company['company_name']}: {company['stage_count']} stages, {company['message_count']} messages, {company['channels']} channels"
        )


def main():
    """Main demo function"""
    print("🚀 ETL DATA USAGE DEMO")
    print("=" * 50)

    # Load ETL data
    data = load_etl_data()
    if not data:
        return

    # Show basic stats
    stats = data.get("statistics", {})
    print(f"📊 Loaded data for {stats.get('total_companies', 0)} companies")
    print(f"   Slack: {stats.get('companies_with_slack', 0)} companies")
    print(f"   Telegram: {stats.get('companies_with_telegram', 0)} companies")
    print(f"   Calendar: {stats.get('companies_with_calendar', 0)} companies")
    print(f"   HubSpot: {stats.get('companies_with_hubspot', 0)} companies")

    # Run demos
    demo_company_search(data)
    demo_data_analysis(data)
    demo_stage_analysis(data)
    demo_meeting_analysis(data)
    demo_data_export(data)
    demo_commission_analysis(data)

    print("\n✅ Demo completed!")
    print("\n💡 The ETL data is now ready for machine processing!")
    print("   - All data is structured and searchable")
    print("   - Easy to filter and analyze")
    print("   - Perfect for commission calculations")
    print("   - Can be used by any programming language")


if __name__ == "__main__":
    main()
