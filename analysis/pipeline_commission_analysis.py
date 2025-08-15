#!/usr/bin/env python3
"""
Pipeline Commission Analysis
Maps conversations to pipeline stages for commission calculation
"""

import os
import asyncio
import aiohttp
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PipelineCommissionAnalyzer:
    def __init__(self):
        self.token = os.getenv("SLACK_TOKEN")
        if not self.token:
            raise ValueError("SLACK_TOKEN not found in .env file")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://slack.com/api"
        
        # Pipeline stages with commission weights based on CBTC onboarding process
        self.pipeline_stages = {
            "waitlist_interest": {
                "weight": 10,
                "keywords": ["waitlist", "join waitlist", "interest", "inquiry", "reach out", "intro", 
                           "connect", "initial", "first contact", "discovery call"]
            },
            "use_case_definition": {
                "weight": 20,
                "keywords": ["use case", "utility", "intended use", "what do you want to do", "purpose", 
                           "requirements", "needs", "challenge", "timeline", "budget", "decision maker"]
            },
            "msa_execution": {
                "weight": 25,
                "keywords": ["MSA", "master services agreement", "contract", "agreement", "terms", "legal", 
                           "docusign", "dropbox sign", "sign", "execute", "return MSA", "signed MSA"]
            },
            "reserve_funding": {
                "weight": 20,
                "keywords": ["deposit address", "fund reserve", "canton coins", "send coins", "wallet address", 
                           "funding", "payment", "billing", "reserve active", "canton scan", "funding round"]
            },
            "technical_setup": {
                "weight": 15,
                "keywords": ["utility application", "utility UI", "setup", "installation", "onboard to utility", 
                           "credential user service", "digital asset", "approval", "technical", "infrastructure"]
            },
            "credential_issuance": {
                "weight": 10,
                "keywords": ["notify bitsafe", "credential offer", "accept offer", "credential status", 
                           "active credential", "go live", "launch", "deploy", "production", "completed"]
            }
        }
        
        # Sales team members (using actual user IDs from export)
        self.sales_team = {
            "U05FZBDQ4RJ": {"name": "Aki Balogh", "role": "founder", "commission_rate": 0.3},
            "U092B2GUASF": {"name": "Addie Tackman", "role": "sales", "commission_rate": 0.4},
            "U092DKJ8L4Q": {"name": "Amy Wu", "role": "sales", "commission_rate": 0.3},
            "U07DGAEHEJF": {"name": "Kadeem Clarke", "role": "sales", "commission_rate": 0.3}
        }
    
    async def get_conversations(self):
        """Get all conversations (DMs, group DMs, channels)"""
        conversations = []
        
        async with aiohttp.ClientSession() as session:
            # Get DMs
            async with session.get(f"{self.base_url}/conversations.list", 
                                  headers=self.headers, 
                                  params={"types": "im", "limit": 1000}) as response:
                data = await response.json()
                if data.get("ok"):
                    conversations.extend([{"type": "dm", "data": conv} for conv in data["channels"]])
            
            # Get group DMs
            async with session.get(f"{self.base_url}/conversations.list", 
                                  headers=self.headers, 
                                  params={"types": "mpim", "limit": 1000}) as response:
                data = await response.json()
                if data.get("ok"):
                    conversations.extend([{"type": "group_dm", "data": conv} for conv in data["channels"]])
            
            # Get channels
            async with session.get(f"{self.base_url}/conversations.list", 
                                  headers=self.headers, 
                                  params={"types": "public_channel,private_channel", "limit": 1000}) as response:
                data = await response.json()
                if data.get("ok"):
                    conversations.extend([{"type": "channel", "data": conv} for conv in data["channels"]])
        
        return conversations
    
    async def get_conversation_history(self, conversation_id, limit=100):
        """Get recent conversation history"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/conversations.history", 
                                  headers=self.headers, 
                                  params={"channel": conversation_id, "limit": limit}) as response:
                data = await response.json()
                if data.get("ok"):
                    return data["messages"]
                return []
    
    def analyze_message_pipeline_stage(self, message_text):
        """Analyze a message to determine pipeline stage"""
        text = message_text.lower()
        stage_scores = {}
        
        for stage, config in self.pipeline_stages.items():
            score = 0
            for keyword in config["keywords"]:
                if keyword.lower() in text:
                    score += 1
            
            if score > 0:
                stage_scores[stage] = {
                    "score": score,
                    "weight": config["weight"],
                    "keywords_found": [kw for kw in config["keywords"] if kw.lower() in text]
                }
        
        # Return stage with highest score
        if stage_scores:
            best_stage = max(stage_scores.keys(), key=lambda x: stage_scores[x]["score"])
            return best_stage, stage_scores[best_stage]
        
        return None, None
    
    def identify_sales_activity(self, messages):
        """Identify sales activity and pipeline progression"""
        pipeline_activity = []
        
        for msg in messages:
            if msg.get("type") == "message" and msg.get("text"):
                stage, details = self.analyze_message_pipeline_stage(msg["text"])
                
                if stage:
                    pipeline_activity.append({
                        "timestamp": msg.get("ts"),
                        "user": msg.get("user"),
                        "stage": stage,
                        "details": details,
                        "message_preview": msg["text"][:100]
                    })
        
        return pipeline_activity
    
    def calculate_commission_splits(self, pipeline_activity):
        """
        Calculate commission splits based on pipeline activity.
        
        Commission Logic:
        - Each pipeline stage has a weight (total = 100%)
        - Commission is split among participants in each stage
        - Even if we don't see all conversations, pipeline progression 
          proves sales activity occurred
        - Pipeline changes = Evidence of sales involvement
        """
        """Calculate commission splits based on pipeline activity"""
        commission_splits = {}
        
        # Group activity by stage
        stage_activity = {}
        for activity in pipeline_activity:
            stage = activity["stage"]
            if stage not in stage_activity:
                stage_activity[stage] = []
            stage_activity[stage].append(activity)
        
        # Calculate commission for each stage
        for stage, activities in stage_activity.items():
            stage_weight = self.pipeline_stages[stage]["weight"]
            
            # Identify who was involved in this stage
            participants = {}
            for activity in activities:
                user_id = activity["user"]
                if user_id in self.sales_team:
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
    
    async def analyze_pipeline_commissions(self):
        """Main analysis function"""
        print("🔍 Starting Pipeline Commission Analysis...")
        
        # Get conversations
        conversations = await self.get_conversations()
        print(f"✅ Found {len(conversations)} conversations")
        
        all_pipeline_activity = []
        
        # Analyze each conversation
        for i, conv in enumerate(conversations):  # Analyze ALL conversations
            conv_type = conv["type"]
            conv_data = conv["data"]
            
            print(f"\n📊 Analyzing {conv_type}: {conv_data.get('name', conv_data.get('id', 'Unknown'))}")
            
            # Get conversation history
            messages = await self.get_conversation_history(conv_data["id"], limit=50)
            
            if messages:
                # Analyze pipeline activity
                pipeline_activity = self.identify_sales_activity(messages)
                all_pipeline_activity.extend(pipeline_activity)
                
                if pipeline_activity:
                    print(f"   🎯 Found {len(pipeline_activity)} pipeline activities")
                    for activity in pipeline_activity[:3]:  # Show first 3
                        print(f"      - {activity['stage']}: {activity['message_preview']}")
                else:
                    print("   ⚠️  No pipeline activity detected")
            
            # Rate limiting
            if i < len(conversations) - 1:
                await asyncio.sleep(1)
        
        # Calculate commission splits
        print(f"\n💰 Calculating Commission Splits...")
        commission_splits = self.calculate_commission_splits(all_pipeline_activity)
        
        # Display results
        print(f"\n📊 Pipeline Activity Summary:")
        print(f"Total pipeline activities: {len(all_pipeline_activity)}")
        
        print(f"\n💵 Commission Splits:")
        for user_id, commission in commission_splits.items():
            user_info = self.sales_team.get(user_id, {"name": "Unknown", "role": "Unknown"})
            print(f"   {user_info['name']} ({user_info['role']}): {commission:.1f}%")
        
        # Save results
        results = {
            "analysis_date": datetime.now().isoformat(),
            "pipeline_activity": all_pipeline_activity,
            "commission_splits": commission_splits,
            "sales_team": self.sales_team,
            "pipeline_stages": self.pipeline_stages
        }
        
        with open("pipeline_commission_analysis.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: pipeline_commission_analysis.json")
        
        return results

async def main():
    analyzer = PipelineCommissionAnalyzer()
    await analyzer.analyze_pipeline_commissions()

if __name__ == "__main__":
    asyncio.run(main())
