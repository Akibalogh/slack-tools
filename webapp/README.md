# Customer Group Admin Panel (v1.6.0)

**Production URL**: https://bitsafe-group-admin-30c4bbdb5186.herokuapp.com

Web-based read-only dashboard with **real-time progress tracking** for monitoring team member access to customer Slack channels and Telegram groups.

## Features

- **⚡ Real-Time Progress**: Live incremental updates every 50 Telegram groups during audits
- **🎨 Brand Logos**: Official Slack and Telegram icons throughout UI (Font Awesome)
- **🔐 Saved Sessions**: One-time 2FA authentication, then automatic audits (StringSession)
- **📊 Dashboard**: Real-time overview with live progress (120 Slack channels, 413 Telegram groups)
- **👥 Team Members**: View 11 employees with sortable columns and checkmarks
- **🔍 Automated Slack Audits**: Daily at 2:00 AM UTC via Heroku Scheduler (Slack-only, no 2FA)
- **✈️ One-Click Telegram Audit**: Full audit (Slack + Telegram) using saved session
- **📈 Enhanced Audit Visualization**: Detailed tables showing:
  - **Category** (BD Customer / Marketing / Internal)
  - **Has BitSafe Name** (active vs retired groups)
  - **Admin Status** (Owner / Admin / Member) ← flags groups where you lack admin rights
  - **History Visibility** (Hidden / Visible) ← privacy concerns
  - **Missing Members** (Sarah, Kevin, Aliya, Jesse, etc.)
  - **Completeness** (e.g., 6/9 required)
- **🗄️ Persistent Storage**: Heroku Postgres (survives dyno restarts)
- **🔒 Security**: HTTPS, temporary 2FA storage (30 min max), StringSession for Telegram

**Read-Only Design**: No employee editing, no Slack audit triggers, no offboarding via UI. All write operations done via command-line scripts.

## Quick Start

### 1. Setup

```bash
# From project root
cd webapp

# Install dependencies (if not already in venv)
pip install -r requirements.txt

# Initialize database
python3 database.py
```

### 2. Start the Server

```bash
# Using the startup script (recommended)
./start.sh

# Or manually
python3 app.py
```

### 3. Access the Panel

Open your browser to: **http://localhost:5001**

## Project Structure

```
webapp/
├── app.py              # Main Flask application
├── database.py         # Database setup and schema
├── scheduler.py        # Background scheduler for cron jobs
├── start.sh            # Startup script
├── requirements.txt    # Python dependencies
├── templates/          # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── employees.html
│   ├── employee_form.html
│   ├── audits.html
│   └── offboarding.html
└── README.md           # This file
```

## Database Schema (Heroku Postgres)

### employees
- **11 team members** with required/optional status per platform
- Fields: `name`, `email`, `slack_username`, `slack_user_id`, `telegram_username`, `status`, `slack_required`, `telegram_required`
- Status: `active` (11), `inactive` (0), `optional` (1 - Anna)
- Slack required: 11 members
- Telegram required: 9 members (Kevin, Aliya, Sarah added in v1.5.0)

### audit_runs
- Tracks audit execution history (scheduled Slack + manual Telegram)
- Fields: `run_type`, `status`, `started_at`, `completed_at`, `slack_channels_total`, `slack_channels_complete`, `telegram_groups_total`, `telegram_groups_complete`, `report_path`, `results_json` (full audit data)
- **results_json**: Complete audit results with all fields (Category, Admin Status, History Visibility, etc.)

### audit_findings
- Stores incomplete channels/groups from each audit
- Links to `audit_runs` via foreign key
- Fields: `channel_name`, `platform`, `missing_members`, `required_members`

### telegram_audit_status
- **Single-row table** (id=1) for tracking Telegram audit state across workers
- Fields: `status`, `message`, `error`, `code`, `password`, `session_string`, `updated_at`
- Status values: `idle`, `requesting_code`, `waiting_for_code`, `authenticating`, `running`, `completed`, `error`
- **session_string**: Telethon StringSession for persistent authentication

### offboarding_tasks
- Tracks offboarding history (view-only, no triggers from UI)
- Fields: `employee_id`, `platform`, `status`, `started_at`, `completed_at`, `channels_removed`, `channels_failed`

## Usage

### Viewing Team Members

1. Go to **Employees** tab
2. View all 11 team members with:
   - Full names
   - Slack usernames and IDs
   - Telegram handles
   - Required/optional status for each platform
3. **No editing available** - employee data managed via `webapp/database.py`

### Running Audits

**Automated Daily Slack Audit:**
- Runs automatically every day at 2:00 AM UTC via Heroku Scheduler
- Command: `python scripts/customer_group_audit.py --skip-telegram`
- Takes 5-10 minutes
- Results appear in "Scheduled Slack Audits" section
- **No manual trigger available** (automated only)

**Manual Telegram Audit (Full Audit):**
1. Go to **Audits** tab
2. Click **✈️ Run Telegram Audit** button
3. Modal opens requesting 2FA authentication
4. **Enter SMS code** from Telegram
5. **Enter 2FA password** if you have cloud password enabled
6. Wait 13-18 minutes for full audit (Slack + Telegram)
7. Modal shows real-time progress
8. Results appear in "Manual Telegram Audits" section
9. Click **View Details** to see comprehensive report with:
   - All 120 Slack channels
   - All 413 Telegram groups
   - Category, Admin Status, History Visibility
   - Has BitSafe Name flag
   - Missing members per group

