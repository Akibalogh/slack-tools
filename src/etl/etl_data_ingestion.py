#!/usr/bin/env python3
"""
Comprehensive ETL Data Ingestion Script
Ingests all data sources and outputs machine-readable JSON format
"""

import os
import sqlite3
import csv
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import threading
import multiprocessing
from .utils.text_formatter import ETLTextFormatter
from .utils.company_matcher import CompanyMatcher

# Set up logging with better visibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/etl_ingestion.log'),
        logging.StreamHandler()
    ],
    force=True  # Force reconfiguration
)
logger = logging.getLogger(__name__)

# Multiprocessing worker function (must be at module level)
def process_telegram_chat_worker(chat_dir: str, chats_dir: str) -> Optional[Dict[str, Any]]:
    """Worker function for processing a single Telegram chat (multiprocessing compatible)"""
    try:
        chat_path = os.path.join(chats_dir, chat_dir)
        messages_file = os.path.join(chat_path, "messages.html")
        
        if not os.path.exists(messages_file):
            return None
            
        with open(messages_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract chat name from page header if available, otherwise use directory name
        page_header = soup.find('div', class_='page_header')
        if page_header:
            header_text = page_header.get_text(strip=True)
            if header_text and header_text != "Exported Data":
                chat_name = header_text.replace(" ", "-").lower()
            else:
                chat_name = chat_dir.replace('_', ' ').replace('-', ' ')
        else:
            chat_name = chat_dir.replace('_', ' ').replace('-', ' ')
        
        # Extract messages
        messages = []
        message_elements = soup.find_all('div', class_='message')
        
        for msg_elem in message_elements:
            try:
                # Extract sender
                sender_elem = msg_elem.find('div', class_='from_name')
                sender = sender_elem.get_text(strip=True) if sender_elem else 'Unknown'
                
                # Extract timestamp
                date_elem = msg_elem.find('div', class_='date')
                timestamp = date_elem.get_text(strip=True) if date_elem else ''
                
                # Extract message text
                text_elem = msg_elem.find('div', class_='text')
                text = text_elem.get_text(strip=True) if text_elem else ''
                
                if text:  # Only include messages with text
                    messages.append({
                        'sender': sender,
                        'timestamp': timestamp,
                        'text': text
                    })
            except Exception as e:
                continue  # Skip malformed messages
        
        if not messages:
            return None
            
        # Count unique participants
        participants = set(msg['sender'] for msg in messages)
        
        return {
            'chat_name': chat_name,
            'message_count': len(messages),
            'participant_count': len(participants),
            'messages': messages,
            'participants': list(participants)
        }
        
    except Exception as e:
        return None

# Add a custom handler for real-time progress
class ProgressHandler(logging.StreamHandler):
    def emit(self, record):
        if 'Processed' in record.getMessage() or 'batch' in record.getMessage():
            print(f"\r{record.getMessage()}", end='', flush=True)
        else:
            print(f"\n{record.getMessage()}", flush=True)

progress_handler = ProgressHandler()
progress_handler.setLevel(logging.INFO)
logger.addHandler(progress_handler)

class DataETL:
    def __init__(self, max_workers: int = None, batch_size: int = 100, quick_mode: bool = False, use_multiprocessing: bool = True):
        # Generate output filename - main file for easy access, timestamped copy for archive
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = "output/notebooklm/etl_output.txt"  # Main file for NotebookLM
        self.archive_file = f"output/notebooklm/archive/etl_output_{timestamp}.txt"  # Timestamped archive
        self.db_path = "data/slack/repsplit.db"
        self.company_mapping_file = "data/company_mapping.csv"
        
        # Companies to exclude from analysis (internal companies)
        self.excluded_companies = {
            'bitsafe', 'bitsafe-minter', 'bitsafe-mainnet', 'bitsafe-validator',
            'bitsafe-canton', 'bitsafe-wallet', 'bitsafe-node', 'bitsafe-company',
            'bitsafe-product', 'bitsafe-bd', 'bitsafe-board-of-directors', 'bitsafe-marketing'
        }
        
        # Performance settings
        if max_workers is None:
            # Use optimal worker count based on CPU cores
            cpu_count = multiprocessing.cpu_count()
            self.max_workers = min(cpu_count * 2, 16)  # 2x CPU cores, max 16
        else:
            self.max_workers = max_workers
        self.batch_size = batch_size
        self.quick_mode = quick_mode
        self.use_multiprocessing = use_multiprocessing
        
        # Load environment variables
        load_dotenv()
        
        # Initialize data structures
        self.companies = {}
        self.slack_data = {}
        self.telegram_data = {}
        self.calendar_data = {}
        self.hubspot_data = {}
        
        # Performance tracking
        self.stats = {
            'start_time': None,
            'end_time': None,
            'total_processed': 0,
            'total_errors': 0,
            'processing_times': {},
            'memory_usage': []
        }
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Enhanced company matcher
        self.matcher = CompanyMatcher()
    
    def _start_timer(self, operation: str):
        """Start timing an operation"""
        self.stats['processing_times'][operation] = time.time()
    
    def _end_timer(self, operation: str):
        """End timing an operation and log duration"""
        if operation in self.stats['processing_times']:
            duration = time.time() - self.stats['processing_times'][operation]
            # Store the duration, not the start time
            self.stats['processing_times'][operation] = duration
            logger.info(f"{operation} completed in {duration:.2f} seconds")
            return duration
        return 0
    
    def _log_error(self, error: Exception, context: str = ""):
        """Log error with context and increment error counter"""
        with self._lock:
            self.stats['total_errors'] += 1
        logger.error(f"Error in {context}: {str(error)}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
    
    def _safe_file_read(self, file_path: str, encoding: str = 'utf-8') -> Optional[str]:
        """Safely read a file with error handling"""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"File not found: {file_path}")
            return None
        except PermissionError:
            logger.error(f"Permission denied: {file_path}")
            return None
        except UnicodeDecodeError as e:
            logger.warning(f"Encoding error in {file_path}: {e}. Trying with 'latin-1'")
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e2:
                logger.error(f"Failed to read {file_path} with any encoding: {e2}")
                return None
        except Exception as e:
            self._log_error(e, f"reading file {file_path}")
            return None
    
    def _match_calendar_by_email_domain(self, company_name: str, company_info: Dict, attendee_domains: set) -> bool:
        """Match calendar meetings by attendee email domains"""
        if not attendee_domains:
            return False
        
        # Check if any attendee domain matches company domain patterns
        for domain in attendee_domains:
            # 1. Direct domain match
            if company_info.get('calendar_domain') and domain == company_info['calendar_domain'].lower():
                return True
            
            # 2. Company name in domain (e.g., "company.com" matches "Company Inc.")
            company_name_clean = company_name.lower().replace(' ', '').replace('-', '').replace('_', '')
            domain_clean = domain.replace('.com', '').replace('.org', '').replace('.net', '').replace('.io', '')
            
            if company_name_clean in domain_clean or domain_clean in company_name_clean:
                return True
            
            # 3. Check against base company
            if company_info.get('base_company'):
                base_company_clean = company_info['base_company'].lower().replace(' ', '').replace('-', '').replace('_', '')
                if base_company_clean in domain_clean or domain_clean in base_company_clean:
                    return True
            
            # 4. Check against variants
            if company_info.get('variant_type'):
                variants_str = company_info['variant_type']
                if variants_str:
                    variants = [v.strip() for v in variants_str.split(',')]
                    for variant in variants:
                        variant_clean = variant.lower().replace(' ', '').replace('-', '').replace('_', '')
                        if variant_clean in domain_clean or domain_clean in variant_clean:
                            return True
            
            # 5. Fuzzy domain matching for partial matches
            if len(domain_clean) > 3 and len(company_name_clean) > 3:
                # Check if significant portion of company name is in domain
                if len(company_name_clean) >= 4:
                    for i in range(len(company_name_clean) - 3):
                        substring = company_name_clean[i:i+4]
                        if substring in domain_clean:
                            return True
        
        return False
    
    def _match_calendar_by_attendee_domains(self, company_name: str, company_info: Dict, attendee_domains: set) -> bool:
        """Match calendar meetings by attendee email domains - primary matching strategy"""
        if not attendee_domains:
            return False
        
        # Check if any attendee domain matches company domain patterns
        for domain in attendee_domains:
            # 1. Direct domain match with calendar_domain
            if company_info.get('calendar_domain') and domain == company_info['calendar_domain'].lower():
                return True
            
            # 2. Company name in domain (e.g., "company.com" matches "Company Inc.")
            company_name_clean = company_name.lower().replace(' ', '').replace('-', '').replace('_', '')
            domain_clean = domain.replace('.com', '').replace('.org', '').replace('.net', '').replace('.io', '').replace('.co', '')
            
            if company_name_clean in domain_clean or domain_clean in company_name_clean:
                return True
            
            # 3. Check against base company
            if company_info.get('base_company'):
                base_company_clean = company_info['base_company'].lower().replace(' ', '').replace('-', '').replace('_', '')
                if base_company_clean in domain_clean or domain_clean in base_company_clean:
                    return True
            
            # 4. Check against variants
            if company_info.get('variant_type'):
                variants_str = company_info['variant_type']
                if variants_str:
                    variants = [v.strip() for v in variants_str.split(',')]
                    for variant in variants:
                        variant_clean = variant.lower().replace(' ', '').replace('-', '').replace('_', '')
                        if variant_clean in domain_clean or domain_clean in variant_clean:
                            return True
            
            # 5. Fuzzy domain matching for partial matches
            if len(domain_clean) > 3 and len(company_name_clean) > 3:
                # Check if significant portion of company name is in domain
                if len(company_name_clean) >= 4:
                    for i in range(len(company_name_clean) - 3):
                        substring = company_name_clean[i:i+4]
                        if substring in domain_clean:
                            return True
        
        return False
        
    def load_company_mapping(self) -> Dict[str, Any]:
        """Load company mapping from CSV, filtered to only include companies from the provided list"""
        logger.info("Loading company mapping...")
        companies = {}
        
        if not os.path.exists(self.company_mapping_file):
            logger.error(f"Company mapping file not found: {self.company_mapping_file}")
            return companies
        
        # Load the filtered company list
        filtered_companies = self._load_filtered_company_list()
        if not filtered_companies:
            logger.warning("No filtered company list found, processing all companies")
        else:
            logger.info(f"Loaded {len(filtered_companies)} companies from filter list")
            
        with open(self.company_mapping_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                company_name = row['Company Name']
                
                # Only include companies from the filtered list
                if filtered_companies and not self._is_company_in_filtered_list(company_name, filtered_companies):
                    logger.debug(f"Filtering out company: {company_name}")
                    continue
                    
                companies[company_name] = {
                    'full_node_address': row['Full Node Address'],
                    'slack_groups': row['Slack Groups'],
                    'telegram_groups': row['Telegram Groups'],
                    'calendar_domain': row['Calendar Search Domain'],
                    'variant_type': row['Variants'],
                    'base_company': row['Base Company']
                }
        
        logger.info(f"Loaded {len(companies)} companies from mapping file (filtered from provided list)")
        return companies
    
    def _load_filtered_company_list(self) -> List[str]:
        """Load the list of companies to filter for, supporting validator node format"""
        filter_file = "data/company_filter_list.txt"
        if not os.path.exists(filter_file):
            logger.warning(f"Company filter file not found: {filter_file}")
            return []
        
        try:
            with open(filter_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
            
            companies = []
            for line in lines:
                # Handle validator node format: "company_name::hash"
                if '::' in line:
                    company_name = line.split('::')[0].strip()
                    companies.append(company_name)
                else:
                    # Handle plain company name format
                    companies.append(line)
            
            logger.info(f"Loaded {len(companies)} companies from filter list (validator node format supported)")
            return companies
        except Exception as e:
            logger.error(f"Error loading company filter list: {e}")
            return []
    
    def _is_company_in_filtered_list(self, company_name: str, filtered_companies: List[str]) -> bool:
        """Check if a company name matches any company in the filtered list"""
        company_lower = company_name.lower().strip()
        
        for filtered_company in filtered_companies:
            filtered_lower = filtered_company.lower().strip()
            
            # Direct match
            if company_lower == filtered_lower:
                return True
            
            # Check if company name contains the filtered company name
            if filtered_lower in company_lower or company_lower in filtered_lower:
                return True
            
            # Check variants (remove common suffixes/prefixes)
            company_clean = company_lower.replace(' inc', '').replace(' llc', '').replace(' corp', '').replace(' ltd', '').replace(' limited', '').replace(' company', '').replace(' co', '').replace(' group', '').replace(' holdings', '').replace(' enterprises', '').replace(' the ', ' ').strip()
            filtered_clean = filtered_lower.replace(' inc', '').replace(' llc', '').replace(' corp', '').replace(' ltd', '').replace(' limited', '').replace(' company', '').replace(' co', '').replace(' group', '').replace(' holdings', '').replace(' enterprises', '').replace(' the ', ' ').strip()
            
            if company_clean == filtered_clean:
                return True
                
            # Check if cleaned names contain each other
            if filtered_clean in company_clean or company_clean in filtered_clean:
                return True
        
        return False
    
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
                SELECT conv_id, name, type, created, purpose, topic
                FROM conversations
                ORDER BY name
            ''')
            conversations = cursor.fetchall()
            
            for conv_id, name, conv_type, created, purpose, topic in conversations:
                # Get messages for this conversation
                cursor.execute('''
                    SELECT m.author, m.text, m.timestamp, u.real_name
                    FROM messages m
                    LEFT JOIN users u ON m.author = u.id
                    WHERE m.conv_id = ?
                    ORDER BY m.timestamp
                ''', (conv_id,))
                messages = cursor.fetchall()
                
                # Count unique members from messages
                member_count = len(set(msg[0] for msg in messages if msg[0]))
                
                # Skip stage detections for now (table doesn't exist)
                stage_detections = []
                
                slack_data[conv_id] = {
                    'name': name,
                    'member_count': member_count,
                    'creation_date': created,
                    'is_bitsafe': name.endswith('-bitsafe'),
                    'messages': [
                        {
                            'author': author,
                            'text': text,
                            'timestamp': timestamp,
                            'display_name': real_name if real_name else author
                        }
                        for author, text, timestamp, real_name in messages
                    ],
                    'stage_detections': []
                }
            
            logger.info(f"Ingested {len(slack_data)} Slack conversations")
            
        except Exception as e:
            logger.error(f"Error ingesting Slack data: {e}")
        finally:
            conn.close()
            
        return slack_data
    
    def _process_single_chat(self, chat_dir: str, chats_dir: str) -> Optional[Dict[str, Any]]:
        """Process a single chat directory - designed for parallel execution"""
        try:
            chat_path = os.path.join(chats_dir, chat_dir)
            
            # Look for HTML files in the chat directory
            try:
                html_files = [f for f in os.listdir(chat_path) if f.endswith('.html')]
            except (OSError, PermissionError) as e:
                logger.warning(f"Cannot access directory {chat_dir}: {e}")
                return None
            
            if not html_files:
                return None
                
            # Process all HTML files in this chat directory
            chat_messages = []
            chat_participants = set()
            chat_name = chat_dir  # Use directory name as base identifier
            
            for html_file in html_files:
                html_path = os.path.join(chat_path, html_file)
                content = self._safe_file_read(html_path)
                
                if not content:
                    continue
                    
                try:
                    soup = BeautifulSoup(content, 'html.parser')
                except Exception as e:
                    logger.warning(f"Failed to parse HTML in {html_path}: {e}")
                    continue
                
                # Extract messages from this HTML file
                message_divs = soup.find_all('div', class_='message')
                
                # Extract chat name from page header if available
                page_header = soup.find('div', class_='page_header')
                if page_header:
                    header_text = page_header.get_text(strip=True)
                    if header_text and header_text != "Exported Data":
                        chat_name = header_text.replace(" ", "-").lower()
                
                for msg_div in message_divs:
                    try:
                        # Determine message type
                        message_classes = msg_div.get('class', [])
                        is_service = 'service' in message_classes
                        
                        # Extract author
                        author_elem = msg_div.find('div', class_='from_name')
                        author = author_elem.text.strip() if author_elem else "System"
                        
                        # Extract text
                        text_elem = msg_div.find('div', class_='text')
                        text = text_elem.text.strip() if text_elem else ""
                        
                        # For service messages, try to get text from body details
                        if is_service and not text:
                            body_details = msg_div.find('div', class_='body details')
                            if body_details:
                                text = body_details.text.strip()
                        
                        # Extract timestamp
                        date_elem = msg_div.find('div', class_='date')
                        timestamp = date_elem.get('title', '') if date_elem else ""
                        
                        # Extract message ID
                        message_id = msg_div.get('id', '')
                        
                        # Only include messages with meaningful content
                        if text and text not in ["", " "]:
                            chat_messages.append({
                                'author': author,
                                'text': text,
                                'timestamp': timestamp,
                                'message_id': message_id,
                                'message_type': 'service' if is_service else 'regular',
                                'is_service': is_service
                            })
                            
                            # Add to participants if it's a regular message or service message with a person
                            if not is_service or (is_service and author != "System"):
                                chat_participants.add(author)
                    except Exception as e:
                        logger.debug(f"Error processing message in {html_path}: {e}")
                        continue
                
                # Try to extract actual chat name from participants or first message
                if not chat_messages:
                    # Look for participant names in userpics
                    userpics = soup.find_all('div', class_='userpic')
                    for userpic in userpics:
                        initials_elem = userpic.find('div', class_='initials')
                        if initials_elem:
                            initials = initials_elem.text.strip()
                            if initials and len(initials) > 1:
                                chat_participants.add(f"User_{initials}")
            
            # Create a more meaningful chat name if possible
            # Only override chat_name if we didn't extract a company name from page header
            original_chat_name = chat_name
            if chat_participants and not any(indicator in original_chat_name.lower() for indicator in ['company', 'team', 'group', 'channel']):
                participant_list = list(chat_participants)
                
                if len(participant_list) == 1:
                    chat_name = f"{participant_list[0]}-telegram"
                elif len(participant_list) <= 5:
                    # For small groups, use participant names
                    chat_name = f"{'-'.join(participant_list[:3])}-telegram"
                else:
                    # For larger groups, use directory name
                    chat_name = f"{chat_dir}-telegram"
            elif not any(indicator in original_chat_name.lower() for indicator in ['company', 'team', 'group', 'channel']):
                chat_name = f"{chat_dir}-telegram"
            
            # Store the chat data if it has messages
            if chat_messages:
                # Calculate additional statistics
                regular_messages = [m for m in chat_messages if not m['is_service']]
                service_messages = [m for m in chat_messages if m['is_service']]
                
                # Extract unique authors
                unique_authors = list(set(m['author'] for m in chat_messages if m['author'] != "System"))
                
                return {
                    'messages': chat_messages,
                    'message_count': len(chat_messages),
                    'regular_message_count': len(regular_messages),
                    'service_message_count': len(service_messages),
                    'participants': list(chat_participants),
                    'participant_count': len(chat_participants),
                    'unique_authors': unique_authors,
                    'directory': chat_dir,
                    'chat_name': chat_name,
                    'last_message_time': max([m['timestamp'] for m in chat_messages if m['timestamp']], default=""),
                    'first_message_time': min([m['timestamp'] for m in chat_messages if m['timestamp']], default="")
                }
            
            return None
            
        except Exception as e:
            self._log_error(e, f"processing chat {chat_dir}")
            return None

    def ingest_telegram_data(self) -> Dict[str, Any]:
        """Ingest Telegram data from HTML export with parallel processing"""
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
            
        try:
            chat_dirs = [d for d in os.listdir(chats_dir) if os.path.isdir(os.path.join(chats_dir, d))]
        except (OSError, PermissionError) as e:
            logger.error(f"Cannot access chats directory: {e}")
            return telegram_data
        
        # Quick mode: limit to first 100 chats for faster testing
        if self.quick_mode:
            original_count = len(chat_dirs)
            chat_dirs = chat_dirs[:100]
            logger.info(f"QUICK MODE: Processing only first {len(chat_dirs)} of {original_count} chat directories")
        else:
            logger.info(f"Found {len(chat_dirs)} chat directories to process")
        
        processed_count = 0
        error_count = 0
        
        # Process in batches for better memory management
        total_batches = (len(chat_dirs) + self.batch_size - 1) // self.batch_size
        print(f"\n🚀 Starting Telegram processing: {len(chat_dirs)} chats in {total_batches} batches")
        print(f"⚙️  Using {self.max_workers} workers, batch size: {self.batch_size}")
        
        for i in range(0, len(chat_dirs), self.batch_size):
            batch = chat_dirs[i:i + self.batch_size]
            batch_num = i//self.batch_size + 1
            print(f"\n📦 Processing batch {batch_num}/{total_batches} ({len(batch)} chats)")
            
            # Use ProcessPoolExecutor for multiprocessing or ThreadPoolExecutor for threading
            if self.use_multiprocessing:
                with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                    # Submit all tasks in the batch
                    future_to_chat = {
                        executor.submit(process_telegram_chat_worker, chat_dir, chats_dir): chat_dir 
                        for chat_dir in batch
                    }
                    
                    # Process completed tasks
                    for future in as_completed(future_to_chat):
                        chat_dir = future_to_chat[future]
                        try:
                            result = future.result()
                            if result:
                                chat_name = result['chat_name']
                                telegram_data[chat_name] = result
                                processed_count += 1
                                
                                if processed_count % 50 == 0:
                                    print(f"\r🔄 Processed {processed_count} chats so far...", end='', flush=True)
                        except Exception as e:
                            error_count += 1
                            logger.error(f"Error processing chat {chat_dir}: {e}")
            else:
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    # Submit all tasks in the batch
                    future_to_chat = {
                        executor.submit(self._process_single_chat, chat_dir, chats_dir): chat_dir 
                        for chat_dir in batch
                    }
                    
                    # Process completed tasks
                    for future in as_completed(future_to_chat):
                        chat_dir = future_to_chat[future]
                        try:
                            result = future.result()
                            if result:
                                chat_name = result['chat_name']
                                telegram_data[chat_name] = result
                                processed_count += 1
                                
                                if processed_count % 50 == 0:
                                    print(f"\r🔄 Processed {processed_count} chats so far...", end='', flush=True)
                        except Exception as e:
                            error_count += 1
                            self._log_error(e, f"processing chat {chat_dir}")
            
            # Log progress
            print(f"✅ Completed batch {batch_num}. Processed: {processed_count}, Errors: {error_count}")
        
        print(f"\n🎉 Telegram processing complete!")
        print(f"📊 Results: {processed_count} chats processed, {error_count} errors")
        return telegram_data
    
    def ingest_calendar_data(self) -> Dict[str, Any]:
        """Ingest Google Calendar data"""
        logger.info("Ingesting Calendar data...")
        calendar_data = {}
        
        try:
            # Try real Google Calendar integration first
            try:
                from .integrations.google_calendar_integration import GoogleCalendarIntegration
                calendar = GoogleCalendarIntegration()
                use_mock = False
            except ImportError:
                # Fall back to mock integration for testing
                from .integrations.mock_calendar_integration import MockCalendarIntegration
                calendar = MockCalendarIntegration()
                use_mock = True
                logger.info("Using mock calendar integration for testing")
            
            if calendar.authenticate():
                # Get meetings for the past 180 days
                end_date = datetime.now()
                start_date = end_date - timedelta(days=180)
                
                # Get all meetings
                meetings = calendar.get_meetings(start_date, end_date)
                
                # Match meetings to companies using attendee domain matching
                for meeting in meetings:
                    summary = meeting.get('summary', '')
                    description = meeting.get('description', '')
                    attendees = meeting.get('attendees', [])
                    
                    # Skip large group meetings (10+ attendees) - these are not business meetings
                    if len(attendees) >= 10:
                        continue
                    
                    # Extract attendee emails and domains
                    attendee_emails = []
                    attendee_domains = set()
                    for attendee in attendees:
                        if isinstance(attendee, dict) and 'email' in attendee:
                            email = attendee['email']
                            attendee_emails.append(email)
                            # Extract domain from email
                            if '@' in email:
                                domain = email.split('@')[1].lower()
                                attendee_domains.add(domain)
                    
                    # Primary matching strategy: Attendee domain matching (if external attendees)
                    matched_company = None
                    if attendee_domains:
                        for company_name, company_info in self.companies.items():
                            if self._match_calendar_by_attendee_domains(company_name, company_info, attendee_domains):
                                matched_company = company_name
                                break
                    
                    # Fallback: Text-based matching for meetings with company names in title
                    if not matched_company:
                        meeting_text = f"{summary} {description} {' '.join(attendee_emails)}".lower()
                        for company_name, company_info in self.companies.items():
                            if self.matcher.match_company_to_channel(company_name, company_info, meeting_text, 'calendar'):
                                matched_company = company_name
                                break
                    
                    # Add meeting to matched company
                    if matched_company:
                        if matched_company not in calendar_data:
                            calendar_data[matched_company] = []
                        
                        calendar_data[matched_company].append({
                            'title': meeting.get('summary', ''),
                            'description': meeting.get('description', ''),
                            'start_time': meeting.get('start_time', ''),
                            'end_time': meeting.get('end_time', ''),
                            'location': meeting.get('location', ''),
                            'attendees': meeting.get('attendees', []),
                            'meeting_url': meeting.get('meeting_url', ''),
                            'calendar_id': meeting.get('calendar_id', ''),
                            'html_link': meeting.get('html_link', '')
                        })
                        
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
        
        try:
            from .integrations.hubspot_export_integration import HubSpotExportIntegration
            
            # Initialize HubSpot export integration
            hubspot = HubSpotExportIntegration()
            
            if hubspot.load_export_files():
                # Get deals grouped by company
                company_deals = hubspot.get_deals_by_company()
                
                # Convert to the format expected by the ETL system
                for company_name, deals in company_deals.items():
                    hubspot_data[company_name] = {
                        'deals': deals,
                        'deal_count': len(deals),
                        'total_value': sum(float(deal.get('deal_value', 0) or 0) for deal in deals),
                        'active_deals': len([d for d in deals if d.get('deal_stage', '').lower() not in ['closed won', 'closed lost', 'closed']]),
                    }
                
                logger.info(f"Ingested HubSpot data for {len(hubspot_data)} companies")
            else:
                logger.warning("No HubSpot export files found or failed to load")
            
        except Exception as e:
            logger.error(f"Error ingesting HubSpot data: {e}")
            
        return hubspot_data
    
    def match_data_to_companies(self) -> Dict[str, Any]:
        """Match all data sources to companies"""
        logger.info("Matching data to companies...")
        
        matched_data = {}
        excluded_count = 0
        
        for company_name, company_info in self.companies.items():
            # Skip excluded companies (internal companies)
            if company_name.lower() in self.excluded_companies:
                excluded_count += 1
                logger.debug(f"Excluding internal company: {company_name}")
                continue
            matched_data[company_name] = {
                'company_info': company_info,
                'slack_channels': [],
                'telegram_chats': [],
                'calendar_meetings': [],
                'hubspot_deals': []
            }
            
            # Match Slack channels using enhanced matcher
            slack_matches = self.matcher.find_best_matches(
                company_name, company_info, self.slack_data, 'slack'
            )
            
            for conv_id, confidence in slack_matches:
                slack_info = self.slack_data[conv_id]
                matched_data[company_name]['slack_channels'].append({
                    'conv_id': conv_id,
                    'name': slack_info['name'],
                    'message_count': len(slack_info['messages']),
                    'stage_detection_count': len(slack_info['stage_detections']),
                    'match_confidence': confidence,
                    'data': slack_info
                })
            
            # Match Telegram chats using enhanced matcher
            telegram_matches = self.matcher.find_best_matches(
                company_name, company_info, self.telegram_data, 'telegram'
            )
            
            for chat_name, confidence in telegram_matches:
                telegram_info = self.telegram_data[chat_name]
                matched_data[company_name]['telegram_chats'].append({
                    'chat_name': chat_name,
                    'message_count': len(telegram_info['messages']),
                    'match_confidence': confidence,
                    'data': telegram_info
                })
            
            # Match Calendar meetings (already matched during ingestion)
            if company_name in self.calendar_data:
                matched_data[company_name]['calendar_meetings'].extend(self.calendar_data[company_name])
            
            # Match HubSpot deals using enhanced fuzzy matching
            for deal_company, deal_info in self.hubspot_data.items():
                # Use the enhanced company matcher for better HubSpot matching
                if self.matcher.match_company_to_channel(company_name, company_info, deal_company, 'hubspot'):
                    matched_data[company_name]['hubspot_deals'].append(deal_info)
        
        logger.info(f"Matched data for {len(matched_data)} companies")
        logger.info(f"Excluded {excluded_count} internal companies")
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
        """Run the complete ETL process with comprehensive error handling and performance tracking"""
        self.stats['start_time'] = time.time()
        print("\n" + "="*60)
        print("🚀 STARTING ETL DATA INGESTION")
        print("="*60)
        logger.info("Starting ETL data ingestion...")
        
        try:
            # Load company mapping
            self._start_timer("company_mapping")
            self.companies = self.load_company_mapping()
            self._end_timer("company_mapping")
            
            # Ingest all data sources with error handling
            self._start_timer("slack_ingestion")
            try:
                self.slack_data = self.ingest_slack_data()
            except Exception as e:
                self._log_error(e, "Slack data ingestion")
                self.slack_data = {}
            self._end_timer("slack_ingestion")
            
            self._start_timer("telegram_ingestion")
            try:
                self.telegram_data = self.ingest_telegram_data()
            except Exception as e:
                self._log_error(e, "Telegram data ingestion")
                self.telegram_data = {}
            self._end_timer("telegram_ingestion")
            
            self._start_timer("calendar_ingestion")
            try:
                self.calendar_data = self.ingest_calendar_data()
            except Exception as e:
                self._log_error(e, "Calendar data ingestion")
                self.calendar_data = {}
            self._end_timer("calendar_ingestion")
            
            self._start_timer("hubspot_ingestion")
            try:
                self.hubspot_data = self.ingest_hubspot_data()
            except Exception as e:
                self._log_error(e, "HubSpot data ingestion")
                self.hubspot_data = {}
            self._end_timer("hubspot_ingestion")
            
            # Match data to companies
            self._start_timer("data_matching")
            try:
                matched_data = self.match_data_to_companies()
            except Exception as e:
                self._log_error(e, "Data matching")
                matched_data = {}
            self._end_timer("data_matching")
            
            # Generate summary statistics
            self._start_timer("statistics_generation")
            try:
                stats = self.generate_summary_stats(matched_data)
            except Exception as e:
                self._log_error(e, "Statistics generation")
                stats = self._generate_fallback_stats()
            self._end_timer("statistics_generation")
            
            # Add performance statistics to output
            self.stats['end_time'] = time.time()
            self.stats['total_duration'] = self.stats['end_time'] - self.stats['start_time']
            
            # Create final output structure
            output_data = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'etl_version': '1.0.0',
                    'data_sources': ['slack', 'telegram', 'calendar', 'hubspot'],
                    'total_companies': len(self.companies),
                    'performance_stats': {
                        'total_duration_seconds': self.stats['total_duration'],
                        'processing_times': self.stats['processing_times'],
                        'total_errors': self.stats['total_errors'],
                        'max_workers': self.max_workers,
                        'batch_size': self.batch_size
                    }
                },
                'statistics': stats,
                'companies': matched_data
            }
            
            # Ensure output directories exist
            os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
            os.makedirs(os.path.dirname(self.archive_file), exist_ok=True)
            
            # Generate text output for NotebookLM (no JSON needed)
            logger.info("Generating text output for NotebookLM...")
            self._start_timer("output_writing")
            try:
                formatter = ETLTextFormatter()
                text_output = formatter.format_etl_output(output_data)
                
                # Write to main file (easy access for NotebookLM)
                with open(self.output_file, 'w', encoding='utf-8') as f:
                    f.write(text_output)
                
                # Write to timestamped archive file
                with open(self.archive_file, 'w', encoding='utf-8') as f:
                    f.write(text_output)
                
                logger.info(f"ETL completed! Text output written to {self.output_file}")
                logger.info(f"Archived copy written to {self.archive_file}")
                
                # End timer for successful output writing
                self._end_timer("output_writing")
                    
            except Exception as e:
                self._log_error(e, "Writing output file")
                # Try to write a minimal text output file
                fallback_text = f"""ETL ERROR REPORT
Generated: {datetime.now().isoformat()}
Error: {str(e)}

This is a fallback output due to an error during text generation.
The ETL process encountered an issue and could not complete normally.

Companies processed: {len(matched_data)}
"""
                with open(self.output_file + '.fallback', 'w', encoding='utf-8') as f:
                    f.write(fallback_text)
                with open(self.archive_file + '.fallback', 'w', encoding='utf-8') as f:
                    f.write(fallback_text)
                logger.error(f"Wrote fallback output to {self.output_file}.fallback")
                logger.error(f"Wrote fallback archive to {self.archive_file}.fallback")
                # End timer for failed output writing
                self._end_timer("output_writing")
            
            # Log final statistics
            print("\n" + "="*60)
            print("🎉 ETL PROCESS COMPLETED SUCCESSFULLY!")
            print("="*60)
            print(f"⏱️  Total Duration: {self.stats['total_duration']:.2f} seconds")
            print(f"📊 Companies Processed: {len(matched_data)}")
            print(f"❌ Total Errors: {self.stats['total_errors']}")
            print(f"📈 Data Coverage:")
            print(f"   • Slack: {stats.get('companies_with_slack', 0)} companies")
            print(f"   • Telegram: {stats.get('companies_with_telegram', 0)} companies")
            print(f"   • Calendar: {stats.get('companies_with_calendar', 0)} companies")
            print(f"   • HubSpot: {stats.get('companies_with_hubspot', 0)} companies")
            print(f"📁 Output File: {self.output_file}")
            print("="*60)
            
            logger.info(f"ETL completed in {self.stats['total_duration']:.2f} seconds")
            logger.info(f"Processed {len(matched_data)} companies")
            logger.info(f"Total errors encountered: {self.stats['total_errors']}")
            logger.info(f"Slack: {stats.get('companies_with_slack', 0)} companies")
            logger.info(f"Telegram: {stats.get('companies_with_telegram', 0)} companies")
            logger.info(f"Calendar: {stats.get('companies_with_calendar', 0)} companies")
            logger.info(f"HubSpot: {stats.get('companies_with_hubspot', 0)} companies")
            
        except Exception as e:
            self._log_error(e, "ETL process")
            logger.error("ETL process failed completely")
            raise
    
    def _generate_fallback_stats(self) -> Dict[str, Any]:
        """Generate basic statistics when the main stats generation fails"""
        return {
            'total_companies': len(self.companies),
            'companies_with_slack': len([c for c in self.companies.values() if c.get('slack')]),
            'companies_with_telegram': len([c for c in self.companies.values() if c.get('telegram')]),
            'companies_with_calendar': len([c for c in self.companies.values() if c.get('calendar')]),
            'companies_with_hubspot': len([c for c in self.companies.values() if c.get('hubspot')]),
            'total_slack_channels': len(self.slack_data),
            'total_telegram_chats': len(self.telegram_data),
            'total_calendar_meetings': sum(len(c.get('meetings', [])) for c in self.calendar_data.values()),
            'total_hubspot_deals': len(self.hubspot_data)
        }

def main():
    """Main function"""
    etl = DataETL()
    etl.run_etl()

if __name__ == "__main__":
    main()
