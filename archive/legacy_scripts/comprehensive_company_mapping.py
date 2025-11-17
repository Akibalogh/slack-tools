#!/usr/bin/env python3
"""
Comprehensive Company Commission Mapping
Maps ALL pipeline activities to ALL available conversations
"""

import json
import os
from collections import defaultdict
from datetime import datetime
import re

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

def load_all_conversations():
    """Load ALL conversation data from Slack export"""
    export_dir = "slack_export_20250815_064939"
    
    conversations = {}
    
    # Load private channels
    try:
        with open(f"{export_dir}/channels/private_channels.json", "r") as f:
            private_channels = json.load(f)
            for channel in private_channels:
                channel_name = channel.get("name", "")
                if channel_name:
                    company_name = extract_company_name_from_channel(channel_name)
                    conversations[channel["id"]] = {
                        "name": company_name,
                        "type": "private_channel",
                        "channel_name": channel_name,
                        "is_archived": channel.get("is_archived", False),
                        "num_members": channel.get("num_members", 0)
                    }
    except Exception as e:
        print(f"⚠️  Error loading private channels: {e}")
    
    # Load public channels
    try:
        with open(f"{export_dir}/channels/public_channels.json", "r") as f:
            public_channels = json.load(f)
            for channel in public_channels:
                channel_name = channel.get("name", "")
                if channel_name:
                    company_name = extract_company_name_from_channel(channel_name)
                    conversations[channel["id"]] = {
                        "name": company_name,
                        "type": "public_channel",
                        "channel_name": channel_name,
                        "is_archived": channel.get("is_archived", False),
                        "num_members": channel.get("num_members", 0)
                    }
    except Exception as e:
        print(f"⚠️  Error loading public channels: {e}")
    
    # Load channel message files
    channels_dir = f"{export_dir}/channels"
    if os.path.exists(channels_dir):
        for filename in os.listdir(channels_dir):
            if filename.endswith("_messages.json"):
                channel_name = filename.replace("_messages.json", "")
                company_name = extract_company_name_from_channel(channel_name)
                
                try:
                    with open(f"{channels_dir}/{filename}", "r") as f:
                        messages = json.load(f)
                        # Find the channel ID that matches this name
                        for conv_id, conv_data in conversations.items():
                            if conv_data.get("channel_name") == channel_name:
                                conv_data["messages"] = messages
                                conv_data["message_count"] = len(messages)
                                break
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
                            "channel_name": f"dm-{user_id}",
                            "messages": messages,
                            "message_count": len(messages),
                            "is_archived": False,
                            "num_members": 2
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
    name = name.replace("-minter", "")
    name = name.replace("_", " ")
    name = name.replace("-", " ")
    
    # Convert to title case
    company_name = " ".join(word.capitalize() for word in name.split())
    
    # Handle special cases
    if company_name == "Dm With":
        return "Direct Message"
    
    return company_name

def find_conversation_for_activity(activity, conversations):
    """Find which conversation an activity belongs to using improved matching"""
    activity_ts = float(activity.get("timestamp", 0))
    activity_text = activity.get("message_preview", "")
    
    best_match = None
    best_score = 0
    
    for conv_id, conv_data in conversations.items():
        if "messages" not in conv_data:
            continue
            
        score = 0
        
        # Check if any message in this conversation matches
        for message in conv_data["messages"]:
            message_ts = float(message.get("ts", 0))
            message_text = message.get("text", "")
            
            # Time proximity (within 2 hours for better matching)
            if abs(activity_ts - message_ts) < 7200:
                score += 1
            
            # Text similarity (partial matches)
            if activity_text.lower() in message_text.lower() or message_text.lower() in activity_text.lower():
                score += 10
            
            # Exact text match
            if activity_text == message_text:
                score += 100
            
            # Keyword matching for better coverage
            activity_words = set(activity_text.lower().split())
            message_words = set(message_text.lower().split())
            common_words = activity_words.intersection(message_words)
            if len(common_words) >= 3:  # At least 3 common words
                score += 5
        
        if score > best_score:
            best_score = score
            best_match = conv_id
    
    return best_match if best_score > 0 else None

def comprehensive_company_mapping():
    """Map ALL pipeline activities to ALL available conversations"""
    
    print("🔍 COMPREHENSIVE COMPANY COMMISSION MAPPING")
    print("=" * 60)
    
    # Load all conversations
    conversations = load_all_conversations()
    print(f"📚 Loaded {len(conversations)} total conversations")
    
    # Show conversation types
    type_counts = defaultdict(int)
    for conv in conversations.values():
        type_counts[conv["type"]] += 1
    
    print("\n📊 Conversation Types:")
    for conv_type, count in type_counts.items():
        print(f"   {conv_type}: {count}")
    
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
    
    print(f"\n📊 Found {len(pipeline_activity)} pipeline activities")
    
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
        channel_name = conv_data.get("channel_name", "")
        
        print(f"\n🏢 {company_name.upper()}")
        if channel_name:
            print(f"   Channel: {channel_name}")
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
            rounded_commission = round_to_nearest_25(commission)
            print(f"   {user_info['name']}: {rounded_commission:.0f}%")
            total_commission += rounded_commission
        
        print(f"   Total: {total_commission:.0f}%")
        
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
        rounded_total = round_to_nearest_25(total_commission)
        print(f"\n{user_info['name']} ({user_info['role']}): {rounded_total:.0f}%")
        print(f"   Companies: {', '.join(companies[:5])}{'...' if len(companies) > 5 else ''}")
    
    # Save comprehensive results
    results = {
        "analysis_date": datetime.now().isoformat(),
        "company_commissions": company_commissions,
        "rep_totals": dict(rep_totals),
        "rep_companies": dict(rep_companies),
        "mapped_activities": len([a for acts in conversation_activities.values() for a in acts]),
        "unmapped_activities": len(unmapped_activities),
        "total_conversations": len(conversation_activities),
        "total_available_conversations": len(conversations),
        "conversation_types": dict(type_counts)
    }
    
    with open("comprehensive_company_commissions.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Comprehensive results saved to: comprehensive_company_commissions.json")
    
    # Show unmapped activities for debugging
    if unmapped_activities:
        print(f"\n🔍 Sample Unmapped Activities:")
        for i, activity in enumerate(unmapped_activities[:5]):
            print(f"   {i+1}. [{activity.get('stage', 'unknown')}] {activity.get('message_preview', 'No preview')[:80]}")

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
    comprehensive_company_mapping()
