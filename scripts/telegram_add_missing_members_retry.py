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
    # nohup python3 scripts/telegram_add_missing_members_retry.py --auto-wait \
    #   > /tmp/telegram_retry_$(date +%Y%m%d_%H%M%S).log 2>&1 &
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


def check_if_done(log_file):
    """Check if there are still rate-limited operations remaining"""
    if not os.path.exists(log_file):
        return False, 0

    try:
        with open(log_file, "r") as f:
            content = f.read()
            # Look for rate limit errors in the final statistics
            if "📊 FINAL STATISTICS" in content:
                # Extract error count from final statistics
                error_pattern = r"⚠️\s+Errors:\s+(\d+)"
                match = re.search(error_pattern, content)
                if match:
                    error_count = int(match.group(1))
                    rate_limit_pattern = r"Rate limited:\s+(\d+)"
                    rate_match = re.search(rate_limit_pattern, content)
                    if rate_match:
                        rate_limit_count = int(rate_match.group(1))
                        return rate_limit_count == 0, rate_limit_count
                    # If no rate limit count but error count is 0, we're done
                    return error_count == 0, error_count
                # Check if success rate is 100% or very high
                success_rate_pattern = r"Success rate:\s+(\d+(?:\.\d+)?)%"
                success_match = re.search(success_rate_pattern, content)
                if success_match:
                    rate = float(success_match.group(1))
                    # If success rate is very high (>95%), consider it done
                    if rate > 95.0:
                        return True, 0
    except Exception as e:
        print(f"⚠️  Error checking completion status: {e}")
        return False, 999  # Assume not done if we can't check

    return False, 999


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

    minutes = seconds // 60
    msg = (
        f"\n⏳ Waiting {seconds} seconds ({minutes} minutes) "
        "for rate limit cooldown..."
    )
    log_print(msg)
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
            time_str = datetime.now().strftime("%H:%M:%S")
            log_print(f"  ⏱️  {minutes_remaining} minutes remaining... ({time_str})")
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
    parser.add_argument(
        "--until-done",
        action="store_true",
        help="Keep retrying until all operations complete (no rate limits remaining)",
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
        minutes = wait_seconds // 60
        msg = (
            f"⏱️  Using specified wait time: {wait_seconds} seconds "
            f"({minutes} minutes)"
        )
        print(msg)
    elif args.auto_wait:
        latest_log = find_latest_log()
        if latest_log:
            print(f"📄 Found latest log: {latest_log}")
            wait_seconds = extract_rate_limit_seconds(latest_log)
            if wait_seconds:
                # Add a small buffer (5 minutes) to ensure cooldown is complete
                wait_seconds += 300
                minutes = wait_seconds // 60
                msg = (
                    f"⏱️  Calculated wait time: {wait_seconds} seconds "
                    f"({minutes} minutes)"
                )
                print(msg)
            else:
                msg = (
                    "Could not extract rate limit time from log. "
                    "Using default 45 min."
                )
                print(f"⚠️  {msg}")
                wait_seconds = 45 * 60  # 45 minutes default
        else:
            print("⚠️  No log file found. Using default 45 minutes.")
            wait_seconds = 45 * 60  # 45 minutes default
    else:
        # Default: wait 45 minutes
        wait_seconds = 45 * 60
        minutes = wait_seconds // 60
        msg = (
            f"⏱️  Using default wait time: {wait_seconds} seconds "
            f"({minutes} minutes)"
        )
        print(msg)

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

    iteration = 1
    max_iterations = 100  # Safety limit to prevent infinite loops

    while iteration <= max_iterations:
        print(f"\n{'=' * 80}")
        print(f"🔄 RETRY ITERATION #{iteration}")
        print(f"{'=' * 80}\n")
        sys.stdout.flush()

        exit_code = run_member_addition(log_file)

        print("\n" + "=" * 80)
        if exit_code == 0:
            print("✅ Retry iteration completed successfully!")
        else:
            print(f"⚠️  Retry iteration completed with exit code: {exit_code}")
        print("=" * 80)
        sys.stdout.flush()

        # Check if we should continue
        if args.until_done:
            # Find the latest member addition log to check completion
            latest_member_log = find_latest_log()
            if latest_member_log:
                is_done, remaining_errors = check_if_done(latest_member_log)
                if is_done:
                    print("\n" + "=" * 80)
                    print("✅ ALL OPERATIONS COMPLETE!")
                    print("No more rate-limited operations remaining.")
                    print("=" * 80)
                    sys.stdout.flush()
                    log_fd.close()
                    return 0
                else:
                    print(
                        f"\n⚠️  Still {remaining_errors} rate-limited operations remaining."
                    )
                    print("Continuing to next retry iteration...\n")
                    sys.stdout.flush()
                    # Calculate wait time for next iteration
                    wait_seconds = extract_rate_limit_seconds(latest_member_log)
                    if wait_seconds:
                        wait_seconds += 300  # Add 5 minute buffer
                    else:
                        wait_seconds = 45 * 60  # Default 45 minutes

                    if wait_seconds > 0:
                        wait_with_progress(wait_seconds, log_file)
                    iteration += 1
                    continue
            else:
                print("⚠️  Could not find latest log file. Stopping retries.")
                break
        else:
            # Not in loop mode, just exit
            break

    if iteration > max_iterations:
        print("\n⚠️  Reached maximum iteration limit. Stopping.")

    log_fd.close()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
