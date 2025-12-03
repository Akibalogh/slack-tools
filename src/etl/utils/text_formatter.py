#!/usr/bin/env python3
"""
ETL Text Output Formatter

Converts ETL JSON output to human-readable text format suitable for NotebookLM.
"""

import json
from datetime import datetime
from typing import Any, Dict, List


class ETLTextFormatter:
    """Formats ETL output as human-readable text for NotebookLM"""

    def __init__(self):
        self.output_lines = []

    def format_etl_output(self, data: Dict[str, Any]) -> str:
        """Convert ETL JSON data to formatted text"""
        self.output_lines = []

        try:
            # Header
            self._add_header(data)

            # Metadata section
            self._add_metadata(data.get("metadata", {}))

            # Statistics section
            self._add_statistics(data.get("statistics", {}))

            # Companies section
            self._add_companies(data.get("companies", {}))

            # Add comprehensive summary for NotebookLM
            self._add_notebooklm_summary(data)

            # Debug: Check for non-string items in output_lines
            for i, line in enumerate(self.output_lines):
                if not isinstance(line, str):
                    print(f"ERROR: Non-string item at index {i}: {type(line)} - {line}")
                    self.output_lines[i] = str(line)

            return "\n".join(self.output_lines)
        except Exception as e:
            print(f"ERROR in format_etl_output: {e}")
            print(f"output_lines type: {type(self.output_lines)}")
            print(f"output_lines length: {len(self.output_lines)}")
            if self.output_lines:
                print(f"First item type: {type(self.output_lines[0])}")
                print(f"First item: {self.output_lines[0]}")
            raise

    def _add_header(self, data: Dict[str, Any]):
        """Add document header with NotebookLM analysis requests"""
        metadata = data.get("metadata", {})
        generated_at = metadata.get("generated_at", "Unknown")

        self.output_lines.extend(
            [
                "=" * 80,
                "COMMISSION CALCULATOR - ETL DATA INGESTION REPORT",
                "=" * 80,
                f"Generated: {generated_at}",
                f"ETL Version: {metadata.get('etl_version', 'Unknown')}",
                f"Data Sources: {', '.join(str(s) for s in metadata.get('data_sources', []))}",
                f"Total Companies: {metadata.get('total_companies', 0)}",
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
                "3. COMMUNICATION PATTERNS:",
                "   - What are the common communication themes across companies?",
                "   - Which companies have the most diverse communication channels?",
                "   - What patterns indicate strong customer relationships?",
                "",
                "4. COMMISSION CALCULATION INSIGHTS:",
                "   - Which companies would generate the highest commissions based on activity?",
                "   - What companies show potential for increased commission opportunities?",
                "   - How should commission rates be adjusted based on engagement levels?",
                "",
                "5. DATA COVERAGE GAPS:",
                "   - Which companies have limited data coverage and need more attention?",
                "   - What data sources are missing for key companies?",
                "   - How can we improve data collection for better insights?",
                "",
                "=" * 80,
                "DATA SUMMARY",
                "=" * 80,
            ]
        )

    def _add_metadata(self, metadata: Dict[str, Any]):
        """Add metadata section"""
        self.output_lines.extend(
            [
                "METADATA",
                "-" * 40,
            ]
        )

        # Performance stats
        perf_stats = metadata.get("performance_stats", {})
        if perf_stats:
            self.output_lines.extend(
                [
                    f"Total Duration: {perf_stats.get('total_duration_seconds', 0):.2f} seconds",
                    f"Total Errors: {perf_stats.get('total_errors', 0)}",
                    f"Max Workers: {perf_stats.get('max_workers', 0)}",
                    f"Batch Size: {perf_stats.get('batch_size', 0)}",
                    "",
                ]
            )

            # Processing times
            processing_times = perf_stats.get("processing_times", {})
            if processing_times:
                self.output_lines.append("Processing Times:")
                for operation, duration in processing_times.items():
                    self.output_lines.append(f"  {operation}: {duration:.2f}s")
                self.output_lines.append("")

    def _add_statistics(self, stats: Dict[str, Any]):
        """Add statistics section"""
        self.output_lines.extend(
            [
                "DATA COVERAGE STATISTICS",
                "-" * 40,
                f"Total Companies: {stats.get('total_companies', 0)}",
                f"Companies with Slack: {stats.get('companies_with_slack', 0)}",
                f"Companies with Telegram: {stats.get('companies_with_telegram', 0)}",
                f"Companies with Calendar: {stats.get('companies_with_calendar', 0)}",
                f"Companies with HubSpot: {stats.get('companies_with_hubspot', 0)}",
                "",
                f"Total Slack Channels: {stats.get('total_slack_channels', 0)}",
                f"Total Telegram Chats: {stats.get('total_telegram_chats', 0)}",
                f"Total Calendar Meetings: {stats.get('total_calendar_meetings', 0)}",
                f"Total HubSpot Deals: {stats.get('total_hubspot_deals', 0)}",
                "",
            ]
        )

    def _add_companies(self, companies: Dict[str, Any]):
        """Add companies section"""
        self.output_lines.extend(
            [
                "COMPANY DATA",
                "-" * 40,
            ]
        )

        # Handle both dict and list formats
        if isinstance(companies, dict):
            company_items = companies.items()
        elif isinstance(companies, list):
            # Convert list to dict format
            company_items = [
                (f"company_{i}", company) for i, company in enumerate(companies)
            ]
        else:
            self.output_lines.append(
                f"ERROR: Unexpected companies data type: {type(companies)}"
            )
            return

        for company_name, company_data in company_items:
            self._add_company_section(company_name, company_data)
            self.output_lines.append("")

    def _add_company_section(self, company_name: str, company_data: Dict[str, Any]):
        """Add individual company section with comprehensive data for NotebookLM"""
        self.output_lines.extend(
            [
                f"COMPANY: {company_name.upper()}",
                "=" * 50,
            ]
        )

        # Company info
        company_info = company_data.get("company_info", {})
        if company_info:
            self.output_lines.extend(
                [
                    "COMPANY INFORMATION:",
                    f"  Base Company: {company_info.get('base_company', 'N/A')}",
                    f"  Variant Type: {company_info.get('variant_type', 'N/A')}",
                    f"  Slack Groups: {company_info.get('slack_groups', 'N/A')}",
                    f"  Telegram Groups: {company_info.get('telegram_groups', 'N/A')}",
                    f"  Calendar Domain: {company_info.get('calendar_domain', 'N/A')}",
                    f"  Full Node Address: {company_info.get('full_node_address', 'N/A')}",
                    "",
                ]
            )

        # Slack data - EXPANDED
        slack_channels = company_data.get("slack_channels", [])
        if slack_channels:
            self.output_lines.append("SLACK CHANNELS:")
            for channel in slack_channels:
                channel_name = channel.get("name", "Unknown")
                channel_data = channel.get("data", {})
                message_count = len(channel_data.get("messages", []))

                self.output_lines.append(
                    f"  - {channel_name} ({message_count} messages)"
                )

                # Show message summary for NotebookLM analysis (compact version)
                messages = channel_data.get("messages", [])
                if messages:
                    # Get unique senders and key message samples
                    unique_senders = set(
                        msg.get("author", msg.get("user", "Unknown"))
                        for msg in messages
                    )
                    recent_messages = messages[-5:] if len(messages) > 5 else messages

                    self.output_lines.extend(
                        [
                            "    MESSAGE SUMMARY:",
                            f"    - Total messages: {len(messages)}",
                            f"    - Unique senders: {len(unique_senders)}",
                            f"    - Senders: {', '.join(sorted(unique_senders))}",
                            f"    - Date range: {messages[0].get('timestamp', messages[0].get('ts', 'Unknown'))} to {messages[-1].get('timestamp', messages[-1].get('ts', 'Unknown'))}",
                            "",
                            "    RECENT MESSAGES (last 5):",
                        ]
                    )

                    for i, msg in enumerate(recent_messages, 1):
                        sender = msg.get("display_name", msg.get("author", "Unknown"))
                        text = msg.get("text", "")[:100] + (
                            "..." if len(msg.get("text", "")) > 100 else ""
                        )
                        timestamp = msg.get("timestamp", msg.get("ts", ""))
                        self.output_lines.append(
                            f"      [{i}] [{timestamp}] {sender}: {text}"
                        )
        else:
            self.output_lines.append("SLACK: No data")

        self.output_lines.append("")

        # Telegram data - EXPANDED
        telegram_chats = company_data.get("telegram_chats", [])
        if telegram_chats:
            self.output_lines.append("TELEGRAM CHATS:")
            for chat in telegram_chats:
                chat_name = chat.get("chat_name", "Unknown")
                message_count = chat.get("message_count", 0)
                chat_data = chat.get("data", {})
                participants = chat_data.get("participant_count", 0)

                self.output_lines.append(
                    f"  - {chat_name} ({message_count} messages, {participants} participants)"
                )

                # Show ALL messages for NotebookLM analysis
                messages = chat_data.get("messages", [])
                if messages:
                    self.output_lines.append("    ALL MESSAGES:")
                    for i, msg in enumerate(messages, 1):
                        sender = msg.get("author", msg.get("sender", "Unknown"))
                        text = msg.get("text", "")
                        timestamp = msg.get("timestamp", "")
                        # Don't truncate - show full messages for analysis
                        self.output_lines.append(
                            f"      [{i:3d}] [{timestamp}] {sender}: {text}"
                        )

                    # Add conversation analysis
                    self.output_lines.extend(
                        [
                            "",
                            "    CONVERSATION ANALYSIS:",
                            f"    - Total messages: {len(messages)}",
                            f"    - Unique senders: {len(set(msg.get('sender', 'Unknown') for msg in messages))}",
                            f"    - Date range: {messages[0].get('timestamp', 'Unknown')} to {messages[-1].get('timestamp', 'Unknown')}",
                        ]
                    )
        else:
            self.output_lines.append("TELEGRAM: No data")

        self.output_lines.append("")

        # Calendar data - EXPANDED
        calendar_meetings = company_data.get("calendar_meetings", [])
        if calendar_meetings:
            self.output_lines.append(f"CALENDAR: {len(calendar_meetings)} meetings")
            for i, meeting in enumerate(calendar_meetings, 1):
                title = meeting.get("title", "Unknown")
                start_time = meeting.get("start_time", "Unknown")
                end_time = meeting.get("end_time", "Unknown")
                attendees = meeting.get("attendees", [])
                description = meeting.get("description", "")
                location = meeting.get("location", "")

                self.output_lines.extend(
                    [
                        f"  [{i:2d}] {title}",
                        f"      Time: {start_time} - {end_time}",
                        f"      Location: {location}",
                        f"      Attendees: {', '.join(str(a) for a in attendees) if attendees else 'None'}",
                        f"      Description: {description}",
                        "",
                    ]
                )
        else:
            self.output_lines.append("CALENDAR: No data")

        self.output_lines.append("")

        # HubSpot data - EXPANDED
        hubspot_deals = company_data.get("hubspot_deals", [])
        if hubspot_deals:
            self.output_lines.append(f"HUBSPOT: {len(hubspot_deals)} deals")
            for i, deal in enumerate(hubspot_deals, 1):
                deal_name = deal.get("deal_name", "Unknown")
                deal_stage = deal.get("deal_stage", "Unknown")
                deal_value = deal.get("deal_value", "Unknown")
                deal_owner = deal.get("deal_owner", "Unknown")
                close_date = deal.get("close_date", "Unknown")
                created_date = deal.get("created_date", "Unknown")
                deal_type = deal.get("deal_type", "Unknown")
                description = deal.get("description", "")

                self.output_lines.extend(
                    [
                        f"  [{i:2d}] {deal_name}",
                        f"      Stage: {deal_stage}",
                        f"      Value: ${deal_value}",
                        f"      Owner: {deal_owner}",
                        f"      Close Date: {close_date}",
                        f"      Created: {created_date}",
                        f"      Type: {deal_type}",
                        f"      Description: {description}",
                        "",
                    ]
                )
        else:
            self.output_lines.append("HUBSPOT: No data")

        # Add comprehensive company analysis
        self._add_company_analysis(company_name, company_data)

    def _add_company_analysis(self, company_name: str, company_data: Dict[str, Any]):
        """Add comprehensive analysis for NotebookLM"""
        self.output_lines.extend(
            [
                "COMPANY ANALYSIS FOR NOTEBOOKLM:",
                "-" * 40,
            ]
        )

        # Data source analysis
        slack_channels = company_data.get("slack_channels", [])
        telegram_chats = company_data.get("telegram_chats", [])
        calendar_meetings = company_data.get("calendar_meetings", [])
        hubspot_deals = company_data.get("hubspot_deals", [])

        # Calculate engagement metrics
        total_slack_messages = sum(ch.get("message_count", 0) for ch in slack_channels)
        total_telegram_messages = sum(
            ch.get("message_count", 0) for ch in telegram_chats
        )
        total_meetings = len(calendar_meetings)
        total_deals = len(hubspot_deals)

        # Engagement score calculation
        engagement_score = (
            total_slack_messages * 0.4
            + total_telegram_messages * 0.3
            + total_meetings * 10
            + total_deals * 20
        )

        self.output_lines.extend(
            [
                f"ENGAGEMENT METRICS:",
                f"  - Slack Messages: {total_slack_messages}",
                f"  - Telegram Messages: {total_telegram_messages}",
                f"  - Calendar Meetings: {total_meetings}",
                f"  - HubSpot Deals: {total_deals}",
                f"  - Engagement Score: {engagement_score:.1f}",
                "",
                f"COMMISSION POTENTIAL ANALYSIS:",
                f"  - High Activity: {'Yes' if total_slack_messages > 100 or total_telegram_messages > 50 else 'No'}",
                f"  - Multiple Channels: {'Yes' if len(slack_channels) > 1 or len(telegram_chats) > 1 else 'No'}",
                f"  - Active Deals: {'Yes' if total_deals > 0 else 'No'}",
                f"  - Meeting Activity: {'Yes' if total_meetings > 0 else 'No'}",
                "",
                f"RECOMMENDED ACTIONS:",
            ]
        )

        # Generate specific recommendations
        if engagement_score > 100:
            self.output_lines.append(
                "  - HIGH PRIORITY: This company shows strong engagement"
            )
        elif engagement_score > 50:
            self.output_lines.append(
                "  - MEDIUM PRIORITY: Moderate engagement, consider follow-up"
            )
        else:
            self.output_lines.append(
                "  - LOW PRIORITY: Limited engagement, needs attention"
            )

        if total_slack_messages > 200:
            self.output_lines.append(
                "  - High Slack activity indicates strong relationship"
            )
        if total_telegram_messages > 100:
            self.output_lines.append(
                "  - High Telegram activity shows diverse communication"
            )
        if total_deals > 0:
            self.output_lines.append("  - Active deals present - monitor closely")
        if total_meetings > 5:
            self.output_lines.append(
                "  - Regular meetings indicate ongoing collaboration"
            )

        self.output_lines.extend(
            [
                "",
                f"DATA SOURCES AVAILABLE:",
                f"  Slack: {'Yes' if slack_channels else 'No'} ({len(slack_channels)} channels)",
                f"  Telegram: {'Yes' if telegram_chats else 'No'} ({len(telegram_chats)} chats)",
                f"  Calendar: {'Yes' if calendar_meetings else 'No'} ({len(calendar_meetings)} meetings)",
                f"  HubSpot: {'Yes' if hubspot_deals else 'No'} ({len(hubspot_deals)} deals)",
                "",
            ]
        )

        # Communication patterns
        total_messages = 0
        if slack_channels:
            for channel in slack_channels:
                total_messages += len(channel.get("data", {}).get("messages", []))
        if telegram_chats:
            for chat in telegram_chats:
                total_messages += len(chat.get("data", {}).get("messages", []))

        self.output_lines.extend(
            [
                f"COMMUNICATION PATTERNS:",
                f"  Total messages across all channels: {total_messages}",
                f"  Primary communication channel: {'Slack' if slack_channels else 'Telegram' if telegram_chats else 'None'}",
                f"  Meeting frequency: {len(calendar_meetings)} meetings",
                f"  Deal activity: {len(hubspot_deals)} deals",
                "",
            ]
        )

        # Sales stage indicators
        self.output_lines.append("SALES STAGE INDICATORS:")
        if hubspot_deals:
            stages = [deal.get("deal_stage", "Unknown") for deal in hubspot_deals]
            stage_counts = {}
            for stage in stages:
                stage_counts[stage] = stage_counts.get(stage, 0) + 1

            for stage, count in stage_counts.items():
                self.output_lines.append(f"  {stage}: {count} deals")
        else:
            self.output_lines.append("  No deal stage data available")

        self.output_lines.append("")

        # Key participants
        all_senders = set()
        if slack_channels:
            for channel in slack_channels:
                messages = channel.get("data", {}).get("messages", [])
                for msg in messages:
                    all_senders.add(msg.get("user", "Unknown"))
        if telegram_chats:
            for chat in telegram_chats:
                messages = chat.get("data", {}).get("messages", [])
                for msg in messages:
                    all_senders.add(msg.get("sender", "Unknown"))

        if all_senders:
            self.output_lines.extend(
                [
                    f"KEY PARTICIPANTS:",
                    f"  Total unique participants: {len(all_senders)}",
                    f"  Participants: {', '.join(sorted(str(s) for s in all_senders))}",
                    "",
                ]
            )

    def _add_notebooklm_summary(self, data: Dict[str, Any]):
        """Add comprehensive summary for NotebookLM analysis"""
        companies = data.get("companies", {})
        stats = data.get("statistics", {})

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
                }
            )

        # Sort by engagement score
        company_engagement.sort(key=lambda x: x["engagement_score"], reverse=True)

        self.output_lines.extend(
            [
                "=" * 80,
                "NOTEBOOKLM EXECUTIVE SUMMARY",
                "=" * 80,
                "",
                "TOP 10 HIGHEST ENGAGEMENT COMPANIES:",
                "-" * 50,
            ]
        )

        for i, company in enumerate(company_engagement[:10], 1):
            self.output_lines.extend(
                [
                    f"{i:2d}. {company['name']}",
                    f"    Engagement Score: {company['engagement_score']:.1f}",
                    f"    Slack Messages: {company['slack_messages']}",
                    f"    Telegram Messages: {company['telegram_messages']}",
                    f"    Meetings: {company['meetings']}",
                    f"    Deals: {company['deals']}",
                    f"    Total Channels: {company['channels']}",
                    "",
                ]
            )

        # Data coverage analysis
        high_engagement = len(
            [c for c in company_engagement if c["engagement_score"] > 100]
        )
        medium_engagement = len(
            [c for c in company_engagement if 50 <= c["engagement_score"] <= 100]
        )
        low_engagement = len(
            [c for c in company_engagement if c["engagement_score"] < 50]
        )

        self.output_lines.extend(
            [
                "ENGAGEMENT DISTRIBUTION:",
                f"  High Engagement (>100): {high_engagement} companies",
                f"  Medium Engagement (50-100): {medium_engagement} companies",
                f"  Low Engagement (<50): {low_engagement} companies",
                "",
                "COMMISSION OPPORTUNITY RANKINGS:",
                "-" * 40,
            ]
        )

        # Commission potential analysis
        for i, company in enumerate(company_engagement[:5], 1):
            commission_potential = (
                "HIGH"
                if company["engagement_score"] > 150
                else "MEDIUM"
                if company["engagement_score"] > 75
                else "LOW"
            )
            self.output_lines.append(
                f"{i}. {company['name']} - {commission_potential} POTENTIAL"
            )

        self.output_lines.extend(
            [
                "",
                "DATA COVERAGE GAPS TO ADDRESS:",
                "-" * 40,
                f"Companies with no Slack data: {len([c for c in company_engagement if c['slack_messages'] == 0])}",
                f"Companies with no Telegram data: {len([c for c in company_engagement if c['telegram_messages'] == 0])}",
                f"Companies with no meeting data: {len([c for c in company_engagement if c['meetings'] == 0])}",
                f"Companies with no deal data: {len([c for c in company_engagement if c['deals'] == 0])}",
                "",
                "RECOMMENDED NEXT ACTIONS:",
                "-" * 30,
                "1. Focus on top 10 high-engagement companies for immediate commission opportunities",
                "2. Investigate medium-engagement companies for growth potential",
                "3. Address data coverage gaps for low-engagement companies",
                "4. Implement calendar and HubSpot integrations for complete data picture",
                "5. Set up automated monitoring for engagement score changes",
                "",
                "=" * 80,
                "END OF ETL DATA REPORT",
                "=" * 80,
            ]
        )

        # Conversation themes (basic keyword analysis)
        if slack_channels or telegram_chats:
            self.output_lines.append("CONVERSATION THEMES:")
            # This would be expanded with actual keyword analysis
            self.output_lines.append("  (Theme analysis would be implemented here)")
            self.output_lines.append("")

    def format_company_summary(self, companies: Dict[str, Any]) -> str:
        """Create a summary table of all companies"""
        lines = [
            "COMPANY SUMMARY TABLE",
            "-" * 80,
            f"{'Company':<30} {'Slack':<8} {'Telegram':<10} {'Calendar':<10} {'HubSpot':<10}",
            "-" * 80,
        ]

        for company_name, company_data in companies.items():
            slack = "✓" if company_data.get("slack_channels") else "✗"
            telegram = "✓" if company_data.get("telegram_chats") else "✗"
            calendar = "✓" if company_data.get("calendar_meetings") else "✗"
            hubspot = "✓" if company_data.get("hubspot_deals") else "✗"

            lines.append(
                f"{company_name:<30} {slack:<8} {telegram:<10} {calendar:<10} {hubspot:<10}"
            )

        return "\n".join(lines)


def main():
    """CLI interface for text formatting"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert ETL JSON output to text format"
    )
    parser.add_argument("input", help="Input JSON file")
    parser.add_argument("output", help="Output text file")
    parser.add_argument(
        "--summary-only", action="store_true", help="Generate only summary table"
    )

    args = parser.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)

        formatter = ETLTextFormatter()

        if args.summary_only:
            companies = data.get("companies", {})
            text_output = formatter.format_company_summary(companies)
        else:
            text_output = formatter.format_etl_output(data)

        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text_output)

        print(f"✅ Text output written to {args.output}")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
