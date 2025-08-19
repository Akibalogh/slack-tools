# RepSplit - Sales Commission Calculator

RepSplit analyzes private Slack channels ending with `-bitsafe` to calculate commission splits based on deal stage participation for your sales team.

## Features

- **Automatic Stage Detection**: Uses keyword patterns to identify deal stages
- **Commission Calculation**: Applies configurable weights and rules for fair distribution
- **Audit Trail**: Every commission allocation is backed by specific message references
- **Flexible Configuration**: Customizable stage weights, keywords, and participant settings
- **25% Commission Rounding**: Clean, predictable commission percentages
- **Automatic Normalization**: Ensures commissions always sum to 100%

## Business Model

Each `company-bitsafe` Slack channel represents an **entire deal** including both:
- **Holder Product**: Main BitSafe functionality
- **Minter Product**: Minter functionality

Since both products are typically sold together as a package, commission tracking treats each channel as one complete deal for simplicity and accuracy.

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

- **`deal_splits.csv`**: Commission splits per deal/channel (25% rounded percentages)
- **`person_rollup.csv`**: Total commission percentages per person across all deals
- **`deal_rationale.csv`**: **NEW** - Enhanced analysis with stage-by-stage breakdown, contestation levels, and rationale
- **`justifications/`**: Detailed markdown files per deal with stage analysis and commission breakdown

### Enhanced Analysis Features (deal_rationale.csv)
The new `deal_rationale.csv` provides comprehensive deal analysis with:
- **Commission percentages** for each team member (25% rounded)
- **Contestation Level**: CLEAR OWNERSHIP, HIGH CONTESTATION, or MODERATE CONTESTATION
- **Most Likely Owner**: Primary deal owner recommendation
- **Stage Breakdown**: Who handled each sales stage (Sourcing, Discovery, Solution, Technical, Pricing, Contract, Scheduling, Closing)
- **Rationale**: Detailed explanation of commission split reasoning with stage participation details
- **`COMMISSION_CALCULATION.md`**: Complete documentation of commission calculation logic

## Deal Stages & Weights

| Stage | Weight | Keywords |
|-------|--------|----------|
| **sourcing_intro** | 3% | intro, connect, loop in, reached out, waitlist, referral |
| **discovery_qual** | 10% | questions, requirements, use case, needs, challenge, timeline, docs, installation |
| **solution_presentation** | 18% | credential, rewards, CC, CBTC, overview, explain, how it works, BitSafe |
| **objection_handling** | 20% | concern, worried, hesitant, not sure, doubt, question, issue, problem, challenge |
| **technical_discussion** | 12% | API, integration, technical, architecture, implementation, script, infrastructure |
| **pricing_terms** | 15% | cost, payment, billing, subscription, pricing, fee, rate, discount, tier |
| **contract_legal** | 8% | MSA, contract, agreement, terms, legal, docusign, dropbox sign, signature |
| **scheduling_coordination** | 5% | Calendly, schedule, meeting, call, demo, follow up, availability |
| **closing_onboarding** | 12% | signed, accept, onboard, credential issued, go live, activate, launch |

## Commission Rules

- **25% Rounding**: All commission percentages are rounded to nearest 25% (0%, 25%, 50%, 75%, 100%)
- **Normalization**: Commissions automatically sum to 100% (no over-allocation)
- **Internal Team Only**: Only internal team members earn commission (external prospects/clients are excluded)
- **Diminishing Returns**: Repeated contributions in same stage get reduced weight
- **Founder Cap**: Aki capped at 30% unless in later deal stages
- **Presence Floor**: Minimum 5% for any participant in channel
- **Automatic Stage Detection**: Uses keyword analysis to identify deal stages from Slack messages

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