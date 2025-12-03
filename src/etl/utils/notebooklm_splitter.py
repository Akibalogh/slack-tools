#!/usr/bin/env python3
"""
NotebookLM File Splitter
Splits large ETL output into smaller, focused files for better NotebookLM compatibility
"""

import json
import os
from typing import Any, Dict, List


class NotebookLMSplitter:
    """Splits ETL output into focused files for NotebookLM"""

    def __init__(self, output_dir: str = "output/notebooklm"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def split_etl_output(self, etl_data: Dict[str, Any]) -> List[str]:
        """Split ETL data into focused files"""
        created_files = []

        # 1. Executive Summary (small, high-level overview)
        summary_file = self._create_executive_summary(etl_data)
        created_files.append(summary_file)

        # 2. Company Rankings (top companies by engagement)
        rankings_file = self._create_company_rankings(etl_data)
        created_files.append(rankings_file)

        # 3. Data Coverage Analysis
        coverage_file = self._create_coverage_analysis(etl_data)
        created_files.append(coverage_file)

        # 4. High-Value Companies (detailed data for top companies)
        high_value_file = self._create_high_value_companies(etl_data)
        created_files.append(high_value_file)

        # 5. Commission Opportunities
        commission_file = self._create_commission_opportunities(etl_data)
        created_files.append(commission_file)

        return created_files

    def _create_executive_summary(self, data: Dict[str, Any]) -> str:
        """Create executive summary file"""
        companies = data.get("companies", {})
        stats = data.get("statistics", {})
        metadata = data.get("metadata", {})

        # Calculate engagement metrics
        company_engagement = []
        for company_name, company_data in companies.items():
            slack_channels = company_data.get("slack_channels", [])
            telegram_chats = company_data.get("telegram_chats", [])
            calendar_meetings = company_data.get("calendar_meetings", [])
            hubspot_deals = company_data.get("hubspot_deals", [])

            total_slack_messages = sum(
                ch.get("message_count", 0) for ch in slack_channels
            )
            total_telegram_messages = sum(
                ch.get("message_count", 0) for ch in telegram_chats
            )
            total_meetings = len(calendar_meetings)
            total_deals = len(hubspot_deals)

            engagement_score = (
                total_slack_messages * 0.4
                + total_telegram_messages * 0.3
                + total_meetings * 10
                + total_deals * 20
            )

            company_engagement.append(
                {
                    "name": company_name,
                    "engagement_score": engagement_score,
                    "slack_messages": total_slack_messages,
                    "telegram_messages": total_telegram_messages,
                    "meetings": total_meetings,
                    "deals": total_deals,
                    "channels": len(slack_channels) + len(telegram_chats),
                }
            )

        # Sort by engagement score
        company_engagement.sort(key=lambda x: x["engagement_score"], reverse=True)

        # Create summary content
        content = [
            "=" * 80,
            "COMMISSION CALCULATOR - EXECUTIVE SUMMARY",
            "=" * 80,
            f"Generated: {metadata.get('generated_at', 'Unknown')}",
            f"Total Companies: {len(companies)}",
            "",
            "=" * 80,
            "NOTEBOOKLM ANALYSIS REQUESTS",
            "=" * 80,
            "Please analyze this data and provide insights on:",
            "",
            "1. COMPANY ENGAGEMENT ANALYSIS:",
            "   - Which companies have the highest engagement across Slack channels?",
            "   - What are the most active companies based on message volume?",
            "   - Which companies show signs of high-value relationships?",
            "",
            "2. SALES OPPORTUNITY IDENTIFICATION:",
            "   - Which companies appear to be in early stages (based on channel activity)?",
            "   - What companies show signs of scaling or growth?",
            "   - Which companies might need more attention or follow-up?",
            "",
            "3. COMMISSION CALCULATION INSIGHTS:",
            "   - Which companies would generate the highest commissions based on activity?",
            "   - What companies show potential for increased commission opportunities?",
            "   - How should commission rates be adjusted based on engagement levels?",
            "",
            "=" * 80,
            "DATA COVERAGE SUMMARY",
            "=" * 80,
            f"Companies with Slack data: {stats.get('companies_with_slack', 0)}",
            f"Companies with Telegram data: {stats.get('companies_with_telegram', 0)}",
            f"Companies with Calendar data: {stats.get('companies_with_calendar', 0)}",
            f"Companies with HubSpot data: {stats.get('companies_with_hubspot', 0)}",
            "",
            f"Total Slack Channels: {stats.get('total_slack_channels', 0)}",
            f"Total Telegram Chats: {stats.get('total_telegram_chats', 0)}",
            f"Total Calendar Meetings: {stats.get('total_calendar_meetings', 0)}",
            f"Total HubSpot Deals: {stats.get('total_hubspot_deals', 0)}",
            "",
            "=" * 80,
            "TOP 20 HIGHEST ENGAGEMENT COMPANIES",
            "=" * 80,
        ]

        for i, company in enumerate(company_engagement[:20], 1):
            commission_potential = (
                "HIGH"
                if company["engagement_score"] > 150
                else "MEDIUM"
                if company["engagement_score"] > 75
                else "LOW"
            )
            content.extend(
                [
                    f"{i:2d}. {company['name']}",
                    f"    Engagement Score: {company['engagement_score']:.1f}",
                    f"    Commission Potential: {commission_potential}",
                    f"    Slack Messages: {company['slack_messages']}",
                    f"    Telegram Messages: {company['telegram_messages']}",
                    f"    Meetings: {company['meetings']}",
                    f"    Deals: {company['deals']}",
                    f"    Total Channels: {company['channels']}",
                    "",
                ]
            )

        # Engagement distribution
        high_engagement = len(
            [c for c in company_engagement if c["engagement_score"] > 100]
        )
        medium_engagement = len(
            [c for c in company_engagement if 50 <= c["engagement_score"] <= 100]
        )
        low_engagement = len(
            [c for c in company_engagement if c["engagement_score"] < 50]
        )

        content.extend(
            [
                "=" * 80,
                "ENGAGEMENT DISTRIBUTION",
                "=" * 80,
                f"High Engagement (>100): {high_engagement} companies",
                f"Medium Engagement (50-100): {medium_engagement} companies",
                f"Low Engagement (<50): {low_engagement} companies",
                "",
                "=" * 80,
                "RECOMMENDED NEXT ACTIONS",
                "=" * 80,
                "1. Focus on top 10 high-engagement companies for immediate commission opportunities",
                "2. Investigate medium-engagement companies for growth potential",
                "3. Address data coverage gaps for low-engagement companies",
                "4. Implement calendar and HubSpot integrations for complete data picture",
                "5. Set up automated monitoring for engagement score changes",
                "",
                "=" * 80,
                "END OF EXECUTIVE SUMMARY",
                "=" * 80,
            ]
        )

        # Write file
        file_path = os.path.join(self.output_dir, "executive_summary.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

        return file_path

    def _create_company_rankings(self, data: Dict[str, Any]) -> str:
        """Create detailed company rankings file"""
        companies = data.get("companies", {})

        # Calculate engagement metrics for all companies
        company_engagement = []
        for company_name, company_data in companies.items():
            slack_channels = company_data.get("slack_channels", [])
            telegram_chats = company_data.get("telegram_chats", [])
            calendar_meetings = company_data.get("calendar_meetings", [])
            hubspot_deals = company_data.get("hubspot_deals", [])

            total_slack_messages = sum(
                ch.get("message_count", 0) for ch in slack_channels
            )
            total_telegram_messages = sum(
                ch.get("message_count", 0) for ch in telegram_chats
            )
            total_meetings = len(calendar_meetings)
            total_deals = len(hubspot_deals)

            engagement_score = (
                total_slack_messages * 0.4
                + total_telegram_messages * 0.3
                + total_meetings * 10
                + total_deals * 20
            )

            company_engagement.append(
                {
                    "name": company_name,
                    "engagement_score": engagement_score,
                    "slack_messages": total_slack_messages,
                    "telegram_messages": total_telegram_messages,
                    "meetings": total_meetings,
                    "deals": total_deals,
                    "channels": len(slack_channels) + len(telegram_chats),
                    "slack_channels": len(slack_channels),
                    "telegram_chats": len(telegram_chats),
                }
            )

        # Sort by engagement score
        company_engagement.sort(key=lambda x: x["engagement_score"], reverse=True)

        content = [
            "=" * 80,
            "COMPANY ENGAGEMENT RANKINGS",
            "=" * 80,
            "Complete ranking of all companies by engagement score",
            "",
            "RANKING METHODOLOGY:",
            "- Engagement Score = (Slack Messages × 0.4) + (Telegram Messages × 0.3) + (Meetings × 10) + (Deals × 20)",
            "- Higher scores indicate more active relationships",
            "- Commission potential based on engagement level",
            "",
            "=" * 80,
            "ALL COMPANIES RANKED BY ENGAGEMENT",
            "=" * 80,
        ]

        for i, company in enumerate(company_engagement, 1):
            commission_potential = (
                "HIGH"
                if company["engagement_score"] > 150
                else "MEDIUM"
                if company["engagement_score"] > 75
                else "LOW"
            )
            content.extend(
                [
                    f"{i:3d}. {company['name']}",
                    f"     Engagement Score: {company['engagement_score']:.1f}",
                    f"     Commission Potential: {commission_potential}",
                    f"     Slack: {company['slack_messages']} messages in {company['slack_channels']} channels",
                    f"     Telegram: {company['telegram_messages']} messages in {company['telegram_chats']} chats",
                    f"     Meetings: {company['meetings']}",
                    f"     Deals: {company['deals']}",
                    f"     Total Channels: {company['channels']}",
                    "",
                ]
            )

        # Write file
        file_path = os.path.join(self.output_dir, "company_rankings.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

        return file_path

    def _create_coverage_analysis(self, data: Dict[str, Any]) -> str:
        """Create data coverage analysis file"""
        companies = data.get("companies", {})
        stats = data.get("statistics", {})

        content = [
            "=" * 80,
            "DATA COVERAGE ANALYSIS",
            "=" * 80,
            "Analysis of data coverage gaps and opportunities for improvement",
            "",
            "=" * 80,
            "OVERALL COVERAGE STATISTICS",
            "=" * 80,
            f"Total Companies: {len(companies)}",
            f"Companies with Slack data: {stats.get('companies_with_slack', 0)} ({stats.get('companies_with_slack', 0)/len(companies)*100:.1f}%)",
            f"Companies with Telegram data: {stats.get('companies_with_telegram', 0)} ({stats.get('companies_with_telegram', 0)/len(companies)*100:.1f}%)",
            f"Companies with Calendar data: {stats.get('companies_with_calendar', 0)} ({stats.get('companies_with_calendar', 0)/len(companies)*100:.1f}%)",
            f"Companies with HubSpot data: {stats.get('companies_with_hubspot', 0)} ({stats.get('companies_with_hubspot', 0)/len(companies)*100:.1f}%)",
            "",
            f"Total Slack Channels: {stats.get('total_slack_channels', 0)}",
            f"Total Telegram Chats: {stats.get('total_telegram_chats', 0)}",
            f"Total Calendar Meetings: {stats.get('total_calendar_meetings', 0)}",
            f"Total HubSpot Deals: {stats.get('total_hubspot_deals', 0)}",
            "",
            "=" * 80,
            "COVERAGE GAPS BY COMPANY",
            "=" * 80,
        ]

        # Analyze coverage gaps
        no_slack = []
        no_telegram = []
        no_calendar = []
        no_hubspot = []

        for company_name, company_data in companies.items():
            slack_channels = company_data.get("slack_channels", [])
            telegram_chats = company_data.get("telegram_chats", [])
            calendar_meetings = company_data.get("calendar_meetings", [])
            hubspot_deals = company_data.get("hubspot_deals", [])

            if not slack_channels:
                no_slack.append(company_name)
            if not telegram_chats:
                no_telegram.append(company_name)
            if not calendar_meetings:
                no_calendar.append(company_name)
            if not hubspot_deals:
                no_hubspot.append(company_name)

        content.extend(
            [
                f"Companies with NO Slack data ({len(no_slack)}):",
                *[f"  - {name}" for name in no_slack[:20]],  # Show first 20
                f"{'  ...' if len(no_slack) > 20 else ''}",
                "",
                f"Companies with NO Telegram data ({len(no_telegram)}):",
                *[f"  - {name}" for name in no_telegram[:20]],  # Show first 20
                f"{'  ...' if len(no_telegram) > 20 else ''}",
                "",
                f"Companies with NO Calendar data ({len(no_calendar)}):",
                *[f"  - {name}" for name in no_calendar[:20]],  # Show first 20
                f"{'  ...' if len(no_calendar) > 20 else ''}",
                "",
                f"Companies with NO HubSpot data ({len(no_hubspot)}):",
                *[f"  - {name}" for name in no_hubspot[:20]],  # Show first 20
                f"{'  ...' if len(no_hubspot) > 20 else ''}",
                "",
                "=" * 80,
                "RECOMMENDATIONS FOR IMPROVING COVERAGE",
                "=" * 80,
                "1. PRIORITY: Implement Google Calendar integration",
                "   - Would add meeting data for all companies",
                "   - Critical for understanding relationship depth",
                "",
                "2. PRIORITY: Implement HubSpot integration",
                "   - Would add deal data for sales tracking",
                "   - Essential for commission calculations",
                "",
                "3. MEDIUM: Improve Telegram matching algorithms",
                "   - Current coverage is low (14%)",
                "   - Many companies likely have Telegram presence",
                "",
                "4. LOW: Expand Slack data collection",
                "   - Already at 97% coverage",
                "   - Focus on message quality over quantity",
                "",
                "=" * 80,
                "END OF COVERAGE ANALYSIS",
                "=" * 80,
            ]
        )

        # Write file
        file_path = os.path.join(self.output_dir, "coverage_analysis.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

        return file_path

    def _create_high_value_companies(self, data: Dict[str, Any]) -> str:
        """Create detailed data for high-value companies"""
        companies = data.get("companies", {})

        # Calculate engagement metrics and get top companies
        company_engagement = []
        for company_name, company_data in companies.items():
            slack_channels = company_data.get("slack_channels", [])
            telegram_chats = company_data.get("telegram_chats", [])
            calendar_meetings = company_data.get("calendar_meetings", [])
            hubspot_deals = company_data.get("hubspot_deals", [])

            total_slack_messages = sum(
                ch.get("message_count", 0) for ch in slack_channels
            )
            total_telegram_messages = sum(
                ch.get("message_count", 0) for ch in telegram_chats
            )
            total_meetings = len(calendar_meetings)
            total_deals = len(hubspot_deals)

            engagement_score = (
                total_slack_messages * 0.4
                + total_telegram_messages * 0.3
                + total_meetings * 10
                + total_deals * 20
            )

            company_engagement.append(
                {
                    "name": company_name,
                    "engagement_score": engagement_score,
                    "company_data": company_data,
                }
            )

        # Sort by engagement score and get top 10
        company_engagement.sort(key=lambda x: x["engagement_score"], reverse=True)
        top_companies = company_engagement[:10]

        content = [
            "=" * 80,
            "HIGH-VALUE COMPANIES - DETAILED ANALYSIS",
            "=" * 80,
            "Detailed data for the top 10 highest engagement companies",
            "These companies represent the highest commission potential",
            "",
        ]

        for i, company in enumerate(top_companies, 1):
            company_name = company["name"]
            company_data = company["company_data"]
            engagement_score = company["engagement_score"]

            slack_channels = company_data.get("slack_channels", [])
            telegram_chats = company_data.get("telegram_chats", [])
            calendar_meetings = company_data.get("calendar_meetings", [])
            hubspot_deals = company_data.get("hubspot_deals", [])

            content.extend(
                [
                    "=" * 60,
                    f"{i}. {company_name}",
                    f"   Engagement Score: {engagement_score:.1f}",
                    "=" * 60,
                    "",
                    "SLACK CHANNELS:",
                ]
            )

            if slack_channels:
                for channel in slack_channels:
                    content.extend(
                        [
                            f"  - {channel.get('name', 'Unknown')}",
                            f"    Messages: {channel.get('message_count', 0)}",
                            f"    Stage Detections: {channel.get('stage_detection_count', 0)}",
                            f"    Match Confidence: {channel.get('match_confidence', 'N/A')}",
                            "",
                        ]
                    )
            else:
                content.append("  No Slack data")

            content.extend(
                [
                    "TELEGRAM CHATS:",
                ]
            )

            if telegram_chats:
                for chat in telegram_chats:
                    content.extend(
                        [
                            f"  - {chat.get('chat_name', 'Unknown')}",
                            f"    Messages: {chat.get('message_count', 0)}",
                            f"    Match Confidence: {chat.get('match_confidence', 'N/A')}",
                            "",
                        ]
                    )
            else:
                content.append("  No Telegram data")

            content.extend(
                [
                    "CALENDAR MEETINGS:",
                ]
            )

            if calendar_meetings:
                for meeting in calendar_meetings:
                    content.extend(
                        [
                            f"  - {meeting.get('title', 'Unknown')}",
                            f"    Time: {meeting.get('start_time', 'Unknown')} - {meeting.get('end_time', 'Unknown')}",
                            f"    Location: {meeting.get('location', 'Unknown')}",
                            "",
                        ]
                    )
            else:
                content.append("  No Calendar data")

            content.extend(
                [
                    "HUBSPOT DEALS:",
                ]
            )

            if hubspot_deals:
                for deal in hubspot_deals:
                    content.extend(
                        [
                            f"  - {deal.get('deal_name', 'Unknown')}",
                            f"    Stage: {deal.get('deal_stage', 'Unknown')}",
                            f"    Value: ${deal.get('deal_value', 'Unknown')}",
                            f"    Owner: {deal.get('deal_owner', 'Unknown')}",
                            "",
                        ]
                    )
            else:
                content.append("  No HubSpot data")

            content.append("")

        content.extend(
            [
                "=" * 80,
                "END OF HIGH-VALUE COMPANIES ANALYSIS",
                "=" * 80,
            ]
        )

        # Write file
        file_path = os.path.join(self.output_dir, "high_value_companies.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

        return file_path

    def _create_commission_opportunities(self, data: Dict[str, Any]) -> str:
        """Create commission opportunities analysis file"""
        companies = data.get("companies", {})

        # Calculate engagement metrics
        company_engagement = []
        for company_name, company_data in companies.items():
            slack_channels = company_data.get("slack_channels", [])
            telegram_chats = company_data.get("telegram_chats", [])
            calendar_meetings = company_data.get("calendar_meetings", [])
            hubspot_deals = company_data.get("hubspot_deals", [])

            total_slack_messages = sum(
                ch.get("message_count", 0) for ch in slack_channels
            )
            total_telegram_messages = sum(
                ch.get("message_count", 0) for ch in telegram_chats
            )
            total_meetings = len(calendar_meetings)
            total_deals = len(hubspot_deals)

            engagement_score = (
                total_slack_messages * 0.4
                + total_telegram_messages * 0.3
                + total_meetings * 10
                + total_deals * 20
            )

            # Calculate commission potential
            if engagement_score > 150:
                commission_tier = "HIGH"
                estimated_commission = engagement_score * 0.1
            elif engagement_score > 75:
                commission_tier = "MEDIUM"
                estimated_commission = engagement_score * 0.05
            else:
                commission_tier = "LOW"
                estimated_commission = engagement_score * 0.02

            company_engagement.append(
                {
                    "name": company_name,
                    "engagement_score": engagement_score,
                    "commission_tier": commission_tier,
                    "estimated_commission": estimated_commission,
                    "slack_messages": total_slack_messages,
                    "telegram_messages": total_telegram_messages,
                    "meetings": total_meetings,
                    "deals": total_deals,
                    "channels": len(slack_channels) + len(telegram_chats),
                }
            )

        # Sort by estimated commission
        company_engagement.sort(key=lambda x: x["estimated_commission"], reverse=True)

        content = [
            "=" * 80,
            "COMMISSION OPPORTUNITIES ANALYSIS",
            "=" * 80,
            "Analysis of commission potential for all companies",
            "",
            "COMMISSION CALCULATION METHODOLOGY:",
            "- HIGH Tier (>150 engagement): 10% of engagement score",
            "- MEDIUM Tier (75-150 engagement): 5% of engagement score",
            "- LOW Tier (<75 engagement): 2% of engagement score",
            "",
            "=" * 80,
            "TOP COMMISSION OPPORTUNITIES",
            "=" * 80,
        ]

        # Top 20 commission opportunities
        for i, company in enumerate(company_engagement[:20], 1):
            content.extend(
                [
                    f"{i:2d}. {company['name']}",
                    f"    Commission Tier: {company['commission_tier']}",
                    f"    Estimated Commission: ${company['estimated_commission']:.2f}",
                    f"    Engagement Score: {company['engagement_score']:.1f}",
                    f"    Slack Messages: {company['slack_messages']}",
                    f"    Telegram Messages: {company['telegram_messages']}",
                    f"    Meetings: {company['meetings']}",
                    f"    Deals: {company['deals']}",
                    f"    Total Channels: {company['channels']}",
                    "",
                ]
            )

        # Commission tier distribution
        high_tier = len(
            [c for c in company_engagement if c["commission_tier"] == "HIGH"]
        )
        medium_tier = len(
            [c for c in company_engagement if c["commission_tier"] == "MEDIUM"]
        )
        low_tier = len([c for c in company_engagement if c["commission_tier"] == "LOW"])

        total_estimated_commission = sum(
            c["estimated_commission"] for c in company_engagement
        )

        content.extend(
            [
                "=" * 80,
                "COMMISSION TIER DISTRIBUTION",
                "=" * 80,
                f"High Tier Companies: {high_tier}",
                f"Medium Tier Companies: {medium_tier}",
                f"Low Tier Companies: {low_tier}",
                "",
                f"Total Estimated Commission Potential: ${total_estimated_commission:.2f}",
                f"Average Commission per Company: ${total_estimated_commission/len(company_engagement):.2f}",
                "",
                "=" * 80,
                "RECOMMENDATIONS FOR MAXIMIZING COMMISSIONS",
                "=" * 80,
                "1. IMMEDIATE FOCUS: High-tier companies",
                "   - These companies already show strong engagement",
                "   - Focus on maintaining and growing these relationships",
                "   - Implement regular check-ins and value-add activities",
                "",
                "2. GROWTH OPPORTUNITIES: Medium-tier companies",
                "   - These companies have potential for increased engagement",
                "   - Identify specific needs and pain points",
                "   - Develop targeted outreach strategies",
                "",
                "3. DEVELOPMENT PROJECTS: Low-tier companies",
                "   - These companies need more attention",
                "   - Investigate why engagement is low",
                "   - Consider if they're worth continued investment",
                "",
                "4. DATA-DRIVEN INSIGHTS:",
                "   - Monitor engagement score changes over time",
                "   - Track which activities drive higher engagement",
                "   - Adjust commission rates based on actual performance",
                "",
                "=" * 80,
                "END OF COMMISSION OPPORTUNITIES ANALYSIS",
                "=" * 80,
            ]
        )

        # Write file
        file_path = os.path.join(self.output_dir, "commission_opportunities.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

        return file_path
