#!/usr/bin/env python3
"""
Generate Data Availability Report

This script analyzes the deal_rationale.csv file to generate a comprehensive report
showing which companies have stage data available and which stages are missing.
"""

import csv
import os
from pathlib import Path


def generate_data_availability_report():
    """Generate comprehensive data availability report"""

    csv_file = "output/deal_rationale.csv"
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return

    # Stage column names (in order)
    stage_columns = [
        "Sourcing/Intro",
        "Discovery/Qual",
        "Solution",
        "Objection",
        "Technical",
        "Pricing",
        "Contract",
        "Scheduling",
        "Closing",
    ]

    # Stage column indices (0-based, starting from column 10)
    stage_indices = list(range(10, 19))

    print("📊 DATA AVAILABILITY REPORT")
    print("=" * 80)
    print()

    # Read CSV and analyze
    companies_data = []
    total_companies = 0

    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip header

        for row in reader:
            if len(row) < 19:  # Ensure we have enough columns
                continue

            company_name = row[1]  # Company name is in column 2
            full_node_name = row[0]  # Full node name is in column 1

            # Check which stages have data vs "None"
            stage_status = {}
            missing_stages = []
            available_stages = []

            for i, stage_name in enumerate(stage_columns):
                stage_value = row[stage_indices[i]]
                if stage_value == "None":
                    stage_status[stage_name] = "Missing"
                    missing_stages.append(stage_name)
                else:
                    stage_status[stage_name] = "Available"
                    available_stages.append(stage_name)

            companies_data.append(
                {
                    "company": company_name,
                    "full_node_name": full_node_name,
                    "stage_status": stage_status,
                    "missing_stages": missing_stages,
                    "available_stages": available_stages,
                    "missing_count": len(missing_stages),
                    "available_count": len(available_stages),
                }
            )
            total_companies += 1

    # Sort companies by missing stage count (most missing first)
    companies_data.sort(key=lambda x: x["missing_count"], reverse=True)

    # Summary statistics
    total_stages = total_companies * 9  # 9 stages per company
    total_available = sum(c["available_count"] for c in companies_data)
    total_missing = sum(c["missing_count"] for c in companies_data)
    overall_coverage = (total_available / total_stages) * 100 if total_stages > 0 else 0

    print(f"📈 OVERALL STATISTICS")
    print(f"   Total Companies: {total_companies}")
    print(f"   Total Stages: {total_stages}")
    print(f"   Available Stages: {total_available}")
    print(f"   Missing Stages: {total_missing}")
    print(f"   Data Coverage: {overall_coverage:.1f}%")
    print()

    # Companies with complete data (no missing stages)
    complete_companies = [c for c in companies_data if c["missing_count"] == 0]
    print(f"✅ COMPANIES WITH COMPLETE STAGE DATA ({len(complete_companies)})")
    print("-" * 50)
    for company in complete_companies:
        print(f"   {company['company']}")
    print()

    # Companies with partial data (some stages missing)
    partial_companies = [c for c in companies_data if 0 < c["missing_count"] < 9]
    print(f"⚠️  COMPANIES WITH PARTIAL STAGE DATA ({len(partial_companies)})")
    print("-" * 50)
    for company in partial_companies:
        print(
            f"   {company['company']}: {company['available_count']}/9 stages available"
        )
        if company["missing_count"] <= 3:  # Show missing stages if few
            print(f"      Missing: {', '.join(company['missing_stages'])}")
    print()

    # Companies with no stage data (all stages missing)
    no_data_companies = [c for c in companies_data if c["missing_count"] == 9]
    print(f"❌ COMPANIES WITH NO STAGE DATA ({len(no_data_companies)})")
    print("-" * 50)
    for company in no_data_companies:
        print(f"   {company['company']}")
        print(f"      Full Node: {company['full_node_name']}")
    print()

    # Stage-by-stage analysis
    print(f"🔍 STAGE-BY-STAGE ANALYSIS")
    print("-" * 50)
    stage_stats = {}
    for stage_name in stage_columns:
        available_count = sum(
            1 for c in companies_data if stage_name in c["available_stages"]
        )
        missing_count = sum(
            1 for c in companies_data if stage_name in c["missing_stages"]
        )
        coverage = (
            (available_count / total_companies) * 100 if total_companies > 0 else 0
        )
        stage_stats[stage_name] = {
            "available": available_count,
            "missing": missing_count,
            "coverage": coverage,
        }
        print(
            f"   {stage_name:20}: {available_count:2d}/{total_companies} ({coverage:5.1f}%)"
        )
    print()

    # Recommendations
    print(f"💡 RECOMMENDATIONS")
    print("-" * 50)

    if no_data_companies:
        print(f"   🔴 PRIORITY: Process Telegram messages for companies with no data:")
        for company in no_data_companies:
            print(f"      - {company['company']}")
        print()

    # Find stages with lowest coverage
    lowest_coverage_stages = sorted(stage_stats.items(), key=lambda x: x[1]["coverage"])
    print(f"   🟡 FOCUS: Improve coverage for stages with lowest data:")
    for stage_name, stats in lowest_coverage_stages[:3]:
        print(f"      - {stage_name}: {stats['coverage']:.1f}% coverage")
    print()

    # Save detailed report to file
    report_file = "output/data_availability_report.txt"
    with open(report_file, "w") as f:
        f.write("DATA AVAILABILITY REPORT\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Overall Coverage: {overall_coverage:.1f}%\n")
        f.write(f"Total Companies: {total_companies}\n")
        f.write(f"Total Stages: {total_stages}\n")
        f.write(f"Available Stages: {total_available}\n")
        f.write(f"Missing Stages: {total_missing}\n\n")

        f.write("COMPANIES WITH NO STAGE DATA:\n")
        f.write("-" * 30 + "\n")
        for company in no_data_companies:
            f.write(f"{company['company']}: {company['full_node_name']}\n")
        f.write("\n")

        f.write("STAGE COVERAGE DETAILS:\n")
        f.write("-" * 30 + "\n")
        for stage_name, stats in stage_stats.items():
            f.write(
                f"{stage_name}: {stats['coverage']:.1f}% ({stats['available']}/{total_companies})\n"
            )

    print(f"📄 Detailed report saved to: {report_file}")


if __name__ == "__main__":
    generate_data_availability_report()
