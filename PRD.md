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
- ✅ Fetch all Slack channels containing "bitsafe" in the name (ALWAYS use live API, never cached exports)
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
- ✅ Automated invitations to add missing members (See Feature 4)
- ⏳ Slack/Telegram notifications when gaps are found
- ⏳ Dashboard view of audit results
- ⏳ Integration with CRM for customer account mapping

**Won't Have (Yet):**
- ❌ Automated group creation from templates
- ❌ Auto-removal of departed team members
- ❌ Real-time monitoring (audit is batch/scheduled)

#### Technical Implementation

**Data Sources:**
- **Slack**: **Always queries live Slack API** via `conversations.list` to fetch current channels (never uses cached exports to ensure newly created channels are included)
- **Telegram**: Queries Telegram API for groups shared with @mojo_onchain (401+ groups)
- **Critical Note**: Using cached export data was causing newly created Slack channels (e.g., hellomoon-bitsafe created after Aug 2024) to be missed in audits and bulk operations

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
3. Script fetches all Slack channels via live API (ensures newly created channels are included)
4. Script audits each Slack channel (fetches members via API)
5. Script connects to Telegram, finds 401+ shared groups with @mojo_onchain
6. Script audits each Telegram group
7. Script categorizes groups and flags issues
8. Script generates Excel report in output/audit_reports/
9. User reviews report, identifies gaps
10. User manually adds missing members or uses bulk addition tool

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

### Feature 4: Bulk Member Addition (Slack)

#### Description
Automate adding team members to all BitSafe customer Slack channels in bulk. Addresses the manual remediation step after running the audit tool.

#### Requirements

**Must Have:**
- ✅ Add multiple members to all BitSafe channels at once
- ✅ Automatically look up user IDs from usernames
- ✅ Skip channels where members are already present
- ✅ Dry-run mode to preview changes before execution
- ✅ Detailed logging of all operations
- ✅ Handle archived/deleted channels gracefully
- ✅ Progress tracking with real-time console output
- ✅ Save operation log to file for audit purposes

**Should Have:**
- ✅ Non-interactive mode for automation (--yes flag)
- ✅ Summary report of successful/failed operations
- 🔄 Selective channel addition (choose specific channels)
- 🔄 Batch operations with configurable concurrency

**Could Have:**
- ⏳ Telegram group member addition
- ⏳ Role-based member addition (e.g., "add all BD team")
- ⏳ Schedule recurring member additions
- ⏳ Slack notification when operation completes

**Won't Have (Yet):**
- ❌ Member removal functionality
- ❌ Channel creation
- ❌ Permission management

#### Technical Implementation

**Prerequisites:**
- Slack token with `groups:write` and `channels:write` scopes
- User token (not bot token) for private channel access
- See [add-write-scope.md](docs/add-write-scope.md) for setup

**API Endpoints:**
- `users.list` - Look up user IDs from usernames
- `conversations.members` - Check existing channel members
- `conversations.invite` - Add members to channels

**Rate Limiting:**
- 0.5 second delay between operations
- Respects Slack tier 3 limits (50+ requests per minute)
- Async implementation for parallel processing

**Error Handling:**
- `already_in_channel` - Skipped (logged as info)
- `channel_not_found` - Skipped (archived/deleted channels)
- `missing_scope` - Fatal error with clear remediation steps
- Other errors - Logged and continues with next operation

#### User Flow

1. User runs audit tool to identify missing members
2. User reviews audit report and decides which members to add
3. User runs: `python3 scripts/add_members_to_channels.py aliya kevin --dry-run`
4. Script shows preview of all channels and members to be added
5. User confirms operation is correct
6. User runs without --dry-run: `python3 scripts/add_members_to_channels.py aliya kevin --yes`
7. Script adds members to all channels with progress updates
8. Script generates summary report and saves log file
9. User reviews log file to confirm all operations succeeded

#### Example Usage

