# ETL Data Ingestion System

A comprehensive Extract, Transform, Load (ETL) system for processing multi-source data including Slack, Telegram, Google Calendar, and HubSpot data.

## Overview

The ETL system ingests data from multiple sources, normalizes it, and outputs a unified JSON format for analysis and reporting. It's designed to handle large volumes of data efficiently with robust error handling and performance optimizations.

## Features

- **Multi-Source Data Ingestion**: Slack, Telegram, Google Calendar, HubSpot
- **Parallel Processing**: Multi-threaded processing for optimal performance
- **Batch Processing**: Memory-efficient processing of large datasets
- **Comprehensive Error Handling**: Graceful handling of missing data and errors
- **Real-time Progress Tracking**: Visual progress indicators and detailed logging
- **Performance Monitoring**: Detailed timing and statistics for all operations
- **Flexible Configuration**: Configurable workers and batch sizes

## Data Sources

### 1. Slack Data
- **Source**: SQLite database (`data/slack/repsplit.db`)
- **Content**: Channel messages, user information, timestamps
- **Status**: Optional (gracefully handles missing database)

### 2. Telegram Data
- **Source**: HTML export files (`data/telegram/DataExport_YYYY-MM-DD/`)
- **Content**: Chat messages, participants, metadata
- **Processing**: 3,958+ chat directories with parallel processing
- **Performance**: ~87 seconds for full processing

### 3. Google Calendar Data
- **Source**: Google Calendar API
- **Content**: Meeting information, attendees, schedules
- **Status**: Optional (requires API credentials)

### 4. HubSpot Data
- **Source**: CSV export files (`data/hubspot/`)
- **Content**: Deal information, contact data
- **Status**: Optional (gracefully handles missing files)

## Directory Structure

```
src/etl/
├── README.md                    # This documentation
├── etl_data_ingestion.py       # Main ETL script
└── google_calendar_integration.py  # Calendar API integration

data/
├── company_mapping.csv         # Company mapping configuration
├── etl_output.json            # Generated output file
├── etl_ingestion.log          # Processing logs
├── slack/                     # Slack data directory
├── telegram/                  # Telegram export directory
├── calendar/                  # Calendar data directory
└── hubspot/                   # HubSpot data directory
```

## Usage

### Basic Usage

```bash
# Run from project root
python src/etl/etl_data_ingestion.py
```

### Configuration

The ETL system can be configured by modifying the `DataETL` class parameters:

```python
# Default configuration
etl = DataETL(
    max_workers=4,      # Number of parallel workers
    batch_size=100      # Chats per batch
)

# High-performance configuration
etl = DataETL(
    max_workers=8,      # More workers for faster processing
    batch_size=200      # Larger batches for better throughput
)
```

## Output Format

The ETL system generates a comprehensive JSON output with the following structure:

```json
{
  "metadata": {
    "generated_at": "2025-09-13T14:21:34.037Z",
    "etl_version": "1.0.0",
    "data_sources": ["slack", "telegram", "calendar", "hubspot"],
    "total_companies": 113,
    "performance_stats": {
      "total_duration_seconds": 87.20,
      "processing_times": {
        "company_mapping": 0.00,
        "telegram_ingestion": 86.95,
        "calendar_ingestion": 0.00,
        "hubspot_ingestion": 0.00,
        "data_matching": 0.24,
        "statistics_generation": 0.00,
        "output_writing": 0.13
      },
      "total_errors": 0,
      "max_workers": 4,
      "batch_size": 100
    }
  },
  "statistics": {
    "total_companies": 113,
    "companies_with_slack": 0,
    "companies_with_telegram": 45,
    "companies_with_calendar": 0,
    "companies_with_hubspot": 0,
    "total_slack_channels": 0,
    "total_telegram_chats": 1351,
    "total_calendar_meetings": 0,
    "total_hubspot_deals": 0
  },
  "companies": {
    "company_name": {
      "slack": { /* Slack data */ },
      "telegram": { /* Telegram data */ },
      "calendar": { /* Calendar data */ },
      "hubspot": { /* HubSpot data */ }
    }
  }
}
```

## Performance Characteristics

### Telegram Processing
- **Total Chats**: 3,958 directories
- **Processing Time**: ~87 seconds
- **Parallel Workers**: 4 (configurable)
- **Batch Size**: 100 chats per batch
- **Memory Usage**: Optimized with batch processing
- **Error Rate**: 0% (robust error handling)

### Performance Optimizations
1. **Parallel Processing**: Multiple threads process different chat directories simultaneously
2. **Batch Processing**: Memory-efficient processing in configurable batches
3. **Safe File Reading**: Multiple encoding attempts for problematic files
4. **Progress Tracking**: Real-time progress updates every 50 chats
5. **Error Recovery**: Graceful handling of individual file failures

