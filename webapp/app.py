"""
Flask Admin Panel for Customer Group Access Management
Read-only dashboard - no authentication required
"""
import os
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for
from database import Database
import threading
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize database
db = Database()

# Telegram audit session state helpers (database-backed for multi-worker support)
def get_telegram_status():
    """Get Telegram audit status from database"""
    conn = None
    try:
        conn = db.get_connection()
        cursor = db.get_cursor(conn)
        db.execute_query(cursor, "SELECT status, message, error, code, password FROM telegram_audit_status WHERE id = 1")
        row = cursor.fetchone()
        
        if row:
            # Access by key for RealDictCursor compatibility
            row_dict = dict(row) if not isinstance(row, dict) else row
            return {
                'status': row_dict.get('status') or 'idle',
                'message': row_dict.get('message') or '',
                'error': row_dict.get('error'),
                'code': row_dict.get('code'),
                'password': row_dict.get('password')
            }
        return {'status': 'idle', 'message': '', 'error': None, 'code': None, 'password': None}
    except Exception as e:
        if conn:
            conn.rollback()
        # Return default state on error
        return {'status': 'idle', 'message': '', 'error': str(e), 'code': None, 'password': None}
    finally:
        if conn:
            conn.close()

def set_telegram_status(status, message='', error=None):
    """Update Telegram audit status in database"""
    conn = None
    try:
        conn = db.get_connection()
        cursor = db.get_cursor(conn)
        db.execute_query(cursor, """
            UPDATE telegram_audit_status 
            SET status = ?, message = ?, error = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """, (status, message, error))
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def get_telegram_code():
    """Get stored code from database and clear it"""
    conn = None
    try:
        conn = db.get_connection()
        cursor = db.get_cursor(conn)
        db.execute_query(cursor, "SELECT code FROM telegram_audit_status WHERE id = 1")
        row = cursor.fetchone()
        row_dict = dict(row) if row and not isinstance(row, dict) else row
        code = row_dict.get('code') if row_dict else None
        if code:
            # Clear code after reading
            db.execute_query(cursor, "UPDATE telegram_audit_status SET code = NULL WHERE id = 1")
            conn.commit()
        return code
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def get_telegram_password():
    """Get stored password from database and clear it"""
    conn = None
    try:
        conn = db.get_connection()
        cursor = db.get_cursor(conn)
        db.execute_query(cursor, "SELECT password FROM telegram_audit_status WHERE id = 1")
        row = cursor.fetchone()
        row_dict = dict(row) if row and not isinstance(row, dict) else row
        password = row_dict.get('password') if row_dict else None
        if password:
            # Clear password after reading
            db.execute_query(cursor, "UPDATE telegram_audit_status SET password = NULL WHERE id = 1")
            conn.commit()
        return password
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

# In-memory storage for client objects (not shared across workers, but needed for auth flow)
telegram_client_storage = {}


def get_telegram_session():
    """Get stored Telegram session string from database"""
    conn = None
    try:
        conn = db.get_connection()
        cursor = db.get_cursor(conn)
        db.execute_query(cursor, "SELECT session_string FROM telegram_audit_status WHERE id = 1")
        row = cursor.fetchone()
        return row['session_string'] if row and row.get('session_string') else ''
    except Exception as e:
        print(f"Error getting session: {e}")
        return ''
    finally:
        if conn:
            conn.close()


def save_telegram_session(session_string):
    """Save Telegram session string to database"""
    conn = None
    try:
        conn = db.get_connection()
        cursor = db.get_cursor(conn)
        db.execute_query(cursor, """
            UPDATE telegram_audit_status 
            SET session_string = ?
            WHERE id = 1
        """, (session_string,))
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error saving session: {e}")
    finally:
        if conn:
            conn.close()

# Auto-seed database if empty (for Heroku ephemeral filesystem)
def ensure_data_seeded():
    """Ensure database has employee data on startup"""
    conn = db.get_connection()
    cursor = db.get_cursor(conn)
    db.execute_query(cursor, "SELECT COUNT(*) as count FROM employees")
    row = cursor.fetchone()
    count = row['count'] if isinstance(row, dict) else row[0]
    conn.close()
    
    if count == 0:
        print("🌱 Database empty, seeding initial data...")
        db.seed_initial_data()
        print("✅ Seeding complete")

# Seed data on startup
ensure_data_seeded()

# ============================================================================
# Dashboard Routes
# ============================================================================

