# Admin Panel Testing Plan

## Pre-Deployment Checklist

### 1. Local Testing (Before Push)
- [ ] Run linters: `black --check webapp/ scripts/` and `isort --check webapp/ scripts/`
- [ ] Fix any linting errors
- [ ] Test database initialization: `python webapp/database.py`
- [ ] Test Flask app locally: `cd webapp && python app.py`
- [ ] Verify all pages load: `/`, `/employees`, `/audits`

### 2. Code Review
- [ ] Check all database queries use `db.execute_query()` (not raw `cursor.execute()`)
- [ ] Verify all row access uses dictionary keys (not integer indices)
- [ ] Confirm all transactions have try-except-finally with rollback
- [ ] Ensure RETURNING id used for Postgres INSERTs (not lastrowid)

### 3. Git & Deployment
- [ ] Commit with clear message
- [ ] Push to origin/main
- [ ] Wait for GitHub Actions CI to pass (check lint + tests)
- [ ] If CI fails, fix before deploying to Heroku
- [ ] Push to Heroku: `git push heroku main`
- [ ] Monitor release phase: `heroku releases:output`
- [ ] Check for worker timeouts: `heroku logs --tail` (watch for SIGKILL)

## Post-Deployment Testing

### 4. Basic Functionality
- [ ] **Dashboard loads**: curl https://bitsafe-group-admin-30c4bbdb5186.herokuapp.com/
- [ ] **Employees page**: Verify all 10 employees show
- [ ] **Audits page**: Check separated sections display
- [ ] **No 500 errors**: Check logs for errors
- [ ] **Workers stable**: No CRITICAL WORKER TIMEOUT in logs

### 5. Database Verification
- [ ] **Connect**: `heroku pg:psql --app bitsafe-group-admin`
- [ ] **Employee count**: `SELECT COUNT(*) FROM employees;` (should be 10)
- [ ] **Audit count**: `SELECT COUNT(*) FROM audit_runs;`
- [ ] **Schema check**: `\d audit_runs` (verify columns exist)
- [ ] **Test query**: `SELECT id, status FROM audit_runs ORDER BY id DESC LIMIT 3;`

### 6. API Endpoint Testing
- [ ] **Status API**: `curl https://...herokuapp.com/api/audit/telegram/status`
  - Should return JSON with status, message, error fields
  - Status should be "idle" if no audit running
- [ ] **Employees API**: `curl https://...herokuapp.com/api/employees`
  - Should return array of 10 employees

### 7. Telegram Audit (Full UI Flow)
- [ ] **Click button**: "Run Telegram Audit"
- [ ] **Modal opens**: Not stuck on "idle" or "completed"
- [ ] **Status updates**: Shows "requesting_code" or "waiting_for_code"
- [ ] **Code input appears**: Input field visible within 5 seconds
- [ ] **Submit code**: Enter 5-digit code, click Submit
- [ ] **Password prompt** (if 2FA enabled): Input field appears
- [ ] **Submit password**: Click Submit Password
- [ ] **Progress updates**: Modal shows "Running full audit..."
- [ ] **Completion**: Status changes to "completed" after ~13 minutes
- [ ] **Database record**: New audit appears in Manual Telegram Audits section

### 8. Audit Results Verification
- [ ] **Coverage stats**: Audit shows "X/Y" not "-" for Telegram
- [ ] **Slack stats**: Shows Slack coverage if applicable  
- [ ] **View Details**: Click to see audit detail page
- [ ] **Full Report**: "📊 Full Audit Report" section visible
- [ ] **Channel list**: Tables show Slack channels and Telegram groups
- [ ] **Data accuracy**: Verify channel names, member counts look correct
- [ ] **Missing members**: Channels with issues highlighted in red

### 9. Scheduled Audit (Heroku Scheduler)
- [ ] **Scheduler config**: Verify command has `--skip-telegram` flag
- [ ] **Manual trigger test**: `heroku run "python scripts/customer_group_audit.py --skip-telegram"`
  - Should complete in ~5-10 minutes
  - Should audit 120 Slack channels
  - Should show "Telegram audit skipped" message
  - Should NOT require 2FA
- [ ] **Check output**: Look for "AUDIT_RESULTS_JSON_START" in output
- [ ] **Verify results**: Run should save to audit_runs with proper data

