"""
Scheduler for automated audits and offboarding tasks
Integrates with existing scripts in /scripts directory
"""
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

# Add parent directory to path to import database
sys.path.insert(0, str(Path(__file__).parent))
from database import Database

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database
db = Database()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent


# ============================================================================
# Audit Job
# ============================================================================

def run_audit_job(audit_id=None):
    """
    Run customer group audit using existing customer_group_audit.py script
    """
    logger.info("🔍 Starting scheduled audit job")
    
    conn = None
    cursor = None
    
    try:
        conn = db.get_connection()
        cursor = db.get_cursor(conn)
        
        # Create audit run record if not provided
        if audit_id is None:
            if db.is_postgres:
                db.execute_query(cursor, """
                    INSERT INTO audit_runs (run_type, status)
                    VALUES ('scheduled', 'running')
                    RETURNING id
                """)
                audit_id = cursor.fetchone()['id']
            else:
                db.execute_query(cursor, """
                    INSERT INTO audit_runs (run_type, status)
                    VALUES ('scheduled', 'running')
                """)
                audit_id = cursor.lastrowid
            conn.commit()
        else:
            # Update existing audit to running
            db.execute_query(cursor, """
                UPDATE audit_runs 
                SET status = 'running', started_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (audit_id,))
            conn.commit()
        # Run the audit script
        script_path = PROJECT_ROOT / "scripts" / "customer_group_audit.py"
        output_dir = PROJECT_ROOT / "output" / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"audit_report_{timestamp}.json"
        
        logger.info(f"Running audit script: {script_path}")
        
        # Run audit script and capture output
        # Increased timeout to 30 minutes for full Slack + Telegram audits
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout (audits can take 10-15 minutes)
            )
        except subprocess.TimeoutExpired:
            raise Exception("Audit script timed out after 30 minutes. This may happen with very large audits. Try running locally or check logs for specific issues.")
        
        if result.returncode != 0:
            raise Exception(f"Audit script failed: {result.stderr}")
        
        # Parse audit results from output
        # The script should output JSON results
        audit_results = parse_audit_output(result.stdout)
        
        # Save results to database
        save_audit_results(audit_id, audit_results, str(report_path))
        
        # Update audit run status
        db.execute_query(cursor, """
            UPDATE audit_runs 
            SET status = 'completed',
                completed_at = CURRENT_TIMESTAMP,
                slack_channels_total = ?,
                slack_channels_complete = ?,
                telegram_groups_total = ?,
                telegram_groups_complete = ?,
                report_path = ?,
                results_json = ?
            WHERE id = ?
        """, (
            audit_results.get('slack_total', 0),
            audit_results.get('slack_complete', 0),
            audit_results.get('telegram_total', 0),
            audit_results.get('telegram_complete', 0),
            str(report_path),
            json.dumps(audit_results),
            audit_id
        ))
        conn.commit()
        
        logger.info(f"✅ Audit completed successfully (ID: {audit_id})")
        
    except Exception as e:
        logger.error(f"❌ Audit failed: {str(e)}")
        try:
            db.execute_query(cursor, """
                UPDATE audit_runs 
                SET status = 'failed',
                    completed_at = CURRENT_TIMESTAMP,
                    error_message = ?
                WHERE id = ?
            """, (str(e), audit_id))
            conn.commit()
        except Exception as update_error:
            logger.error(f"Failed to update audit status: {update_error}")
            conn.rollback()
    
    finally:
        if conn:
            conn.close()


def parse_audit_output(output):
    """Parse audit script output to extract JSON results"""
    # Look for JSON between markers
    try:
        if 'AUDIT_RESULTS_JSON_START' in output and 'AUDIT_RESULTS_JSON_END' in output:
            start_marker = 'AUDIT_RESULTS_JSON_START'
            end_marker = 'AUDIT_RESULTS_JSON_END'
            
            start_idx = output.find(start_marker) + len(start_marker)
            end_idx = output.find(end_marker)
            
            if start_idx > 0 and end_idx > start_idx:
                json_str = output[start_idx:end_idx].strip()
                results = json.loads(json_str)
                logger.info(f"📊 Parsed audit results: {results.get('slack_total', 0)} Slack, {results.get('telegram_total', 0)} Telegram")
                return results
    except Exception as e:
        logger.warning(f"Failed to parse JSON results: {e}")
    
    # Fallback: return empty results
    logger.warning("No JSON results found in audit output, returning empty results")
    return {
        'slack_total': 0,
        'slack_complete': 0,
        'telegram_total': 0,
        'telegram_complete': 0,
        'incomplete_channels': []
    }


def save_audit_results(audit_id, results, report_path):
    """Save audit findings to database"""
    conn = None
    try:
        conn = db.get_connection()
        cursor = db.get_cursor(conn)
        
        for channel in results.get('incomplete_channels', []):
            db.execute_query(cursor, """
                INSERT INTO audit_findings 
                (audit_run_id, platform, channel_name, channel_id, missing_members, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                audit_id,
                channel.get('platform', 'slack'),
                channel.get('name'),
                channel.get('id'),
                json.dumps(channel.get('missing', [])),
                channel.get('status', 'incomplete')
            ))
        
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