@app.route('/')
def dashboard():
    """Main dashboard with overview stats"""
    conn = db.get_connection()
    cursor = db.get_cursor(conn)
    
    # Get employee stats
    db.execute_query(cursor, "SELECT COUNT(*) as count FROM employees WHERE status = 'active'")
    row = cursor.fetchone()
    active_count = row['count'] if isinstance(row, dict) else row[0]
    
    db.execute_query(cursor, "SELECT COUNT(*) as count FROM employees WHERE status = 'inactive'")
    row = cursor.fetchone()
    inactive_count = row['count'] if isinstance(row, dict) else row[0]
    
    db.execute_query(cursor, "SELECT COUNT(*) as count FROM employees WHERE status = 'optional'")
    row = cursor.fetchone()
    optional_count = row['count'] if isinstance(row, dict) else row[0]
    
    # Get latest audit
    db.execute_query(cursor, """
        SELECT * FROM audit_runs 
        ORDER BY started_at DESC 
        LIMIT 1
    """)
    latest_audit = cursor.fetchone()
    
    # Get recent offboarding tasks
    db.execute_query(cursor, """
        SELECT ot.*, e.name as employee_name 
        FROM offboarding_tasks ot
        JOIN employees e ON ot.employee_id = e.id
        ORDER BY ot.created_at DESC
        LIMIT 5
    """)
    recent_offboarding = cursor.fetchall()
    
    conn.close()
    
    return render_template('dashboard.html',
        active_count=active_count,
        inactive_count=inactive_count,
        optional_count=optional_count,
        latest_audit=latest_audit,
        recent_offboarding=recent_offboarding
    )


# ============================================================================
# Employee Management Routes
# ============================================================================

@app.route('/employees')
def employees():
    """List all employees"""
    conn = db.get_connection()
    cursor = db.get_cursor(conn)
    
    status_filter = request.args.get('status', 'all')
    
    if status_filter == 'all':
        db.execute_query(cursor, "SELECT * FROM employees ORDER BY name")
    else:
        db.execute_query(cursor, "SELECT * FROM employees WHERE status = ? ORDER BY name", (status_filter,))
    
    employees = cursor.fetchall()
    conn.close()
    
    return render_template('employees.html', employees=employees, status_filter=status_filter)


@app.route('/employees/add', methods=['GET', 'POST'])
def add_employee():
    """Add new employee"""
    if request.method == 'POST':
        conn = db.get_connection()
        cursor = db.get_cursor(conn)
        
        db.execute_query(cursor, """
            INSERT INTO employees 
            (name, slack_username, slack_user_id, telegram_username, email, 
             status, slack_required, telegram_required)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form['name'],
            request.form.get('slack_username'),
            request.form.get('slack_user_id'),
            request.form.get('telegram_username'),
            request.form.get('email'),
            request.form['status'],
            bool(request.form.get('slack_required')),
            bool(request.form.get('telegram_required'))
        ))
        
        conn.commit()
        conn.close()
        
        return redirect(url_for('employees'))
    
    return render_template('employee_form.html', employee=None)


@app.route('/employees/<int:employee_id>/edit', methods=['GET', 'POST'])
def edit_employee(employee_id):
    """Edit existing employee"""
    conn = db.get_connection()
    cursor = db.get_cursor(conn)
    
    if request.method == 'POST':
        db.execute_query(cursor, """
            UPDATE employees 
            SET name = ?, slack_username = ?, slack_user_id = ?, 
                telegram_username = ?, email = ?, status = ?,
                slack_required = ?, telegram_required = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            request.form['name'],
            request.form.get('slack_username'),
            request.form.get('slack_user_id'),
            request.form.get('telegram_username'),
            request.form.get('email'),
            request.form['status'],
            bool(request.form.get('slack_required')),
            bool(request.form.get('telegram_required')),
            employee_id
        ))
        
        conn.commit()
        conn.close()
        
        return redirect(url_for('employees'))
    
    db.execute_query(cursor, "SELECT * FROM employees WHERE id = ?", (employee_id,))
    employee = cursor.fetchone()
    conn.close()
    
    return render_template('employee_form.html', employee=employee)


# ============================================================================
# Audit Routes
# ============================================================================

