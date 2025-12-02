#!/usr/bin/env python3
"""
Audit Management CLI Tool
Manage running, stuck, or failed audits
"""
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "webapp"))
from database import Database


def list_audits(db, status=None, limit=10):
    """List recent audits"""
    conn = db.get_connection()
    cursor = db.get_cursor(conn)
    
    if status:
        db.execute_query(cursor, """
            SELECT id, run_type, status, started_at, completed_at, error_message
            FROM audit_runs 
            WHERE status = ?
            ORDER BY started_at DESC LIMIT ?
        """, (status, limit))
    else:
        db.execute_query(cursor, """
            SELECT id, run_type, status, started_at, completed_at, error_message
            FROM audit_runs 
            ORDER BY started_at DESC LIMIT ?
        """, (limit,))
    
    audits = cursor.fetchall()
    conn.close()
    
    if not audits:
        print(f"No audits found{' with status: ' + status if status else ''}")
        return
    
    print(f"\n{'ID':<5} {'Type':<10} {'Status':<12} {'Started':<20} {'Duration':<10}")
    print("-" * 70)
    
    for audit in audits:
        audit_dict = dict(audit) if not isinstance(audit, dict) else audit
        duration = "-"
        if audit_dict.get('completed_at'):
            start = audit_dict['started_at']
            end = audit_dict['completed_at']
            if isinstance(start, str):
                from datetime import datetime
                start = datetime.fromisoformat(start.replace('Z', '+00:00'))
                end = datetime.fromisoformat(end.replace('Z', '+00:00'))
            delta = end - start
            minutes = int(delta.total_seconds() / 60)
            duration = f"{minutes}m"
        
        print(f"{audit_dict['id']:<5} {audit_dict['run_type']:<10} "
              f"{audit_dict['status']:<12} "
              f"{str(audit_dict['started_at'])[:19]:<20} {duration:<10}")
        
        if audit_dict.get('error_message'):
            print(f"      Error: {audit_dict['error_message'][:60]}")
    print()


def cancel_audit(db, audit_id):
    """Cancel a running audit"""
    conn = db.get_connection()
    cursor = db.get_cursor(conn)
    
    try:
        # Check if audit exists and is running
        db.execute_query(cursor, 
            "SELECT id, status FROM audit_runs WHERE id = ?", 
            (audit_id,))
        audit = cursor.fetchone()
        
        if not audit:
            print(f"❌ Audit #{audit_id} not found")
            conn.close()
            return False
        
        audit_dict = dict(audit) if not isinstance(audit, dict) else audit
        if audit_dict['status'] != 'running':
            print(f"⚠️  Audit #{audit_id} is not running "
                  f"(status: {audit_dict['status']})")
            conn.close()
            return False
        
        # Mark as cancelled
        db.execute_query(cursor, """
            UPDATE audit_runs 
            SET status = 'cancelled', 
                completed_at = ?,
                error_message = 'Manually cancelled via CLI'
            WHERE id = ?
        """, (datetime.utcnow(), audit_id))
        
        conn.commit()
        print(f"✅ Audit #{audit_id} cancelled successfully")
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error cancelling audit: {e}")
        return False
    finally:
        if conn:
            conn.close()


def cleanup_telegram_session(db):
    """Reset Telegram audit status and clear session locks"""
    conn = db.get_connection()
    cursor = db.get_cursor(conn)
    
    try:
        # Reset telegram_audit_status table
        db.execute_query(cursor, """
            UPDATE telegram_audit_status 
            SET status = 'idle', 
                message = '', 
                error = NULL,
                code = NULL,
                password = NULL
            WHERE id = 1
        """)
        
        conn.commit()
        print("✅ Telegram session status cleared")
        
        # Try to clean up session files if they exist
        session_files = list(Path.cwd().glob("*.session*"))
        if session_files:
            for f in session_files:
                try:
                    f.unlink()
                    print(f"🗑️  Removed session file: {f.name}")
                except Exception as e:
                    print(f"⚠️  Could not remove {f.name}: {e}")
        else:
            print("ℹ️  No session files found to clean up")
        
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error cleaning up session: {e}")
        return False
    finally:
        if conn:
            conn.close()


def cancel_all_running(db):
    """Cancel all running audits"""
    conn = db.get_connection()
    cursor = db.get_cursor(conn)
    
    try:
        # Find all running audits
        db.execute_query(cursor, 
            "SELECT id FROM audit_runs WHERE status = 'running'")
        running = cursor.fetchall()
        
        if not running:
            print("ℹ️  No running audits to cancel")
            return True
        
        count = 0
        for audit in running:
            audit_dict = dict(audit) if not isinstance(audit, dict) else audit
            audit_id = audit_dict['id']
            db.execute_query(cursor, """
                UPDATE audit_runs 
                SET status = 'cancelled',
                    completed_at = ?,
                    error_message = 'Bulk cancelled via CLI'
                WHERE id = ?
            """, (datetime.utcnow(), audit_id))
            count += 1
            print(f"✅ Cancelled audit #{audit_id}")
        
        conn.commit()
        print(f"\n✅ Cancelled {count} audit(s)")
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error cancelling audits: {e}")
        return False
    finally:
        if conn:
            conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Manage customer group audits"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List recent audits')
    list_parser.add_argument(
        '--status', 
        choices=['running', 'completed', 'failed', 'cancelled'],
        help='Filter by status'
    )
    list_parser.add_argument(
        '--limit', 
        type=int, 
        default=10,
        help='Number of audits to show (default: 10)'
    )
    
    # Cancel command
    cancel_parser = subparsers.add_parser(
        'cancel', 
        help='Cancel a running audit'
    )
    cancel_parser.add_argument('audit_id', type=int, help='Audit ID to cancel')
    
    # Cancel all command
    subparsers.add_parser(
        'cancel-all', 
        help='Cancel all running audits'
    )
    
    # Cleanup command
    subparsers.add_parser(
        'cleanup', 
        help='Clean up Telegram session locks and reset status'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize database
    db = Database()
    
    # Execute command
    if args.command == 'list':
        list_audits(db, args.status, args.limit)
    
    elif args.command == 'cancel':
        cancel_audit(db, args.audit_id)
    
    elif args.command == 'cancel-all':
        cancel_all_running(db)
    
    elif args.command == 'cleanup':
        cleanup_telegram_session(db)
        # Also cancel any stuck running audits after cleanup
        print("\nChecking for stuck running audits...")
        cancel_all_running(db)


if __name__ == "__main__":
    main()

