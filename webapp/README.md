# Customer Group Admin Panel

Web-based admin panel for viewing team member access to customer Slack channels and Telegram groups.

## Features

- **📊 Dashboard**: Overview of team members, audit status, and recent activity
- **👥 Employee Management**: View team member status (active/inactive/optional)
- **🔍 Automated Audits**: Daily scheduled audits via Heroku Scheduler (2:00 AM UTC)
- **🚪 Offboarding Center**: View offboarding history (actual offboarding done via scripts)
- **📈 Audit History**: Track audit runs and incomplete channels over time
- **⏰ Scheduler**: Daily automated audits run via Heroku Scheduler

**Note**: This webapp is read-only. All write operations (editing employees, running manual audits, triggering offboarding) are done via command-line scripts.

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

## Database Schema

### employees
- Stores team member information
- Fields: name, email, slack_username, slack_user_id, telegram_username, status
- Status: `active`, `inactive`, `optional`

### audit_runs
- Tracks audit execution history
- Records: run type, status, coverage stats, report paths

### audit_findings
- Stores incomplete channels from audits
- Links to audit runs, includes missing members

### offboarding_tasks
- Tracks offboarding processes
- Records: employee, platform, status, success/failure stats

## Usage

### Managing Employees

1. Go to **Employees** page
2. Click **+ Add Employee** to add new team members
3. Edit employee details or toggle status (Active/Inactive/Optional)
4. Inactive employees can be offboarded from the Offboarding Center

### Running Audits

**Manual Audit:**
1. Go to **Dashboard** or **Audits** page
2. Click **▶ Run Manual Audit**
3. Wait 2-3 minutes for completion
4. View results on Audits page

**Scheduled Audit:**
- Runs automatically every day at 2:00 AM
- No manual intervention required
- Results saved to database and report files

### Offboarding Process

1. Set employee status to **Inactive** on Employees page
2. Go to **Offboarding** page
3. Click **Remove from Slack/Telegram** button for the employee
4. Process runs in background (10-30 minutes for Telegram)
5. Check progress in Offboarding History table

## Integration with Existing Scripts

The webapp integrates with existing CLI scripts:

- **Audits**: Calls `scripts/customer_group_audit.py`
- **Telegram Offboarding**: Calls `scripts/telegram_user_delete.py`
- **Slack Offboarding**: Manual process (typically done via Slack admin console)

## API Endpoints

**Note**: Write endpoints are disabled. The webapp is read-only.

### Employees
- `GET /api/employees` - List all employees
- ~~`PATCH /api/employees/<id>/status`~~ - *(Disabled)* Update employee status

### Audits
- ~~`POST /api/audit/run`~~ - *(Disabled)* Trigger manual audit (audits run via Heroku Scheduler)
- `GET /api/audit/latest` - Get latest audit results

### Offboarding
- ~~`POST /api/offboard`~~ - *(Disabled)* Start offboarding process (done via scripts)
- `GET /api/offboard/status/<id>` - Get offboarding status

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
./start.sh
```

### Production (Heroku)

1. Add to `Procfile`:
```
web: cd webapp && gunicorn app:app
worker: cd webapp && python scheduler.py
```

2. Install gunicorn:
```bash
pip install gunicorn
```

3. Deploy:
```bash
git push heroku main
```

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

