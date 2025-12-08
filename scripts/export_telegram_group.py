#!/usr/bin/env python3
"""
Export messages from a Telegram group to a text file

Generic script to export messages from any Telegram group for a specified time period.

Usage:
    # Export last 3 months (default)
    python3 scripts/export_telegram_group.py "Group Name"
    
    # Export last 30 days
    python3 scripts/export_telegram_group.py "Group Name" --days 30
    
    # Export last 2 weeks
    python3 scripts/export_telegram_group.py "Group Name" --weeks 2
    
    # Export last 6 months
    python3 scripts/export_telegram_group.py "Group Name" --months 6
    
    # Export last 1 year
    python3 scripts/export_telegram_group.py "Group Name" --years 1
    
    # Custom output file
    python3 scripts/export_telegram_group.py "Group Name" --days 30 -o output/custom_export.txt
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime, timedelta

import psycopg2
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

load_dotenv()


def calculate_date_threshold(days=None, weeks=None, months=None, years=None):
    """Calculate date threshold based on provided time period"""
    total_days = 0
    
    if days:
        total_days += days
    if weeks:
        total_days += weeks * 7
    if months:
        total_days += months * 30  # Approximate month as 30 days
    if years:
        total_days += years * 365  # Approximate year as 365 days
    
    # Default to 3 months if nothing specified
    if total_days == 0:
        total_days = 90
    
    return datetime.now() - timedelta(days=total_days), total_days


def format_time_period(days):
    """Format time period in human-readable format"""
    if days >= 365:
        years = days // 365
        remainder = days % 365
        if remainder >= 30:
            months = remainder // 30
            return f"{years} year{'s' if years > 1 else ''} {months} month{'s' if months > 1 else ''}"
        return f"{years} year{'s' if years > 1 else ''}"
    elif days >= 30:
        months = days // 30
        remainder = days % 30
        if remainder >= 7:
            weeks = remainder // 7
            return f"{months} month{'s' if months > 1 else ''} {weeks} week{'s' if weeks > 1 else ''}"
        return f"{months} month{'s' if months > 1 else ''}"
    elif days >= 7:
        weeks = days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''}"
    else:
        return f"{days} day{'s' if days > 1 else ''}"


async def export_group_messages(group_name, days=None, weeks=None, months=None, years=None, output_file=None):
    """Export messages from a Telegram group for the specified time period"""
    date_threshold, total_days = calculate_date_threshold(days, weeks, months, years)
    time_period = format_time_period(total_days)
    
    print(f"📤 Exporting messages from '{group_name}'")
    print(f"📅 Time range: Last {time_period} (since {date_threshold.strftime('%Y-%m-%d')})")
    print("=" * 80)

    # Connect to Telegram
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cursor = conn.cursor()
    cursor.execute("SELECT session_string FROM telegram_audit_status WHERE id = 1")
    session_string = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    await client.connect()

    # Find the group
    dialogs = await client.get_dialogs()
    target_dialog = None
    for dialog in dialogs:
        if dialog.title == group_name:
            target_dialog = dialog
            break

    if not target_dialog:
        print(f"❌ Group '{group_name}' not found!")
        print("\nAvailable groups (first 20):")
        for dialog in dialogs[:20]:
            print(f"  - {dialog.title}")
        await client.disconnect()
        return 1

    print(f"✅ Found group: {target_dialog.title}")
    time_period = format_time_period(total_days)
    print(f"📊 Collecting messages since {date_threshold.strftime('%Y-%m-%d')}...\n")

    # Collect messages
    messages = []
    message_count = 0
    async for message in client.iter_messages(target_dialog.entity, offset_date=date_threshold):
        message_count += 1
        if message_count % 50 == 0:
            print(f"  Collected {message_count} messages...", end="\r")

        # Get sender name
        sender_name = "Unknown"
        if message.sender:
            if hasattr(message.sender, "first_name"):
                sender_name = (
                    f"{message.sender.first_name or ''} {message.sender.last_name or ''}".strip()
                    or (
                        f"@{message.sender.username}"
                        if message.sender.username
                        else "Unknown"
                    )
                )
            elif hasattr(message.sender, "title"):
                sender_name = message.sender.title
            elif hasattr(message.sender, "username"):
                sender_name = f"@{message.sender.username}" if message.sender.username else "Unknown"

        # Format message
        msg_date = message.date.strftime("%Y-%m-%d %H:%M:%S")
        msg_text = message.text or "[Media/Sticker/Other]"

        # Handle replies
        reply_info = ""
        if message.is_reply and message.reply_to_msg_id:
            reply_info = " [REPLY]"

        messages.append(
            {
                "date": msg_date,
                "sender": sender_name,
                "text": msg_text,
                "id": message.id,
                "is_reply": message.is_reply,
            }
        )

    print(f"\n✅ Collected {len(messages)} messages")

    # Sort by date (oldest first)
    messages.sort(key=lambda m: m["date"])

    # Generate output filename if not provided
    if not output_file:
        safe_name = group_name.replace(" ", "_").replace("/", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"output/telegram_export_{safe_name}_{timestamp}.txt"

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Write to file
    print(f"💾 Writing to {output_file}...")
    time_period_str = format_time_period(total_days)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"Telegram Group Export: {group_name}\n")
        f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Time Range: Last {time_period_str} (since {date_threshold.strftime('%Y-%m-%d')})\n")
        f.write(f"Total Messages: {len(messages)}\n")
        f.write("=" * 80 + "\n\n")

        for msg in messages:
            reply_marker = " ↳ " if msg["is_reply"] else ""
            f.write(f"{msg['date']} | {msg['sender']}{reply_marker}\n")
            f.write(f"{msg['text']}\n")
            f.write("-" * 80 + "\n")

    await client.disconnect()

    print(f"\n{'='*80}")
    print(f"✅ Export complete!")
    print(f"📄 File: {output_file}")
    print(f"📊 Messages: {len(messages)}")
    print(f"{'='*80}")
    return 0


async def main():
    parser = argparse.ArgumentParser(
        description="Export messages from a Telegram group for a specified time period",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export last 3 months (default)
  %(prog)s "BitSafe Leadership Team"
  
  # Export last 30 days
  %(prog)s "Group Name" --days 30
  
  # Export last 2 weeks
  %(prog)s "Group Name" --weeks 2
  
  # Export last 6 months
  %(prog)s "Group Name" --months 6
  
  # Custom output file
  %(prog)s "Group Name" --days 30 -o output/custom_export.txt
        """,
    )
    parser.add_argument("group_name", help="Name of the Telegram group to export")
    parser.add_argument("--days", type=int, help="Number of days to export")
    parser.add_argument("--weeks", type=int, help="Number of weeks to export")
    parser.add_argument(
        "--months",
        type=int,
        help="Number of months to export (default: 3 if no other period specified)",
    )
    parser.add_argument("--years", type=int, help="Number of years to export")
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path (default: auto-generated in output/ directory)",
    )
    args = parser.parse_args()

    return await export_group_messages(
        args.group_name,
        days=args.days,
        weeks=args.weeks,
        months=args.months,
        years=args.years,
        output_file=args.output,
    )


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