### 10. Audit Management CLI
- [ ] **List audits**: `heroku run "python scripts/manage_audits.py list"`
- [ ] **List running**: `heroku run "python scripts/manage_audits.py list --status running"`
- [ ] **Cleanup**: `heroku run "python scripts/manage_audits.py cleanup"`
  - Should clear telegram_audit_status
  - Should cancel any stuck running audits

## Regression Testing

### 11. After Schema Changes
- [ ] Add column: `ALTER TABLE ... ADD COLUMN ...`
- [ ] Restart app: `heroku restart`
- [ ] Verify app doesn't crash
- [ ] Test queries that use new column

### 12. After Code Changes
- [ ] Format with black/isort
- [ ] Run local tests if available
- [ ] Check GitHub Actions status
- [ ] Deploy to Heroku
- [ ] Monitor for worker timeouts (first 2 minutes after deploy)
- [ ] Test affected feature end-to-end

## Common Issues & Solutions

### Workers Timing Out
**Symptoms:** CRITICAL WORKER TIMEOUT in logs, app shows "Application Error"
**Causes:**
- Syntax error in Python code (IndentationError, NameError)
- Blocking code in module-level imports
- Database query hanging

**Fix:**
- Check release output: `heroku releases:output`
- Rollback if needed: `heroku rollback v##`
- Fix syntax error and redeploy

### Audit Shows No Data (0/0 or -)
**Symptoms:** Audit completes but coverage shows "-" or "0/0"
**Causes:**
- JSON output not being parsed
- Results not being saved to results_json column
- Audit script error not captured

**Debug:**
- Check logs for "Parsed audit results: X Slack, Y Telegram"
- Verify results_json column exists: `\d audit_runs`
- Check audit record: `SELECT results_json FROM audit_runs WHERE id = X;`

### Modal Stuck on "idle"
**Symptoms:** Click button, modal shows "idle" and never updates
**Causes:**
- telegram_audit_status not being updated
- API returning wrong status
- JavaScript polling not working

**Debug:**
- Check DB: `SELECT * FROM telegram_audit_status;`
- Check API: `curl .../api/audit/telegram/status`
- Compare database value vs API response
- Run cleanup: `heroku run "python scripts/manage_audits.py cleanup"`

### "Error: 0" or Strange Error Messages
**Symptoms:** Modal shows "Error: 0" or number instead of message
**Causes:**
- Integer index access on RealDictCursor (`row[0]` instead of `row['column']`)
- Error field storing integer instead of string

**Fix:**
- Use dictionary access: `row_dict.get('column')`
- Convert row to dict: `dict(row) if not isinstance(row, dict) else row`

## Performance Benchmarks

**Expected Timings:**
- Slack-only audit: 5-10 minutes (120 channels)
- Telegram-only audit: 10-15 minutes (412 groups)
- Full audit (Slack + Telegram): 13-18 minutes
- Modal code input: Appears within 5 seconds of clicking button
- Audit results display: Page loads in < 2 seconds

**Database:**
- Employee count: 10 records
- Audit retention: Keep last 20 audits, delete older
- Connection pool: 20 max connections (Essential-0 plan)

## Security Testing

- [ ] **HTTPS only**: All URLs use https://
- [ ] **Credentials cleared**: 2FA code/password removed from DB after use
- [ ] **Session persists**: Telegram session_string stored and reused
- [ ] **No credentials in logs**: Verify no passwords in Heroku logs
- [ ] **Database encryption**: Heroku Postgres encrypts at rest (automatic)

## Documentation Review

- [ ] **README updated**: Installation, deployment, usage instructions
- [ ] **PRD updated**: Feature 7 reflects current implementation
- [ ] **CHANGELOG updated**: All changes documented
- [ ] **Security.md**: Security posture documented
- [ ] **Testing_Plan.md**: This file kept up to date

## Pre-Production Checklist

Before marking as "production ready":
- [ ] All tests above pass
- [ ] CI/CD pipeline green
- [ ] At least 3 successful end-to-end audit tests
- [ ] Scheduled audit tested (manually trigger scheduler command)
- [ ] No critical issues in past 24 hours of logs
- [ ] Documentation complete and accurate
- [ ] Team trained on how to use admin panel
- [ ] Backup/recovery plan documented