**Note**: Manual Telegram audit runs BOTH Slack AND Telegram checks. Use "View Details" to see full tables with all audit fields.

### Viewing Audit Results

**Dashboard Summary:**
- Latest audit coverage (120/120 Slack, 413/413 Telegram)
- Quick link to detailed audit report

**Audit Detail Page:**
- **Slack Channels Table**: All 120 channels with required/missing members
- **Telegram Groups Table**: First 50 of 413 groups showing:
  - Group Name
  - **Category** (BD Customer highlighted)
  - **Has BitSafe Name** (✓ YES green for active, No gray for retired)
  - **Admin Status** (Member in red = no admin rights warning)
  - **History Visibility** (Hidden in red = privacy concern)
  - Missing Members
  - Completeness (6/9 required)

### Managing Team Members (via CLI)

**Adding a new employee:**
```bash
# Edit webapp/database.py
# Add to team_members list in seed_database()
# Re-run database seeding
heroku run --app bitsafe-group-admin "python webapp/database.py"
```

**Employee offboarding:**
```bash
# Use command-line scripts (not via webapp)
python scripts/telegram_user_delete.py
# Slack offboarding done manually via Slack admin console
```

## Integration with Existing Scripts

The webapp integrates with existing CLI scripts:

- **Audits**: Calls `scripts/customer_group_audit.py`
- **Telegram Offboarding**: Calls `scripts/telegram_user_delete.py`
- **Slack Offboarding**: Manual process (typically done via Slack admin console)

## API Endpoints

### Read-Only Endpoints
- `GET /` - Dashboard page
- `GET /employees` - Employee list page
- `GET /audits` - Audit history page
- `GET /audits/<id>` - Detailed audit report with full tables
- `GET /api/employees` - JSON list of all employees
- `GET /api/audit/latest` - Latest audit summary

### Telegram Audit Endpoints (Interactive)
- `POST /api/audit/telegram/start` - Start Telegram audit (requests 2FA)
- `GET /api/audit/telegram/status` - Check audit status (polling endpoint)
- `POST /api/audit/telegram/code` - Submit SMS code
- `POST /api/audit/telegram/password` - Submit 2FA password

### Disabled Endpoints (Read-Only Design)
- ~~`PATCH /api/employees/<id>/status`~~ - Employee editing (use database.py)
- ~~`POST /api/audit/run`~~ - Manual Slack audit (use Heroku Scheduler)
- ~~`POST /api/offboard`~~ - Offboarding (use CLI scripts)

## Configuration

### Environment Variables

Required for operation:
- `SLACK_USER_TOKEN` - Slack API token
- `TELEGRAM_API_ID` - Telegram API ID
- `TELEGRAM_API_HASH` - Telegram API hash
- `TELEGRAM_PHONE` - Telegram phone number

Optional:
- `PORT` - Web server port (default: 5001)
- `FLASK_ENV` - Flask environment (development/production)
- `FLASK_SECRET_KEY` - Flask secret key (set for production)

### Scheduler Configuration

Edit `scheduler.py` to change:
- Audit schedule (default: daily at 2 AM)
- Timeout values
- Report paths

## Deployment

### Local Development
```bash
cd webapp
python3 database.py  # Initialize DB
python3 app.py       # Start Flask dev server on port 5001
```

### Production (Heroku)

**Current Deployment**: https://bitsafe-group-admin-30c4bbdb5186.herokuapp.com

**Procfile Configuration**:
```
web: cd webapp && gunicorn app:app --timeout 300
release: python database.py
```

**Heroku Add-ons**:
- `heroku-postgresql` (Standard-0 plan) - Persistent database
- Heroku Scheduler - Daily Slack audits at 2:00 AM UTC

**Scheduler Configuration**:
- Command: `python scripts/customer_group_audit.py --skip-telegram`
- Frequency: Daily at 2:00 AM UTC
- Duration: 5-10 minutes

**Environment Variables** (set via `heroku config:set`):
```bash
SLACK_USER_TOKEN=xoxp-...
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=abc123...
TELEGRAM_PHONE=+1234567890
DATABASE_URL=postgres://...  # Auto-set by Heroku Postgres
FLASK_SECRET_KEY=random-secret-key
```

**Deploy Command**:
```bash
git push heroku main
# Database auto-initializes via release phase
# No manual seeding required
```

**Database Seeding**:
- Automatic on first deployment (release phase runs `database.py`)
- Manual re-seed: `heroku run --app bitsafe-group-admin "python database.py"`

## Troubleshooting

### Database Issues
```bash
# Reset database
rm data/admin_panel.db
python3 database.py
```

### Scheduler Not Running
```bash
# Check process
ps aux | grep scheduler.py

# Restart
pkill -f scheduler.py
python3 scheduler.py &
```

### Audit Fails
- Check that `scripts/customer_group_audit.py` runs successfully
- Verify environment variables are set
- Check logs in `output/reports/`

### Offboarding Fails
- Check Telegram session file exists
- Verify Telegram API credentials
- Check logs in `output/offboarding/`

## Future Enhancements

- [ ] Email notifications for audit results
- [ ] Slack notifications for offboarding completion
- [ ] Multi-user authentication
- [ ] Approval workflow for offboarding
- [ ] Export audit reports to PDF
- [ ] Real-time progress updates (WebSockets)
- [ ] Slack offboarding automation

## Support

For issues or questions, check:
- Main project README
- Employee Offboarding Guide: `docs/Employee_Offboarding_Guide.md`
- Customer Group Audit SOP: `docs/Customer_Group_Membership_Audit_SOP.md`

