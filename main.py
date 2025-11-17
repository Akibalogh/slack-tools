#!/usr/bin/env python3
"""
Main Application Runner

Unified command-line interface for running ETL data ingestion,
commission processing, or both sequentially.
"""

import sys
import os
import argparse
import logging
from pathlib import Path
import subprocess

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/main_runner.log'),
            logging.StreamHandler()
        ]
    )


def check_etl_output(output_file: str) -> bool:
    """Check if ETL output exists and is valid"""
    if not os.path.exists(output_file):
        return False
    
    try:
        # Check if it's a readable text file with content
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if len(content.strip()) == 0:
                return False
            
            # Check if it looks like our ETL output (has our header)
            if "COMMISSION CALCULATOR - ETL DATA INGESTION REPORT" not in content:
                return False
        
        # Check if it's recent (within last 24 hours)
        import datetime
        file_mtime = os.path.getmtime(output_file)
        age_hours = (datetime.datetime.now().timestamp() - file_mtime) / 3600
        if age_hours > 24:
            return False
        
        return True
    except:
        return False


def run_etl(workers: int = None, batch_size: int = 100, output_file: str = None, verbose: bool = False, quick: bool = False, use_multiprocessing: bool = True):
    """Run ETL data ingestion"""
    print("🔄 Running ETL data ingestion...")
    
    cmd = [
        sys.executable, 'src/etl/run_etl.py',
        '--batch-size', str(batch_size)
    ]
    
    # Add workers if specified
    if workers is not None:
        cmd.extend(['--workers', str(workers)])
    
    # Only add output file if specified
    if output_file:
        cmd.extend(['--output', output_file])
    
    if verbose:
        cmd.append('--verbose')
    
    if quick:
        cmd.append('--quick')
    
    if not use_multiprocessing:
        cmd.append('--no-multiprocessing')
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print("✅ ETL completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ETL failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ ETL error: {e}")
        return False


def run_commission_processing(etl_output: str = 'output/notebooklm/etl_output.txt', verbose: bool = False):
    """Run commission processing (placeholder for now)"""
    print("🔄 Running commission processing...")
    
    # Check if ETL output exists
    if not check_etl_output(etl_output):
        print(f"❌ ETL output not found or invalid: {etl_output}")
        print("   Please run ETL first or specify a valid output file")
        return False
    
    # TODO: Implement full commission processing pipeline
    # For now, just show what would be processed from ETL output
    try:
        with open(etl_output, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract basic stats from text output
        lines = content.split('\n')
        companies_count = 0
        slack_count = 0
        telegram_count = 0
        calendar_count = 0
        hubspot_count = 0
        
        for line in lines:
            if "Total Companies:" in line:
                companies_count = int(line.split(':')[1].strip())
            elif "Companies with Slack:" in line:
                slack_count = int(line.split(':')[1].strip())
            elif "Companies with Telegram:" in line:
                telegram_count = int(line.split(':')[1].strip())
            elif "Companies with Calendar:" in line:
                calendar_count = int(line.split(':')[1].strip())
            elif "Companies with HubSpot:" in line:
                hubspot_count = int(line.split(':')[1].strip())
        
        print(f"📊 Processing {companies_count} companies")
        print(f"   • Slack: {slack_count} companies")
        print(f"   • Telegram: {telegram_count} companies")
        print(f"   • Calendar: {calendar_count} companies")
        print(f"   • HubSpot: {hubspot_count} companies")
        
        print("⚠️  Commission processing not yet implemented")
        print("   This is a placeholder for future commission calculation logic")
        
        return True
        
    except Exception as e:
        print(f"❌ Commission processing error: {e}")
        return False


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        description='Unified runner for ETL and commission processing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py etl                          # Run ETL only
  python main.py commission                   # Run commission processing only
  python main.py both                         # Run both ETL and commission processing
  python main.py etl --workers 8              # Run ETL with 8 workers
  python main.py commission --etl-output custom.json  # Use custom ETL output
  python main.py both --verbose               # Run both with verbose logging
        """
    )
    
    parser.add_argument(
        'command',
        choices=['etl', 'commission', 'both'],
        help='Command to run: etl (data ingestion only), commission (processing only), or both'
    )
    
    parser.add_argument(
        '--workers', 
        type=int, 
        default=4,
        help='Number of parallel workers for ETL (default: 4)'
    )
    
    parser.add_argument(
        '--batch-size', 
        type=int, 
        default=100,
        help='Batch size for ETL processing (default: 100)'
    )
    
    parser.add_argument(
        '--etl-output',
        type=str,
        default=None,  # Will be auto-generated with timestamp if not provided
        help='ETL output file path (default: auto-generated with timestamp)'
    )
    
    parser.add_argument(
        '--verbose', '-v', 
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--force-etl', 
        action='store_true',
        help='Force ETL to run even if recent output exists'
    )
    
    parser.add_argument(
        '--quick', 
        action='store_true',
        help='Quick test mode: process only first 100 Telegram chats for faster testing'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    print("🚀 Commission Calculator - Main Runner")
    print("=" * 50)
    print(f"Command: {args.command}")
    print(f"ETL Output: {args.etl_output}")
    print(f"Workers: {args.workers}")
    print(f"Batch Size: {args.batch_size}")
    print(f"Verbose: {args.verbose}")
    print("=" * 50)
    
    success = True
    
    try:
        if args.command in ['etl', 'both']:
            # Check if we need to run ETL
            if not args.force_etl and check_etl_output(args.etl_output):
                print(f"✅ Recent ETL output found: {args.etl_output}")
                print("   Use --force-etl to regenerate")
            else:
                success = run_etl(
                    workers=args.workers,
                    batch_size=args.batch_size,
                    output_file=args.etl_output,
                    verbose=args.verbose,
                    quick=args.quick
                )
                
                if not success:
                    print("❌ ETL failed, stopping")
                    return 1
        
        if args.command in ['commission', 'both'] and success:
            success = run_commission_processing(
                etl_output=args.etl_output,
                verbose=args.verbose
            )
            
            if not success:
                print("❌ Commission processing failed")
                return 1
        
        if success:
            print("\n🎉 All operations completed successfully!")
            return 0
        else:
            print("\n❌ Some operations failed")
            return 1
            
    except KeyboardInterrupt:
        print("\n❌ Operation interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
