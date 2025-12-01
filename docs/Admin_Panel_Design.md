# Admin Panel Design - Customer Group Access Management

## Overview
Web application for managing team member access to customer Slack channels and Telegram groups, with automated daily audits and offboarding capabilities.

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

## Features

### 1. Employee Management
- **List View**: All employees with status badges
- **Add/Edit**: Form to manage employee details
- **Status Toggle**: Quick toggle between active/inactive/optional
- **Bulk Actions**: Set multiple employees to inactive at once

### 2. Audit Dashboard
- **Current Status**: Live view of latest audit results
- **Run Manual Audit**: Trigger immediate audit
- **Audit History**: Past audit runs with drill-down
- **Incomplete Channels**: List of channels missing members
- **Quick Fix**: One-click to add missing members

### 3. Offboarding Center
- **Inactive Employees**: List of employees marked inactive
- **Trigger Offboarding**: Start removal process
- **Progress Tracking**: Real-time status of offboarding
- **History**: Past offboarding tasks with logs

### 4. Scheduled Jobs
- **Daily Audit**: Runs at 2 AM daily
- **Weekly Report**: Email summary every Monday
- **Auto-remediation** (optional): Automatically add missing members

## API Endpoints

### Employee Management
- `GET /api/employees` - List all employees
- `POST /api/employees` - Create new employee
- `PUT /api/employees/<id>` - Update employee
- `DELETE /api/employees/<id>` - Delete employee
- `PATCH /api/employees/<id>/status` - Update status

### Audit Operations
- `POST /api/audit/run` - Trigger manual audit
- `GET /api/audit/latest` - Get latest audit results
- `GET /api/audit/history` - Get audit history
- `GET /api/audit/<id>` - Get specific audit details
- `POST /api/audit/<id>/remediate` - Fix incomplete channels

### Offboarding
- `POST /api/offboard` - Start offboarding process
- `GET /api/offboard/status/<id>` - Get offboarding status
- `GET /api/offboard/history` - Get offboarding history

### Scheduler
- `GET /api/scheduler/status` - Scheduler status
- `POST /api/scheduler/pause` - Pause scheduled jobs
- `POST /api/scheduler/resume` - Resume scheduled jobs

## UI Pages

### 1. Dashboard (`/`)
- Quick stats (total employees, active, inactive)
- Latest audit summary
- Recent offboarding tasks
- Quick actions (Run Audit, View Reports)

### 2. Employees (`/employees`)
- Sortable/filterable table
- Status badges (🟢 Active, 🔴 Inactive, 🟡 Optional)
- Quick actions (Edit, Toggle Status, Offboard)
- Add new employee button

### 3. Audits (`/audits`)
- Audit history table
- Latest audit detailed view
- Incomplete channels list
- Manual audit trigger button
- Remediation actions

### 4. Offboarding (`/offboarding`)
- Pending offboarding tasks
- Active offboarding progress
- Completed offboarding history
- Bulk offboard inactive employees

### 5. Settings (`/settings`)
- Scheduler configuration
- Notification settings
- Platform credentials check
- Export/import employee list

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

