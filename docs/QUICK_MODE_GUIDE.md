# ETL Quick Mode Guide

## Overview
Quick Mode is a development and testing feature that significantly speeds up ETL processing by limiting the amount of data processed. This is particularly useful during development, testing new features, or when you need a quick data sample.

## Performance Comparison

| Mode | Duration | Telegram Chats | Use Case |
|------|----------|----------------|----------|
| **Quick Mode** | ~1.3 seconds | 100 chats | Development, Testing |
| **Full Mode** | ~2 minutes | 3,958 chats | Production, Complete Analysis |

**Speedup**: 77x faster than full mode

## Usage

### Command Line Options

#### Main Script
```bash
# Quick mode via main.py
python main.py etl --quick

# Quick mode with additional options
python main.py etl --quick --workers 2 --batch-size 50
```

#### Direct ETL Script
```bash
# Quick mode via direct script
python src/etl/run_etl.py --quick

# Quick mode with workers and batch size
python src/etl/run_etl.py --quick --workers 4 --batch-size 100
```

### Programmatic Usage
```python
from src.etl.etl_data_ingestion import DataETL

# Create ETL instance with quick mode
etl = DataETL(max_workers=4, batch_size=100, quick_mode=True)

# Run ETL process
etl.run_etl()
```

## What Quick Mode Does

### Data Processing Limits
- **Telegram**: Processes only the first 100 chat directories
- **Slack**: Processes all available Slack data (no limit)
- **Calendar**: Processes all available calendar data (no limit)
- **HubSpot**: Processes all available HubSpot data (no limit)

### Output Differences
Quick mode produces the same output format as full mode, but with:
- Limited Telegram conversation data
- Same Slack data coverage
- Same company matching logic
- Same output file structure

### Example Output Comparison

#### Quick Mode Output
```
📈 Data Coverage:
   • Slack: 58 companies
   • Telegram: 1 company (limited by quick mode)
   • Total Messages: ~1,456
   • File Size: ~0.28 MB
```

#### Full Mode Output
```
📈 Data Coverage:
   • Slack: 58 companies
   • Telegram: 46 companies
   • Total Messages: 12,736
   • File Size: 1.74 MB
```

## When to Use Quick Mode

### ✅ Recommended For:
- **Development**: Testing new features or bug fixes
- **Debugging**: Investigating specific issues
- **Validation**: Quick checks of data format and structure
- **CI/CD**: Automated testing in pipelines
- **Prototyping**: Rapid iteration on new functionality

### ❌ Not Recommended For:
- **Production**: Final data generation for analysis
- **Complete Analysis**: When you need all conversation data
- **NotebookLM**: Upload to AI analysis (use full mode)
- **Commission Calculations**: When accuracy is critical

## Implementation Details

### Code Changes
The quick mode feature is implemented in `src/etl/etl_data_ingestion.py`:

```python
class DataETL:
    def __init__(self, max_workers: int = 4, batch_size: int = 100, quick_mode: bool = False):
        # ... other initialization ...
        self.quick_mode = quick_mode

    def ingest_telegram_data(self) -> Dict[str, Any]:
        # ... existing code ...
        
        # Quick mode: limit to first 100 chats for faster testing
        if self.quick_mode:
            original_count = len(chat_dirs)
            chat_dirs = chat_dirs[:100]
            logger.info(f"QUICK MODE: Processing only first {len(chat_dirs)} of {original_count} chat directories")
        else:
            logger.info(f"Found {len(chat_dirs)} chat directories to process")
```

### Configuration
Quick mode can be enabled through:
1. **Command line flag**: `--quick`
2. **Constructor parameter**: `quick_mode=True`
3. **Main script argument**: `python main.py etl --quick`

## Validation

### Quick Validation
```bash
# Run validation script to check output
python scripts/validate_etl_output_simple.py
```

### Expected Quick Mode Results
- **File Size**: ~0.28 MB (much smaller than full mode)
- **Companies with Data**: 58-59 (mostly Slack data)
- **Total Messages**: ~1,456 (limited by Telegram restriction)
- **Processing Time**: ~1.3 seconds

## Best Practices

### Development Workflow
1. **Start with Quick Mode**: Use for initial development and testing
2. **Validate Changes**: Run quick mode to ensure code changes work
3. **Full Mode for Final**: Switch to full mode for production data
4. **Automated Testing**: Include quick mode in CI/CD pipelines

### Testing Strategy
```bash
# Test new feature with quick mode
python main.py etl --quick

# Validate output
python scripts/validate_etl_output_simple.py

# If successful, run full mode
python main.py etl
```

### Performance Monitoring
- Monitor processing times in both modes
- Track data coverage differences
- Validate output quality in quick mode

## Troubleshooting

### Common Issues

#### Quick Mode Too Slow
- **Cause**: Still processing too much data
- **Solution**: Consider reducing batch size or workers

#### Missing Data in Quick Mode
- **Expected**: Telegram data will be limited
- **Check**: Ensure Slack data is still present

#### Validation Failures
- **Cause**: Different data coverage between modes
- **Solution**: Use appropriate validation thresholds

### Debug Commands
```bash
# Check ETL logs
tail -f logs/etl.log

# Validate with verbose output
python scripts/validate_etl_output_simple.py

# Compare file sizes
ls -la output/notebooklm/etl_output.txt
```

## Future Enhancements

### Potential Improvements
- **Configurable Limits**: Allow custom chat limits instead of fixed 100
- **Smart Sampling**: Select representative chats instead of first 100
- **Memory Optimization**: Further reduce memory usage in quick mode
- **Progress Indicators**: Better progress reporting for quick mode

### Advanced Usage
- **Selective Processing**: Process specific companies only
- **Time-based Limits**: Limit by date ranges
- **Source Selection**: Choose which data sources to process

## Conclusion

Quick Mode provides an essential development tool that enables rapid iteration and testing while maintaining the same data quality and output format as full mode. It's particularly valuable for:

- **77x faster** development cycles
- **Consistent testing** environment
- **Reduced resource usage** during development
- **Maintained data quality** for validation

Use quick mode for development and testing, then switch to full mode for production data generation.