```bash
# Preview what would happen
python3 scripts/add_members_to_channels.py aliya kevin --dry-run

# Add with confirmation prompt
python3 scripts/add_members_to_channels.py aliya kevin

# Add without confirmation (automation)
python3 scripts/add_members_to_channels.py aliya kevin --yes

# Add different members
python3 scripts/add_members_to_channels.py shin_novation j_eisenberg --yes
```

#### Success Metrics

- **Time Savings**: Add members to 67 channels in ~60 seconds (vs. ~30 minutes manually)
- **Error Rate**: <1% failed operations (only for truly inaccessible channels)
- **Adoption**: Used immediately after each audit run
- **Coverage**: Reduces "missing member" count from 294 to <10 per audit

#### Dependencies

- **Python 3.9+**
- **aiohttp**: Async HTTP for Slack API
- **python-dotenv**: Environment variable management
- Same dependencies as audit tool (already installed)

---

### Feature 5: Telegram Export

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

### Feature 6: Telegram Admin Tool

#### Description
Unified command-line tool for common Telegram group administration tasks, consolidating multiple ad-hoc operations into a single, reusable interface.

#### Requirements

**Must Have:**
- ✅ **Find User**: Search for any user across all Telegram groups
- ✅ **Remove User**: Bulk remove user from groups where you have admin rights
- ✅ **Ownership Management**: Generate transfer request messages for groups you don't control
- ✅ **Bulk Rename**: Pattern-based or JSON-mapping-based group renaming
- ✅ **Admin Status Check**: Show your permission level in each group
- ✅ **Excel Reports**: Generate reports for all operations
- ✅ **Rate Limit Handling**: Gracefully handle Telegram API rate limits

**Should Have:**
- ✅ Command-line interface with subcommands
- ✅ Support for batch operations from text files
- ✅ Detailed logging and error reporting
- ✅ Session management (reuse authenticated sessions)

**Nice to Have:**
- ⏳ Progress bars for long-running operations
- ⏳ Dry-run mode for destructive operations
- ⏳ Integration with audit tool for targeting specific groups
- ⏳ Undo functionality for recent operations

#### Use Cases

1. **Employee Offboarding**:
   - Find all groups where former employee has access
   - Remove them from groups you control
   - Generate ownership transfer requests for the rest

2. **Rebranding**:
   - Bulk rename groups to remove deprecated terminology
   - Pattern-based replacements (e.g., "iBTC" → "BitSafe (CBTC)")
   - JSON mappings for precise control

3. **Access Auditing**:
   - Find where contractors/consultants have access
   - Verify access aligns with their scope of work
   - Generate reports for compliance

#### Implementation Status

**Completed:**
- ✅ Created unified `telegram_admin.py` script with 4 subcommands
- ✅ Implemented find-user, remove-user, request-ownership, rename
- ✅ Added Excel report generation for all operations
- ✅ Created comprehensive documentation (docs/telegram-admin-tool.md)
- ✅ Successfully used for @nftaddie removal:
  - 33 groups identified
  - 3 groups removed (where we had admin rights)
  - 24 ownership transfer requests generated
- ✅ Successfully used for iBTC rebranding:
  - 40 groups renamed
  - Standardized naming convention applied
  - Rate limit handling validated

**Technical Implementation:**
- CLI: argparse with subcommands
- Telegram: Telethon client (reuses audit infrastructure)
- Reports: pandas + openpyxl
- Session: Reuses telegram_session.session file
- Output: Saves to `output/` directory

---

### Feature 7: Admin Panel Web Application

#### Description
Web-based read-only dashboard for viewing team member access, audit results, and reports. Includes interactive Telegram audit trigger with 2FA support.

#### Requirements

