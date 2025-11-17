# Product Requirements Document: Sales Commission Calculator

## Overview
The Sales Commission Calculator (RepSplit) is a comprehensive system for analyzing sales activities across Slack and Telegram channels to calculate commission splits for the sales team.

## Core Requirements

### 1. Company Processing Scope
- **Targeted Analysis**: The system processes only a specific list of companies defined in `data/company_mapping.csv`
- **Company Variants**: All variants are processed including base companies, minter variants, mainnet variants, validator variants, and other special variants
- **Validator Node Input Method**: The system accepts company lists in the format of validator nodes with company names and variants (e.g., "allnodes::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2"). The system automatically extracts company names from this format and matches them against the company mapping database
- **HubSpot Deal Filtering**: Only HubSpot deals with "commit" or "closed won" status are processed, as these represent completed deals that should be analyzed for commission calculation
- **Comprehensive Mapping**: The `data/company_mapping.csv` file contains complete mapping of all 113 companies with their:
  - **Slack Groups**: Actual Slack channel names (e.g., "allnodes-bitsafe", "alumlabs-minter")
  - **Telegram Groups**: Actual Telegram group names (e.g., "allnodes", "alum-labs")
  - **Calendar Search Domain**: Email domain used to search calendar invites (e.g., "allnodes.com", "alumlabs.com")
  - **Calendar Meeting Filtering**: Large group meetings (10+ attendees) are excluded as these are typically not business meetings with specific companies
  - **Full Node Addresses**: Complete node addresses with hashes
  - **Variant Types**: Classification of variants (base, minter, mainnet, validator, canton, wallet, etc.)
  - **Base Company**: Company name for grouping variants with identical commission data
- **Variant Types**: Includes base, minter, mainnet, validator, canton, wallet, and other special variants
- **Unified Commission Data**: All variants of the same base company must show exactly the same commission splits, stage breakdowns, and rationale
- **Separate Output Rows**: Each variant should appear as a separate row in the deal rationale output with its respective full node address
- **Full Node Address Format**: First column must be the full node address in format `company_name::hash`

### 2. Sales Representative Constraints
- **Authorized Sales Reps**: Only Aki, Addie, Amy, and Mayank can earn full commission and move deals forward
- **Non-Sales Reps**: Kadeem, Prateek, and Will are excluded from sales rep status and their contributions are weighted at 50%
- **Most Likely Owner**: The "Most Likely Owner" column must always show a sales rep's name, never "Split"

### 3. Output Requirements
- **Output Directory**: All output files must be generated in the `output/` directory
- **File Format**: All output files must be in CSV format
- **Required Files**: 
  - `deal_rationale.csv` (primary output)
  - `deal_splits.csv`
  - `person_rollup.csv`
  - `deal_outline.txt`
  - Individual justification files in `output/justifications/`

### 4. Data Sources
- **Slack Channels**: Private channels ending with `-bitsafe`, `-minter`, or `-mainnet*`
- **Telegram Conversations**: Company-specific Telegram groups identified by company name
- **Google Calendar**: Meeting data for in-person interactions
- **HubSpot CRM**: Deal data filtered to only include "commit" or "closed won" status deals
- **Database**: SQLite database (`repsplit.db`) for persistent storage

### 5. Commission Calculation Logic
- **Stage-Based Weights**: Different sales stages have different commission weights
- **Participation Tracking**: Tracks team member involvement across all sales stages
- **Rounding**: Percentages rounded to nearest 25% (0%, 25%, 50%, 75%, 100%)
- **Contestation Levels**: Identifies clear ownership vs. contested deals
- **Channel Prioritization**: When multiple channels exist for a company (Slack and Telegram), the system prioritizes Slack channels for commission calculation as they contain more structured sales data
- **Slack Channel Detection**: Slack channels are identified by IDs starting with 'C' (e.g., C094MRJ3669)
- **Telegram Fallback**: If no Slack channels exist, the system falls back to Telegram channels for commission calculation

### 6. Company Name Normalization
- **Suffix Removal**: Automatically removes `-bitsafe`, `-minter`, `-mainnet-1`, `-mainnet1` suffixes
- **Case Insensitive**: Company name matching is case-insensitive
- **Unified Data**: All variants of a company (base, minter, mainnet) show the same commission data

## Technical Implementation

### Company Mapping File Structure
The `data/company_mapping.csv` file serves as the authoritative source for all company information:

| Column | Description | Example |
|--------|-------------|---------|
| Company Name | Full company name as it appears in the system | "allnodes", "alum-labs-minter" |
| Full Node Address | Complete node address with hash | "allnodes::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2" |
| Slack Groups | Actual Slack channel names | "allnodes-bitsafe", "alumlabs-minter" |
| Telegram Groups | Actual Telegram group names | "allnodes", "alum-labs" |
| Calendar Search Domain | Email domain for calendar invite searches | "allnodes.com", "alumlabs.com" |
| Variants | Type of company variant | "base", "minter", "mainnet", "validator", "canton", "wallet" |
| Base Company | Company name for grouping variants | "allnodes", "alum-labs" |

### Database Schema
- `conversations`: Slack channel information
- `messages`: Slack message data
- `telegram_messages`: Telegram conversation data
- `users`: Team member information
- `stage_detections`: Sales stage identification

### Key Methods
- `run_analysis()`: Main analysis engine with hardcoded company filtering and variant grouping
- `calculate_commission_splits()`: Commission calculation logic
- `generate_justification()`: Detailed justification generation
- `generate_rationale_csv()`: CSV output generation

