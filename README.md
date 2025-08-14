# RepSplit - Sales Commission Calculator

RepSplit analyzes private Slack channels ending with `-bitsafe` to calculate commission splits based on deal stage participation for your sales team.

## Features

- **Automatic Stage Detection**: Uses keyword patterns to identify deal stages
- **Commission Calculation**: Applies configurable weights and rules for fair distribution
- **Audit Trail**: Every commission allocation is backed by specific message references
- **Flexible Configuration**: Customizable stage weights, keywords, and participant settings

## Sales Team

**Commission-Earning Members:**
- Aki (Founder cap applies)
- Addie
- Amy  
- Mayank

**Non-Commission Members:**
- Prateek
- Will
- Kadeem

## Setup

### 1. Create Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name: `RepSplit` (or your preferred name)
4. Select your workspace

### 2. Configure OAuth Scopes

Add these **User Token Scopes**:
- `groups:read` - Read private channels
- `groups:history` - Read private channel messages  
- `users:read` - Read user information
- `team:read` - Read workspace information

### 3. Install App

1. Go to "OAuth & Permissions" in your app settings
2. Click "Install to Workspace"
3. Copy the **User OAuth Token** (starts with `xoxp-`)

### 4. Configure RepSplit

1. Edit `config.json`:
   - Replace `xoxp-your-slack-token-here` with your actual token
   - Update participant information (Slack IDs, display names, emails)

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 1. Ingest Slack Data

Download data from your `-bitsafe` channels:

```bash
python slack_ingest.py
```

This will:
- Find all private channels ending with `-bitsafe`
- Download message history (test mode: 1 channel, full mode: all channels)
- Store data in local SQLite database

### 2. Run Commission Analysis

Calculate commission splits:

```bash
python repsplit.py
```

This will:
- Analyze message content for deal stage signals
- Calculate commission percentages per participant
- Generate detailed justifications
- Output CSV files with results

## Output Files

- **`deal_splits.csv`**: Commission splits per deal/channel
- **`person_rollup.csv`**: Total commission percentages per person
- **`deal_outline.txt`**: Typical deal stage progression
- **`justifications/`**: Detailed markdown files per deal

## Deal Stages & Weights

| Stage | Weight | Keywords |
|-------|--------|----------|
| **first_touch** | 15% | intro, introduce, connect, loop in, reached out |
| **discovery** | 25% | use case, requirements, scope, pain, timeline |
| **solutioning** | 20% | proposal, deck, spec, POC, integration, API |
| **negotiation** | 20% | price, discount, terms, MSA, SOW, quote |
| **scheduling_ops** | 10% | Calendly, schedule, agenda, follow up, notes |
| **closing** | 10% | signed, countersigned, PO, invoice, closed won |

## Commission Rules

- **Diminishing Returns**: Repeated contributions in same stage get reduced weight
- **Founder Cap**: Aki capped at 30% unless in negotiation/closing stages
- **Presence Floor**: Minimum 5% for any participant in channel
- **Closer Bonus**: Additional 2% for closing stage participants

## Configuration

Edit `config.json` to customize:
- Stage weights and keywords
- Participant information
- Commission rules and thresholds
- Slack API settings

## Privacy & Security

- All data stored locally in SQLite database
- No data uploaded to external services
- Slack token stored in local config file only
- Full audit trail for transparency

## Troubleshooting

### Common Issues

1. **"Slack token not found"**: Check `config.json` has valid token
2. **"No channels found"**: Verify app has correct OAuth scopes
3. **"Permission denied"**: Ensure app is installed in workspace
4. **Rate limiting**: Tool includes delays, but may need adjustment for large workspaces

### Logs

Check these log files for detailed information:
- `slack_ingest.log` - Ingestion process logs
- `repsplit.log` - Analysis process logs

## Support

For issues or questions:
1. Check the logs for error details
2. Verify Slack app configuration
3. Ensure all dependencies are installed
4. Check database file permissions

## License

Internal tool for sales commission calculation. 