**Must Have:**
- ✅ **Read-Only Dashboard**: View employees, audit history, and reports
- ✅ **Automated Daily Audits**: Slack audits run automatically via Heroku Scheduler (2:00 AM UTC)
- ✅ **Interactive Telegram Audit**: Manual trigger button with 2FA code/password input
- ✅ **Audit History**: View past audit runs with detailed findings
- ✅ **Employee Management View**: View all team members with status (active/inactive/optional)
- ✅ **Database Integration**: SQLite database storing employees, audits, findings
- ✅ **Heroku Deployment**: Production-ready deployment with Gunicorn

**Should Have:**
- ✅ Session file sharing between webapp and audit script
- ✅ Real-time progress updates via polling
- ✅ Background job processing to prevent timeouts

**Could Have:**
- ⏳ Email notifications for audit failures
- ⏳ Export audit reports to PDF
- ⏳ Historical trend charts

**Won't Have (Yet):**
- ❌ Write operations via UI (employee editing, manual Slack audits)
- ❌ Offboarding triggers via UI (done via scripts only)
- ❌ Multi-user authentication (public read-only access)

#### Technical Implementation

**Stack:**
- **Flask**: Python web framework
- **Heroku Postgres**: Production database (Essential-0, 1 GB, persistent)  
- **SQLite**: Local development fallback
- **Gunicorn**: WSGI server (2 workers, sync)
- **Heroku Scheduler**: Daily automated **Slack-only** audits at 2:00 AM UTC

**Authentication Flow (Telegram - Manual Only):**
1. User clicks "Run Telegram Audit" button
2. Backend connects with StringSession from database
3. Requests SMS code if not authenticated
4. Modal displays code input field (real-time polling)
5. User enters code from Telegram app
6. If 2FA enabled, prompts for cloud password
7. **Session string saved to Postgres** (not file)
8. Audit runs in background thread
9. **Full results saved to database** (all channels + JSON)

