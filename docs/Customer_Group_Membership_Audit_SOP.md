# Customer Group Membership Audit - Standard Operating Procedure

**Last Updated:** November 27, 2024  
**Version:** 1.0  
**Owner:** BitSafe Operations Team

---

## Overview

This document outlines the standard operating procedure for auditing and maintaining team member access across all customer communication channels (Slack and Telegram).

## Membership Policy

### Slack Channels - Required Members (8 Total)

**All BitSafe customer Slack channels must include:**
1. Aki Balogh (CEO) - @aki
2. Gabi Tui (Head of Product) - @gabi
3. Mayank (Sales Engineer) - @mayank
4. Kadeem Clarke (Head of Growth) - @kadeem
5. Amy Wu (BD) - @amy
6. Kevin Huet - @kevin
7. Aliya Gordon - @aliya
8. Dave Shin - @dave

**Note:** Dae Lee's inclusion policy is under review (TBD)

### Telegram Groups - Required Members (5 Core Only)

**Only core team members required in Telegram groups:**
1. Aki Balogh (CEO) - @akibalogh
2. Gabi Tui (Head of Product) - @gabitui
3. Mayank (Sales Engineer) - @mojo_onchain
4. Kadeem Clarke (Head of Growth) - @kadeemclarke
5. Amy Wu (BD) - @NonFungibleAmy

**NOT required in Telegram groups:** Kevin, Aliya, Dave, Dae

---

## Audit Process

### Phase 1: Identification

**Objective:** Identify all customer channels/groups and determine which are missing required team members.

**Steps:**

1. **Run Full Audit Script**
   ```bash
   cd /Users/akibalogh/apps/slack-tools
   source venv/bin/activate
   python3 scripts/customer_group_audit.py
   ```

2. **Review Generated Report**
   - Location: `output/audit_reports/customer_group_audit_[timestamp].xlsx`
   - Check Slack channels for 8/8 required members
   - Check Telegram groups for 5/5 required members
   - Note any missing members

3. **Generate Missing Members Report** (for Slack)
   ```python
   import pandas as pd
   df = pd.read_excel('output/audit_reports/customer_group_audit_[latest].xlsx')
   slack_df = df[df['Platform'] == 'Slack']
   missing = slack_df[~slack_df['Completeness'].str.startswith('8/')]
   missing.to_csv('output/reports/slack_missing_members_[date].csv', index=False)
   ```

**Expected Output:**
- Excel report with 528+ records (118 Slack + 410 Telegram)
- CSV of Slack channels with missing members
- Console summary with statistics

### Phase 2: Remediation (Slack Only)

**Objective:** Add missing team members to Slack channels.

**Steps:**

1. **Use Targeted Addition Script** (for specific missing members)
   ```bash
   python3 scripts/add_missing_members_targeted.py --dry-run
   # Review output, then:
   python3 scripts/add_missing_members_targeted.py --yes
   ```

2. **Use Bulk Addition Script** (for adding one person to all channels)
   ```bash
   python3 scripts/add_members_to_channels.py <username> --dry-run
   # Review output, then:
   python3 scripts/add_members_to_channels.py <username> --yes
   ```

3. **Verify Additions**
   - Run audit script again to confirm completeness
   - Check sample channels manually in Slack workspace
   - Document any errors (archived channels, permission issues)

**Expected Results:**
- 100% of active Slack channels have all 8 required members
- Archived channels documented as exceptions
- Addition logs saved to `logs/` directory

### Phase 3: Verification & Documentation

**Objective:** Confirm all changes were successful and document the audit.

**Steps:**

1. **Run Final Verification Audit**
   ```bash
   python3 scripts/customer_group_audit.py
   ```

2. **Review Final Report**
   - Verify Slack channels show 8/8 for active channels
   - Verify Telegram groups show 5/5 (or acceptable variations)
   - Document any exceptions with reasons

3. **Document Results**
   - Update this SOP if process changed
   - Save final report to permanent location
   - Create summary for stakeholders if needed

---

## Key Scripts & Tools

### 1. customer_group_audit.py

**Purpose:** Comprehensive audit of all Slack and Telegram customer groups

**Features:**
- Automatically fetches live data from Slack API (not cached exports)
- Audits all Telegram groups via Telegram API
- Generates detailed Excel reports with 14 columns
- Supports separate membership policies per platform
- Tracks completeness, privacy, history visibility, admin status

**Usage:**
```bash
python3 scripts/customer_group_audit.py
```

**Output:**
- Excel report: `output/audit_reports/customer_group_audit_[timestamp].xlsx`
- Console summary with statistics and flags

**Configuration:**
- Edit `REQUIRED_SLACK_MEMBERS` for Slack membership policy
- Edit `REQUIRED_TELEGRAM_MEMBERS` for Telegram membership policy
- Edit `SLACK_USERNAME_MAP` to map Slack usernames
- Update categorization rules in `config/customer_group_categories.json`

### 2. add_members_to_channels.py

**Purpose:** Bulk add one or more team members to all BitSafe Slack channels

