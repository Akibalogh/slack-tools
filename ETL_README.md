# ETL Data Ingestion System

A comprehensive Extract, Transform, Load (ETL) system that ingests all available data sources and outputs machine-readable JSON format for analysis.

## Data Sources

The ETL system ingests data from the following sources:

### 1. **Slack Data** (`data/slack/repsplit.db`)
- **Source**: SQLite database with Slack messages, users, and stage detections
- **Content**: Private channels ending with '-bitsafe', messages, stage detections
- **Format**: Structured database with conversations, messages, users, and stage_detections tables

### 2. **Telegram Data** (`data/telegram/DataExport_2025-08-19/`)
- **Source**: HTML export from Telegram with 3984 chats
- **Content**: Group conversations, messages, timestamps
- **Format**: HTML files parsed to extract chat names, authors, messages, and timestamps

### 3. **Google Calendar Data** (via API)
- **Source**: Google Calendar API integration
- **Content**: Meeting data with company names and key people
- **Format**: Events with titles, descriptions, attendees, and timestamps
- **Scope**: Past 180 days of meeting data

### 4. **HubSpot CRM Data** (`data/hubspot/hubspot-crm-exports-all-deals-2025-08-11-1.csv`)
- **Source**: CSV export from HubSpot CRM
- **Content**: Deal pipeline data with 231 companies
- **Format**: Structured CSV with deal information, stages, values, and ownership

### 5. **Company Mapping** (`data/company_mapping.csv`)
- **Source**: Central mapping file with 113 companies
- **Content**: Company names, variants, Slack groups, Telegram groups, calendar domains
- **Format**: CSV with comprehensive company metadata

## Output Format

The ETL system outputs a machine-readable JSON file (`data/etl_output.json`) with the following structure:

```json
{
  "metadata": {
    "generated_at": "2025-01-10T00:00:00",
    "etl_version": "1.0.0",
    "data_sources": ["slack", "telegram", "calendar", "hubspot"],
    "total_companies": 113
  },
  "statistics": {
    "total_companies": 113,
    "companies_with_slack": 47,
    "companies_with_telegram": 6,
    "companies_with_calendar": 12,
    "companies_with_hubspot": 89,
    "total_slack_channels": 96,
    "total_telegram_chats": 6,
    "total_calendar_meetings": 45,
    "total_hubspot_deals": 231,
    "data_coverage": {
      "company_name": {
        "sources_count": 3,
        "has_slack": true,
        "has_telegram": false,
        "has_calendar": true,
        "has_hubspot": true
      }
    }
  },
  "companies": {
    "company_name": {
      "company_info": {
        "full_node_address": "company::hash",
        "slack_groups": "company-bitsafe",
        "telegram_groups": "company",
        "calendar_domain": "company.com",
        "variant_type": "base",
        "base_company": "company"
      },
      "slack_channels": [
        {
          "conv_id": "C1234567890",
          "name": "company-bitsafe",
          "message_count": 150,
          "stage_detection_count": 25,
          "data": {
            "messages": [...],
            "stage_detections": [...]
          }
        }
      ],
      "telegram_chats": [
        {
          "chat_name": "Company <> BitSafe",
          "message_count": 77,
          "data": {
            "messages": [...]
          }
        }
      ],
      "calendar_meetings": [
        {
          "summary": "Meeting with Company",
          "description": "Discussion about BitSafe",
          "start_time": "2025-01-10T10:00:00Z",
          "end_time": "2025-01-10T11:00:00Z",
          "attendees": ["aki@bitsafe.com", "contact@company.com"],
          "calendar_id": "primary"
        }
      ],
      "hubspot_deals": [
        {
          "deal_name": "Company BitSafe Deal",
          "deal_stage": "Closed Won",
          "deal_value": "$50000",
          "close_date": "2025-01-15",
          "owner": "Aki",
          "pipeline": "BitSafe Pipeline"
        }
      ]
    }
  }
}
```

## Usage

### Quick Start

```bash
# Run the complete ETL process
python run_etl.py
```

### Individual Components

```bash
# Run only ETL ingestion
python etl_data_ingestion.py

# Run only data analysis
python analyze_etl_data.py
```

## Scripts

### 1. `etl_data_ingestion.py`
Main ETL script that:
- Loads company mapping from CSV
- Ingests data from all sources (Slack, Telegram, Calendar, HubSpot)
- Matches data to companies using fuzzy matching
- Generates comprehensive JSON output
- Creates summary statistics

### 2. `analyze_etl_data.py`
Analysis script that:
- Loads and parses the ETL output
- Generates data coverage reports
- Identifies companies with multiple data sources
- Exports company summary to CSV
- Provides data quality metrics

### 3. `run_etl.py`
Runner script that:
- Checks for required files
- Executes ETL ingestion
- Runs data analysis
- Reports on generated files

## Output Files

- **`data/etl_output.json`**: Complete ETL output with all data
- **`data/company_data_summary.csv`**: Summary of company data coverage
- **`etl_ingestion.log`**: ETL process logs

## Data Quality Metrics

The system provides several data quality metrics:

- **Data Coverage**: Percentage of companies with data from each source
- **Source Distribution**: Number of companies with single vs. multiple sources
- **Completeness Score**: Overall data completeness percentage
- **Company Matching**: Success rate of matching data to companies

## Machine-Readable Benefits

The JSON output format provides several advantages for machine processing:

1. **Structured Data**: All data is organized in a consistent, hierarchical structure
2. **Metadata**: Includes generation timestamps, version info, and statistics
3. **Complete Context**: Each company includes all available data sources
4. **Searchable**: Easy to search and filter by company, source, or data type
5. **Extensible**: Easy to add new data sources or fields
6. **Standard Format**: JSON is universally supported by all programming languages

## Example Use Cases

### 1. Commission Analysis
```python
import json

# Load ETL data
with open('data/etl_output.json', 'r') as f:
    data = json.load(f)

# Find companies with Slack data
slack_companies = [name for name, company in data['companies'].items() 
                  if company['slack_channels']]

# Get stage detections for a specific company
company_data = data['companies']['chainsafe']
stage_detections = company_data['slack_channels'][0]['data']['stage_detections']
```

### 2. Data Coverage Analysis
```python
# Get coverage statistics
stats = data['statistics']
print(f"Slack coverage: {stats['companies_with_slack']}/{stats['total_companies']}")

# Find companies with multiple sources
multi_source = [name for name, company in data['companies'].items()
               if len([s for s in ['slack_channels', 'telegram_chats', 'calendar_meetings', 'hubspot_deals']
                      if company[s]]) >= 2]
```

### 3. Meeting Analysis
```python
# Find all calendar meetings
all_meetings = []
for company_data in data['companies'].values():
    all_meetings.extend(company_data['calendar_meetings'])

# Filter meetings by date range
recent_meetings = [m for m in all_meetings 
                  if m['start_time'] > '2025-01-01']
```

## Requirements

- Python 3.7+
- Required packages: `aiohttp`, `beautifulsoup4`, `python-dotenv`
- Google Calendar API credentials (for calendar data)
- Slack API token (for Slack data)
- Access to data files in `data/` directory

## Error Handling

The ETL system includes comprehensive error handling:

- **Missing Files**: Gracefully handles missing data sources
- **API Failures**: Continues processing if APIs are unavailable
- **Data Parsing**: Logs warnings for unparseable data
- **Company Matching**: Uses fuzzy matching to handle name variations

## Performance

- **Incremental Processing**: Only processes new/changed data
- **Memory Efficient**: Streams large datasets
- **Parallel Processing**: Uses async/await for API calls
- **Caching**: Caches API responses to avoid redundant calls

