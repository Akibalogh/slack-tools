#!/usr/bin/env python3
"""
Commission Analysis Script

Analyzes commission splits and effort percentages for all customers based on:
- RepSplit commission rules
- Slack activity data
- Real billing revenue data
- Business ownership assignments
"""

import sqlite3
import json
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
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

class CommissionAnalyzer:
    def __init__(self):
        self.conn = sqlite3.connect('repsplit.db')
        self.cursor = self.conn.cursor()
        
        # Load RepSplit configuration
        with open('config.json', 'r') as f:
            self.config = json.load(f)
        
        # Commission rules from RepSplit
        self.commission_rules = {
            "diminishing_returns": True,
            "founder_cap": 0.40,  # 40% max for founders
            "closer_bonus": 0.05,  # 5% bonus for closer
            "presence_floor": 0.05,  # 5% minimum for participation
            "min_participation": 0.10  # 10% minimum to earn commission
        }
        
        # Real billing data with ownership assignments
        self.billing_data = {
            "allnodes": {"revenue": 338225, "sourced_by": "Aki", "owned_by": "Aki", "closed": "No"},
            "alum-labs": {"revenue": 354914, "sourced_by": "Aki", "owned_by": "Aki", "closed": "No"},
            "artichoke-capital": {"revenue": 17374, "sourced_by": "Aki", "owned_by": "Aki", "closed": "No"},
            "b2c2": {"revenue": 312235, "sourced_by": "Aki", "owned_by": "Aki", "closed": "No"},
            "bitgo": {"revenue": 17378, "sourced_by": "Aki", "owned_by": "Aki", "closed": "No"},
            "bitsafe": {"revenue": 477193, "sourced_by": "", "owned_by": "", "closed": "No"},
            "black-manta": {"revenue": 121957, "sourced_by": "Aki", "owned_by": "Aki", "closed": "Yes"},
            "brikly": {"revenue": 503715, "sourced_by": "Aki", "owned_by": "Aki", "closed": "Yes"},
            "chainsafe": {"revenue": 337691, "sourced_by": "Aki", "owned_by": "Aki", "closed": "Yes"},
            "digik": {"revenue": 355359, "sourced_by": "Aki", "owned_by": "Aki", "closed": "No"},
            "distributed-lab": {"revenue": 109038, "sourced_by": "Aki", "owned_by": "Aki", "closed": "No"},
            "everstake": {"revenue": 354792, "sourced_by": "Aki", "owned_by": "Aki", "closed": "No"},
            "falconx": {"revenue": 338905, "sourced_by": "Aki", "owned_by": "Aki", "closed": "No"},
            "figment": {"revenue": 17385, "sourced_by": "Aki", "owned_by": "Aki", "closed": "No"},
            "finoa": {"revenue": 354237, "sourced_by": "Aki", "owned_by": "Aki", "closed": "No"},
            "five-north": {"revenue": 397814, "sourced_by": "Aki", "owned_by": "Aki", "closed": "Yes"},
            "foundinals": {"revenue": 451867, "sourced_by": "Addie", "owned_by": "Aki", "closed": "Yes"},
            "gomaestro": {"revenue": 334930, "sourced_by": "Aki", "owned_by": "Aki", "closed": "No"},
            "hashkey-cloud": {"revenue": 159931, "sourced_by": "Aki", "owned_by": "Aki", "closed": "Yes"},
            "igor-gusarov": {"revenue": 358534, "sourced_by": "Aki", "owned_by": "Aki", "closed": "Yes"},
            "incyt": {"revenue": 338636, "sourced_by": "Aki", "owned_by": "Aki", "closed": "No"},
            "komonode": {"revenue": 280443, "sourced_by": "Aki", "owned_by": "Aki", "closed": "Yes"},
            "launchnodes": {"revenue": 306942, "sourced_by": "Aki", "owned_by": "Mayank", "closed": "Yes"},
            "linkpool": {"revenue": 353851, "sourced_by": "Aki", "owned_by": "Aki", "closed": "No"},
            "lithium-digital": {"revenue": 347077, "sourced_by": "Addie", "owned_by": "Aki", "closed": "Yes"},
            "meria": {"revenue": 354076, "sourced_by": "Aki", "owned_by": "Aki", "closed": "Yes"},
            "mintify": {"revenue": 352586, "sourced_by": "Aki", "owned_by": "Aki", "closed": "Yes"},
            "modulo-finance": {"revenue": 353983, "sourced_by": "Aki", "owned_by": "Aki", "closed": "Yes"},
            "mpch": {"revenue": 79159, "sourced_by": "Aki", "owned_by": "Aki", "closed": "Yes"},
            "nansen": {"revenue": 338159, "sourced_by": "Aki", "owned_by": "Aki", "closed": "No"},
            "nethermind": {"revenue": 206187, "sourced_by": "Aki", "owned_by": "Aki", "closed": "Yes"},
            "nodemonsters": {"revenue": 356019, "sourced_by": "Mayank", "owned_by": "Aki", "closed": "Yes"},
            "notabene": {"revenue": 337614, "sourced_by": "Aki", "owned_by": "Aki", "closed": "No"},
            "obsidian": {"revenue": 472159, "sourced_by": "Addie", "owned_by": "Aki", "closed": "Yes"},
            "p2p": {"revenue": 353463, "sourced_by": "Aki", "owned_by": "Aki", "closed": "Yes"},
            "pier-two": {"revenue": 161236, "sourced_by": "Aki", "owned_by": "Aki", "closed": "Yes"},
            "redstone": {"revenue": 160508, "sourced_by": "Addie", "owned_by": "Aki", "closed": "Yes"},
            "register-labs": {"revenue": 394582, "sourced_by": "Addie", "owned_by": "Mayank", "closed": "Yes"},
            "republic": {"revenue": 239003, "sourced_by": "Aki", "owned_by": "Aki", "closed": "Yes"},
            "round13": {"revenue": 334747, "sourced_by": "Aki", "owned_by": "Aki", "closed": "Yes"},
            "send-cantonwallet": {"revenue": 34233, "sourced_by": "Aki", "owned_by": "Aki", "closed": "Yes"},
            "sendit": {"revenue": 438767, "sourced_by": "Addie", "owned_by": "Aki", "closed": "Yes"},
            "tall-oak-midstream": {"revenue": 471641, "sourced_by": "Addie", "owned_by": "Addie", "closed": "Yes"},
            "tenkai": {"revenue": 351723, "sourced_by": "Aki", "owned_by": "Aki", "closed": "No"},
            "trakx": {"revenue": 14166, "sourced_by": "Amy", "owned_by": "Amy", "closed": "Yes"},
            "t-rize": {"revenue": 195707, "sourced_by": "Aki", "owned_by": "Aki", "closed": "Yes"},
            "unlock-it": {"revenue": 99084, "sourced_by": "Addie", "owned_by": "Aki", "closed": "Yes"},
            "xbto": {"revenue": 308365, "sourced_by": "Aki", "owned_by": "Aki", "closed": "Yes"},
            "xlabs": {"revenue": 352180, "sourced_by": "Aki", "owned_by": "Aki", "closed": "No"}
        }
    
    def get_slack_activity(self, company_name: str) -> Dict[str, int]:
        """Get Slack activity for a company's bitsafe channel"""
        # Try different channel name variations
        channel_variations = [
            f"{company_name}-bitsafe",
            f"{company_name.replace('-', '')}-bitsafe",
            f"{company_name.replace('-', ' ').replace(' ', '')}-bitsafe"
        ]
        
        for channel_name in channel_variations:
            self.cursor.execute("""
                SELECT c.conv_id, c.name, COUNT(*) as msg_count 
                FROM conversations c 
                JOIN messages m ON c.conv_id = m.conv_id 
                WHERE c.name = ? 
                GROUP BY c.conv_id, c.name
            """, (channel_name,))
            
            result = self.cursor.fetchone()
            if result:
                conv_id, name, msg_count = result
                
                # Get individual user message counts
                self.cursor.execute("""
                    SELECT m.author, COUNT(*) as user_msg_count
                    FROM messages m 
                    WHERE m.conv_id = ?
                    GROUP BY m.author
                    ORDER BY user_msg_count DESC
                """, (conv_id,))
                
                user_counts = {}
                for author, count in self.cursor.fetchall():
                    # Get user display name
                    self.cursor.execute("""
                        SELECT display_name, real_name 
                        FROM users 
                        WHERE id = ?
                    """, (author,))
                    
                    user_result = self.cursor.fetchone()
                    if user_result:
                        display_name, real_name = user_result
                        user_key = display_name or real_name or author
                        user_counts[user_key] = count
                
                return {
                    "total_messages": msg_count,
                    "user_breakdown": user_counts,
                    "channel_name": name
                }
        
        return {"total_messages": 0, "user_breakdown": {}, "channel_name": "Not found"}
    
    def calculate_effort_percentages(self, company_name: str, activity_data: Dict, 
                                   billing_info: Dict) -> Dict[str, float]:
        """Calculate effort percentages combining Slack activity and business ownership"""
        
        # Base effort from Slack activity
        total_messages = activity_data.get("total_messages", 0)
        user_breakdown = activity_data.get("user_breakdown", {})
        
        # Map Slack names to participant names
        name_mapping = {
            "Aki": "Aki",
            "Aki Balogh": "Aki", 
            "Addie": "Addie",
            "Addie Tackman": "Addie",
            "Amy": "Amy",
            "Amy Wu": "Amy",
            "Mayank": "Mayank",
            "Mayank Sachdev": "Mayank"
        }
        
        # Initialize effort percentages
        effort_percentages = {"Aki": 0.0, "Addie": 0.0, "Amy": 0.0, "Mayank": 0.0}
        
        # Calculate Slack-based effort
        for participant_name in effort_percentages:
            for slack_name, count in user_breakdown.items():
                if slack_name in name_mapping and name_mapping[slack_name] == participant_name:
                    effort_percentages[participant_name] = (count / total_messages) * 100
                    break
        
        # Apply business ownership adjustments
        sourced_by = billing_info.get("sourced_by", "")
        owned_by = billing_info.get("owned_by", "")
        closed = billing_info.get("closed", "No")
        
        # Business ownership gives additional effort weight
        if sourced_by and sourced_by in effort_percentages:
            effort_percentages[sourced_by] += 20.0  # Sourcing bonus
        
        if owned_by and owned_by in effort_percentages:
            effort_percentages[owned_by] += 15.0  # Ownership bonus
        
        if closed == "Yes" and owned_by in effort_percentages:
            effort_percentages[owned_by] += 10.0  # Closing bonus
        
        # Normalize to 100%
        total_effort = sum(effort_percentages.values())
        if total_effort > 0:
            for participant in effort_percentages:
                effort_percentages[participant] = (effort_percentages[participant] / total_effort) * 100
        
        return effort_percentages
    
    def calculate_commission_splits(self, company_name: str, revenue: float, 
                                  effort_percentages: Dict, billing_info: Dict) -> Dict:
        """Calculate commission splits based on effort percentages and business rules"""
        
        commission_splits = {}
        
        for participant_name, effort_pct in effort_percentages.items():
            if effort_pct > 0:
                # Base commission based on effort
                base_commission = effort_pct / 100.0
                
                # Apply presence floor
                if base_commission < self.commission_rules["presence_floor"]:
                    base_commission = self.commission_rules["presence_floor"]
                
                # Apply minimum participation threshold
                if base_commission < self.commission_rules["min_participation"]:
                    base_commission = 0.0
                
                # Apply founder cap (Aki is founder)
                if participant_name == "Aki" and base_commission > self.commission_rules["founder_cap"]:
                    base_commission = self.commission_rules["founder_cap"]
                
                # Round commission percentage to nearest 25%
                commission_splits[participant_name] = {
                    "effort_percentage": effort_pct,
                    "commission_percentage": round_to_nearest_25(base_commission * 100),
                    "commission_amount": base_commission * revenue
                }
        
        return commission_splits
    
    def analyze_all_customers(self) -> List[Dict]:
        """Analyze all customers using real billing data and ownership"""
        
        results = []
        
        for company, billing_info in self.billing_data.items():
            # Get Slack activity
            activity_data = self.get_slack_activity(company)
            
            # Get revenue and ownership info
            revenue = billing_info["revenue"]
            sourced_by = billing_info["sourced_by"]
            owned_by = billing_info["owned_by"]
            closed = billing_info["closed"]
            
            # Calculate effort percentages
            effort_percentages = self.calculate_effort_percentages(
                company, activity_data, billing_info
            )
            
            # Calculate commission splits
            commission_splits = self.calculate_commission_splits(
                company, revenue, effort_percentages, billing_info
            )
            
            # Format results
            company_result = {
                "company_name": company.replace('-', ' ').title(),
                "slack_channel": activity_data.get("channel_name", "Not found"),
                "total_messages": activity_data.get("total_messages", 0),
                "revenue_cc": revenue,
                "sourced_by": sourced_by,
                "owned_by": owned_by,
                "closed": closed,
                "effort_percentages": effort_percentages,
                "commission_splits": commission_splits,
                "total_commission_pct": sum(
                    p["commission_percentage"] for p in commission_splits.values()
                )
            }
            
            results.append(company_result)
        
        return results
    
    def generate_summary_table(self, results: List[Dict]) -> str:
        """Generate a formatted summary table with effort and commission data"""
        
        table = []
        table.append("=" * 140)
        table.append(f"{'Company':<25} {'Channel':<20} {'Revenue':<12} {'Sourced':<8} {'Owned':<8} {'Closed':<7} {'Aki':<8} {'Addie':<8} {'Amy':<8} {'Mayank':<8}")
        table.append("=" * 140)
        
        total_revenue = 0
        total_commission = {"Aki": 0, "Addie": 0, "Amy": 0, "Mayank": 0}
        
        for result in results:
            company = result["company_name"]
            channel = result["slack_channel"][:18] if result["slack_channel"] != "Not found" else "No Slack"
            revenue = result["revenue_cc"]
            sourced = result["sourced_by"][:7] if result["sourced_by"] else "None"
            owned = result["owned_by"][:7] if result["owned_by"] else "None"
            closed = result["closed"][:6]
            
            # Get effort percentages
            effort = result["effort_percentages"]
            aki_effort = effort.get("Aki", 0)
            addie_effort = effort.get("Addie", 0)
            amy_effort = effort.get("Amy", 0)
            mayank_effort = effort.get("Mayank", 0)
            
            # Get commission amounts
            commission = result["commission_splits"]
            aki_comm = commission.get("Aki", {}).get("commission_amount", 0)
            addie_comm = commission.get("Addie", {}).get("commission_amount", 0)
            amy_comm = commission.get("Amy", {}).get("commission_amount", 0)
            mayank_comm = commission.get("Mayank", {}).get("commission_amount", 0)
            
            # Accumulate totals
            total_revenue += revenue
            total_commission["Aki"] += aki_comm
            total_commission["Addie"] += addie_comm
            total_commission["Amy"] += amy_comm
            total_commission["Mayank"] += mayank_comm
            
            table.append(f"{company:<25} {channel:<20} {revenue:<12,.0f} {sourced:<8} {owned:<8} {closed:<7} {aki_effort:<8.1f}% {addie_effort:<8.1f}% {amy_effort:<8.1f}% {mayank_effort:<8.1f}%")
        
        table.append("=" * 140)
        table.append(f"{'TOTALS':<25} {'':<20} {total_revenue:<12,.0f} {'':<8} {'':<8} {'':<7} {total_commission['Aki']:<8,.0f} {total_commission['Addie']:<8,.0f} {total_commission['Amy']:<8,.0f} {total_commission['Mayank']:<8,.0f}")
        table.append("=" * 140)
        
        return "\n".join(table)
    
    def generate_effort_analysis(self, results: List[Dict]) -> str:
        """Generate detailed effort analysis by participant"""
        
        analysis = []
        analysis.append("\n📊 DETAILED EFFORT ANALYSIS BY PARTICIPANT")
        analysis.append("=" * 80)
        
        participants = ["Aki", "Addie", "Amy", "Mayank"]
        
        for participant in participants:
            analysis.append(f"\n🎯 {participant}:")
            analysis.append("-" * 40)
            
            # Companies where this participant has significant effort
            participant_companies = []
            for result in results:
                effort = result["effort_percentages"].get(participant, 0)
                if effort > 5.0:  # Only show companies with >5% effort
                    participant_companies.append({
                        "company": result["company_name"],
                        "effort": effort,
                        "revenue": result["revenue_cc"],
                        "role": self._get_participant_role(result, participant)
                    })
            
            # Sort by effort percentage
            participant_companies.sort(key=lambda x: x["effort"], reverse=True)
            
            if participant_companies:
                for company_info in participant_companies[:10]:  # Top 10
                    analysis.append(f"  • {company_info['company']:<25} {company_info['effort']:>6.1f}% {company_info['revenue']:>10,.0f} CC ({company_info['role']})")
            else:
                analysis.append("  No significant effort in any companies")
        
        return "\n".join(analysis)
    
    def _get_participant_role(self, result: Dict, participant: str) -> str:
        """Get the role of a participant in a specific deal"""
        roles = []
        
        if result["sourced_by"] == participant:
            roles.append("Sourced")
        if result["owned_by"] == participant:
            roles.append("Owned")
        if result["closed"] == "Yes" and result["owned_by"] == participant:
            roles.append("Closed")
        
        return ", ".join(roles) if roles else "Participant"
    
    def close(self):
        """Close database connection"""
        self.conn.close()

