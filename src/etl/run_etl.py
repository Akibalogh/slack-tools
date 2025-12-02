#!/usr/bin/env python3
"""
Standalone ETL Runner

Runs only the ETL data ingestion process without commission processing.
This allows for modular execution of the ETL system.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.etl.etl_data_ingestion import DataETL


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("logs/etl_standalone.log"),
            logging.StreamHandler(),
        ],
    )


def check_output_file(output_file: str) -> bool:
    """Check if the ETL output file exists and is readable"""
    print(f"\n🔍 Checking ETL output: {output_file}")

    try:
        if not os.path.exists(output_file):
            print(f"❌ Output file not found: {output_file}")
            return False

        # Check if file is readable and has content
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            if len(content.strip()) == 0:
                print("❌ Output file is empty")
                return False

        print("✅ ETL output file is valid and readable")
        return True

    except Exception as e:
        print(f"❌ Error reading output file: {e}")
        return False


def main():
    """Main ETL runner function"""
    parser = argparse.ArgumentParser(
        description="Run ETL data ingestion process",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/etl/run_etl.py                    # Run with default settings
  python src/etl/run_etl.py --workers 8       # Use 8 parallel workers
  python src/etl/run_etl.py --batch-size 200  # Process 200 items per batch
  python src/etl/run_etl.py --output custom.json  # Custom output file
  python src/etl/run_etl.py --validate-only    # Only validate existing output
  python src/etl/run_etl.py --verbose          # Verbose logging
        """,
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of parallel workers (default: auto-detect based on CPU cores)",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for processing (default: 100)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,  # Will be auto-generated with timestamp if not provided
        help="Output file path (default: auto-generated with timestamp)",
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate existing output file, do not run ETL",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    parser.add_argument(
        "--force", action="store_true", help="Force overwrite existing output file"
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick test mode: process only first 100 Telegram chats for faster testing",
    )

    parser.add_argument(
        "--no-multiprocessing",
        action="store_true",
        help="Disable multiprocessing and use threading instead",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Initialize ETL to get auto-generated filename if not specified
    etl = DataETL(
        max_workers=args.workers,
        batch_size=args.batch_size,
        quick_mode=args.quick,
        use_multiprocessing=not args.no_multiprocessing,
    )

    # Use auto-generated filename if not specified
    if not args.output:
        args.output = etl.output_file

    print("🚀 ETL Data Ingestion Runner")
    print("=" * 50)
    print(f"Workers: {args.workers}")
    print(f"Batch Size: {args.batch_size}")
    print(f"Output: {args.output}")
    print(f"Verbose: {args.verbose}")
    print("=" * 50)

    # Output file will be overwritten automatically if it exists

    # Validate-only mode
    if args.validate_only:
        success = check_output_file(args.output)
        return 0 if success else 1

    # Run ETL process
    try:
        print("\n🔄 Starting ETL process...")

        # Initialize ETL system
        etl = DataETL(
            max_workers=args.workers,
            batch_size=args.batch_size,
            quick_mode=args.quick,
            use_multiprocessing=not args.no_multiprocessing,
        )

        # Set custom output file
        etl.output_file = args.output

        # Run ETL
        etl.run_etl()

        print(f"\n✅ ETL completed successfully!")
        print(f"📁 Output written to: {args.output}")

        # Check output file
        if check_output_file(args.output):
            print("🎉 ETL output is ready for NotebookLM analysis!")
            return 0
        else:
            print("⚠️  ETL completed but output file check failed")
            return 1

    except KeyboardInterrupt:
        print("\n❌ ETL interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"ETL failed: {e}")
        print(f"\n❌ ETL failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