@app.route('/audits')
def audits():
    """View audit history and results"""
    conn = db.get_connection()
    cursor = db.get_cursor(conn)
    
    # Get scheduled audits (full Slack + Telegram audits)
    db.execute_query(cursor, """
        SELECT * FROM audit_runs 
        WHERE run_type = 'scheduled' 
        ORDER BY started_at DESC LIMIT 10
    """)
    scheduled_audits = cursor.fetchall()
    
    # Get manual audits (Telegram-only audits)
    db.execute_query(cursor, """
        SELECT * FROM audit_runs 
        WHERE run_type = 'manual' 
        ORDER BY started_at DESC LIMIT 10
    """)
    manual_audits = cursor.fetchall()
    
    # Get latest audit findings (from most recent audit of either type)
    db.execute_query(cursor, "SELECT * FROM audit_runs ORDER BY started_at DESC LIMIT 1")
    latest_audit = cursor.fetchone()
    if latest_audit:
        db.execute_query(cursor, """
            SELECT * FROM audit_findings 
            WHERE audit_run_id = ? AND status = 'incomplete'
            ORDER BY platform, channel_name
        """, (latest_audit['id'],))
        findings = cursor.fetchall()
    else:
        findings = []
    
    conn.close()
    
    return render_template('audits.html', 
                         scheduled_audits=scheduled_audits, 
                         manual_audits=manual_audits, 
                         findings=findings)


@app.route('/audits/<int:audit_id>')
def audit_detail(audit_id):
    """View specific audit details"""
    conn = db.get_connection()
    cursor = db.get_cursor(conn)
    
    db.execute_query(cursor, "SELECT * FROM audit_runs WHERE id = ?", (audit_id,))
    audit = cursor.fetchone()
    
    db.execute_query(cursor, """
        SELECT * FROM audit_findings 
        WHERE audit_run_id = ?
        ORDER BY platform, channel_name
    """, (audit_id,))
    findings = cursor.fetchall()
    
    conn.close()
    
    return render_template('audit_detail.html', audit=audit, findings=findings)


# ============================================================================
# Offboarding Routes
# ============================================================================

@app.route('/offboarding')
def offboarding():
    """Offboarding center"""
    conn = db.get_connection()
    cursor = db.get_cursor(conn)
    
    # Get inactive employees
    db.execute_query(cursor, "SELECT * FROM employees WHERE status = 'inactive' ORDER BY name")
    inactive_employees = cursor.fetchall()
    
    # Get offboarding tasks
    db.execute_query(cursor, """
        SELECT ot.*, e.name as employee_name, e.slack_username, e.telegram_username
        FROM offboarding_tasks ot
        JOIN employees e ON ot.employee_id = e.id
        ORDER BY ot.created_at DESC
        LIMIT 20
    """)
    tasks = cursor.fetchall()
    
    conn.close()
    
    return render_template('offboarding.html', 
        inactive_employees=inactive_employees,
        tasks=tasks
    )


# ============================================================================
# API Endpoints
# ============================================================================

@app.route('/api/employees', methods=['GET'])
def api_get_employees():
    """Get all employees as JSON"""
    conn = db.get_connection()
    cursor = db.get_cursor(conn)
    db.execute_query(cursor, "SELECT * FROM employees ORDER BY name")
    employees = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(employees)


# Employee status update endpoint disabled - webapp is read-only
# @app.route('/api/employees/<int:employee_id>/status', methods=['PATCH'])
# def api_update_employee_status(employee_id):
#     """Update employee status"""
#     data = request.get_json()
#     new_status = data.get('status')
#     
#     if new_status not in ['active', 'inactive', 'optional']:
#         return jsonify({'error': 'Invalid status'}), 400
#     
#     conn = db.get_connection()
#     cursor = db.get_cursor(conn)
#     db.execute_query(cursor, """
#         UPDATE employees 
#         SET status = ?, updated_at = CURRENT_TIMESTAMP 
#         WHERE id = ?
#     """, (new_status, employee_id))
#     conn.commit()
#     conn.close()
#     
#     return jsonify({'success': True, 'status': new_status})


# Manual audit endpoint disabled - audits only run via Heroku Scheduler
# @app.route('/api/audit/run', methods=['POST'])
# def api_run_audit():
#     """Trigger manual audit"""
#     conn = db.get_connection()
#     cursor = db.get_cursor(conn)
#     
#     # Create audit run record
#     db.execute_query(cursor, """
#         INSERT INTO audit_runs (run_type, status)
#         VALUES ('manual', 'running')
#     """)
#     audit_id = cursor.lastrowid
#     conn.commit()
#     conn.close()
#     
#     # Run audit in background
#     from scheduler import run_audit_job
#     import threading
#     thread = threading.Thread(target=run_audit_job, args=(audit_id,))
#     thread.start()
#     
#     return jsonify({'success': True, 'audit_id': audit_id})


