# ETL System Technical Documentation

## Architecture Overview

The ETL (Extract, Transform, Load) system is designed as a modular, scalable data processing pipeline that ingests data from multiple sources and outputs a unified JSON format for analysis.

### Core Components

1. **DataETL Class**: Main orchestrator class
2. **Data Source Handlers**: Individual modules for each data source
3. **Performance Monitoring**: Built-in timing and statistics tracking
4. **Error Handling**: Comprehensive error recovery and logging
5. **Output Generation**: Unified JSON output with metadata

## Class Structure

### DataETL Class

```python
class DataETL:
    def __init__(self, max_workers: int = 4, batch_size: int = 100)
    def load_company_mapping(self) -> Dict[str, Any]
    def ingest_slack_data(self) -> Dict[str, Any]
    def ingest_telegram_data(self) -> Dict[str, Any]
    def ingest_calendar_data(self) -> Dict[str, Any]
    def ingest_hubspot_data(self) -> Dict[str, Any]
    def match_data_to_companies(self) -> Dict[str, Any]
    def generate_summary_stats(self, matched_data: Dict) -> Dict[str, Any]
    def run_etl(self) -> None
```

### Key Methods

#### `__init__(max_workers, batch_size)`
Initializes the ETL system with performance configuration:
- `max_workers`: Number of parallel threads for processing
- `batch_size`: Number of items processed per batch
- `stats`: Performance tracking dictionary
- `_lock`: Thread safety lock

#### `ingest_telegram_data()`
Core method for processing Telegram data with parallel processing:
- Processes 3,958+ chat directories
- Uses ThreadPoolExecutor for parallel processing
- Implements batch processing for memory efficiency
- Returns structured data with metadata

#### `_process_single_chat(chat_dir, chats_dir)`
Worker method for processing individual chat directories:
- Designed for parallel execution
- Handles HTML parsing and data extraction
- Implements error recovery for individual files
- Returns structured chat data or None on failure

## Data Flow

### 1. Initialization Phase
```
Load Configuration → Initialize Data Structures → Setup Logging
```

### 2. Data Ingestion Phase
```
Company Mapping → Slack Data → Telegram Data → Calendar Data → HubSpot Data
```

### 3. Processing Phase
```
Data Matching → Statistics Generation → Output Creation
```

### 4. Output Phase
```
JSON Serialization → File Writing → Logging → Summary
```

## Performance Optimizations

### Parallel Processing
- **ThreadPoolExecutor**: Manages worker threads
- **Batch Processing**: Groups work items for efficiency
- **Memory Management**: Prevents memory overflow
- **Progress Tracking**: Real-time progress updates

### Memory Optimization
- **Batch Size Control**: Configurable batch sizes
- **Lazy Loading**: Load data only when needed
- **Garbage Collection**: Automatic cleanup of processed data
- **Resource Monitoring**: Track memory usage

### Error Recovery
- **Graceful Degradation**: Continue processing on individual failures
- **Retry Logic**: Multiple attempts for transient failures
- **Fallback Output**: Create backup files on main output failure
- **Comprehensive Logging**: Detailed error tracking

## Data Structures

### Company Mapping Structure
```python
{
    "base_company": str,
    "variant_name": str,
    "slack_group": str,
    "telegram_group": str,
    "calendar_domain": str,
    "full_node_address": str,
    "variant_type": str
}
```

### Telegram Chat Structure
```python
{
    "messages": List[Dict],
    "message_count": int,
    "regular_message_count": int,
    "service_message_count": int,
    "participants": List[str],
    "participant_count": int,
    "unique_authors": List[str],
    "directory": str,
    "chat_name": str,
    "last_message_time": str,
    "first_message_time": str
}
```

### Message Structure
```python
{
    "author": str,
    "text": str,
    "timestamp": str,
    "message_id": str,
    "message_type": str,  # "service" or "regular"
    "is_service": bool
}
```

## Error Handling Strategy

### File-Level Errors
1. **Missing Files**: Log warning, continue processing
2. **Permission Errors**: Log error, skip file
3. **Encoding Errors**: Try multiple encodings, skip if all fail
4. **Malformed HTML**: Log warning, skip file

### System-Level Errors
1. **Memory Issues**: Reduce batch size, retry
2. **Thread Errors**: Log error, continue with remaining threads
3. **Output Errors**: Create fallback output file
4. **API Errors**: Log error, continue without API data

### Error Recovery Patterns
```python
try:
    # Main processing logic
    result = process_data()
except SpecificError as e:
    # Handle specific error type
    logger.warning(f"Specific error: {e}")
    result = fallback_value
except Exception as e:
    # Handle general errors
    self._log_error(e, "context")
    result = None
```

## Logging Architecture

### Log Levels
- **DEBUG**: Detailed debugging information
- **INFO**: Normal operation progress
- **WARNING**: Non-critical issues
- **ERROR**: Processing errors

### Log Handlers
1. **File Handler**: Writes to `etl_ingestion.log`
2. **Console Handler**: Outputs to terminal
3. **Progress Handler**: Real-time progress updates

### Log Format
```
%(asctime)s - %(levelname)s - %(message)s
```

## Configuration Management

### Environment Variables
- `GOOGLE_CALENDAR_CREDENTIALS`: Calendar API credentials
- `HUBSPOT_API_KEY`: HubSpot API key
- Other service-specific credentials

### Configuration Files
- `data/company_mapping.csv`: Company mapping data
- `.env`: Environment variables
- `etl_ingestion.log`: Processing logs

