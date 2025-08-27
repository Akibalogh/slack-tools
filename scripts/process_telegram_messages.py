#!/usr/bin/env python3
"""
Process Telegram Messages for Stage Detection

This script processes Telegram messages for companies that currently have no stage data
and adds them to the main messages table so they can be analyzed for stages.
"""

import sys
from pathlib import Path
from telegram_parser import TelegramParser


def main():
    """Process Telegram messages for companies with no stage data"""

    # Companies that currently have no stage data (only Telegram conversations)
    companies_to_process = ["allnodes", "b2c2", "falconx", "nodemonsters", "xbto"]

    print("Processing Telegram messages for companies with no stage data...")
    print("=" * 60)

    # Initialize Telegram parser
    telegram_export_path = "data/telegram/DataExport_2025-08-19"
    db_path = "data/slack/repsplit.db"

    if not Path(telegram_export_path).exists():
        print(f"❌ Telegram export not found at {telegram_export_path}")
        return

    if not Path(db_path).exists():
        print(f"❌ Database not found at {db_path}")
        return

    parser = TelegramParser(telegram_export_path, db_path)

    # Process each company
    success_count = 0
    for company in companies_to_process:
        print(f"\n📱 Processing {company}...")

        try:
            success = parser.parse_company_chat(company)
            if success:
                print(f"✅ Successfully processed {company}")
                success_count += 1
            else:
                print(f"❌ Failed to process {company}")
        except Exception as e:
            print(f"❌ Error processing {company}: {e}")

    print(
        f"\n🎯 Summary: {success_count}/{len(companies_to_process)} companies processed successfully"
    )

    if success_count > 0:
        print("\n📝 Next steps:")
        print(
            "1. Run populate_stage_detections.py to detect stages in Telegram messages"
        )
        print("2. Run repsplit.py to regenerate commission analysis with stage data")
    else:
        print("\n❌ No companies were processed. Check the logs above for errors.")


if __name__ == "__main__":
    main()
