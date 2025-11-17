# Product Requirements Document: Slack Tools

**Version**: 1.0  
**Date**: November 17, 2024  
**Owner**: Aki Balogh  
**Status**: In Development

---

## Executive Summary

Slack Tools is a suite of Python utilities for managing, analyzing, and auditing Slack and Telegram customer engagement groups at BitSafe. The primary use cases are:

1. **Customer Group Audit**: Automatically verify that required BitSafe team members are present in all customer groups across Slack and Telegram
2. **Slack Export**: Export private Slack channel message history including threaded conversations
3. **Telegram Export**: Export Telegram group message history for archival and analysis

---

## Problem Statement

### Current Challenges

1. **Manual Group Management**: When creating new customer groups (Slack or Telegram), we manually invite BD and Product team members. This process is error-prone and leads to:
   - Team members missing from important customer conversations
   - Inconsistent coverage across customer accounts
   - Difficulty tracking which groups are properly staffed

2. **iBTC Rebranding**: Historical groups contain "iBTC" in their names. We need to:
   - Identify all groups with "iBTC" branding
   - Rename them to use current product naming
   - Track progress on the renaming effort

3. **Group Categorization**: Different types of groups require different team coverage:
   - BD Customer groups need full team presence
   - Marketing groups may only need select members
   - Internal groups have different requirements
   - No systematic way to categorize and audit accordingly

4. **Data Archival**: Need to export Slack and Telegram conversations for:
   - Compliance and record-keeping
   - Historical reference during customer transitions
   - Analysis of customer engagement patterns

---

## Goals & Success Metrics

### Goals

1. **Automated Auditing**: Generate comprehensive reports of team member presence across all customer groups
2. **Gap Identification**: Highlight which groups are missing required team members
3. **iBTC Tracking**: Flag all groups needing rebranding from "iBTC" to current naming
4. **Category Management**: Support different team requirements for different group types
5. **Dual Platform**: Support both Slack and Telegram in a unified workflow

### Success Metrics

- **Coverage Rate**: % of BD Customer groups with all 5 required members present
- **Audit Frequency**: Ability to run weekly audits to catch new groups or changes
- **Time Savings**: Reduce manual group audits from hours to minutes
- **iBTC Sunset Progress**: Track % of groups renamed away from "iBTC" branding

---

## User Personas

### Primary User: Head of Growth (Kadeem Clarke)
- **Needs**: Weekly audit reports to ensure proper team coverage
- **Use Case**: Reviews report, identifies gaps, coordinates with team to add missing members

### Secondary User: Sales Engineer (Mayank @ mojo_onchain)
- **Needs**: Visibility into which groups he should be added to
- **Use Case**: Uses Telegram as primary customer communication channel, needs to be in all 401+ groups

### Tertiary Users: BD Team (Amy Wu, Aki Balogh)
- **Needs**: Ensure they're present in high-value customer conversations
- **Use Case**: Reviews audit to identify important groups they're missing from

---

## Features & Requirements

### Feature 1: Customer Group Audit

#### Description
Automatically audit all Slack and Telegram customer groups to verify required and optional team members are present.

#### Requirements

**Must Have:**
- ✅ Fetch all Slack channels containing "bitsafe" in the name
- ✅ Fetch all Telegram groups shared with @mojo_onchain
- ✅ Verify presence of 5 required team members
- ✅ Track 4 optional team members
- ✅ Generate Excel report with audit results
- ✅ Flag groups with "iBTC" that need renaming
- ✅ Categorize groups (BD Customer, Marketing, Internal, Intro)
- ✅ Show completeness score (e.g., "5/5 required")
- ✅ Flag public Slack channels that should be private