### Runtime Configuration
- `max_workers`: Parallel processing threads
- `batch_size`: Items per batch
- `output_file`: Output file path
- `db_path`: Database file path

## Testing Strategy

### Unit Tests
- Individual method testing
- Error condition testing
- Data structure validation
- Performance benchmarking

### Integration Tests
- End-to-end processing
- Multi-source data integration
- Error recovery testing
- Performance testing

### Load Testing
- Large dataset processing
- Memory usage monitoring
- Performance under load
- Error rate analysis

## Monitoring and Metrics

### Performance Metrics
- Processing time per operation
- Memory usage tracking
- Error rate monitoring
- Throughput measurement

### Key Performance Indicators
- **Processing Speed**: Chats per second
- **Error Rate**: Percentage of failed operations
- **Memory Usage**: Peak memory consumption
- **Throughput**: Data processed per minute

### Monitoring Tools
- Built-in performance tracking
- Log file analysis
- System resource monitoring
- Custom metrics collection

## Security Considerations

### Data Protection
- No sensitive data in logs
- Secure file handling
- Access control for data files
- API key protection

### Error Information
- Sanitized error messages
- No sensitive data in stack traces
- Secure logging practices
- Access control for log files

## Scalability Considerations

### Horizontal Scaling
- Multiple worker processes
- Distributed processing
- Load balancing
- Resource sharing

### Vertical Scaling
- Increased memory allocation
- More CPU cores
- Faster storage
- Optimized algorithms

### Performance Bottlenecks
1. **File I/O**: Disk read/write operations
2. **Memory Usage**: Large dataset processing
3. **CPU Usage**: HTML parsing and data processing
4. **Network I/O**: API calls and data transfer

## Maintenance Procedures

### Regular Maintenance
1. **Log Rotation**: Manage log file sizes
2. **Data Cleanup**: Remove temporary files
3. **Performance Review**: Analyze processing metrics
4. **Error Analysis**: Review and address common errors

### Troubleshooting Procedures
1. **Check Logs**: Review error logs for issues
2. **Verify Data Sources**: Ensure data availability
3. **Test Configuration**: Validate settings
4. **Monitor Resources**: Check system resources

### Backup and Recovery
1. **Data Backup**: Regular backup of data sources
2. **Configuration Backup**: Save configuration files
3. **Output Backup**: Archive output files
4. **Recovery Procedures**: Document recovery steps

## Future Enhancements

### Planned Features
1. **Real-time Processing**: Streaming data ingestion
2. **Data Validation**: Schema validation and quality checks
3. **Incremental Updates**: Process only changed data
4. **API Integration**: RESTful API for data access

### Performance Improvements
1. **Caching**: Implement data caching
2. **Compression**: Compress output files
3. **Optimization**: Algorithm improvements
4. **Parallelization**: Enhanced parallel processing

### Monitoring Enhancements
1. **Dashboard**: Web-based monitoring interface
2. **Alerting**: Automated error notifications
3. **Metrics**: Advanced performance metrics
4. **Reporting**: Automated reporting system

## API Reference

### DataETL Class Methods

#### `load_company_mapping() -> Dict[str, Any]`
Loads company mapping from CSV file.
- **Returns**: Dictionary of company mappings
- **Raises**: FileNotFoundError if mapping file not found

#### `ingest_telegram_data() -> Dict[str, Any]`
Processes Telegram data with parallel processing.
- **Returns**: Dictionary of processed chat data
- **Performance**: ~87 seconds for 3,958 chats
- **Threads**: Uses configured max_workers

#### `run_etl() -> None`
Runs the complete ETL process.
- **Output**: Generates `data/etl_output.json`
- **Logging**: Creates detailed logs
- **Performance**: Tracks timing and statistics

### Utility Methods

#### `_safe_file_read(file_path, encoding) -> Optional[str]`
Safely reads files with error handling.
- **Parameters**: file_path, encoding
- **Returns**: File content or None on error
- **Error Handling**: Multiple encoding attempts

#### `_log_error(error, context) -> None`
Logs errors with context and increments error counter.
- **Parameters**: error, context
- **Thread Safety**: Uses locks for thread safety

#### `_start_timer(operation) -> None`
Starts timing an operation.
- **Parameters**: operation name
- **Usage**: Performance tracking

#### `_end_timer(operation) -> float`
Ends timing and returns duration.
- **Parameters**: operation name
- **Returns**: Duration in seconds

## Dependencies

### Required Packages
- `beautifulsoup4`: HTML parsing
- `python-dotenv`: Environment variable management

### Standard Library
- `os`: File system operations
- `json`: JSON serialization
- `sqlite3`: Database operations
- `csv`: CSV file processing
- `datetime`: Date/time handling
- `logging`: Logging system
- `time`: Time operations
- `traceback`: Error handling
- `concurrent.futures`: Parallel processing
- `threading`: Thread management

### Optional Dependencies
- Google Calendar API client
- HubSpot API client
- Other service-specific APIs

## Version Compatibility

### Python Version
- **Minimum**: Python 3.7
- **Recommended**: Python 3.9+
- **Tested**: Python 3.7-3.11

### Operating System
- **Linux**: Full support
- **macOS**: Full support
- **Windows**: Full support

### Dependencies
- **BeautifulSoup4**: 4.9.0+
- **python-dotenv**: 0.19.0+
- **Standard Library**: As available in Python version