**Session Management:**
- **StringSession** stored in Postgres `telegram_audit_status.session_string`
- Database-backed (no file locking on Heroku's ephemeral filesystem)
- Persists across deployments and workers
- Minimizes re-authentication frequency

**Database Schema (Postgres):**
- `employees`: Team data (name, Slack ID, Telegram handle, status, requirements)
- `audit_runs`: Execution records (type, status, timestamps, coverage stats, **results_json**)
- `audit_findings`: Channels/groups with issues only (missing members)
- `telegram_audit_status`: Real-time status, session, 2FA (cleared after use)
- `offboarding_tasks`: Offboarding history (read-only)

**Data Persistence:**
- ✅ All audit data saved to Postgres (permanent)
- ✅ Employee data persists across restarts
- ✅ Telegram session persists (no re-auth needed)
- ✅ Full audit results (120+ Slack, 412+ Telegram) stored as JSON

#### User Flow

**Daily Automated Audit:**
1. Heroku Scheduler triggers at 2:00 AM UTC
2. Runs `scripts/customer_group_audit.py`
3. Results saved to database
4. Webapp displays latest audit on Dashboard

**Manual Telegram Audit:**
1. User navigates to Audits page
2. Clicks "✈️ Run Telegram Audit" button
3. Modal opens requesting authentication
4. User enters SMS code from Telegram app
5. If 2FA enabled, enters cloud password
6. Audit runs in background (Slack + Telegram)
7. Modal shows progress updates
8. Results appear in Audit History when complete

#### Deployment

**Heroku Configuration:**
- **App**: `bitsafe-group-admin`
- **URL**: https://bitsafe-group-admin-30c4bbdb5186.herokuapp.com/
- **Scheduler**: Daily **Slack-only** audit at 2:00 AM UTC (uses `--skip-telegram` flag)
- **Database**: Heroku Postgres Essential-0 (persistent, 1 GB, 20 max connections)
- **Dynos**: Web dyno only (worker removed - using Heroku Scheduler instead)
- **Environment Variables**: `DATABASE_URL`, `SLACK_USER_TOKEN`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`
- **Python Version**: 3.11 (specified in `.python-version`)

#### Success Metrics

- **Accessibility**: Dashboard accessible 24/7 for viewing audit results
- **Audit Frequency**: Daily automated Slack audits catch new channels immediately
- **User Adoption**: Head of Growth reviews dashboard weekly
- **Telegram Audit Usage**: On-demand Telegram audits when needed (typically weekly)

#### Dependencies

- **Flask 3.0.0**: Web framework
- **Telethon 1.36.0**: Telegram API client
- **APScheduler 3.10.4**: Background job scheduling (not used - Heroku Scheduler instead)
- **Gunicorn 21.2.0**: Production WSGI server
- **pandas, openpyxl**: Audit script dependencies

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

### V1.0 (Current Release) - Completed
- ✅ **Web UI / Dashboard** - Built as read-only admin panel (v1.4.2)
- ❌ Automated member invitations (partially - bulk addition tool exists)
- ❌ CRM integration
- ❌ Multi-workspace Slack support
- ❌ Historical trend analysis
- ❌ Real-time monitoring/alerts

### Future Considerations
- **V1.5**: Write operations via UI (employee editing, status changes)
- **V2.0**: Automated member management (invite/remove) via UI
- **V2.5**: Historical trend analysis and charts
- **V3.0**: CRM integration and customer account mapping
- **V4.0**: AI-powered insights on customer engagement

---

## Technical Architecture

### Components

```
slack-tools/
├── scripts/
│   ├── customer_group_audit.py      # Main audit script
│   ├── add_members_to_channels.py   # Bulk member addition tool
│   ├── slack_export.py              # Slack export utilities
│   └── telegram_export.py           # Telegram export utilities
├── config/
│   └── customer_group_categories.json  # Group categorization config
├── data/
│   └── raw/
│       └── slack_export_*/
│           └── channels/
│               └── private_channels.json  # Slack channel metadata
├── docs/
│   ├── customer-group-audit.md      # Audit tool documentation
│   ├── add-members-tool.md          # Member addition tool documentation
│   ├── add-write-scope.md           # Slack write permissions setup
│   └── slack-export-howto.md        # Slack export guide
├── output/
│   ├── audit_reports/               # Audit Excel reports
│   └── add_members_*.log            # Member addition operation logs
└── .env                              # API credentials (git-ignored)
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
- `conversations.invite` - Add members to channels (bulk addition tool)
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
- [Bulk Member Addition Tool Documentation](docs/add-members-tool.md)
- [Slack Write Permissions Setup](docs/add-write-scope.md)
- [Slack Export How-To](docs/slack-export-howto.md)

### Changelog

- **2025-12-01**: V1.4.2 - Admin Panel Web Application with Interactive Telegram Audit
  - Built read-only Flask webapp for viewing employees, audits, and reports
  - Deployed to Heroku: https://bitsafe-group-admin-30c4bbdb5186.herokuapp.com/
  - Interactive Telegram audit with 2FA support (SMS code + password)
  - Automated daily Slack audits via Heroku Scheduler (2:00 AM UTC)
  - SQLite database with 4 tables (employees, audit_runs, audit_findings, offboarding_tasks)
  - Session file sharing between webapp and audit script
  - Background job processing for long-running audits
  - Read-only UI design - all write operations via command-line scripts
- **2025-12-01**: V1.4.1 - Admin Panel Made Fully Read-Only
  - Removed all edit/deactivate buttons from Employees page
  - Removed Actions column entirely
  - Removed Offboarding tab from navigation (to avoid alarming employees)
  - Removed all manual audit triggers (audits only via scheduler)
  - All write operations now done via scripts/database directly
- **2025-01-19**: V1.1 - Added Feature 4: Bulk Member Addition tool
  - Automates adding team members to all BitSafe Slack channels
  - Dry-run mode for safe testing
  - Detailed logging and error handling
  - Successfully added Aliya Gordon and Kevin Huet to 67 channels (132 memberships)
- **2024-11-17**: V1.0 - Initial PRD created with customer group audit as primary feature