**Features:**
- Supports dry-run mode for testing
- Uses live Slack API (not cached exports)
- Handles errors gracefully (archived channels, permission issues)
- Provides detailed statistics

**Usage:**
```bash
# Single member
python3 scripts/add_members_to_channels.py dave --dry-run
python3 scripts/add_members_to_channels.py dave --yes

# Multiple members (space-separated)
python3 scripts/add_members_to_channels.py kevin aliya --yes
```

**Output:**
- Console summary with success/error counts
- Logs saved to `logs/` if using tee

### 3. add_missing_members_targeted.py

**Purpose:** Add only specific missing members to specific channels (targeted approach)

**Features:**
- Reads from missing members CSV report
- Adds only the members actually missing from each channel
- More efficient than bulk addition for partial updates
- Hardcoded user IDs for reliability

**Usage:**
```bash
python3 scripts/add_missing_members_targeted.py --dry-run
python3 scripts/add_missing_members_targeted.py --yes
```

**Prerequisites:**
- Requires `output/reports/slack_missing_members_[date].csv` to exist
- Generate this from audit report first

**Output:**
- Console output with per-channel results
- Summary statistics

---

## Common Scenarios

### Scenario 1: New Team Member Joins

**Steps:**
1. Add new member to appropriate policy list in `customer_group_audit.py`:
   - `REQUIRED_SLACK_MEMBERS` if they should be in all Slack channels
   - `REQUIRED_TELEGRAM_MEMBERS` if they should be in all Telegram groups
2. Add username mapping to `SLACK_USERNAME_MAP`
3. Run bulk addition script for Slack:
   ```bash
   python3 scripts/add_members_to_channels.py <username> --yes 2>&1 | tee logs/add_<username>_$(date +%Y%m%d_%H%M%S).log
   ```
4. For Telegram (if required), use `telegram_admin.py add-user` command
5. **REQUIRED:** Generate detailed addition report documenting which channels the member was added to
6. Run verification audit
7. Document results and save all reports

**Report Requirements:**
After adding any member to Slack or Telegram groups, ALWAYS create a comprehensive report showing:
- Member name and user ID
- Complete list of channels/groups they were added to
- Channels they were already in
- Any errors or permission issues encountered
- Timestamp of each operation

**Report Format:** Use `output/reports/member_additions_<username>_<timestamp>.md` format

**Recent Example:** Dave Shin added November 27, 2024
- Added to `REQUIRED_SLACK_MEMBERS`
- Ran `add_members_to_channels.py dave --yes`
- Generated comprehensive report: `output/reports/member_additions_comprehensive_20251127.md`
- Successfully added to 20 new channels
- Already in 116 channels
- 6 errors (permission issues)
- 2 archived channels (expected)

### Scenario 2: Quarterly Membership Audit

**Steps:**
1. Run full audit: `python3 scripts/customer_group_audit.py`
2. Review report for completeness
3. Generate missing members CSV for any incomplete channels
4. Run targeted addition script if needed
5. Re-run audit to verify
6. Archive report for compliance records

**Frequency:** Quarterly or after major team changes

### Scenario 3: Member Leaves Company

**For Slack:**
- Use Slack workspace admin console to deactivate account
- Member is automatically removed from all channels

**For Telegram:**
```bash
python3 scripts/telegram_user_delete.py --username <user> --dry-run
# Review, then:
python3 scripts/telegram_user_delete.py --username <user>
```

**Recent Example:** Addie (@nftaddie) offboarded November 7, 2024
- See `docs/Employee_Offboarding_Guide.md` for full process

---

## Error Handling

### Common Errors & Solutions

**1. Archived Channels**
- **Error:** `is_archived`
- **Solution:** Document as exception, no action needed
- **Example:** x-bitsafe, loxor-finance-bitsafe

**2. Permission Issues**
- **Error:** `cant_invite_self`, `missing_scope`
- **Solution:** Verify Slack token has correct scopes, check if user already present
- **Prevention:** Use SLACK_USER_TOKEN with groups:write, channels:write scopes

**3. Telegram Session Locked**
- **Error:** `sqlite3.OperationalError: database is locked`
- **Solution:** Remove session files: `rm -f telegram_session.session*`
- **Prevention:** Ensure only one Telegram script runs at a time

**4. Telegram Authentication**
- **Error:** `EOFError: EOF when reading a line`
- **Solution:** Run interactively in iTerm or set TELEGRAM_CODE environment variable
- **Prevention:** Keep session files for reuse

---

## Automation Opportunities

### Current Manual Steps
1. Running audit script
2. Analyzing report
3. Running addition scripts
4. Verifying results

### Recommended Automation
1. **Scheduled Audits:** Set up cron job to run monthly audits
2. **Auto-Detection:** Flag new channels missing required members
3. **Auto-Addition:** Automatically add required members to new channels
4. **Slack Webhooks:** Trigger audit when new channels created
5. **Dashboard:** Real-time view of channel membership completeness

