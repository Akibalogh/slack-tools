#!/usr/bin/env python3
"""
Company Commission Breakdown
Analyzes each company's pipeline activities and commission attribution by sales rep
"""

import json
from collections import defaultdict
from datetime import datetime

def round_to_nearest_25(percentage: float) -> float:
    """Round a percentage to the nearest 25% (25, 50, 75, or 100)"""
    if percentage <= 0:
        return 0.0
    elif percentage <= 12.5:
        return 0.0
    elif percentage <= 37.5:
        return 25.0
    elif percentage <= 62.5:
        return 50.0
    elif percentage <= 87.5:
        return 75.0
    else:
        return 100.0

def analyze_company_commissions():
    """Analyze commission breakdown by company and sales rep"""
    
    # Load the pipeline analysis results
    try:
        with open("pipeline_commission_analysis.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ pipeline_commission_analysis.json not found. Run pipeline_commission_analysis.py first.")
        return
    
    # Sales team info
    sales_team = data.get("sales_team", {})
    pipeline_stages = data.get("pipeline_stages", {})
    pipeline_activity = data.get("pipeline_activity", [])
    
    print("🏢 COMPANY COMMISSION BREAKDOWN ANALYSIS")
    print("=" * 60)
    
    # Group activities by company/channel
    company_activities = defaultdict(lambda: {
        "activities": [],
        "stages": defaultdict(list),
        "participants": defaultdict(int),
        "total_score": 0
    })
    
    # Process each activity
    for activity in pipeline_activity:
        # Extract company name from channel/DM info
        company_name = extract_company_name(activity)
        
        if company_name:
            company_activities[company_name]["activities"].append(activity)
            
            # Group by stage
            stage = activity.get("stage", "unknown")
            company_activities[company_name]["stages"][stage].append(activity)
            
            # Track participant involvement
            user_id = activity.get("user", "unknown")
            if user_id in sales_team:
                company_activities[company_name]["participants"][user_id] += 1
            
            # Calculate total score
            details = activity.get("details", {})
            score = details.get("score", 1)
            company_activities[company_name]["total_score"] += score
    
    # Calculate commission splits for each company
    company_commissions = {}
    
    for company, data in company_activities.items():
        if not data["activities"]:
            continue
            
        print(f"\n🏢 {company.upper()}")
        print("-" * 40)
        
        # Show pipeline stages
        print("📊 Pipeline Stages:")
        for stage, activities in data["stages"].items():
            stage_weight = pipeline_stages.get(stage, {}).get("weight", 0)
            print(f"   {stage}: {len(activities)} activities ({stage_weight}% weight)")
        
        # Show participants
        print("\n👥 Sales Team Involvement:")
        for user_id, count in data["participants"].items():
            user_info = sales_team.get(user_id, {"name": "Unknown", "role": "Unknown"})
            print(f"   {user_info['name']} ({user_info['role']}): {count} activities")
        
        # Calculate commission splits
        commission_splits = calculate_company_commissions(data, pipeline_stages, sales_team)
        company_commissions[company] = commission_splits
        
        print(f"\n💰 Commission Attribution:")
        total_commission = 0
        for user_id, commission in commission_splits.items():
            user_info = sales_team.get(user_id, {"name": "Unknown", "role": "Unknown"})
            print(f"   {user_info['name']}: {round_to_nearest_25(commission):.1f}%")
            total_commission += commission
        
        print(f"   Total: {round_to_nearest_25(total_commission):.1f}%")
        
        # Show sample activities
        print(f"\n💬 Sample Activities ({len(data['activities'])} total):")
        for i, activity in enumerate(data["activities"][:3]):  # Show first 3
            stage = activity.get("stage", "unknown")
            message = activity.get("message_preview", "No preview")[:80]
            user_id = activity.get("user", "unknown")
            user_name = sales_team.get(user_id, {}).get("name", user_id)
            print(f"   {i+1}. [{stage}] {user_name}: {message}")
        
        if len(data["activities"]) > 3:
            print(f"   ... and {len(data['activities']) - 3} more activities")
    
    # Summary by sales rep
    print(f"\n" + "=" * 60)
    print("👥 SALES REP COMMISSION SUMMARY")
    print("=" * 60)
    
    rep_totals = defaultdict(float)
    rep_companies = defaultdict(list)
    
    for company, commissions in company_commissions.items():
        for user_id, commission in commissions.items():
            rep_totals[user_id] += commission
            rep_companies[user_id].append(company)
    
    for user_id, total_commission in rep_totals.items():
        user_info = sales_team.get(user_id, {"name": "Unknown", "role": "Unknown"})
        companies = rep_companies[user_id]
        print(f"\n{user_info['name']} ({user_info['role']}): {round_to_nearest_25(total_commission):.1f}%")
        print(f"   Companies: {', '.join(companies[:5])}{'...' if len(companies) > 5 else ''}")
    
    # Save detailed breakdown
    breakdown_data = {
        "analysis_date": datetime.now().isoformat(),
        "company_commissions": company_commissions,
        "rep_totals": dict(rep_totals),
        "rep_companies": dict(rep_companies),
        "total_companies": len(company_commissions),
        "total_activities": len(pipeline_activity)
    }
    
    with open("company_commission_breakdown.json", "w") as f:
        json.dump(breakdown_data, f, indent=2)
    
    print(f"\n💾 Detailed breakdown saved to: company_commission_breakdown.json")