# ============================================================================
# Offboarding Job
# ============================================================================

def run_offboarding_job(task_id, employee_id, platform='both'):
    """
    Run offboarding process using existing telegram_user_delete.py script
    """
    logger.info(f"🚪 Starting offboarding job for employee {employee_id}")
    
    conn = None
    cursor = None
    
    try:
        conn = db.get_connection()
        cursor = db.get_cursor(conn)
        
        # Get employee details
        db.execute_query(cursor, "SELECT * FROM employees WHERE id = ?", (employee_id,))
        employee = cursor.fetchone()
        
        if not employee:
            logger.error(f"Employee {employee_id} not found")
            return
        
        # Update task status
        db.execute_query(cursor, """
            UPDATE offboarding_tasks 
            SET status = 'running', started_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (task_id,))
        conn.commit()
        results = {
            'groups_processed': 0,
            'groups_removed': 0,
            'groups_failed': 0
        }
        
        # Offboard from Slack (if applicable)
        if platform in ['slack', 'both'] and employee['slack_username']:
            logger.info(f"Removing {employee['name']} from Slack...")
            # Note: Slack offboarding typically done via admin console
            # This would need a separate script or manual process
            # For now, just log it
            logger.info(f"⚠️  Slack offboarding for {employee['name']} requires manual action")
        
        # Offboard from Telegram (if applicable)
        if platform in ['telegram', 'both'] and employee['telegram_username']:
            logger.info(f"Removing {employee['name']} from Telegram...")
            
            telegram_script = PROJECT_ROOT / "scripts" / "telegram_user_delete.py"
            output_dir = PROJECT_ROOT / "output" / "offboarding"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = output_dir / f"offboarding_{employee['telegram_username']}_{timestamp}.log"
            
            # Run telegram offboarding script
            result = subprocess.run(
                [
                    sys.executable,
                    str(telegram_script),
                    '--username', employee['telegram_username']
                ],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )
            
            # Save log
            with open(log_file, 'w') as f:
                f.write(result.stdout)
                f.write(result.stderr)
            
            if result.returncode == 0:
                # Parse results from output
                telegram_results = parse_telegram_output(result.stdout)
                results['groups_processed'] += telegram_results.get('processed', 0)
                results['groups_removed'] += telegram_results.get('removed', 0)
                results['groups_failed'] += telegram_results.get('failed', 0)
            else:
                raise Exception(f"Telegram offboarding failed: {result.stderr}")
        
        # Update task as completed
        db.execute_query(cursor, """
            UPDATE offboarding_tasks 
            SET status = 'completed',
                completed_at = CURRENT_TIMESTAMP,
                groups_processed = ?,
                groups_removed = ?,
                groups_failed = ?
            WHERE id = ?
        """, (
            results['groups_processed'],
            results['groups_removed'],
            results['groups_failed'],
            task_id
        ))
        conn.commit()
        
        logger.info(f"✅ Offboarding completed for {employee['name']}")
        
    except Exception as e:
        logger.error(f"❌ Offboarding failed: {str(e)}")
        try:
            db.execute_query(cursor, """
                UPDATE offboarding_tasks 
                SET status = 'failed',
                    completed_at = CURRENT_TIMESTAMP,
                    error_message = ?
                WHERE id = ?
            """, (str(e), task_id))
            conn.commit()
        except Exception as update_error:
            logger.error(f"Failed to update offboarding status: {update_error}")
            if conn:
                conn.rollback()
    
    finally:
        if conn:
            conn.close()


def parse_telegram_output(output):
    """Parse telegram offboarding script output"""
    results = {
        'processed': 0,
        'removed': 0,
        'failed': 0
    }
    
    # Parse output for statistics
    import re
    
    removed_match = re.search(r'Successfully removed from (\d+)', output)
    if removed_match:
        results['removed'] = int(removed_match.group(1))
    
    failed_match = re.search(r'Failed to remove from (\d+)', output)
    if failed_match:
        results['failed'] = int(failed_match.group(1))
    
    results['processed'] = results['removed'] + results['failed']
    
    return results


# ============================================================================
# Scheduler Setup
# ============================================================================

def start_scheduler():
    """Start the background scheduler"""
    scheduler = BackgroundScheduler()
    
    # Daily audit at 2 AM
    scheduler.add_job(
        run_audit_job,
        trigger=CronTrigger(hour=2, minute=0),
        id='daily_audit',
        name='Daily Customer Group Audit',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✅ Scheduler started - Daily audit at 2:00 AM")
    
    return scheduler


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    logger.info("🚀 Starting scheduler service...")
    scheduler = start_scheduler()
    
    # Keep the script running
    try:
        import time
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()