### Company Variant Handling
- **Grouping Logic**: Companies are grouped by base name (removing suffixes like `-minter`)
- **Variant Pattern**: Only base companies (e.g., "allnodes") and their minter variants (e.g., "allnodes-minter") are processed
- **Excluded Variants**: Mainnet, validator, and other special variants are excluded from processing
- **Unified Analysis**: Commission splits are calculated once per base company and applied to base and minter variants
- **Data Consistency**: Base companies and their minter variants show identical commission data
- **Output Representation**: Each processed variant appears as a separate row in the output with its own full node address, but identical commission data

### Performance Features
- Structured JSON logging with rotation
- Database connection pooling
- Performance monitoring and metrics
- Data freshness validation

## Current Status
✅ **Implemented**: Hardcoded company list filtering
✅ **Implemented**: Company name normalization and suffix removal
✅ **Implemented**: Company variants unified data (minter/mainnet variants show same commission data)
✅ **Implemented**: Separate output rows for each variant (when variants exist)
✅ **Implemented**: Sales rep constraints and authorization
✅ **Implemented**: Full node address as first column
✅ **Implemented**: Most likely owner showing sales rep names only
✅ **Implemented**: Output directory structure and CSV format
✅ **Implemented**: Slack and Telegram data integration
✅ **Implemented**: Channel prioritization logic (Slack over Telegram for commission calculation)
✅ **Implemented**: Central mapping table for company name normalization
✅ **Fixed**: Commission calculation bug where Telegram channels were incorrectly used for commission calculation
✅ **Fixed**: Fuzzy matching algorithm bug causing incorrect channel-to-company matches

**Note**: Currently the dataset contains primarily `-bitsafe` channels. The system processes only base companies and `-minter` variants, excluding mainnet, validator, and other special variants. Base companies and their minter variants will show identical commission data in separate output rows.

## ETL and Processing Architecture

### 1. Modular ETL System
- **ETL Data Ingestion**: Standalone system for extracting, transforming, and loading data from multiple sources
- **Commission Processing**: Separate system for calculating commission splits and generating outputs
- **Flexible Execution**: Ability to run ETL only, commission processing only, or both sequentially

### 2. ETL System Features
- **Multi-Source Ingestion**: Slack, Telegram, Google Calendar, HubSpot data
- **Parallel Processing**: Multi-threaded processing for optimal performance
- **Error Handling**: Comprehensive error recovery and logging
- **Output Format**: Human-readable text format (`output/etl_output.txt`) optimized for NotebookLM analysis
- **Performance Monitoring**: Detailed timing and statistics tracking

### 3. Commission Processing System
- **Data Input**: Reads from ETL output text file
- **Weight Determination**: Calculates commission weights based on sales activities
- **Output Generation**: Creates CSV files and justification documents
- **Company Mapping**: Uses centralized company mapping for variant handling

### 4. Execution Modes
- **ETL Only**: `python src/etl/etl_data_ingestion.py` - Ingests and processes data sources
- **Commission Only**: `python analysis/commission_processor.py` - Processes ETL output for commission calculation
- **Full Pipeline**: `python run_full_analysis.py` - Runs both ETL and commission processing sequentially

### 5. Data Flow
```
Data Sources → ETL System → etl_output.txt → Commission Processor → CSV Outputs
                                    ↓
                            NotebookLM Analysis
                            (Intelligent Deal Analysis)
```

### 6. NotebookLM Integration
- **Purpose**: Enable conversational AI analysis of deal data
- **Documentation Package**: Comprehensive business context, deal stages, sales team structure, company mapping, and data source documentation
- **Output Organization**: 
  - `output/notebooklm/` - All files for NotebookLM analysis
  - `output/analysis/` - Commission analysis outputs (separate from NotebookLM files)
- **File Management**:
  - **Main File**: `output/notebooklm/etl_output.txt` - Always the latest ETL output for easy NotebookLM upload
  - **Archive**: `output/notebooklm/archive/` - Contains timestamped versions (e.g., `etl_output_YYYYMMDD_HHMMSS.txt`)
  - **Automatic Organization**: ETL creates both main file and timestamped archive on each run
- **File Size Optimization**: 
  - **Company Filtering**: Reduces output file size by processing only specified companies (96 vs 111 companies)
  - **HubSpot Deal Filtering**: Further reduces size by including only commit/closed won deals
  - **NotebookLM Limits**: Optimized file size ensures compatibility with NotebookLM's file size restrictions
  - **Efficient Upload**: Smaller files enable faster upload and better performance in NotebookLM analysis
- **Capabilities**: Deal stage determination, ownership identification, commission split recommendations, data quality analysis

### 7. Expanded Data Output for NotebookLM
- **Complete Conversations**: All messages from Slack and Telegram channels (not just summaries)
- **Full Message Content**: No truncation of message text to preserve context and nuance
- **Comprehensive Metadata**: Complete company information, participant details, and conversation analysis
- **Detailed Meeting Data**: Full calendar meeting information including descriptions and attendees
- **Complete Deal Information**: All HubSpot deal details including stages, values, and descriptions
- **Conversation Analysis**: Message counts, participant analysis, date ranges, and communication patterns
- **Sales Stage Indicators**: Detailed breakdown of deal stages and activity levels
- **Key Participants**: Complete list of all conversation participants across all channels
- **AI-Driven Analysis**: NotebookLM analyzes all conversation data to make its own intelligent determinations about:
  - Deal stages and progression
  - Most likely deal owners based on conversation patterns
  - Important moments and decision points in customer relationships
  - Sales team involvement and contribution levels
  - Customer sentiment and engagement patterns

## Future Enhancements
- Dynamic company list loading from external sources
- Additional data source integrations
- Enhanced commission calculation algorithms
- Real-time data updates and notifications
- Web-based dashboard for ETL monitoring
- API endpoints for data access
