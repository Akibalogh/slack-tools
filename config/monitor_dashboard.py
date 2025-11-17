#!/usr/bin/env python3
"""
RepSplit System Monitoring Dashboard

Provides real-time monitoring of system health, performance, and data freshness.
"""
import json
import time
from datetime import datetime
from pathlib import Path
from repsplit import RepSplit


def print_header(title: str):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def print_status(status: str, message: str):
    """Print formatted status message"""
    status_icons = {
        "healthy": "✅",
        "degraded": "⚠️",
        "critical": "🚨",
        "error": "❌"
    }
    icon = status_icons.get(status, "❓")
    print(f"{icon} {status.upper()}: {message}")


def print_metric(label: str, value: str, unit: str = ""):
    """Print formatted metric"""
    print(f"  {label}: {value}{unit}")


def display_database_health(health_data: dict):
    """Display database health information"""
    print_header("DATABASE HEALTH")
    
    status = health_data.get("status", "unknown")
    print_status(status, "Database performance and structure")
    
    if "database_size_mb" in health_data:
        print_metric("Database Size", f"{health_data['database_size_mb']}", " MB")
    
    if "table_count" in health_data:
        print_metric("Table Count", str(health_data["table_count"]))
    
    if "total_rows" in health_data:
        print_metric("Total Rows", f"{health_data['total_rows']:,}")
    
    if "query_performance_ms" in health_data:
        perf = health_data["query_performance_ms"]
        if perf < 10:
            perf_status = "✅ Excellent"
        elif perf < 100:
            perf_status = "⚠️ Good"
        else:
            perf_status = "🚨 Poor"
        print_metric("Query Performance", f"{perf} ms", f" ({perf_status})")
    
    if "data_freshness_hours" in health_data:
        hours = health_data["data_freshness_hours"]
        if hours and hours < 24:
            freshness_status = "✅ Fresh"
        elif hours and hours < 168:  # 1 week
            freshness_status = "⚠️ Stale"
        else:
            freshness_status = "🚨 Very Stale"
        print_metric("Data Freshness", f"{hours:.1f}", f" hours ({freshness_status})")


def display_data_freshness(freshness_data: dict):
    """Display data freshness information"""
    print_header("DATA FRESHNESS")
    
    overall_status = freshness_data.get("overall_status", "unknown")
    print_status(overall_status, "Data source freshness")
    
    stale_count = len(freshness_data.get("stale_sources", []))
    total_sources = len(freshness_data) - 2  # Exclude overall_status and stale_sources
    
    print_metric("Fresh Sources", f"{total_sources - stale_count}/{total_sources}")
    print_metric("Stale Sources", str(stale_count))
    
    print("\n  Data Source Details:")
    for source, info in freshness_data.items():
        if source in ["overall_status", "stale_sources"]:
            continue
        
        source_status = info.get("status", "unknown")
        if source_status == "fresh":
            icon = "✅"
        elif source_status == "stale":
            icon = "⚠️"
        elif source_status == "no_data":
            icon = "❌"
        else:
            icon = "❓"
        
        if "last_update_hours_ago" in info and info["last_update_hours_ago"]:
            hours = info["last_update_hours_ago"]
            print(f"    {icon} {source}: {hours:.1f} hours ago")
        else:
            print(f"    {icon} {source}: {source_status}")


def display_performance_metrics(perf_data: dict):
    """Display performance metrics"""
    print_header("PERFORMANCE METRICS")
    
    if "message" in perf_data:
        print(f"  {perf_data['message']}")
        return
    
    total_functions = perf_data.get("total_functions_timed", 0)
    if total_functions == 0:
        print("  No performance metrics recorded yet")
        return
    
    print_metric("Functions Timed", str(total_functions))
    
    avg_time = perf_data.get("average_execution_time_ms", 0)
    print_metric("Average Execution Time", f"{avg_time}", " ms")
    
    if "slowest_function" in perf_data:
        slowest = perf_data["slowest_function"]
        print_metric("Slowest Function", f"{slowest[0]} ({slowest[1]*1000:.1f} ms)")
    
    if "fastest_function" in perf_data:
        fastest = perf_data["fastest_function"]
        print(f"  Fastest Function: {fastest[0]} ({fastest[1]*1000:.1f} ms)")


def display_system_info(system_info: dict):
    """Display system information"""
    print_header("SYSTEM INFORMATION")
    
    for key, value in system_info.items():
        if key == "output_directory":
            # Check if directory exists
            path = Path(value)
            if path.exists():
                print_metric(key.replace("_", " ").title(), f"{value} ✅")
            else:
                print_metric(key.replace("_", " ").title(), f"{value} ❌")
        else:
            print_metric(key.replace("_", " ").title(), str(value))


def run_monitoring_dashboard():
    """Run the main monitoring dashboard"""
    print_header("REPSPLIT SYSTEM MONITORING DASHBOARD")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Initialize RepSplit with enhanced logging
        repsplit = RepSplit()
        
        # Generate comprehensive health report
        health_report = repsplit.generate_system_health_report()
        
        # Display all sections
        display_database_health(health_report["database_health"])
        display_data_freshness(health_report["data_freshness"])
        display_performance_metrics(health_report["performance_metrics"])
        display_system_info(health_report["system_info"])
        
        # Overall system status
        print_header("OVERALL SYSTEM STATUS")
        overall_status = health_report["overall_status"]
        if overall_status == "healthy":
            print("🎉 SYSTEM IS HEALTHY - All components operating normally")
        elif overall_status == "degraded":
            print("⚠️  SYSTEM IS DEGRADED - Some issues detected, monitoring required")
        else:
            print("🚨 SYSTEM IS CRITICAL - Immediate attention required")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ Error running monitoring dashboard: {e}")
        print("Please check the logs for more details.")


def continuous_monitoring(interval_seconds: int = 60):
    """Run continuous monitoring with specified interval"""
    print(f"Starting continuous monitoring (refresh every {interval_seconds} seconds)")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            # Clear screen (works on most terminals)
            print("\033[2J\033[H", end="")
            
            # Run dashboard
            run_monitoring_dashboard()
            
            # Wait for next refresh
            print(f"\n🔄 Next refresh in {interval_seconds} seconds...")
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring stopped by user")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        continuous_monitoring(interval)
    else:
        # Single run
        run_monitoring_dashboard()