def main():
    """Main analysis function"""
    analyzer = CommissionAnalyzer()
    
    print("🔍 Analyzing Commission Splits and Effort Percentages")
    print("📊 Using Real Billing Data and Business Ownership")
    print("=" * 80)
    
    # Analyze all customers
    results = analyzer.analyze_all_customers()
    
    # Generate summary table
    summary_table = analyzer.generate_summary_table(results)
    print(summary_table)
    
    # Generate detailed effort analysis
    effort_analysis = analyzer.generate_effort_analysis(results)
    print(effort_analysis)
    
    # Print top companies by revenue
    print("\n💰 TOP COMPANIES BY REVENUE:")
    print("-" * 50)
    
    sorted_results = sorted(results, key=lambda x: x["revenue_cc"], reverse=True)
    for i, result in enumerate(sorted_results[:15]):
        print(f"{i+1}. {result['company_name']}: {result['revenue_cc']:,.0f} CC")
        print(f"    Sourced: {result['sourced_by']}, Owned: {result['owned_by']}, Closed: {result['closed']}")
        for participant, data in result["commission_splits"].items():
            if data["commission_percentage"] > 0:
                print(f"    - {participant}: {data['effort_percentage']:.1f}% effort, {data['commission_percentage']:.0f}% commission (${data['commission_amount']:,.0f})")
        print()
    
    analyzer.close()

if __name__ == "__main__":
    main()
