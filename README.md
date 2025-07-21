# CantonScan Balance Scraper

A Python script that automatically scrapes wallet balances for all parties on [CantonScan](https://cantonscan.com/). This tool extracts balance data from the Canton blockchain explorer and outputs it in a format ready for analysis.

## 🚀 Features

- **Automated scraping** of all party balances from CantonScan
- **Full party ID extraction** (name::hash format)
- **CPU-optimized** with resource blocking and performance enhancements
- **Progressive retry logic** with increasing wait times (15s, 25s, 35s)
- **Comprehensive error handling** and logging
- **Batch processing** for efficient memory usage
- **100% success rate** with robust error recovery

## 📋 Requirements

- Python 3.7+
- Playwright
- Virtual environment (recommended)

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Akibalogh/slack-tools.git
   cd slack-tools
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install playwright
   playwright install chromium
   ```

## 🎯 Usage

### Basic Usage

Run the script to scrape all party balances:

```bash
python3 codascan-dl.py
```

### Output

The script generates a `codascan_balances.txt` file with the following format:

```
Party Name	Party ID	Balance	URL
meria	meria::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	9,704.3101	https://www.cantonscan.com/party/meria%3A%3A1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
digik	digik::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2	9,704.3375	https://www.cantonscan.com/party/digik%3A%3A1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
...
```

### Google Sheets Integration

1. Run the script to generate `codascan_balances.txt`
2. Open the [Google Sheets template](https://drive.google.com/open?id=1B2MXcW24vYuKx7-tUFiw9HcdFbmYc9-asIwQB_Iaeu0&usp=chrome_ntp)
3. Go to the "Balances" tab
4. Copy and paste the contents of `codascan_balances.txt` into the sheet

## ⚡ Performance Optimizations

The script includes several optimizations to minimize CPU usage:

- **Browser optimizations**: Disabled GPU, extensions, plugins, images
- **Resource blocking**: Blocks unnecessary files (images, fonts, CSS)
- **Batch processing**: Processes 25 parties at a time
- **Progressive waits**: Increases wait time on retries
- **Memory management**: Limited memory usage and smaller viewports

## 📊 Sample Results

The script typically processes **238+ parties** with:
- **100% success rate** (all parties processed)
- **Zero errors** (robust error handling)
- **Complete data extraction** (party names, IDs, balances, URLs)

### Top Balances Example:
```
cbtc-treasury-1: 1,901,015.7898 CC
iBTC-validator-1: 2,864,444.8496 CC
bitsafe-minter: 199,124.3593 CC
sendit-minter: 199,050.3247 CC
obsidian-minter: 197,775.9827 CC
```

## 🔧 Configuration

### Test Mode
Set `TEST_MODE = True` in the script to process only the first few parties for testing.

### Batch Size
Adjust `batch_size = 25` to change the number of parties processed simultaneously.

### Wait Times
Modify the `wait_times` list to adjust retry intervals:
```python
wait_times = [15, 25, 35]  # seconds for each retry attempt
```

## 📝 Logging

The script generates detailed logs in `codascan_scraper.log` including:
- Processing progress
- Error details
- Performance metrics
- Debug information

## 🐛 Troubleshooting

### Common Issues

1. **Playwright not installed:**
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **Memory issues:**
   - Reduce batch size in the script
   - Close other applications
   - Ensure sufficient RAM available

3. **Network timeouts:**
   - Check internet connection
   - Increase timeout values in the script
   - Try running during off-peak hours

### Debug Mode

The script includes debug logging. Check the log file for detailed information about any issues.

## 📈 Data Analysis

The generated data can be used for:
- **Balance tracking** across all parties
- **Trend analysis** over time
- **Network health monitoring**
- **Party activity analysis**

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

This project is open source and available under the MIT License.

## 🔗 Links

- **Script**: [codascan-dl.py](https://github.com/Akibalogh/slack-tools/blob/main/codascan-dl.py)
- **Google Sheets Template**: [CantonScan Balances](https://drive.google.com/open?id=1B2MXcW24vYuKx7-tUFiw9HcdFbmYc9-asIwQB_Iaeu0&usp=chrome_ntp)
- **CantonScan**: [https://cantonscan.com/](https://cantonscan.com/)

---

**Note**: This tool is designed for educational and research purposes. Please respect the website's terms of service and rate limits when using this scraper. 