### Implementation Priority
1. **High:** Scheduled monthly audits (low effort, high value)
2. **Medium:** Auto-detection of incomplete channels
3. **Low:** Real-time dashboard (high effort)

---

## Data Files & Locations

### Configuration
- **Slack Token:** `.env` → `SLACK_USER_TOKEN`
- **Telegram Credentials:** `.env` → `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`
- **Team Members:** `scripts/customer_group_audit.py` → `REQUIRED_SLACK_MEMBERS`, `REQUIRED_TELEGRAM_MEMBERS`
- **Group Categories:** `config/customer_group_categories.json`

### Reports
- **Audit Reports:** `output/audit_reports/customer_group_audit_[timestamp].xlsx`
- **Missing Members:** `output/reports/slack_missing_members_[date].csv`
- **Addition Logs:** `logs/add_members_*`, `logs/telegram_*`

### Session Files
- **Telegram Session:** `telegram_session.session` (root directory)
- **Note:** Keep this file to avoid repeated authentication

---

## Compliance & Audit Trail

### Record Retention

**Keep the following for compliance:**
1. All audit reports (Excel files)
2. All addition/removal logs
3. Error logs and exception documentation
4. Timestamps of all operations

**Storage Location:** `output/audit_reports/` and `logs/`

**Retention Period:** Minimum 2 years for compliance

### Audit Trail Components

Each operation creates:
1. **Timestamped logs** - All actions with user IDs and results
2. **Excel reports** - Before and after states
3. **Error documentation** - Reasons for failures
4. **Summary statistics** - Success/failure counts

**Example Trail:**
- `logs/group_audit_20251127_094748.log` - Initial audit
- `output/reports/slack_missing_members_20251125_170324.csv` - Identified gaps
- `logs/add_missing_members_live_20251125_170739.log` - Remediation
- `logs/add_dave_shin_20251125_172241.log` - New member addition
- `output/audit_reports/customer_group_audit_20251127_094748.xlsx` - Final state

---

## Troubleshooting

### Slack API Issues

**Rate Limiting:**
- Scripts include 1-second delays between operations
- If still rate-limited, increase sleep time in scripts

**Missing Scopes:**
- Verify token has: `channels:read`, `channels:write`, `groups:read`, `groups:write`, `users:read`
- Regenerate token if scopes missing

**Channel Not Found:**
- Channel may be archived or deleted
- Check in Slack workspace manually
- Document as exception

### Telegram API Issues

**Session Locked:**
```bash
rm -f telegram_session.session*
```

**Authentication Required:**
- Run script interactively first time
- Or set `TELEGRAM_CODE` environment variable
- Save session file for future use

**Permission Denied:**
- Check admin status in group
- May need to request ownership transfer
- Document groups without admin access

---

## Quick Reference

### Daily Operations

**Check if new member needs access:**
```bash
python3 scripts/customer_group_audit.py
# Review report for their presence
```

**Add single member to all Slack channels:**
```bash
# Always log output and generate report
python3 scripts/add_members_to_channels.py <username> --yes 2>&1 | tee logs/add_<username>_$(date +%Y%m%d_%H%M%S).log

# Then create detailed report showing which channels they were added to
# Save to: output/reports/member_additions_<username>_<timestamp>.md
```

**Add missing members to specific Slack channels:**
```bash
# First generate missing members report from audit
python3 scripts/add_missing_members_targeted.py --yes 2>&1 | tee logs/add_missing_targeted_$(date +%Y%m%d_%H%M%S).log

# Generate report of additions
```

**Run monthly audit:**
```bash
python3 scripts/customer_group_audit.py
# Archive report to permanent storage
```

**⚠️ IMPORTANT:** After ANY member addition operation (Slack or Telegram), you MUST:
1. Save command output logs
2. Generate a detailed report showing which channels/groups the member was added to
3. Document any errors or permission issues
4. Archive the report for compliance and future reference

### Emergency Operations

**Remove member immediately (Telegram):**
```bash
python3 scripts/telegram_user_delete.py --username <user> --dry-run
python3 scripts/telegram_user_delete.py --username <user>
```

**Remove member (Slack):**
- Use Slack workspace admin console
- Deactivate account (auto-removes from all channels)

---

## Change Log

### November 27, 2024
- Updated membership policy to include Kevin, Aliya, and Dave for Slack only
- Clarified Telegram requires only core 5 members
- Updated audit script with separate member lists per platform

### November 25, 2024
- Added Kevin Huet and Aliya Gordon to 49 Slack channels (initial bulk addition)
- Fixed audit script to use live API instead of cached export data
- Created targeted member addition script

### November 7, 2024
- Completed Addie offboarding process
- Documented Telegram and Slack offboarding procedures

---

## Contact & Support

**For questions or issues:**
- Slack: #operations or #tech-team
- Email: ops@bitsafe.finance
- Documentation: This SOP and `docs/Employee_Offboarding_Guide.md`

**Script Maintenance:**
- All scripts located in `scripts/` directory
- README: `scripts/README.md`
- Issues: Create GitHub issue or notify ops team

