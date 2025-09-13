# Getting Started with RepSplit

This guide will walk you through setting up and running your first commission analysis with RepSplit.

## 🚀 Quick Start (5 minutes)

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install test dependencies (optional)
pip install -r requirements-test.txt
```

### 2. Configure API Tokens

Create a `.env` file in your project root:

```bash
# Slack API token
SLACK_TOKEN=xoxp-your-slack-token-here

# Google Calendar API (optional)
GOOGLE_CALENDAR_CREDENTIALS=path/to/credentials.json

# AI API keys (for enhanced features)
ANTHROPIC_API_KEY=sk-ant-your-key-here
PERPLEXITY_API_KEY=pplx-your-key-here
```

### 3. Run Your First Analysis

```bash
# Basic analysis
python repsplit.py --sequential

# With verbose output
python repsplit.py --sequential --verbose

# Check system health first
python monitor_dashboard.py
```

### 4. View Results

Check the `output/` directory for generated files:
- `deal_rationale.csv` - Detailed commission analysis
- `commission_splits.csv` - Summary commission splits
- `justifications/` - Individual deal justifications

## 📋 Prerequisites

### System Requirements

- **Python**: 3.9 or higher
- **Operating System**: macOS, Linux, or Windows
- **Memory**: 512MB RAM minimum, 2GB recommended
- **Storage**: 100MB available space
- **Network**: Internet access for API calls

### Required Accounts

- **Slack Workspace**: With admin access for API tokens
- **Telegram**: For customer group monitoring
- **Google Calendar**: For meeting data integration
- **AI Services**: Anthropic/Perplexity for enhanced features

## 🔧 Detailed Setup

### Step 1: Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd slack-tools

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Slack Configuration

1. **Create Slack App**:
   - Go to [api.slack.com/apps](https://api.slack.com/apps)
   - Click "Create New App" → "From scratch"
   - Name: "RepSplit Commission Calculator"
   - Workspace: Select your workspace

2. **Configure Permissions**:
   - Go to "OAuth & Permissions"
   - Add scopes:
     - `channels:read` - Read channel information
     - `channels:history` - Read channel messages
     - `users:read` - Read user information
     - `groups:read` - Read private channels

3. **Install App**:
   - Click "Install to Workspace"
   - Copy the "Bot User OAuth Token" (starts with `xoxb-`)

4. **Update Configuration**:
   ```bash
   # Add to .env file
   SLACK_TOKEN=xoxb-your-bot-token-here
   ```

### Step 3: Telegram Configuration

1. **Get Telegram Bot Token**:
   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Create new bot: `/newbot`
   - Copy the bot token

2. **Configure Bot**:
   ```bash
   # Add to .env file
   TELEGRAM_BOT_TOKEN=your-bot-token-here
   ```

### Step 4: Google Calendar Setup

1. **Enable Google Calendar API**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing
   - Enable Google Calendar API

2. **Create Service Account**:
   - Go to "IAM & Admin" → "Service Accounts"
   - Create service account
   - Download JSON credentials file

3. **Share Calendar**:
   - Share your calendar with the service account email
   - Grant "Make changes to events" permission

4. **Update Configuration**:
   ```bash
   # Add to .env file
   GOOGLE_CALENDAR_CREDENTIALS=path/to/service-account.json
   ```

## 🧪 Test Your Setup

### 1. Verify Configuration

```bash
# Test configuration loading
python -c "from repsplit import RepSplit; r = RepSplit(); print('✅ Configuration loaded successfully')"
```

### 2. Check System Health

```bash
# Run monitoring dashboard
python monitor_dashboard.py
```

Expected output:
```
============================================================
 REPSPLIT SYSTEM MONITORING DASHBOARD
============================================================
✅ HEALTHY: Database performance and structure
✅ HEALTHY: Data source freshness
✅ HEALTHY: Overall system status
```

### 3. Test Data Processing

```bash
# Run minimal analysis
python repsplit.py --sequential --limit 5
```

## 📊 Understanding Your First Run

### What Happens During Analysis

1. **Data Collection**: System fetches data from all configured sources
2. **Company Matching**: Normalizes and matches company names across platforms
3. **Stage Detection**: Analyzes messages for sales stage indicators
4. **Contribution Calculation**: Determines team member contributions
5. **Commission Splits**: Calculates fair commission percentages
6. **Report Generation**: Creates detailed output files

### Expected Output Files

- **`deal_rationale.csv`**: Main analysis with full node addresses
- **`commission_splits.csv`**: Summary commission percentages
- **`justifications/`**: Individual deal analysis files

### Sample Output Structure

```csv
Full Node Address,Aki %,Addie %,Mayank %,Amy %,Contestation Level,Most Likely Owner,Calendar Meetings,Sourcing/Intro,Discovery/Qual,Solution,Objection,Technical,Pricing,Contract,Scheduling,Closing,Rationale
allnodes::1220...,75,25,0,0,Low,Aki,2,1,1,0,0,0,0,0,0,Aki led intro and discovery
```

## 🚨 Common Issues & Solutions

### Issue: "No channels found"
**Solution**: Verify Slack token permissions and channel access

### Issue: "Database connection failed"
**Solution**: Check file permissions and database path

### Issue: "API rate limit exceeded"
**Solution**: Wait and retry, or implement rate limiting

### Issue: "Configuration file not found"
**Solution**: Verify `.env` file exists and has correct format

## 📚 Next Steps

After successful setup:

1. **Read Core Features**: Understand [commission calculation logic](core_features.md)
2. **Configure Workflows**: Set up [automated analysis](workflows.md)
3. **Customize Output**: Learn about [output file formats](output_files.md)
4. **Monitor Performance**: Set up [system monitoring](monitoring.md)

## 🆘 Need Help?

- **Check Logs**: Look in `logs/repsplit.log` for detailed error information
- **Run Diagnostics**: Use `python monitor_dashboard.py` for system health
- **Review Configuration**: Verify all environment variables are set correctly
- **Check Permissions**: Ensure API tokens have required scopes

---

*Continue to [Core Features](core_features.md) to learn about RepSplit's capabilities.*