@app.route('/api/audit/latest', methods=['GET'])
def api_latest_audit():
    """Get latest audit results"""
    conn = db.get_connection()
    cursor = db.get_cursor(conn)
    
    db.execute_query(cursor, "SELECT * FROM audit_runs ORDER BY started_at DESC LIMIT 1")
    audit = cursor.fetchone()
    
    if audit:
        db.execute_query(cursor, """
            SELECT * FROM audit_findings 
            WHERE audit_run_id = ?
        """, (audit['id'],))
        findings = [dict(row) for row in cursor.fetchall()]
        
        result = dict(audit)
        result['findings'] = findings
    else:
        result = None
    
    conn.close()
    return jsonify(result)


@app.route('/api/audit/telegram/start', methods=['POST'])
def api_start_telegram_audit():
    """Start Telegram audit - requests 2FA code"""
    # Check if already running
    current_status = get_telegram_status()
    if current_status['status'] in ['waiting_for_code', 'authenticating', 'running']:
        return jsonify({'error': 'Telegram audit already in progress'}), 400
    
    # Reset state in database
    set_telegram_status('requesting_code', 'Requesting authentication code from Telegram...')
    
    # Start authentication in background thread
    thread = threading.Thread(target=start_telegram_auth)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'status': 'requesting_code'})


@app.route('/api/audit/telegram/status', methods=['GET'])
def api_telegram_audit_status():
    """Check Telegram audit status"""
    status = get_telegram_status()
    return jsonify(status)


@app.route('/api/audit/telegram/code', methods=['POST'])
def api_submit_telegram_code():
    """Submit 2FA code for Telegram authentication"""
    current_status = get_telegram_status()
    
    if current_status['status'] != 'waiting_for_code':
        return jsonify({'error': 'Not waiting for code'}), 400
    
    data = request.get_json()
    code = data.get('code', '').strip()
    
    if not code:
        return jsonify({'error': 'Code required'}), 400
    
    # Store code in database
    conn = db.get_connection()
    cursor = db.get_cursor(conn)
    db.execute_query(cursor, """
        UPDATE telegram_audit_status 
        SET code = ?, status = 'authenticating', message = 'Authenticating with code...'
        WHERE id = 1
    """, (code,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})


@app.route('/api/audit/telegram/password', methods=['POST'])
def api_submit_telegram_password():
    """Submit 2FA password for Telegram authentication"""
    current_status = get_telegram_status()
    
    if current_status['status'] != 'waiting_for_password':
        return jsonify({'error': 'Not waiting for password'}), 400
    
    data = request.get_json()
    password = data.get('password', '').strip()
    
    if not password:
        return jsonify({'error': 'Password required'}), 400
    
    # Store password in database
    conn = db.get_connection()
    cursor = db.get_cursor(conn)
    db.execute_query(cursor, """
        UPDATE telegram_audit_status 
        SET password = ?, status = 'authenticating_password', message = 'Authenticating with password...'
        WHERE id = 1
    """, (password,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})


# Offboarding endpoint disabled - offboarding done via scripts only
# @app.route('/api/offboard', methods=['POST'])
# def api_start_offboarding():
#     """Start offboarding process for employee"""
#     data = request.get_json()
#     employee_id = data.get('employee_id')
#     platform = data.get('platform', 'both')  # slack, telegram, both
#     
#     if not employee_id:
#         return jsonify({'error': 'employee_id required'}), 400
#     
#     conn = db.get_connection()
#     cursor = db.get_cursor(conn)
#     
#     # Create offboarding task
#     db.execute_query(cursor, """
#         INSERT INTO offboarding_tasks (employee_id, platform, status)
#         VALUES (?, ?, 'pending')
#     """, (employee_id, platform))
#     task_id = cursor.lastrowid
#     conn.commit()
#     conn.close()
#     
#     # Run offboarding in background
#     from scheduler import run_offboarding_job
#     import threading
#     thread = threading.Thread(target=run_offboarding_job, args=(task_id, employee_id, platform))
#     thread.start()
#     
#     return jsonify({'success': True, 'task_id': task_id})


@app.route('/api/offboard/status/<int:task_id>', methods=['GET'])
def api_offboarding_status(task_id):
    """Get offboarding task status"""
    conn = db.get_connection()
    cursor = db.get_cursor(conn)
    db.execute_query(cursor, """
        SELECT ot.*, e.name as employee_name
        FROM offboarding_tasks ot
        JOIN employees e ON ot.employee_id = e.id
        WHERE ot.id = ?
    """, (task_id,))
    task = cursor.fetchone()
    conn.close()
    
    if task:
        return jsonify(dict(task))
    return jsonify({'error': 'Task not found'}), 404


# ============================================================================
# Telegram Audit Helper Functions
# ============================================================================