## Error Handling

The ETL system includes comprehensive error handling:

### File-Level Errors
- **Missing Files**: Gracefully skips missing data sources
- **Permission Errors**: Logs and continues processing
- **Encoding Errors**: Attempts multiple encodings (UTF-8, Latin-1)
- **Malformed HTML**: Skips problematic files and continues

### System-Level Errors
- **Memory Issues**: Batch processing prevents memory overflow
- **Thread Safety**: Proper locking for concurrent operations
- **Output Failures**: Creates fallback output files
- **API Failures**: Graceful degradation for optional services

## Logging

The system provides detailed logging at multiple levels:

### Console Output
- Real-time progress indicators
- Visual progress bars with emojis
- Performance metrics
- Error summaries

### File Logging
- Detailed operation logs (`etl_ingestion.log`)
- Error stack traces
- Performance timing data
- Processing statistics

### Log Levels
- **INFO**: Normal operation progress
- **WARNING**: Non-critical issues
- **ERROR**: Processing errors
- **DEBUG**: Detailed debugging information

## Troubleshooting

### Common Issues

1. **Missing Data Sources**
   - **Symptom**: "Database not found" or "File not found" errors
   - **Solution**: Ensure data files are in correct locations
   - **Impact**: System continues with available data sources

2. **Memory Issues**
   - **Symptom**: System runs out of memory
   - **Solution**: Reduce `batch_size` parameter
   - **Alternative**: Reduce `max_workers` for lower memory usage

3. **Permission Errors**
   - **Symptom**: "Permission denied" errors
   - **Solution**: Check file permissions and ownership
   - **Impact**: Affected files are skipped, processing continues

4. **Encoding Issues**
   - **Symptom**: Unicode decode errors
   - **Solution**: System automatically attempts multiple encodings
   - **Impact**: Problematic files are skipped, processing continues

### Performance Tuning

1. **Increase Throughput**
   - Increase `max_workers` (4-8 recommended)
   - Increase `batch_size` (100-200 recommended)
   - Ensure sufficient system resources

2. **Reduce Memory Usage**
   - Decrease `batch_size` (50-100 recommended)
   - Decrease `max_workers` (2-4 recommended)
   - Monitor system memory usage

3. **Optimize for Reliability**
   - Use default settings for stability
   - Monitor error logs for issues
   - Ensure data source availability

## Dependencies

- Python 3.7+
- BeautifulSoup4 (HTML parsing)
- python-dotenv (Environment variables)
- Standard library modules (os, json, sqlite3, csv, datetime, logging, time, traceback, concurrent.futures, threading)

## Configuration Files

### Company Mapping (`data/company_mapping.csv`)
Required CSV file containing company information and variants:
- `base_company`: Primary company name
- `variant_name`: Specific variant (e.g., "minter", "mainnet")
- `slack_group`: Slack group identifier
- `telegram_group`: Telegram group identifier
- `calendar_domain`: Calendar search domain
- `full_node_address`: Full node address
- `variant_type`: Type of variant

### Environment Variables (`.env`)
Optional configuration for API integrations:
- `GOOGLE_CALENDAR_CREDENTIALS`: Google Calendar API credentials
- `HUBSPOT_API_KEY`: HubSpot API key
- Other service-specific credentials

## Monitoring and Maintenance

### Regular Tasks
1. **Monitor Log Files**: Check `etl_ingestion.log` for errors
2. **Verify Data Sources**: Ensure all data sources are available
3. **Performance Monitoring**: Track processing times and resource usage
4. **Output Validation**: Verify output file integrity and completeness

### Maintenance Schedule
- **Daily**: Check processing logs for errors
- **Weekly**: Verify data source availability
- **Monthly**: Review performance metrics and optimize settings
- **As Needed**: Update company mapping and configuration

## Future Enhancements

1. **Additional Data Sources**: CRM systems, email platforms
2. **Real-time Processing**: Streaming data ingestion
3. **Data Validation**: Schema validation and data quality checks
4. **Incremental Updates**: Process only changed data
5. **API Integration**: RESTful API for data access
6. **Dashboard**: Web-based monitoring and control interface

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review log files for error details
3. Verify data source availability
4. Check system resources and permissions

## Version History

- **v1.0.0**: Initial release with basic ETL functionality
- **v1.1.0**: Added parallel processing and performance optimizations
- **v1.2.0**: Enhanced error handling and logging
- **v1.3.0**: Added comprehensive documentation and monitoring
