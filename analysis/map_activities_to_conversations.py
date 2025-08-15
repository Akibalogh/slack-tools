#!/usr/bin/env python3
"""
Map Pipeline Activities to Conversations
Reconstructs conversation context to extract real company names
"""

import json
import os
from collections import defaultdict
from datetime import datetime

def load_conversation_data():
    """Load conversation data from Slack export"""
    export_dir = "slack_export_20250815_064939"
    
    conversations = {}
    
    # Load channel conversations
    channels_dir = f"{export_dir}/channels"
    if os.path.exists(channels_dir):
        for filename in os.listdir(channels_dir):
            if filename.endswith("_messages.json"):
                channel_name = filename.replace("_messages.json", "")
                
                # Clean up channel name to get company name
                company_name = extract_company_name_from_channel(channel_name)
                
                try:
                    with open(f"{channels_dir}/{filename}", "r") as f:
                        messages = json.load(f)
                        conversations[channel_name] = {
                            "name": company_name,
                            "type": "channel",
                            "messages": messages,
                            "message_count": len(messages)
                        }
                except Exception as e:
                    print(f"⚠️  Error loading {filename}: {e}")
    
    # Load DM conversations
    dms_dir = f"{export_dir}/dms"
    if os.path.exists(dms_dir):
        for filename in os.listdir(dms_dir):
            if filename.endswith("_messages.json"):
                user_id = filename.replace("_messages.json", "")
                
                try:
                    with open(f"{dms_dir}/{filename}", "r") as f:
                        messages = json.load(f)
                        conversations[user_id] = {
                            "name": f"DM with {user_id}",
                            "type": "dm",
                            "messages": messages,
                            "message_count": len(messages)
                        }
                except Exception as e:
                    print(f"⚠️  Error loading DM {filename}: {e}")
    
    return conversations

def extract_company_name_from_channel(channel_name):
    """Extract company name from channel name"""
    if not channel_name:
        return "Unknown"
    
    # Remove common suffixes
    name = channel_name.lower()
    name = name.replace("-bitsafe", "")
    name = name.replace("-cbtc", "")
    name = name.replace("-ibtc", "")
    name = name.replace("_", " ")
    name = name.replace("-", " ")
    
    # Convert to title case
    company_name = " ".join(word.capitalize() for word in name.split())
    
    return company_name

def find_conversation_for_activity(activity, conversations):
    """Find which conversation an activity belongs to based on timestamp and content"""
    activity_ts = float(activity.get("timestamp", 0))
    activity_text = activity.get("message_preview", "")
    
    best_match = None
    best_score = 0
    
    for conv_id, conv_data in conversations.items():
        score = 0
        
        # Check if any message in this conversation matches
        for message in conv_data["messages"]:
            message_ts = float(message.get("ts", 0))
            message_text = message.get("text", "")
            
            # Time proximity (within 1 hour)
            if abs(activity_ts - message_ts) < 3600:
                score += 1
            
            # Text similarity
            if activity_text.lower() in message_text.lower() or message_text.lower() in activity_text.lower():
                score += 10
            
            # Exact text match
            if activity_text == message_text:
                score += 100
        
        if score > best_score:
            best_score = score
            best_match = conv_id
    
    return best_match if best_score > 0 else None

