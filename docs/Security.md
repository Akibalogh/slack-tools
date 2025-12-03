# Security Documentation

## Admin Panel Security

### Data Transmission

**HTTPS/TLS:**
- All communication between browser and server uses HTTPS
- 2FA codes and passwords encrypted in transit
- Heroku provides automatic TLS termination

**Authentication Flow:**
1. User enters 2FA code in browser
2. Transmitted over HTTPS to `/api/audit/telegram/code`
3. Stored temporarily in Postgres database
4. Retrieved by Telegram client for authentication
5. **Immediately cleared from database** after use

### Data Storage

**Telegram Session:**
- Stored as StringSession in Postgres `telegram_audit_status.session_string`
- Persists across deployments
- Used to avoid re-authentication on every audit
- Telegram's session format (encrypted by Telethon library)

**2FA Credentials (Temporary):**
- `code`: Stored temporarily in `telegram_audit_status.code`
- `password`: Stored temporarily in `telegram_audit_status.password`
- **Cleared immediately after use** (one-time use)
- Not logged or persisted in audit records

**Audit Results:**
- Stored permanently in `audit_runs.results_json`
- Contains channel names and member lists
- No sensitive credentials or passwords
- Read-only access (webapp has no write operations)

### Database Access

**Heroku Postgres:**
- Encrypted at rest by Heroku
- Access via `DATABASE_URL` environment variable
- Connection over SSL/TLS
- 1 GB essential-0 plan with 20 max connections

**Environment Variables:**
- `SLACK_USER_TOKEN`: Slack API access
- `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`: Telegram API access
- Stored in Heroku config vars (encrypted, not in code)
- Never committed to git repository

### Webapp Security

**Read-Only Design:**
- No employee editing via UI
- No manual audit triggers for Slack (automated only)
- No offboarding via UI
- All write operations require CLI/database access

**No Authentication Required:**
- Webapp is public (read-only data)
- No user accounts or login
- Suitable for internal team use only

### Scheduled Tasks

**Slack Audits (Automated):**
- Run via Heroku Scheduler at 2:00 AM UTC daily
- Uses `--skip-telegram` flag
- No interactive authentication required
- Results saved to database automatically

**Telegram Audits (Manual Only):**
- Require user to click button and enter 2FA
- Cannot run automatically due to Telegram's security requirements
- Session persists to reduce re-authentication frequency

### API Endpoints

**Public (No Auth):**
- `GET /` - Dashboard
- `GET /employees` - Employee list
- `GET /audits` - Audit history
- `GET /audits/<id>` - Audit details
- `GET /api/employees` - Employee JSON

**Internal (Used by UI):**
- `POST /api/audit/telegram/start` - Start Telegram audit
- `GET /api/audit/telegram/status` - Poll audit status
- `POST /api/audit/telegram/code` - Submit 2FA code
- `POST /api/audit/telegram/password` - Submit 2FA password

### Recommendations

**For Production:**
1. Add authentication/authorization if exposing publicly
2. Consider encrypting 2FA credentials at rest in database
3. Add rate limiting on audit triggers
4. Set up monitoring/alerting for failed audits
5. Regular database backups via Heroku

**Current Security Posture:**
- ✅ Suitable for internal team use
- ✅ Credentials encrypted in transit (HTTPS)
- ✅ Temporary credentials cleared after use
- ✅ Read-only webapp design
- ⚠️ No user authentication (public read access)
- ⚠️ 2FA credentials stored temporarily in plain text

### Audit Trail

**What's Logged:**
- Audit runs (timestamps, status, coverage)
- Channels with missing members
- No sensitive credentials in logs
- No PII beyond employee names/usernames

**What's NOT Logged:**
- 2FA codes or passwords
- Telegram session details
- Customer identifiable information

