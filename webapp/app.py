"""
Flask Admin Panel for Customer Group Access Management
Read-only dashboard - no authentication required
"""
import os
import json
import subprocess
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for
from database import Database
import threading
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize database
db = Database()

# Telegram audit session state (in-memory)
telegram_session_state = {
    'status': 'idle',  # idle, waiting_for_code, authenticating, running, completed, error
    'message': '',
    'phone_code_hash': None,
    'client': None,
    'error': None
}

# Auto-seed database if empty (for Heroku ephemeral filesystem)
def ensure_data_seeded():
    """Ensure database has employee data on startup"""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM employees")
    count = cursor.fetchone()[0]
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
    cursor = conn.cursor()
    
    # Get employee stats
    cursor.execute("SELECT COUNT(*) FROM employees WHERE status = 'active'")
    active_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM employees WHERE status = 'inactive'")
    inactive_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM employees WHERE status = 'optional'")
    optional_count = cursor.fetchone()[0]
    
    # Get latest audit
    cursor.execute("""
        SELECT * FROM audit_runs 
        ORDER BY started_at DESC 
        LIMIT 1
    """)
    latest_audit = cursor.fetchone()
    
    # Get recent offboarding tasks
    cursor.execute("""
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
    cursor = conn.cursor()
    
    status_filter = request.args.get('status', 'all')
    
    if status_filter == 'all':
        cursor.execute("SELECT * FROM employees ORDER BY name")
    else:
        cursor.execute("SELECT * FROM employees WHERE status = ? ORDER BY name", (status_filter,))
    
    employees = cursor.fetchall()
    conn.close()
    
    return render_template('employees.html', employees=employees, status_filter=status_filter)


@app.route('/employees/add', methods=['GET', 'POST'])
def add_employee():
    """Add new employee"""
    if request.method == 'POST':
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
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
    cursor = conn.cursor()
    
    if request.method == 'POST':
        cursor.execute("""
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
    
    cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
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
    cursor = conn.cursor()
    
    # Get audit history
    cursor.execute("SELECT * FROM audit_runs ORDER BY started_at DESC LIMIT 20")
    audit_history = cursor.fetchall()
    
    # Get latest audit findings
    if audit_history:
        latest_audit_id = audit_history[0]['id']
        cursor.execute("""
            SELECT * FROM audit_findings 
            WHERE audit_run_id = ? AND status = 'incomplete'
            ORDER BY platform, channel_name
        """, (latest_audit_id,))
        findings = cursor.fetchall()
    else:
        findings = []
    
    conn.close()
    
    return render_template('audits.html', audit_history=audit_history, findings=findings)


@app.route('/audits/<int:audit_id>')
def audit_detail(audit_id):
    """View specific audit details"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM audit_runs WHERE id = ?", (audit_id,))
    audit = cursor.fetchone()
    
    cursor.execute("""
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
    cursor = conn.cursor()
    
    # Get inactive employees
    cursor.execute("SELECT * FROM employees WHERE status = 'inactive' ORDER BY name")
    inactive_employees = cursor.fetchall()
    
    # Get offboarding tasks
    cursor.execute("""
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
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees ORDER BY name")
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
#     cursor = conn.cursor()
#     cursor.execute("""
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
#     cursor = conn.cursor()
#     
#     # Create audit run record
#     cursor.execute("""
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
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM audit_runs ORDER BY started_at DESC LIMIT 1")
    audit = cursor.fetchone()
    
    if audit:
        cursor.execute("""
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
    global telegram_session_state
    
    # Check if already running
    if telegram_session_state['status'] in ['waiting_for_code', 'authenticating', 'running']:
        return jsonify({'error': 'Telegram audit already in progress'}), 400
    
    # Reset state
    telegram_session_state = {
        'status': 'requesting_code',
        'message': 'Requesting authentication code from Telegram...',
        'phone_code_hash': None,
        'client': None,
        'error': None
    }
    
    # Start authentication in background thread
    thread = threading.Thread(target=start_telegram_auth)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'status': 'requesting_code'})


@app.route('/api/audit/telegram/status', methods=['GET'])
def api_telegram_audit_status():
    """Check Telegram audit status"""
    return jsonify({
        'status': telegram_session_state['status'],
        'message': telegram_session_state['message'],
        'error': telegram_session_state['error']
    })


@app.route('/api/audit/telegram/code', methods=['POST'])
def api_submit_telegram_code():
    """Submit 2FA code for Telegram authentication"""
    global telegram_session_state
    
    if telegram_session_state['status'] != 'waiting_for_code':
        return jsonify({'error': 'Not waiting for code'}), 400
    
    data = request.get_json()
    code = data.get('code', '').strip()
    
    if not code:
        return jsonify({'error': 'Code required'}), 400
    
    # Store code and trigger authentication
    telegram_session_state['code'] = code
    telegram_session_state['status'] = 'authenticating'
    telegram_session_state['message'] = 'Authenticating with code...'
    
    return jsonify({'success': True})


@app.route('/api/audit/telegram/password', methods=['POST'])
def api_submit_telegram_password():
    """Submit 2FA password for Telegram authentication"""
    global telegram_session_state
    
    if telegram_session_state['status'] != 'waiting_for_password':
        return jsonify({'error': 'Not waiting for password'}), 400
    
    data = request.get_json()
    password = data.get('password', '').strip()
    
    if not password:
        return jsonify({'error': 'Password required'}), 400
    
    # Store password and trigger authentication
    telegram_session_state['password'] = password
    telegram_session_state['status'] = 'authenticating_password'
    telegram_session_state['message'] = 'Authenticating with password...'
    
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
#     cursor = conn.cursor()
#     
#     # Create offboarding task
#     cursor.execute("""
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
    cursor = conn.cursor()
    cursor.execute("""
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
    global telegram_session_state
    
    try:
        # Get Telegram credentials from environment
        api_id = int(os.getenv('TELEGRAM_API_ID', '0'))
        api_hash = os.getenv('TELEGRAM_API_HASH', '')
        phone = os.getenv('TELEGRAM_PHONE', '')
        
        if not api_id or not api_hash or not phone:
            telegram_session_state['status'] = 'error'
            telegram_session_state['error'] = 'Telegram credentials not configured'
            return
        
        # Run async authentication
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_telegram_audit(api_id, api_hash, phone))
        loop.close()
        
    except Exception as e:
        telegram_session_state['status'] = 'error'
        telegram_session_state['error'] = str(e)
        print(f"❌ Telegram audit error: {e}")


async def run_telegram_audit(api_id, api_hash, phone):
    """Run Telegram audit with interactive code input"""
    global telegram_session_state
    
    try:
        # Create Telegram client (use same session file name as audit script)
        # Store session file in project root so audit script can find it
        session_path = Path(__file__).parent.parent / 'telegram_session'
        client = TelegramClient(str(session_path), api_id, api_hash)
        await client.connect()
        
        # Check if already authorized
        if not await client.is_user_authorized():
            # Request code
            await client.send_code_request(phone)
            telegram_session_state['status'] = 'waiting_for_code'
            telegram_session_state['message'] = f'Enter the code sent to {phone}'
            telegram_session_state['client'] = client
            
            # Wait for code (poll every second for up to 5 minutes)
            for _ in range(300):
                await asyncio.sleep(1)
                
                if telegram_session_state['status'] == 'authenticating':
                    # Code was submitted
                    code = telegram_session_state.get('code', '')
                    try:
                        await client.sign_in(phone, code)
                        telegram_session_state['status'] = 'running'
                        telegram_session_state['message'] = 'Authenticated! Running audit...'
                        break
                    except SessionPasswordNeededError:
                        # 2FA password is required
                        telegram_session_state['status'] = 'waiting_for_password'
                        telegram_session_state['message'] = 'Enter your 2FA password'
                        telegram_session_state['client'] = client
                        break
                    except Exception as e:
                        telegram_session_state['status'] = 'error'
                        telegram_session_state['error'] = f'Invalid code: {str(e)}'
                        await client.disconnect()
                        return
            
            # Check if we need password (2FA)
            if telegram_session_state['status'] == 'waiting_for_password':
                # Wait for password (poll for up to 5 minutes)
                for _ in range(300):
                    await asyncio.sleep(1)
                    
                    if telegram_session_state['status'] == 'authenticating_password':
                        # Password was submitted
                        password = telegram_session_state.get('password', '')
                        try:
                            await client.sign_in(password=password)
                            telegram_session_state['status'] = 'running'
                            telegram_session_state['message'] = 'Authenticated! Running audit...'
                            break
                        except Exception as e:
                            telegram_session_state['status'] = 'error'
                            telegram_session_state['error'] = f'Invalid password: {str(e)}'
                            await client.disconnect()
                            return
                
                if telegram_session_state['status'] != 'running':
                    telegram_session_state['status'] = 'error'
                    telegram_session_state['error'] = 'Timeout waiting for password'
                    await client.disconnect()
                    return
            
            if telegram_session_state['status'] != 'running':
                telegram_session_state['status'] = 'error'
                telegram_session_state['error'] = 'Timeout waiting for code'
                await client.disconnect()
                return
        else:
            # Already authorized
            telegram_session_state['status'] = 'running'
            telegram_session_state['message'] = 'Already authenticated! Running audit...'
        
        # Run the actual audit
        telegram_session_state['message'] = 'Auditing Telegram groups...'
        
        # Create audit run entry in database
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_runs (run_type, status)
            VALUES ('manual', 'running')
        """)
        audit_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Import and run audit using scheduler's job function
        from scheduler import run_audit_job
        telegram_session_state['message'] = 'Running full audit (Slack + Telegram)...'
        
        # Run audit job (handles Slack + Telegram and saves to DB)
        run_audit_job(audit_id)
        
        telegram_session_state['status'] = 'completed'
        telegram_session_state['message'] = 'Audit completed successfully! Check the Audit History tab to see results.'
        
        await client.disconnect()
        
    except Exception as e:
        telegram_session_state['status'] = 'error'
        telegram_session_state['error'] = str(e)
        print(f"❌ Telegram audit error: {e}")


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)

