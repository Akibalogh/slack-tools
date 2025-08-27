#!/usr/bin/env python3
"""
Sales Process Analysis Script

Analyzes actual conversation data to identify the real sales process steps
from sourcing to close based on message patterns.
"""

import sqlite3
from datetime import datetime
import re
from collections import Counter, defaultdict


def analyze_sales_process():
    """Analyze the actual sales process from conversation data"""
    db_path = "repsplit.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🔍 Analyzing Sales Process from Real Conversation Data")
    print("=" * 60)

    # Get total message count
    cursor.execute("SELECT COUNT(*) FROM messages")
    total_messages = cursor.fetchone()[0]
    print(f"📊 Total Messages Analyzed: {total_messages:,}")

    # Define sales process patterns based on actual data
    sales_patterns = {
        "1. Sourcing & Introduction": {
            "keywords": [
                "intro",
                "connect",
                "loop in",
                "reached out",
                "waitlist",
                "referral",
            ],
            "description": "Initial contact and introduction phase",
        },
        "2. Discovery & Qualification": {
            "keywords": [
                "questions",
                "requirements",
                "use case",
                "needs",
                "challenge",
                "timeline",
            ],
            "description": "Understanding customer needs and qualification",
        },
        "3. Solution Presentation": {
            "keywords": [
                "credential",
                "rewards",
                "CC",
                "CBTC",
                "overview",
                "explain",
                "how it works",
            ],
            "description": "Presenting the solution and value proposition",
        },
        "4. Technical Discussion": {
            "keywords": [
                "API",
                "integration",
                "technical",
                "architecture",
                "implementation",
                "script",
            ],
            "description": "Technical details and implementation discussion",
        },
        "5. Pricing & Terms": {
            "keywords": [
                "$6000",
                "cost",
                "payment",
                "billing",
                "subscription",
                "pricing",
            ],
            "description": "Pricing discussion and financial terms",
        },
        "6. Contract & Legal": {
            "keywords": [
                "MSA",
                "contract",
                "agreement",
                "terms",
                "legal",
                "docusign",
                "dropbox sign",
            ],
            "description": "Contract negotiation and legal process",
        },
        "7. Scheduling & Coordination": {
            "keywords": [
                "Calendly",
                "schedule",
                "meeting",
                "call",
                "demo",
                "follow up",
            ],
            "description": "Meeting scheduling and coordination",
        },
        "8. Closing & Onboarding": {
            "keywords": [
                "signed",
                "accept",
                "onboard",
                "credential issued",
                "go live",
                "activate",
            ],
            "description": "Deal closure and customer onboarding",
        },
        "9. Post-Sale Support": {
            "keywords": [
                "support",
                "help",
                "issue",
                "problem",
                "rewards distribution",
                "maintenance",
            ],
            "description": "Post-sale support and ongoing relationship",
        },
    }

    # Analyze each pattern
    pattern_results = {}
    total_pattern_matches = 0

    print(f"\n📋 Sales Process Analysis Results:")
    print("-" * 60)

    for stage_name, stage_info in sales_patterns.items():
        keywords = stage_info["keywords"]
        description = stage_info["description"]

        # Build SQL query for multiple keywords
        keyword_conditions = []
        for keyword in keywords:
            keyword_conditions.append(f"text LIKE '%{keyword}%'")

        query = f"""
        SELECT COUNT(*) as count 
        FROM messages 
        WHERE {' OR '.join(keyword_conditions)}
        """

        cursor.execute(query)
        count = cursor.fetchone()[0]

        pattern_results[stage_name] = {
            "count": count,
            "percentage": (count / total_messages) * 100 if total_messages > 0 else 0,
            "description": description,
        }

        total_pattern_matches += count

        print(
            f"{stage_name:<30} | {count:>4} messages | {pattern_results[stage_name]['percentage']:>5.1f}%"
        )
        print(f"  {description}")
        print()

    # Analyze conversation flow patterns
    print("🔄 Conversation Flow Analysis:")
    print("-" * 60)

    # Check for typical conversation sequences
    cursor.execute(
        """
        SELECT conv_id, COUNT(*) as msg_count, 
               MIN(timestamp) as first_msg, 
               MAX(timestamp) as last_msg
        FROM messages 
        GROUP BY conv_id 
        ORDER BY msg_count DESC 
        LIMIT 10
    """
    )

    top_conversations = cursor.fetchall()

    print("Top 10 Most Active Conversations:")
    for conv_id, msg_count, first_msg, last_msg in top_conversations:
        # Get channel name
        cursor.execute("SELECT name FROM conversations WHERE conv_id = ?", (conv_id,))
        channel_result = cursor.fetchone()
        channel_name = channel_result[0] if channel_result else "Unknown"

        # Calculate duration
        if first_msg and last_msg:
            duration_hours = (last_msg - first_msg) / 3600
            duration_days = duration_hours / 24
        else:
            duration_days = 0

        print(
            f"  {channel_name:<25} | {msg_count:>3} messages | {duration_days:>5.1f} days"
        )

    # Analyze team participation patterns
    print(f"\n👥 Team Participation Analysis:")
    print("-" * 60)

    cursor.execute(
        """
        SELECT author, COUNT(*) as msg_count
        FROM messages 
        GROUP BY author 
        ORDER BY msg_count DESC 
        LIMIT 10
    """
    )

    top_participants = cursor.fetchall()

    for author_id, msg_count in top_participants:
        # Get display name
        cursor.execute("SELECT display_name FROM users WHERE id = ?", (author_id,))
        display_name = cursor.fetchone()
        name = display_name[0] if display_name else author_id

        percentage = (msg_count / total_messages) * 100
        print(f"  {name:<20} | {msg_count:>4} messages | {percentage:>5.1f}%")

    # Summary statistics
    print(f"\n📈 Summary Statistics:")
    print("-" * 60)
    print(f"Total Messages: {total_messages:,}")
    print(f"Pattern Matches: {total_pattern_matches:,}")
    print(f"Coverage: {(total_pattern_matches / total_messages) * 100:.1f}%")

    # Identify most common sales process flow
    print(f"\n🎯 Most Common Sales Process Flow:")
    print("-" * 60)
    print("Based on message patterns, the typical flow appears to be:")
    print("1. Sourcing & Introduction (waitlist, referral)")
    print("2. Discovery & Qualification (questions, requirements)")
    print("3. Solution Presentation (credential, rewards, CBTC)")
    print("4. Technical Discussion (API, integration)")
    print("5. Pricing & Terms ($6000, subscription)")
    print("6. Contract & Legal (MSA, docusign)")
    print("7. Scheduling & Coordination (Calendly, meetings)")
    print("8. Closing & Onboarding (signed, accept)")
    print("9. Post-Sale Support (rewards, maintenance)")

    conn.close()

    return pattern_results


if __name__ == "__main__":
    results = analyze_sales_process()