def start_telegram_auth():
    """Start Telegram authentication process (runs in background thread)"""
    try:
        # Get Telegram credentials from environment
        api_id = int(os.getenv('TELEGRAM_API_ID', '0'))
        api_hash = os.getenv('TELEGRAM_API_HASH', '')
        phone = os.getenv('TELEGRAM_PHONE', '')
        
        if not api_id or not api_hash or not phone:
            set_telegram_status('error', '', 'Telegram credentials not configured')
            return
        
        # Run async authentication
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_telegram_audit(api_id, api_hash, phone))
        loop.close()
        
    except Exception as e:
        set_telegram_status('error', '', str(e))
        print(f"❌ Telegram audit error: {e}")


async def run_telegram_audit(api_id, api_hash, phone):
    """Run Telegram audit with interactive code input"""
    try:
        # Use StringSession stored in database instead of file-based session
        # This avoids file locking issues on Heroku's ephemeral filesystem
        session_string = get_telegram_session()
        client = TelegramClient(StringSession(session_string), api_id, api_hash)
        await client.connect()
        
        # Check if already authorized
        if not await client.is_user_authorized():
            # Request code
            await client.send_code_request(phone)
            set_telegram_status('waiting_for_code', f'Enter the code sent to {phone}')
            
            # Wait for code (poll every second for up to 5 minutes)
            for _ in range(300):
                await asyncio.sleep(1)
                
                status = get_telegram_status()
                if status['status'] == 'authenticating':
                    # Code was submitted
                    code = get_telegram_code()
                    if code:
                        try:
                            await client.sign_in(phone, code)
                            # Save session to database for future use
                            save_telegram_session(client.session.save())
                            set_telegram_status('running', 'Authenticated! Running audit...')
                            break
                        except SessionPasswordNeededError:
                            # 2FA password is required
                            set_telegram_status('waiting_for_password', 'Enter your 2FA password')
                            break
                        except Exception as e:
                            set_telegram_status('error', '', f'Invalid code: {str(e)}')
                            await client.disconnect()
                            return
            
            # Check if we need password (2FA)
            status = get_telegram_status()
            if status['status'] == 'waiting_for_password':
                # Wait for password (poll for up to 5 minutes)
                for _ in range(300):
                    await asyncio.sleep(1)
                    
                    status = get_telegram_status()
                    if status['status'] == 'authenticating_password':
                        # Password was submitted
                        password = get_telegram_password()
                        if password:
                            try:
                                await client.sign_in(password=password)
                                # Save session to database for future use
                                save_telegram_session(client.session.save())
                                set_telegram_status('running', 'Authenticated! Running audit...')
                                break
                            except Exception as e:
                                set_telegram_status('error', '', f'Invalid password: {str(e)}')
                                await client.disconnect()
                                return
                
                status = get_telegram_status()
                if status['status'] != 'running':
                    set_telegram_status('error', '', 'Timeout waiting for password')
                    await client.disconnect()
                    return
            
            status = get_telegram_status()
            if status['status'] != 'running':
                set_telegram_status('error', '', 'Timeout waiting for code')
                await client.disconnect()
                return
        else:
            # Already authorized
            set_telegram_status('running', 'Already authenticated! Running audit...')
        
        # Run the actual audit
        set_telegram_status('running', 'Auditing Telegram groups...')
        
        # Create audit run entry in database
        conn = db.get_connection()
        cursor = db.get_cursor(conn)
        if db.is_postgres:
            db.execute_query(cursor, """
                INSERT INTO audit_runs (run_type, status)
                VALUES ('manual', 'running')
                RETURNING id
            """)
            audit_id = cursor.fetchone()['id']
        else:
            db.execute_query(cursor, """
                INSERT INTO audit_runs (run_type, status)
                VALUES ('manual', 'running')
            """)
            audit_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Import and run audit using scheduler's job function
        from scheduler import run_audit_job
        set_telegram_status('running', 'Running full audit (Slack + Telegram)... This may take a few minutes...')
        
        # Run audit job in background thread (handles Slack + Telegram and saves to DB)
        def run_audit():
            try:
                run_audit_job(audit_id)
                set_telegram_status('completed', 'Audit completed successfully! Check the Audit History tab to see results.')
            except Exception as e:
                set_telegram_status('error', '', f'Audit failed: {str(e)}')
        
        thread = threading.Thread(target=run_audit)
        thread.daemon = True
        thread.start()
        
        await client.disconnect()
        
    except Exception as e:
        set_telegram_status('error', '', str(e))
        print(f"❌ Telegram audit error: {e}")


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)

