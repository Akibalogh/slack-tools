#!/usr/bin/env python3
"""
ETL Runner Script
Executes the complete ETL process and generates analysis
"""

import os
import sys
import subprocess
from datetime import datetime

def main():
    print("🚀 Starting ETL Data Ingestion Process")
    print("=" * 50)
    
    # Check if required files exist
    required_files = [
        "data/company_mapping.csv",
        "data/slack/repsplit.db"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        print("\nPlease ensure all required files exist before running ETL.")
        return 1
    
    # Run ETL ingestion
    print("\n📥 Running ETL Data Ingestion...")
    try:
        result = subprocess.run([sys.executable, "etl_data_ingestion.py"], 
                              capture_output=True, text=True, check=True)
        print("✅ ETL ingestion completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ ETL ingestion failed: {e}")
        print(f"Error output: {e.stderr}")
        return 1
    
    # Run analysis
    print("\n📊 Running Data Analysis...")
    try:
        result = subprocess.run([sys.executable, "analyze_etl_data.py"], 
                              capture_output=True, text=True, check=True)
        print("✅ Data analysis completed successfully")
        print("\n" + result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Data analysis failed: {e}")
        print(f"Error output: {e.stderr}")
        return 1
    
    # Check output files
    output_files = [
        "data/etl_output.json",
        "data/company_data_summary.csv"
    ]
    
    print("\n📁 Generated Files:")
    for file_path in output_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"   ✅ {file_path} ({size:,} bytes)")
        else:
            print(f"   ❌ {file_path} (not found)")
    
    print(f"\n🎉 ETL process completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

