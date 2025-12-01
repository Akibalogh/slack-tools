# Admin Panel Design - Customer Group Access Management

## Overview
Web application for **viewing** team member access to customer Slack channels and Telegram groups, with automated daily audits. This is a **read-only reporting interface** - all write operations (employee management, manual audits, offboarding) are handled via command-line scripts.

## Current Status (v1.4.1)
The webapp is deployed as a **read-only dashboard**:
- ✅ **View** employees, audits, and reports
- ❌ No manual audit triggers (audits run via Heroku Scheduler at 2:00 AM UTC daily)
- ❌ No employee editing/status changes (managed via scripts/database)
- ❌ No offboarding triggers (done via command-line scripts)
- ❌ Offboarding tab hidden to avoid alarming employees

## Architecture

### Components
1. **Flask Web Application** - Admin UI
2. **SQLite Database** - Employee & audit data
3. **APScheduler** - Automated daily audits
4. **Integration Layer** - Connects to existing scripts

### Database Schema

```sql
-- employees table
CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slack_username TEXT,
    slack_user_id TEXT,
    telegram_username TEXT,
    email TEXT,
    status TEXT NOT NULL DEFAULT 'active',  -- active, inactive, optional
    slack_required BOOLEAN DEFAULT 1,
    telegram_required BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- audit_runs table
CREATE TABLE audit_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_type TEXT NOT NULL,  -- scheduled, manual
    status TEXT NOT NULL,  -- running, completed, failed
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    slack_channels_total INTEGER,
    slack_channels_complete INTEGER,
    telegram_groups_total INTEGER,
    telegram_groups_complete INTEGER,
    report_path TEXT,
    error_message TEXT
);

-- audit_findings table
CREATE TABLE audit_findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_run_id INTEGER NOT NULL,
    platform TEXT NOT NULL,  -- slack, telegram
    channel_name TEXT NOT NULL,
    channel_id TEXT,
    missing_members TEXT,  -- JSON array
    status TEXT,  -- incomplete, permission_denied, archived
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (audit_run_id) REFERENCES audit_runs(id)
);

-- offboarding_tasks table
CREATE TABLE offboarding_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    platform TEXT NOT NULL,  -- slack, telegram, both
    status TEXT NOT NULL,  -- pending, running, completed, failed
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    groups_processed INTEGER,
    groups_removed INTEGER,
    groups_failed INTEGER,
    report_path TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);
```

## Features (Current Implementation)

### 1. Employee Management (Read-Only)
- ✅ **List View**: All employees with status badges
- ❌ **Add/Edit**: Removed - use command-line scripts
- ❌ **Status Toggle**: Removed - update via database directly
- ❌ **Bulk Actions**: Removed - managed via scripts

**Note**: Employee data is seeded from `webapp/database.py`. To modify employees, edit the seed data and redeploy.

### 2. Audit Dashboard (Read-Only)
- ✅ **Current Status**: Live view of latest audit results
- ❌ **Run Manual Audit**: Removed - audits run via Heroku Scheduler
- ✅ **Audit History**: Past audit runs with drill-down
- ✅ **Incomplete Channels**: List of channels missing members
- ❌ **Quick Fix**: Removed - remediation done via scripts

**Note**: Audits run automatically daily at 2:00 AM UTC via Heroku Scheduler job: `cd scripts && python3 customer_group_audit.py`

### 3. Offboarding Center (Hidden)
- ❌ **Tab Removed**: Hidden from navigation to avoid alarming employees
- ❌ **Trigger Offboarding**: Use command-line scripts instead
- ✅ **History**: Still accessible at `/offboarding` URL (view-only)

**Rationale**: Offboarding tab removed to prevent employees from seeing who is being offboarded. Actual offboarding is triggered via:
- Slack: `scripts/slack_admin.py` (or manual via Slack admin console)
- Telegram: `scripts/telegram_user_delete.py`

### 4. Scheduled Jobs
- ✅ **Daily Audit**: Runs at 2:00 AM UTC via Heroku Scheduler
- ❌ **Weekly Report**: Not implemented
- ❌ **Auto-remediation**: Not implemented - manual remediation via scripts

## API Endpoints (Current Implementation)

### Employee Management
- ✅ `GET /api/employees` - List all employees
- ❌ `POST /api/employees` - **DISABLED**
- ❌ `PUT /api/employees/<id>` - **DISABLED**
- ❌ `DELETE /api/employees/<id>` - **DISABLED**
- ❌ `PATCH /api/employees/<id>/status` - **DISABLED** (commented out in code)

### Audit Operations
- ❌ `POST /api/audit/run` - **DISABLED** (commented out in code)
- ✅ `GET /api/audit/latest` - Get latest audit results
- ✅ `GET /api/audit/history` - Get audit history (via `/audits` page)
- ✅ `GET /api/audit/<id>` - Get specific audit details (via `/audits/<id>` page)
- ❌ `POST /api/audit/<id>/remediate` - **DISABLED**

### Offboarding
- ❌ `POST /api/offboard` - **DISABLED** (commented out in code)
- ✅ `GET /api/offboard/status/<id>` - Get offboarding status (read-only)
- ✅ `GET /api/offboard/history` - Get offboarding history (via `/offboarding` page)

### Scheduler
- ❌ Not implemented - scheduler runs via Heroku Scheduler add-on

## UI Pages (Current Implementation)

### 1. Dashboard (`/`)
- ✅ Quick stats (total employees, active, inactive)
- ✅ Latest audit summary
- ❌ Recent offboarding tasks - Removed
- ❌ Quick actions - Removed (except view-only links)
- ℹ️ Shows message: "Audits run automatically daily at 2:00 AM UTC via Heroku Scheduler"

### 2. Employees (`/employees`)
- ✅ Sortable/filterable table (by status: All, Active, Inactive, Optional)
- ✅ Status badges (🟢 Active, 🔴 Inactive, 🟡 Optional)
- ❌ Quick actions - **Removed** (no Edit, Toggle Status, Offboard buttons)
- ❌ Add new employee button - **Removed**
- ❌ Actions column - **Removed entirely**
- ℹ️ Shows message: "This is a read-only view. Use command-line scripts to manage employees."

### 3. Audits (`/audits`)
- ✅ Audit history table
- ✅ Latest audit detailed view
- ✅ Incomplete channels list
- ❌ Manual audit trigger button - **Removed**
- ❌ Remediation actions - **Removed**
- ℹ️ Shows message: "Audits run automatically daily at 2:00 AM UTC via Heroku Scheduler"

### 4. Offboarding (`/offboarding`)
- ❌ **Tab Hidden** - Removed from navigation
- ✅ Still accessible via direct URL `/offboarding` (view-only)
- ✅ Shows offboarding history
- ❌ All action buttons removed

**Rationale**: Tab removed from navigation to avoid alarming employees who might see it.

### 5. Settings (`/settings`)
- ❌ Not implemented

## Security
- Environment variables for API keys
- Session-based authentication (optional)
- CSRF protection
- Input validation
- Rate limiting on API endpoints

## Deployment
- Docker container (optional)
- Heroku-ready with Procfile
- SQLite for simplicity (can upgrade to Postgres)
- Background worker for long-running tasks (Celery or APScheduler)

## Future Enhancements
- Email notifications for audit failures
- Slack notifications for offboarding completion
- Multi-user admin access with roles
- Approval workflow for offboarding
- Audit diff view (changes since last audit)
- Export audit reports to PDF

