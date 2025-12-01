# Slack Tools

A suite of Python utilities for managing and auditing Slack and Telegram customer engagement groups at BitSafe.

## Features

### 🌐 Admin Panel (NEW!)
Web-based admin panel for managing team member access across Slack and Telegram:
- **Dashboard** with quick stats and recent activity
- **Employee Management** - Add/edit/deactivate team members
- **Automated Audits** - Daily scheduled audits + manual triggers
- **Offboarding Center** - One-click removal from all groups
- **Audit History** - Track compliance over time

🚀 **[Launch Admin Panel](webapp/)** | 📖 **[Documentation](webapp/README.md)**

```bash
# Quick start
cd webapp
./start.sh
# Open http://localhost:5001
```

### 🔍 Customer Group Audit
Automatically audit all Slack and Telegram customer groups to verify required team members are present. Generates comprehensive Excel reports with:
- Team member presence tracking (5 required, 4 optional)
- Group categorization (BD Customer, Marketing, Internal, Intro)
- iBTC rebranding flags
- Privacy status checks (Slack channels & Telegram history visibility)
- Completeness scores

📊 **Latest Audit**: 523 groups (118 Slack + 405 Telegram)
- All groups now audited via live API (no cached data)
- 295 BD groups with missing members
- 192 groups need iBTC renaming
- 29 Telegram groups with hidden history

### ➕ Bulk Member Addition
Automatically add team members to all BitSafe Slack customer channels in bulk:
- Add multiple members to 118 channels in ~2-3 minutes
- Dry-run mode to preview changes
- Detailed logging for audit trail
- Skip channels where members already present
- **Always uses live API** to catch newly created channels

✅ **Recent Success**: Added Aliya Gordon and Kevin Huet to 49 newly discovered channels (98 memberships added, bringing total coverage to 116 active channels)

### 🛠️ Telegram Admin Tool (NEW!)
Unified command-line tool for Telegram group administration:
- **Find users** across all groups with permission status
- **Remove users** from groups (bulk operations)
- **Generate ownership transfer messages** for groups you don't control
- **Bulk rename** groups with pattern matching or JSON mappings
- **Excel reports** for all operations

📖 **[Full Documentation](docs/telegram-admin-tool.md)**

```bash
# Find a user
python3 scripts/telegram_admin.py find-user --username someuser

# Remove from groups
python3 scripts/telegram_admin.py remove-user --username someuser

# Rename groups
python3 scripts/telegram_admin.py rename --pattern "old" --replace "new"
```

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

Output: `output/audit_reports/customer_group_audit_YYYYMMDD_HHMMSS.xlsx`

### Add Members to All Channels

```bash
# Preview changes first (dry-run)
python3 scripts/add_members_to_channels.py aliya kevin --dry-run

# Actually add members
python3 scripts/add_members_to_channels.py aliya kevin --yes
```

Output: Console progress + `output/add_members_YYYYMMDD_HHMMSS.log`

## Configuration

### Required Environment Variables

Create a `.env` file with:

```bash
# Slack
# For audit: groups:read, groups:history, channels:read, channels:history, users:read
# For bulk member addition: also needs groups:write, channels:write
SLACK_USER_TOKEN=xoxp-...

# Telegram  
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef...
TELEGRAM_PHONE=+16176820066
```

**Note**: To use the bulk member addition tool, you need to add `groups:write` and `channels:write` scopes to your Slack app. See [docs/add-write-scope.md](docs/add-write-scope.md) for instructions.

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
- **[Bulk Member Addition Tool](docs/add-members-tool.md)** - Guide for adding members to all channels
- **[Slack Write Permissions Setup](docs/add-write-scope.md)** - How to add write scopes to Slack app
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

## Recent Updates

### November 25, 2024 - Critical Fix: Live API Migration
**Issue**: Scripts were using cached Slack export from August 2024, missing 51 newly created channels.

**Resolution**: 
- ✅ All scripts now use live Slack API
- ✅ Fixed bulk member addition to catch new channels
- ✅ Successfully added Kevin & Aliya to 49 missing channels
- ✅ Current coverage: 116/118 active channels (98.3%)

📄 **[Full Incident Report](output/missing_channels_fix_20251125.md)**

### November 21, 2024 - Telegram iBTC Rebranding
- ✅ Renamed 44 Telegram groups to remove iBTC branding
- ✅ Handled rate limits with automated retry logic
- ✅ Generated ownership transfer messages for 5 groups

### November 19, 2024 - Bulk Member Addition Tool
- ✅ Created automated tool for adding members to all Slack channels
- ✅ Successfully added Aliya & Kevin to initial 67 channels
- ✅ Implemented dry-run mode and safety checks

## Roadmap

### V1.0 (Current)
- ✅ Telegram group audit (405 groups)
- ✅ Slack channel audit (118 channels - **FIXED: Now uses live API**)
- ✅ Excel report generation
- ✅ Group categorization
- ✅ iBTC renaming flags
- ✅ Bulk member addition
- ✅ Telegram admin tool

### V2.0 (Q1 2025)
- Automated member removal workflows
- Enhanced exclusion management
- Historical tracking dashboard

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

**Last Updated**: November 25, 2024