def map_activities_to_conversations():
    """Map pipeline activities to actual conversations"""
    
    print("🔍 Mapping Pipeline Activities to Conversations")
    print("=" * 60)
    
    # Load conversations
    conversations = load_conversation_data()
    print(f"📚 Loaded {len(conversations)} conversations")
    
    # Load pipeline activities
    try:
        with open("pipeline_commission_analysis.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ pipeline_commission_analysis.json not found")
        return
    
    pipeline_activity = data.get("pipeline_activity", [])
    sales_team = data.get("sales_team", {})
    pipeline_stages = data.get("pipeline_stages", {})
    
    print(f"📊 Found {len(pipeline_activity)} pipeline activities")
    
    # Map activities to conversations
    conversation_activities = defaultdict(list)
    unmapped_activities = []
    
    for activity in pipeline_activity:
        conv_id = find_conversation_for_activity(activity, conversations)
        if conv_id:
            conversation_activities[conv_id].append(activity)
        else:
            unmapped_activities.append(activity)
    
    print(f"✅ Mapped {sum(len(acts) for acts in conversation_activities.values())} activities to conversations")
    print(f"❌ {len(unmapped_activities)} activities could not be mapped")
    
    # Analyze each conversation
    company_commissions = {}
    
    for conv_id, activities in conversation_activities.items():
        if not activities:
            continue
            
        conv_data = conversations.get(conv_id, {})
        company_name = conv_data.get("name", conv_id)
        
        print(f"\n🏢 {company_name.upper()}")
        print("-" * 50)
        
        # Group activities by stage
        stage_activities = defaultdict(list)
        participants = defaultdict(int)
        
        for activity in activities:
            stage = activity.get("stage", "unknown")
            stage_activities[stage].append(activity)
            
            user_id = activity.get("user", "unknown")
            if user_id in sales_team:
                participants[user_id] += 1
        
        # Show pipeline stages
        print("📊 Pipeline Stages:")
        for stage, stage_acts in stage_activities.items():
            stage_weight = pipeline_stages.get(stage, {}).get("weight", 0)
            print(f"   {stage}: {len(stage_acts)} activities ({stage_weight}% weight)")
        
        # Show participants
        print("\n👥 Sales Team Involvement:")
        for user_id, count in participants.items():
            user_info = sales_team.get(user_id, {"name": "Unknown", "role": "Unknown"})
            print(f"   {user_info['name']} ({user_info['role']}): {count} activities")
        
        # Calculate commission splits
        commission_splits = calculate_commission_splits(activities, pipeline_stages, sales_team)
        company_commissions[company_name] = commission_splits
        
        # Show commission attribution
        print(f"\n💰 Commission Attribution:")
        total_commission = 0
        for user_id, commission in commission_splits.items():
            user_info = sales_team.get(user_id, {"name": "Unknown", "role": "Unknown"})
            print(f"   {user_info['name']}: {commission:.1f}%")
            total_commission += commission
        
        print(f"   Total: {total_commission:.1f}%")
        
        # Show sample activities
        print(f"\n💬 Sample Activities ({len(activities)} total):")
        for i, activity in enumerate(activities[:3]):
            stage = activity.get("stage", "unknown")
            message = activity.get("message_preview", "No preview")[:80]
            user_id = activity.get("user", "unknown")
            user_name = sales_team.get(user_id, {}).get("name", user_id)
            print(f"   {i+1}. [{stage}] {user_name}: {message}")
        
        if len(activities) > 3:
            print(f"   ... and {len(activities) - 3} more activities")
    
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
        print(f"\n{user_info['name']} ({user_info['role']}): {total_commission:.1f}%")
        print(f"   Companies: {', '.join(companies[:5])}{'...' if len(companies) > 5 else ''}")
    
    # Save results
    results = {
        "analysis_date": datetime.now().isoformat(),
        "company_commissions": company_commissions,
        "rep_totals": dict(rep_totals),
        "rep_companies": dict(rep_companies),
        "mapped_activities": len([a for acts in conversation_activities.values() for a in acts]),
        "unmapped_activities": len(unmapped_activities),
        "total_conversations": len(conversation_activities)
    }
    
    with open("conversation_mapped_commissions.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: conversation_mapped_commissions.json")

def calculate_commission_splits(activities, pipeline_stages, sales_team):
    """Calculate commission splits for activities"""
    commission_splits = {}
    
    # Group activities by stage
    stage_activity = defaultdict(list)
    for activity in activities:
        stage = activity.get("stage", "unknown")
        stage_activity[stage].append(activity)
    
    # Calculate commission for each stage
    for stage, stage_acts in stage_activity.items():
        stage_weight = pipeline_stages.get(stage, {}).get("weight", 0)
        
        # Identify who was involved in this stage
        participants = {}
        for activity in stage_acts:
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
    map_activities_to_conversations()
