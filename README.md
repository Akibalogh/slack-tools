# Slack Tools

A suite of Python utilities for managing and auditing Slack and Telegram customer engagement groups at BitSafe.

## Features

### 🔍 Customer Group Audit
Automatically audit all Slack and Telegram customer groups to verify required team members are present. Generates comprehensive Excel reports with:
- Team member presence tracking (5 required, 4 optional)
- Group categorization (BD Customer, Marketing, Internal, Intro)
- iBTC rebranding flags
- Privacy status checks
- Completeness scores

📊 **Current Coverage**: 402 Telegram groups audited (72 Slack channels pending token scope fix)

### 📤 Slack Export
Export private Slack channel message history including threaded conversations.

### 📲 Telegram Export  
Export Telegram group message history for archival.

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd slack-tools

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API credentials
```

### Run Customer Group Audit

```bash
python3 scripts/customer_group_audit.py
```

Output: `~/Desktop/customer_group_audit_YYYYMMDD_HHMMSS.xlsx`

## Configuration

### Required Environment Variables

Create a `.env` file with:

```bash
# Slack
SLACK_USER_TOKEN=xoxp-...  # User token with groups:read and groups:history scopes

# Telegram  
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef...
TELEGRAM_PHONE=+16176820066
```

### Group Categories

Edit `config/customer_group_categories.json` to customize group categories:

```json
{
  "marketing_groups": ["Party Action People", "Artemis"],
  "internal_groups": ["iBTC Offboarding Support Group"],
  "intro_groups": ["Bron <> SIG"]
}
```

## Documentation

- **[Customer Group Audit Guide](docs/customer-group-audit.md)** - Complete guide for the audit tool
- **[Slack Export How-To](docs/slack-export-howto.md)** - Guide for exporting Slack channels
- **[PRD](PRD.md)** - Product requirements and roadmap

## Team Members

### Required (Must be in all BD customer groups)
- @akibalogh - Aki Balogh (CEO)
- @gabitui - Gabi Tui (Head of Product)
- @mojo_onchain - Mayank (Sales Engineer)
- @kadeemclarke - Kadeem Clarke (Head of Growth)
- @NonFungibleAmy - Amy Wu (BD)

### Optional (Should be in most groups)
- @shin_novation - Shin (Strategy Advisor)
- @j_eisenberg - Jesse Eisenberg (CTO)
- @anmatusova - Anna Matusova (VP Finance & Legal)
- @Dae_L - Dae (Sales Advisor)

## Latest Audit Results

**Date**: November 17, 2024 (10:55 AM)

```
✅ Total groups audited: 469
├── Slack channels: 67
└── Telegram groups: 402

By Category:
├── BD Customer: 457
├── Internal: 8
├── Marketing: 3
└── Intro: 1

Flags:
├── Groups needing rename (iBTC): 194
├── PUBLIC Slack channels: 0 ✅
└── BD groups with missing members: 294/457 (64%)
```

## Known Issues

### Slack Channels Not Appearing - FIXED ✅
**Status**: **RESOLVED**  
**Issue**: `.env` file was using the wrong Slack token  
**Solution**: Updated to use the correct token from BitSafe Export Tool app (A09AJJZF718) which has all required scopes:
- `groups:read` - View private channel info
- `groups:history` - View private channel messages
- `channels:read`, `channels:history`, `users:read`

**Correct token**: Get from BitSafe Export Tool app at https://api.slack.com/apps/A09AJJZF718/oauth

Run `python3 scripts/verify_slack_token.py` to verify token access.

## Project Structure

```
slack-tools/
├── scripts/
│   ├── customer_group_audit.py      # Main audit script
│   ├── slack_export.py               # Slack export utilities
│   └── telegram_export.py            # Telegram export utilities
├── config/
│   └── customer_group_categories.json  # Group categorization
├── data/
│   └── raw/slack_export_*/           # Slack channel metadata
├── docs/
│   ├── customer-group-audit.md       # Audit documentation
│   └── slack-export-howto.md         # Export guide
├── output/                            # Analysis and exports
├── .env                               # API credentials (git-ignored)
├── PRD.md                             # Product requirements
└── README.md                          # This file
```

## Dependencies

- **Python 3.9+**
- **aiohttp** - Async HTTP for Slack API
- **telethon** - Telegram API client
- **pandas** - Data manipulation
- **openpyxl** - Excel export
- **python-dotenv** - Environment management

## Contributing

1. Create a feature branch
2. Make your changes
3. Update documentation
4. Test thoroughly
5. Submit pull request

## Roadmap

### V1.0 (Current)
- ✅ Telegram group audit (402 groups)
- 🔄 Slack channel audit (72 channels - pending fix)
- ✅ Excel report generation
- ✅ Group categorization
- ✅ iBTC renaming flags

### V2.0 (Q1 2025)
- Automated member invitations
- Exclusion management
- Historical tracking

### V3.0 (Q2 2025)
- Web dashboard
- Real-time monitoring
- Template-based group creation

## License

Proprietary - BitSafe Internal Use Only

## Support

For issues or questions, contact:
- Aki Balogh (@akibalogh)
- Engineering Team

---

**Last Updated**: November 17, 2024
