#!/usr/bin/env python3
"""
Comprehensive ETL Data Ingestion Script
Ingests all data sources and outputs machine-readable JSON format
"""

import os
import json
import sqlite3
import csv
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path
from dotenv import load_dotenv
import re
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl_ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataETL:
    def __init__(self):
        self.output_file = "data/etl_output.json"
        self.db_path = "data/slack/repsplit.db"
        self.company_mapping_file = "data/company_mapping.csv"
        
        # Load environment variables
        load_dotenv()
        
        # Initialize data structures
        self.companies = {}
        self.slack_data = {}
        self.telegram_data = {}
        self.calendar_data = {}
        self.hubspot_data = {}
        
    def load_company_mapping(self) -> Dict[str, Any]:
        """Load company mapping from CSV"""
        logger.info("Loading company mapping...")
        companies = {}
        
        if not os.path.exists(self.company_mapping_file):
            logger.error(f"Company mapping file not found: {self.company_mapping_file}")
            return companies
            
        with open(self.company_mapping_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                company_name = row['Company Name']
                companies[company_name] = {
                    'full_node_address': row['Full Node Address'],
                    'slack_groups': row['Slack Groups'],
                    'telegram_groups': row['Telegram Groups'],
                    'calendar_domain': row['Calendar Search Domain'],
                    'variant_type': row['Variants'],
                    'base_company': row['Base Company']
                }
        
        logger.info(f"Loaded {len(companies)} companies from mapping file")
        return companies
    
    def ingest_slack_data(self) -> Dict[str, Any]:
        """Ingest Slack data from database"""
        logger.info("Ingesting Slack data...")
        slack_data = {}
        
        if not os.path.exists(self.db_path):
            logger.error(f"Slack database not found: {self.db_path}")
            return slack_data
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get all conversations
            cursor.execute('''
                SELECT conv_id, name, member_count, creation_date, is_bitsafe
                FROM conversations
                ORDER BY name
            ''')
            conversations = cursor.fetchall()
            
            for conv_id, name, member_count, creation_date, is_bitsafe in conversations:
                # Get messages for this conversation
                cursor.execute('''
                    SELECT m.author, m.text, m.timestamp, u.display_name
                    FROM messages m
                    LEFT JOIN users u ON m.author = u.id
                    WHERE m.conv_id = ?
                    ORDER BY m.timestamp
                ''', (conv_id,))
                messages = cursor.fetchall()
                
                # Get stage detections for this conversation
                cursor.execute('''
                    SELECT sd.stage_name, sd.author, sd.timestamp, sd.confidence, u.display_name
                    FROM stage_detections sd
                    LEFT JOIN users u ON sd.author = u.id
                    WHERE sd.conv_id = ?
                    ORDER BY sd.timestamp
                ''', (conv_id,))
                stage_detections = cursor.fetchall()
                
                slack_data[conv_id] = {
                    'name': name,
                    'member_count': member_count,
                    'creation_date': creation_date,
                    'is_bitsafe': bool(is_bitsafe),
                    'messages': [
                        {
                            'author': author,
                            'text': text,
                            'timestamp': timestamp,
                            'display_name': display_name
                        }
                        for author, text, timestamp, display_name in messages
                    ],
                    'stage_detections': [
                        {
                            'stage_name': stage_name,
                            'author': author,
                            'timestamp': timestamp,
                            'confidence': confidence,
                            'display_name': display_name
                        }
                        for stage_name, author, timestamp, confidence, display_name in stage_detections
                    ]
                }
            
            logger.info(f"Ingested {len(slack_data)} Slack conversations")
            
        except Exception as e:
            logger.error(f"Error ingesting Slack data: {e}")
        finally:
            conn.close()
            
        return slack_data
    
    def ingest_telegram_data(self) -> Dict[str, Any]:
        """Ingest Telegram data from HTML export"""
        logger.info("Ingesting Telegram data...")
        telegram_data = {}
        
        telegram_export_path = "data/telegram/DataExport_2025-08-19"
        if not os.path.exists(telegram_export_path):
            logger.error(f"Telegram export not found: {telegram_export_path}")
            return telegram_data
            
        # Get list of chat directories
        chats_dir = os.path.join(telegram_export_path, "chats")
        if not os.path.exists(chats_dir):
            logger.error(f"Telegram chats directory not found: {chats_dir}")
            return telegram_data
            
        chat_dirs = [d for d in os.listdir(chats_dir) if os.path.isdir(os.path.join(chats_dir, d))]
        logger.info(f"Found {len(chat_dirs)} chat directories to process")
        
        processed_count = 0
        error_count = 0
        
        for chat_dir in chat_dirs:
            chat_path = os.path.join(chats_dir, chat_dir)
            
            # Look for HTML files in the chat directory
            html_files = [f for f in os.listdir(chat_path) if f.endswith('.html')]
            
            if not html_files:
                logger.debug(f"No HTML files found in {chat_dir}")
                continue
                
            # Process all HTML files in this chat directory
            chat_messages = []
            chat_participants = set()
            chat_name = chat_dir  # Use directory name as base identifier
            
            for html_file in html_files:
                html_path = os.path.join(chat_path, html_file)
                
                try:
                    with open(html_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Extract messages from this HTML file
                    message_divs = soup.find_all('div', class_='message')
                    
                    for msg_div in message_divs:
                        # Extract author
                        author_elem = msg_div.find('div', class_='from_name')
                        author = author_elem.text.strip() if author_elem else "Unknown"
                        
                        # Extract text
                        text_elem = msg_div.find('div', class_='text')
                        text = text_elem.text.strip() if text_elem else ""
                        
                        # Extract timestamp
                        date_elem = msg_div.find('div', class_='date')
                        timestamp = date_elem.get('title', '') if date_elem else ""
                        
                        if text:  # Only include messages with text
                            chat_messages.append({
                                'author': author,
                                'text': text,
                                'timestamp': timestamp
                            })
                            chat_participants.add(author)
                    
                    # Try to extract actual chat name from participants or first message
                    if not chat_messages:
                        # Look for participant names in userpics
                        userpics = soup.find_all('div', class_='userpic')
                        for userpic in userpics:
                            initials_elem = userpic.find('div', class_='initials')
                            if initials_elem and initials_elem.get('title'):
                                chat_participants.add(initials_elem.get('title'))
                        
                except Exception as e:
                    logger.warning(f"Error processing {html_path}: {e}")
                    error_count += 1
                    continue
            
            # Create a more meaningful chat name if possible
            if chat_participants:
                # Try to identify if this is a company-specific chat
                participant_list = list(chat_participants)
                if len(participant_list) == 1:
                    chat_name = f"{participant_list[0]}-telegram"
                elif len(participant_list) <= 5:
                    # For small groups, use participant names
                    chat_name = f"{'-'.join(participant_list[:3])}-telegram"
                else:
                    # For larger groups, use directory name
                    chat_name = f"{chat_dir}-telegram"
            else:
                chat_name = f"{chat_dir}-telegram"
            
            # Store the chat data if it has messages
            if chat_messages:
                telegram_data[chat_name] = {
                    'messages': chat_messages,
                    'message_count': len(chat_messages),
                    'participants': list(chat_participants),
                    'participant_count': len(chat_participants),
                    'directory': chat_dir
                }
                processed_count += 1
                
                # Log progress every 100 chats
                if processed_count % 100 == 0:
                    logger.info(f"Processed {processed_count} chats so far...")
        
        logger.info(f"Ingested {len(telegram_data)} Telegram chats (processed: {processed_count}, errors: {error_count})")
        return telegram_data
    
    def ingest_calendar_data(self) -> Dict[str, Any]:
        """Ingest Google Calendar data"""
        logger.info("Ingesting Calendar data...")
        calendar_data = {}
        
        try:
            from google_calendar_integration import GoogleCalendarIntegration
            
            calendar = GoogleCalendarIntegration()
            if calendar.authenticate():
                # Get meetings for the past 180 days
                end_date = datetime.now()
                start_date = end_date - timedelta(days=180)
                
                # Get all calendars
                calendar_list = calendar.service.calendarList().list().execute()
                calendar_ids = [item['id'] for item in calendar_list.get('items', [])]
                
                for calendar_id in calendar_ids:
                    try:
                        events_result = calendar.service.events().list(
                            calendarId=calendar_id,
                            timeMin=start_date.isoformat() + 'Z',
                            timeMax=end_date.isoformat() + 'Z',
                            maxResults=1000,
                            singleEvents=True,
                            orderBy='startTime'
                        ).execute()
                        
                        events = events_result.get('items', [])
                        
                        for event in events:
                            summary = event.get('summary', '')
                            description = event.get('description', '')
                            
                            # Extract company names from meeting titles
                            # This is a simple approach - could be enhanced with NLP
                            company_keywords = [
                                'bitsafe', 'btc', 'cbtc', 'bitcoin', 'custody', 'institutional',
                                'p2p', 'chainsafe', 'copper', 'hextrust', 'bitgo', 'allnodes'
                            ]
                            
                            for keyword in company_keywords:
                                if keyword.lower() in summary.lower() or keyword.lower() in description.lower():
                                    if keyword not in calendar_data:
                                        calendar_data[keyword] = []
                                    
                                    calendar_data[keyword].append({
                                        'summary': summary,
                                        'description': description,
                                        'start_time': event.get('start', {}).get('dateTime', ''),
                                        'end_time': event.get('end', {}).get('dateTime', ''),
                                        'attendees': [att.get('email', '') for att in event.get('attendees', [])],
                                        'calendar_id': calendar_id
                                    })
                                    break
                                    
                    except Exception as e:
                        logger.warning(f"Error processing calendar {calendar_id}: {e}")
                        continue
                        
                logger.info(f"Ingested calendar data for {len(calendar_data)} companies")
            else:
                logger.warning("Could not authenticate with Google Calendar")
                
        except ImportError:
            logger.warning("Google Calendar integration not available")
        except Exception as e:
            logger.error(f"Error ingesting calendar data: {e}")
            
        return calendar_data
    
    def ingest_hubspot_data(self) -> Dict[str, Any]:
        """Ingest HubSpot CRM data"""
        logger.info("Ingesting HubSpot data...")
        hubspot_data = {}
        
        hubspot_file = "data/hubspot/hubspot-crm-exports-all-deals-2025-08-11-1.csv"
        if not os.path.exists(hubspot_file):
            logger.error(f"HubSpot file not found: {hubspot_file}")
            return hubspot_data
            
        try:
            with open(hubspot_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    company_name = row.get('Company Name', '').strip()
                    if company_name:
                        hubspot_data[company_name] = {
                            'deal_name': row.get('Deal Name', ''),
                            'deal_stage': row.get('Deal Stage', ''),
                            'deal_value': row.get('Deal Value', ''),
                            'close_date': row.get('Close Date', ''),
                            'owner': row.get('Owner', ''),
                            'pipeline': row.get('Pipeline', ''),
                            'created_date': row.get('Created Date', ''),
                            'last_activity': row.get('Last Activity Date', ''),
                            'source': row.get('Source', ''),
                            'lead_status': row.get('Lead Status', '')
                        }
            
            logger.info(f"Ingested {len(hubspot_data)} HubSpot deals")
            
        except Exception as e:
            logger.error(f"Error ingesting HubSpot data: {e}")
            
        return hubspot_data
    
    def match_data_to_companies(self) -> Dict[str, Any]:
        """Match all data sources to companies"""
        logger.info("Matching data to companies...")
        
        matched_data = {}
        
        for company_name, company_info in self.companies.items():
            matched_data[company_name] = {
                'company_info': company_info,
                'slack_channels': [],
                'telegram_chats': [],
                'calendar_meetings': [],
                'hubspot_deals': []
            }
            
            # Match Slack channels
            for conv_id, slack_info in self.slack_data.items():
                slack_name = slack_info['name'].lower()
                company_name_lower = company_name.lower()
                
                # Try multiple matching strategies
                matched = False
                
                # 1. Direct match with slack_groups
                if company_info['slack_groups'] and company_info['slack_groups'].lower() in slack_name:
                    matched = True
                
                # 2. Match company name in slack channel name
                elif company_name_lower in slack_name or slack_name in company_name_lower:
                    matched = True
                
                # 3. Match base company name
                elif company_info['base_company'] and company_info['base_company'].lower() in slack_name:
                    matched = True
                
                # 4. Match variants (remove common suffixes)
                elif any(variant.lower() in slack_name for variant in [company_name_lower.replace('-minter', ''), 
                                                                      company_name_lower.replace('-mainnet', ''),
                                                                      company_name_lower.replace('-validator', '')]):
                    matched = True
                
                if matched:
                    matched_data[company_name]['slack_channels'].append({
                        'conv_id': conv_id,
                        'name': slack_info['name'],
                        'message_count': len(slack_info['messages']),
                        'stage_detection_count': len(slack_info['stage_detections']),
                        'data': slack_info
                    })
            
            # Match Telegram chats
            for chat_name, telegram_info in self.telegram_data.items():
                chat_name_lower = chat_name.lower()
                company_name_lower = company_name.lower()
                
                # Try multiple matching strategies
                matched = False
                
                # 1. Direct match with telegram_groups
                if company_info['telegram_groups'] and company_info['telegram_groups'].lower() in chat_name_lower:
                    matched = True
                
                # 2. Match company name in chat name
                elif company_name_lower in chat_name_lower or chat_name_lower in company_name_lower:
                    matched = True
                
                # 3. Match base company name
                elif company_info['base_company'] and company_info['base_company'].lower() in chat_name_lower:
                    matched = True
                
                # 4. Match common patterns
                elif any(pattern in chat_name_lower for pattern in [company_name_lower.replace('-', ''), 
                                                                   company_name_lower.replace('-', ' ')]):
                    matched = True
                
                if matched:
                    matched_data[company_name]['telegram_chats'].append({
                        'chat_name': chat_name,
                        'message_count': telegram_info['message_count'],
                        'data': telegram_info
                    })
            
            # Match Calendar meetings
            for keyword, meetings in self.calendar_data.items():
                if keyword.lower() in company_name.lower() or keyword.lower() in company_info['calendar_domain'].lower():
                    matched_data[company_name]['calendar_meetings'].extend(meetings)
            
            # Match HubSpot deals
            for deal_company, deal_info in self.hubspot_data.items():
                deal_company_lower = deal_company.lower()
                company_name_lower = company_name.lower()
                
                # Try multiple matching strategies
                matched = False
                
                # 1. Direct name match
                if (deal_company_lower in company_name_lower or 
                    company_name_lower in deal_company_lower):
                    matched = True
                
                # 2. Match with calendar domain
                elif company_info['calendar_domain'] and deal_company_lower in company_info['calendar_domain'].lower():
                    matched = True
                
                # 3. Match base company name
                elif company_info['base_company'] and deal_company_lower in company_info['base_company'].lower():
                    matched = True
                
                # 4. Match with common variations
                elif any(variant in deal_company_lower for variant in [company_name_lower.replace('-', ''), 
                                                                      company_name_lower.replace('-', ' '),
                                                                      company_name_lower.replace('-minter', ''),
                                                                      company_name_lower.replace('-mainnet', '')]):
                    matched = True
                
                if matched:
                    matched_data[company_name]['hubspot_deals'].append(deal_info)
        
        return matched_data
    
    def generate_summary_stats(self, matched_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics"""
        stats = {
            'total_companies': len(matched_data),
            'companies_with_slack': 0,
            'companies_with_telegram': 0,
            'companies_with_calendar': 0,
            'companies_with_hubspot': 0,
            'total_slack_channels': len(self.slack_data),
            'total_telegram_chats': len(self.telegram_data),
            'total_calendar_meetings': sum(len(meetings) for meetings in self.calendar_data.values()),
            'total_hubspot_deals': len(self.hubspot_data),
            'data_coverage': {}
        }
        
        for company_name, company_data in matched_data.items():
            has_slack = len(company_data['slack_channels']) > 0
            has_telegram = len(company_data['telegram_chats']) > 0
            has_calendar = len(company_data['calendar_meetings']) > 0
            has_hubspot = len(company_data['hubspot_deals']) > 0
            
            if has_slack:
                stats['companies_with_slack'] += 1
            if has_telegram:
                stats['companies_with_telegram'] += 1
            if has_calendar:
                stats['companies_with_calendar'] += 1
            if has_hubspot:
                stats['companies_with_hubspot'] += 1
            
            # Calculate data coverage for this company
            data_sources = sum([has_slack, has_telegram, has_calendar, has_hubspot])
            stats['data_coverage'][company_name] = {
                'sources_count': data_sources,
                'has_slack': has_slack,
                'has_telegram': has_telegram,
                'has_calendar': has_calendar,
                'has_hubspot': has_hubspot
            }
        
        return stats
    
    def run_etl(self) -> None:
        """Run the complete ETL process"""
        logger.info("Starting ETL data ingestion...")
        
        # Load company mapping
        self.companies = self.load_company_mapping()
        
        # Ingest all data sources
        self.slack_data = self.ingest_slack_data()
        self.telegram_data = self.ingest_telegram_data()
        self.calendar_data = self.ingest_calendar_data()
        self.hubspot_data = self.ingest_hubspot_data()
        
        # Match data to companies
        matched_data = self.match_data_to_companies()
        
        # Generate summary statistics
        stats = self.generate_summary_stats(matched_data)
        
        # Create final output structure
        output_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'etl_version': '1.0.0',
                'data_sources': ['slack', 'telegram', 'calendar', 'hubspot'],
                'total_companies': len(self.companies)
            },
            'statistics': stats,
            'companies': matched_data
        }
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        # Write output file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"ETL completed! Output written to {self.output_file}")
        logger.info(f"Processed {len(matched_data)} companies")
        logger.info(f"Slack: {stats['companies_with_slack']} companies")
        logger.info(f"Telegram: {stats['companies_with_telegram']} companies")
        logger.info(f"Calendar: {stats['companies_with_calendar']} companies")
        logger.info(f"HubSpot: {stats['companies_with_hubspot']} companies")

def main():
    """Main function"""
    etl = DataETL()
    etl.run_etl()

if __name__ == "__main__":
    main()