def extract_company_name(activity):
    """Extract company name from activity context"""
    message = activity.get("message_preview", "")
    
    # Look for company names in the message
    company_keywords = [
        "PixelPlex", "Copper", "Digital Asset", "Launch Node", "Obsidian", "Komonode", 
        "Five North", "Barg Systems", "Lightshift", "Lithium Digital", "ChainSafe", 
        "RWA XYZ", "Vigil Markets", "Noders", "Copper", "Launch Nodes", "Pathrock", 
        "Maestro", "Entropy Digital", "Kaleido", "Proof", "BlackSand", "XLabs", 
        "Gateway", "Cense", "Modulo Finance", "MLabs", "Node Monster", "Notabene", 
        "Hashrupt", "Kaiko", "BCW", "P2P", "Integraate", "Block and Bones", "Redstone", 
        "Digik", "XBron", "Theta Nuts", "Zeconomy", "Nova Prime", "Neogenesis", 
        "Incyt", "BlackManta", "Tenkai", "Alum Labs", "OpenBlock", "Temple", 
        "Matrixed Link", "G20", "SBC", "7Ridge", "Anchor Point", "MSE", "HLT", 
        "Levl", "Trakx", "Nethermind", "Palladium", "Ubyx", "LugaNodes", "Blockdaemon"
    ]
    
    for company in company_keywords:
        if company.lower() in message.lower():
            return company
    
    # Look for channel names in the message
    channel_patterns = [
        r"#([a-z0-9-]+)-bitsafe",
        r"#([a-z0-9-]+)-cbtc",
        r"#([a-z0-9-]+)-ibtc"
    ]
    
    import re
    for pattern in channel_patterns:
        match = re.search(pattern, message)
        if match:
            channel_name = match.group(1)
            # Convert to readable company name
            return channel_name.replace("-", " ").title()
    
    # If no company found, use a hash-based identifier
    return "Company_" + str(hash(activity.get("timestamp", "unknown")) % 1000)

def calculate_company_commissions(company_data, pipeline_stages, sales_team):
    """Calculate commission splits for a specific company"""
    commission_splits = {}
    
    # Group activities by stage
    stage_activity = defaultdict(list)
    for activity in company_data["activities"]:
        stage = activity.get("stage", "unknown")
        stage_activity[stage].append(activity)
    
    # Calculate commission for each stage
    for stage, activities in stage_activity.items():
        stage_weight = pipeline_stages.get(stage, {}).get("weight", 0)
        
        # Identify who was involved in this stage
        participants = {}
        for activity in activities:
            user_id = activity.get("user", "unknown")
            if user_id in sales_team:
                if user_id not in participants:
                    participants[user_id] = 0
                participants[user_id] += 1
        
        # Split commission among participants
        if participants:
            total_participation = sum(participants.values())
            for user_id, participation in participants.items():
                if user_id not in commission_splits:
                    commission_splits[user_id] = 0
                
                # Calculate proportional commission
                user_share = participation / total_participation
                stage_commission = stage_weight * user_share
                commission_splits[user_id] += stage_commission
    
    return commission_splits

if __name__ == "__main__":
    analyze_company_commissions()