**Should Have:**
- 🔄 Configurable team member lists via JSON config
- 🔄 Configurable group categories via JSON config
- 🔄 Support for exclusions (groups that legitimately don't need full team)
- 🔄 Historical tracking of audit results over time

**Could Have:**
- ⏳ Automated invitations to add missing members
- ⏳ Slack/Telegram notifications when gaps are found
- ⏳ Dashboard view of audit results
- ⏳ Integration with CRM for customer account mapping

**Won't Have (Yet):**
- ❌ Automated group creation from templates
- ❌ Auto-removal of departed team members
- ❌ Real-time monitoring (audit is batch/scheduled)

#### Technical Implementation

**Data Sources:**
- **Slack**: Loads channel metadata from `data/raw/slack_export_20250815_064939/channels/private_channels.json` (72 channels)
- **Telegram**: Queries Telegram API for groups shared with @mojo_onchain (401+ groups)

**Team Member Mapping:**
- Maps Slack usernames to team member handles
- Maps Telegram usernames to team member handles
- Handles discrepancies (e.g., `@aki` → `akibalogh`)

**Report Generation:**
- Pandas DataFrame construction
- Excel export with openpyxl
- Auto-sized columns for readability
- Multiple sheets possible (future enhancement)

#### User Flow

1. User runs `python3 scripts/customer_group_audit.py`
2. Script maps team members from Slack workspace
3. Script loads 72 Slack channels from export data
4. Script audits each Slack channel (fetches members via API)
5. Script connects to Telegram, finds 401+ shared groups with @mojo_onchain
6. Script audits each Telegram group
7. Script categorizes groups and flags issues
8. Script generates Excel report on Desktop
9. User reviews report, identifies gaps
10. User manually adds missing members (automated in future)

#### Dependencies

- **Python 3.9+**
- **aiohttp**: Async HTTP for Slack API calls
- **telethon**: Telegram API client
- **pandas**: Data manipulation and Excel export
- **openpyxl**: Excel file writing
- **python-dotenv**: Environment variable management

---

### Feature 2: Slack Export

#### Description
Export private Slack channel message history including threaded conversations to text files.

#### Requirements

**Must Have:**
- ✅ Export specific private channel by ID
- ✅ Include all top-level messages
- ✅ Include all threaded replies
- ✅ Show proper indentation for threads
- ✅ Include timestamps and sender names
- ✅ Handle pagination for large channels

**Should Have:**
- 🔄 Batch export of multiple channels
- 🔄 JSON export format option
- 🔄 Date range filtering

**Could Have:**
- ⏳ Automated scheduled exports
- ⏳ Export to cloud storage (S3, GCS)
- ⏳ Search within exported data

#### Technical Implementation

- Uses `conversations.history` API endpoint
- Uses `conversations.replies` for threaded messages
- Requires `groups:read` and `groups:history` scopes
- User token recommended for private channel access

#### User Flow

1. User identifies channel ID from Slack
2. User runs export script with channel ID
3. Script fetches messages with pagination
4. Script fetches thread replies for each message
5. Script formats output with indentation
6. Script saves to text file

---

### Feature 3: Telegram Export

#### Description
Export Telegram group message history for archival.

#### Requirements

**Must Have:**
- ✅ Connect to specific Telegram group
- ✅ Export message history
- ✅ Handle authentication flow

**Should Have:**
- 🔄 Batch export of multiple groups
- 🔄 Media download (images, files)
- 🔄 HTML export format

**Could Have:**
- ⏳ Real-time message syncing
- ⏳ Incremental exports (only new messages)

#### Technical Implementation

- Uses Telethon library
- Session-based authentication
- Requires Telegram API credentials

---

## Non-Functional Requirements

### Performance
- Audit of 474 groups (72 Slack + 402 Telegram) should complete in < 5 minutes
- Slack API rate limits: 20+ requests per minute (handled with async)
- Telegram API rate limits: Handled by Telethon automatically

### Security
- API tokens stored in `.env` file (git-ignored)
- Slack user tokens not committed to repo
- Telegram session files not committed to repo
- Export data stored locally, not in cloud

### Scalability
- Support up to 1000 combined Slack/Telegram groups
- Handle groups with up to 500 members each
- Excel reports support up to 10,000 rows (openpyxl limit is 1M)

### Maintainability
- Modular design with separate functions for Slack/Telegram
- Configuration via JSON files (not hardcoded)
- Comprehensive logging for debugging
- Documentation for all major functions

---

## Out of Scope

### V1.0 (Current Release)
- ❌ Web UI / Dashboard
- ❌ Automated member invitations
- ❌ CRM integration
- ❌ Multi-workspace Slack support
- ❌ Historical trend analysis
- ❌ Real-time monitoring/alerts

### Future Considerations
- **V2.0**: Automated member management (invite/remove)
- **V3.0**: Web dashboard with visualizations
- **V4.0**: CRM integration and customer account mapping
- **V5.0**: AI-powered insights on customer engagement

---

## Technical Architecture

### Components

```
slack-tools/
├── scripts/
│   ├── customer_group_audit.py      # Main audit script
│   ├── slack_export.py               # Slack export utilities
│   └── telegram_export.py            # Telegram export utilities
├── config/
│   └── customer_group_categories.json  # Group categorization config
├── data/
│   └── raw/
│       └── slack_export_*/
│           └── channels/
│               └── private_channels.json  # Slack channel metadata
├── docs/
│   ├── customer-group-audit.md       # Audit tool documentation
│   └── slack-export-howto.md         # Slack export guide
├── output/
│   └── [audit reports on Desktop]
└── .env                               # API credentials (git-ignored)
```

### Data Flow

1. **Configuration Loading**
   - Load team member definitions from code
   - Load group categories from JSON config
   - Load API credentials from `.env`

2. **Slack Audit**
   - Load channel metadata from export file
   - For each channel:
     - Fetch member list via API
     - Compare against required/optional team lists
     - Categorize group
     - Flag issues (missing members, public channels, iBTC naming)

3. **Telegram Audit**
   - Connect to Telegram API
   - Fetch all groups shared with @mojo_onchain
   - For each group:
     - Fetch participant list
     - Compare against required/optional team lists
     - Categorize group
     - Flag issues

4. **Report Generation**
   - Combine Slack and Telegram results
   - Sort by category and completeness
   - Generate Excel file with formatted columns
   - Output summary statistics

### APIs Used

**Slack API:**
- `auth.test` - Get team ID
- `users.list` - Map usernames to user IDs
- `conversations.list` - List channels (fallback)
- `conversations.members` - Get channel member list
- `conversations.history` - Export messages
- `conversations.replies` - Export thread replies

**Telegram API (via Telethon):**
- `GetDialogsRequest` - Get user's groups
- `GetCommonChatsRequest` - Find groups shared with another user
- `get_participants` - Get group member list
- `iter_messages` - Export message history

---

## Risks & Mitigations

### Risk 1: Slack API Rate Limits
**Impact**: HIGH  
**Probability**: MEDIUM  
**Mitigation**: 
- Use async/concurrent requests
- Implement exponential backoff
- Load channel metadata from export file instead of API

### Risk 2: Telegram Session Expiry
**Impact**: MEDIUM  
**Probability**: LOW  
**Mitigation**:
- Session files persist between runs
- Clear error messages for re-authentication
- Documentation for session management

### Risk 3: Team Member Username Changes
**Impact**: MEDIUM  
**Probability**: MEDIUM  
**Mitigation**:
- Use Slack user IDs internally (stable)
- Maintain username mapping table
- Periodic review of mappings

### Risk 4: Private Channel Access
**Impact**: HIGH  
**Probability**: LOW  
**Mitigation**:
- Use user token (not bot token)
- Ensure proper scopes (`groups:read`, `groups:history`)
- Load from export data as fallback

### Risk 5: Large Group Performance
**Impact**: MEDIUM  
**Probability**: LOW  
**Mitigation**:
- Async processing
- Progress indicators
- Option to limit group count

---

## Success Criteria

### Launch Criteria (V1.0)
- ✅ Successfully audit all 72 Slack channels
- ✅ Successfully audit all 401+ Telegram groups
- ✅ Generate Excel report with all required columns
- ✅ Accurate team member presence detection (>95%)
- ✅ Proper categorization of groups
- ✅ iBTC flagging working correctly
- ✅ Documentation complete

### Post-Launch Metrics (30 days)
- **Adoption**: Head of Growth runs audit weekly
- **Coverage Improvement**: 80%+ of BD Customer groups have all required members
- **iBTC Sunset**: 50%+ of groups renamed away from iBTC
- **Time Savings**: <5 minutes to run audit (vs. hours of manual review)

---

## Future Enhancements

### Q1 2025
- **Automated Member Invitations**: One-click to add missing members to groups
- **Exclusion Management**: UI to mark specific group/member combinations as exceptions
- **Historical Tracking**: Database to track audit results over time

### Q2 2025
- **Web Dashboard**: React dashboard for viewing audit results
- **Real-time Monitoring**: Webhook-based alerts when new groups are created
- **Template-based Group Creation**: Standardized setup for new customer groups

### Q3 2025
- **CRM Integration**: Link groups to customer accounts in HubSpot/Salesforce
- **Engagement Analytics**: Track message volume, response times, team participation
- **AI Insights**: Identify at-risk customers based on engagement patterns

---

## Appendix

### Glossary

- **BD Customer Group**: Slack or Telegram group for engaging with a specific customer
- **Required Members**: 5 team members who must be in all BD customer groups
- **Optional Members**: 4 team members who should be in most groups but not all
- **iBTC**: Historical product name that needs to be phased out
- **Slack Connect**: External shared channels with customers
- **Team Coverage**: % of required team members present in a group

### References

- [Slack API Documentation](https://api.slack.com/)
- [Telethon Documentation](https://docs.telethon.dev/)
- [Customer Group Audit Documentation](docs/customer-group-audit.md)
- [Slack Export How-To](docs/slack-export-howto.md)

### Changelog

- **2024-11-17**: V1.0 - Initial PRD created with customer group audit as primary feature

