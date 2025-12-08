#!/usr/bin/env python3
"""
Retry script for adding missing Telegram members after rate limit cooldown

This script automatically calculates the cooldown period from rate limit errors
and retries the member addition process.

Usage:
    # Retry immediately (for manual use)
    python3 scripts/telegram_add_missing_members_retry.py

    # Retry after specific wait time (in seconds)
    python3 scripts/telegram_add_missing_members_retry.py --wait 2600

    # Retry after calculated wait time from latest log
    python3 scripts/telegram_add_missing_members_retry.py --auto-wait

    # Run in background with auto-wait
    nohup python3 scripts/telegram_add_missing_members_retry.py --auto-wait > /tmp/telegram_retry_$(date +%Y%m%d_%H%M%S).log 2>&1 &
"""

import argparse
import glob
import os
import re
import subprocess
import sys
import time
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()


def find_latest_log():
    """Find the most recent telegram_add_members log file"""
    log_pattern = "/tmp/telegram_add_members_*.log"
    logs = glob.glob(log_pattern)
    if not logs:
        return None
    return max(logs, key=os.path.getmtime)


def extract_rate_limit_seconds(log_file):
    """Extract the maximum rate limit wait time from log file"""
    if not os.path.exists(log_file):
        return None

    max_seconds = 0
    pattern = r"rate_limited_(\d+)s"

    try:
        with open(log_file, "r") as f:
            for line in f:
                matches = re.findall(pattern, line)
                for match in matches:
                    seconds = int(match)
                    if seconds > max_seconds:
                        max_seconds = seconds
    except Exception as e:
        print(f"⚠️  Error reading log file: {e}")
        return None

    return max_seconds if max_seconds > 0 else None


def wait_with_progress(seconds, log_file=None):
    """Wait for specified seconds with progress updates"""
    log_fd = None
    if log_file:
        log_fd = open(log_file, "a")

    def log_print(msg):
        print(msg)
        if log_fd:
            log_fd.write(msg + "\n")
            log_fd.flush()  # Ensure it's written immediately

    log_print(
        f"\n⏳ Waiting {seconds} seconds ({seconds // 60} minutes) for rate limit cooldown..."
    )
    log_print("=" * 80)

    start_time = time.time()
    last_update = 0

    while True:
        elapsed = int(time.time() - start_time)
        remaining = seconds - elapsed

        if remaining <= 0:
            break

        # Update every 5 minutes for long waits, every minute for shorter
        if seconds > 600:  # > 10 minutes
            update_interval = 300  # 5 minutes
        else:
            update_interval = 60  # 1 minute

        # Only log if enough time has passed
        if elapsed - last_update >= update_interval:
            minutes_remaining = remaining // 60
            log_print(
                f"  ⏱️  {minutes_remaining} minutes remaining... ({datetime.now().strftime('%H:%M:%S')})"
            )
            last_update = elapsed

        time.sleep(60)  # Check every minute instead of every second

    if log_fd:
        log_fd.close()

    print("\n✅ Cooldown complete! Starting retry...")
    print("=" * 80 + "\n")


def run_member_addition(log_file=None):
    """Run the telegram_add_missing_members script"""
    script_path = os.path.join(
        os.path.dirname(__file__), "telegram_add_missing_members.py"
    )
    cmd = [sys.executable, "-u", script_path, "--yes"]  # -u for unbuffered output

    if log_file:
        log_fd = open(log_file, "a")
        log_fd.write(f"🔄 Running: {' '.join(cmd)}\n")
        log_fd.flush()
        # Redirect stdout/stderr to log file
        result = subprocess.run(cmd, stdout=log_fd, stderr=subprocess.STDOUT)
        log_fd.close()
    else:
        print(f"🔄 Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description="Retry Telegram member addition after rate limit cooldown"
    )
    parser.add_argument(
        "--wait",
        type=int,
        help="Wait time in seconds before retrying",
    )
    parser.add_argument(
        "--auto-wait",
        action="store_true",
        help="Automatically calculate wait time from latest log file",
    )
    parser.add_argument(
        "--log",
        type=str,
        help="Log file path (default: auto-generated in /tmp/)",
    )
    args = parser.parse_args()

    # Set up log file
    log_file = args.log
    if not log_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"/tmp/telegram_retry_{timestamp}.log"

    # Redirect stdout/stderr to log file for background execution
    log_fd = open(log_file, "a")
    sys.stdout = log_fd
    sys.stderr = log_fd

    print("=" * 80)
    print("🔄 TELEGRAM MEMBER ADDITION - RETRY SCRIPT")
    print(f"📄 Log file: {log_file}")
    print("=" * 80)

    # Determine wait time
    wait_seconds = None

    if args.wait:
        wait_seconds = args.wait
        print(
            f"⏱️  Using specified wait time: {wait_seconds} seconds ({wait_seconds // 60} minutes)"
        )
    elif args.auto_wait:
        latest_log = find_latest_log()
        if latest_log:
            print(f"📄 Found latest log: {latest_log}")
            wait_seconds = extract_rate_limit_seconds(latest_log)
            if wait_seconds:
                # Add a small buffer (5 minutes) to ensure cooldown is complete
                wait_seconds += 300
                print(
                    f"⏱️  Calculated wait time: {wait_seconds} seconds ({wait_seconds // 60} minutes)"
                )
            else:
                print(
                    "⚠️  Could not extract rate limit time from log. Using default 45 minutes."
                )
                wait_seconds = 45 * 60  # 45 minutes default
        else:
            print("⚠️  No log file found. Using default 45 minutes.")
            wait_seconds = 45 * 60  # 45 minutes default
    else:
        # Default: wait 45 minutes
        wait_seconds = 45 * 60
        print(
            f"⏱️  Using default wait time: {wait_seconds} seconds ({wait_seconds // 60} minutes)"
        )

    # Wait for cooldown
    if wait_seconds > 0:
        wait_with_progress(wait_seconds, log_file)
    else:
        print("▶️  No wait time specified, running immediately...")

    # Run the script
    print("\n" + "=" * 80)
    print("🚀 Starting member addition retry...")
    print("=" * 80 + "\n")
    sys.stdout.flush()  # Ensure output is written

    exit_code = run_member_addition(log_file)

    print("\n" + "=" * 80)
    if exit_code == 0:
        print("✅ Retry completed successfully!")
    else:
        print(f"⚠️  Retry completed with exit code: {exit_code}")
    print("=" * 80)
    sys.stdout.flush()

    log_fd.close()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
