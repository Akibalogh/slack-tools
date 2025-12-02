#!/usr/bin/env python3
"""
Analysis Scripts Refactoring Helper
This script helps identify and clean up duplicate code in analysis scripts
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple


def find_duplicate_functions(scripts_dir: str = "analysis") -> Dict[str, List[str]]:
    """
    Find duplicate functions across analysis scripts
    """
    print("🔍 Searching for duplicate functions...")

    duplicates = {}
    function_definitions = {}

    # Scan all Python files in the analysis directory
    for file_path in Path(scripts_dir).glob("*.py"):
        if file_path.name == "unified_commission_analysis.py":
            continue  # Skip the new unified script

        print(f"  Scanning {file_path.name}...")

        with open(file_path, "r") as f:
            content = f.read()

        # Find function definitions
        function_pattern = r"def\s+(\w+)\s*\([^)]*\):"
        functions = re.findall(function_pattern, content)

        for func_name in functions:
            if func_name not in function_definitions:
                function_definitions[func_name] = []
            function_definitions[func_name].append(str(file_path))

    # Find duplicates
    for func_name, files in function_definitions.items():
        if len(files) > 1:
            duplicates[func_name] = files

    return duplicates


def analyze_code_duplication(scripts_dir: str = "analysis") -> Dict[str, Dict]:
    """
    Analyze code duplication patterns
    """
    print("📊 Analyzing code duplication patterns...")

    analysis = {}

    # Check for common patterns
    common_patterns = [
        ("round_to_nearest_25", "Commission calculation utility"),
        ("extract_company_name_from_channel", "Company name extraction"),
        ("load_slack_export_data", "Slack data loading"),
        ("load_conversation_data", "Conversation data loading"),
        ("analyze_company_commissions", "Company commission analysis"),
        ("find_conversation_for_activity", "Activity mapping"),
    ]

    for pattern, description in common_patterns:
        files_with_pattern = []
        for file_path in Path(scripts_dir).glob("*.py"):
            if file_path.name == "unified_commission_analysis.py":
                continue

            with open(file_path, "r") as f:
                content = f.read()
                if pattern in content:
                    files_with_pattern.append(str(file_path))

        if len(files_with_pattern) > 1:
            analysis[pattern] = {
                "description": description,
                "files": files_with_pattern,
                "count": len(files_with_pattern),
                "priority": "high" if len(files_with_pattern) > 2 else "medium",
            }

    return analysis


def generate_refactoring_plan(
    duplicates: Dict[str, List[str]], analysis: Dict[str, Dict]
) -> str:
    """
    Generate a refactoring plan
    """
    print("📋 Generating refactoring plan...")

    plan_lines = [
        "# Analysis Scripts Refactoring Plan",
        "=" * 50,
        "",
        "## 🚨 High Priority Duplicates",
        "",
    ]

    # High priority items
    high_priority = [k for k, v in analysis.items() if v["priority"] == "high"]
    for pattern in high_priority:
        data = analysis[pattern]
        plan_lines.append(f"### {pattern}")
        plan_lines.append(f"**Description:** {data['description']}")
        plan_lines.append(f"**Files affected:** {', '.join(data['files'])}")
        plan_lines.append(f"**Action:** Move to utils/commission_utils.py")
        plan_lines.append("")

    plan_lines.append("## 🔧 Medium Priority Duplicates")
    plan_lines.append("")

    # Medium priority items
    medium_priority = [k for k, v in analysis.items() if v["priority"] == "medium"]
    for pattern in medium_priority:
        data = analysis[pattern]
        plan_lines.append(f"### {pattern}")
        plan_lines.append(f"**Description:** {data['description']}")
        plan_lines.append(f"**Files affected:** {', '.join(data['files'])}")
        plan_lines.append(f"**Action:** Consider consolidation")
        plan_lines.append("")

    plan_lines.append("## 📁 Script Consolidation Strategy")
    plan_lines.append("")
    plan_lines.append("### Phase 1: Utility Consolidation")
    plan_lines.append("- Move common functions to utils/commission_utils.py")
    plan_lines.append("- Update imports in all analysis scripts")
    plan_lines.append("")

    plan_lines.append("### Phase 2: Script Consolidation")
    plan_lines.append(
        "- Keep pipeline_commission_analysis.py as base (most comprehensive)"
    )
    plan_lines.append("- Merge functionality from other scripts")
    plan_lines.append("- Create unified_commission_analysis.py")
    plan_lines.append("")

    plan_lines.append("### Phase 3: Cleanup")
    plan_lines.append("- Remove redundant scripts after testing")
    plan_lines.append("- Update documentation")
    plan_lines.append("")

    plan_lines.append("## 🎯 Files to Keep")
    plan_lines.append("- utils/commission_utils.py (NEW - consolidated utilities)")
    plan_lines.append("- analysis/unified_commission_analysis.py (NEW - main script)")
    plan_lines.append(
        "- analysis/pipeline_commission_analysis.py (KEEP - most comprehensive)"
    )
    plan_lines.append("")

    plan_lines.append("## 🗑️ Files to Consider Removing")
    plan_lines.append(
        "- analysis/map_activities_to_conversations.py (basic functionality)"
    )
    plan_lines.append("- analysis/real_company_commission_breakdown.py (duplicates)")
    plan_lines.append("- analysis/company_commission_breakdown.py (duplicates)")
    plan_lines.append("- analysis/comprehensive_company_mapping.py (duplicates)")

    return "\n".join(plan_lines)


def check_import_compatibility(scripts_dir: str = "analysis") -> Dict[str, List[str]]:
    """
    Check which scripts can be updated to use the new utilities
    """
    print("🔍 Checking import compatibility...")

    compatibility = {}

    for file_path in Path(scripts_dir).glob("*.py"):
        if file_path.name == "unified_commission_analysis.py":
            continue

        with open(file_path, "r") as f:
            content = f.read()

        # Check if script uses functions that are now in utilities
        utility_functions = [
            "round_to_nearest_25",
            "extract_company_name_from_channel",
            "load_slack_export_data",
            "load_channel_messages",
            "find_conversation_for_activity",
            "calculate_commission_split",
            "format_commission_report",
        ]

        used_functions = [func for func in utility_functions if func in content]

        if used_functions:
            compatibility[str(file_path)] = {
                "can_update": True,
                "functions_used": used_functions,
                "update_effort": "low" if len(used_functions) <= 3 else "medium",
            }
        else:
            compatibility[str(file_path)] = {
                "can_update": False,
                "functions_used": [],
                "update_effort": "none",
            }

    return compatibility


def main():
    """Main function"""
    print("🚀 Analysis Scripts Refactoring Helper")
    print("=" * 50)

    # Find duplicates
    duplicates = find_duplicate_functions()

    # Analyze patterns
    analysis = analyze_code_duplication()

    # Check compatibility
    compatibility = check_import_compatibility()

    # Generate plan
    plan = generate_refactoring_plan(duplicates, analysis)

    # Save plan
    with open("REFACTORING_PLAN.md", "w") as f:
        f.write(plan)

    # Print summary
    print("\n📊 REFACTORING SUMMARY")
    print("-" * 30)
    print(f"Duplicate functions found: {len(duplicates)}")
    print(
        f"High priority patterns: {len([k for k, v in analysis.items() if v['priority'] == 'high'])}"
    )
    print(
        f"Medium priority patterns: {len([k for k, v in analysis.items() if v['priority'] == 'medium'])}"
    )
    print(
        f"Scripts that can be updated: {len([k for k, v in compatibility.items() if v['can_update']])}"
    )

    print(f"\n📋 Refactoring plan saved to: REFACTORING_PLAN.md")

    # Show high priority items
    print("\n🚨 HIGH PRIORITY ITEMS:")
    for pattern, data in analysis.items():
        if data["priority"] == "high":
            print(f"  • {pattern}: {data['description']} ({data['count']} files)")

    print(f"\n✅ Refactoring analysis complete!")
    print(f"💡 Next steps:")
    print(f"   1. Review REFACTORING_PLAN.md")
    print(f"   2. Update scripts to use utils/commission_utils.py")
    print(f"   3. Test unified_commission_analysis.py")
    print(f"   4. Remove redundant scripts")


if __name__ == "__main__":
    main()
