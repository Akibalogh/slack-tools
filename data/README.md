# Data Organization

This folder contains all data files organized by source:

## `/slack/` - Slack Data
- `repsplit.db` - SQLite database with Slack messages, users, and stage detections
- `config.json` - Main configuration file with stage weights, keywords, and participant info
- `local_config.json` - Local configuration overrides
- `DEAL_BY_DEAL_BREAKDOWN_CLEAN.csv` - Cleaned deal breakdown data

## `/hubspot/` - HubSpot CRM Data
- `hubspot-crm-exports-all-deals-2025-08-11-1.csv` - Complete pipeline export with 231 companies

## `/telegram/` - Telegram Export Data
- `DataExport_2025-08-19/` - Complete Telegram export with 3984 chats
  - `chats/` - Individual chat directories
  - `lists/chats.html` - Index of all chats
  - `export_results.html` - Export summary

## Configuration Files (Root Directory)
- `credentials.json` - Slack API credentials
- `token.json` - Google Calendar API tokens

## `/telegram/` - Telegram Export Data
- `DataExport_2025-08-19/` - Complete Telegram export with 3984 chats
  - `chats/` - Individual chat directories
  - `lists/chats.html` - Index of all chats
  - `export_results.html` - Export summary

## Data Integration Status

### Slack + HubSpot Matches
- 29 out of 190 HubSpot companies have corresponding Slack conversations
- These are stored in `repsplit.db` and analyzed in commission calculations

### Telegram + HubSpot Matches
- P2P.org, Launchnodes, Copper, ChainSafe have rich Telegram data
- Telegram integration pending for commission calculations

### Next Steps
1. Integrate Telegram data for P2P.org deal
2. Expand to other Telegram+HubSpot matches
3. Update commission calculations with multi-source data
