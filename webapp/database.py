"""
Database setup and models for Admin Panel
"""
import os
import sqlite3
from datetime import datetime
from pathlib import Path


class Database:
    def __init__(self, db_path=None):
        """Initialize database connection"""
        if db_path is None:
            # Use absolute path relative to project root
            project_root = Path(__file__).parent.parent
            db_path = project_root / "data" / "admin_panel.db"
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Employees table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                slack_username TEXT,
                slack_user_id TEXT,
                telegram_username TEXT,
                email TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                slack_required BOOLEAN DEFAULT 1,
                telegram_required BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Audit runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_type TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                slack_channels_total INTEGER,
                slack_channels_complete INTEGER,
                telegram_groups_total INTEGER,
                telegram_groups_complete INTEGER,
                report_path TEXT,
                error_message TEXT
            )
        """)

        # Audit findings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audit_run_id INTEGER NOT NULL,
                platform TEXT NOT NULL,
                channel_name TEXT NOT NULL,
                channel_id TEXT,
                missing_members TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (audit_run_id) REFERENCES audit_runs(id)
            )
        """)

        # Offboarding tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS offboarding_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                platform TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                groups_processed INTEGER,
                groups_removed INTEGER,
                groups_failed INTEGER,
                report_path TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            )
        """)

        conn.commit()
        conn.close()

    def seed_initial_data(self):
        """Seed database with current team members"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if already seeded
        cursor.execute("SELECT COUNT(*) FROM employees")
        if cursor.fetchone()[0] > 0:
            print("⚠️  Database already contains employees. Skipping seed.")
            conn.close()
            return

        # Current team members (using actual Slack usernames from workspace)
        team_members = [
            {
                "name": "Aki Balogh",
                "slack_username": "aki",
                "slack_user_id": "U05FZBDQ4RJ",
                "telegram_username": "akibalogh",
                "email": "aki@bitsafe.finance",
                "status": "active",
                "slack_required": True,
                "telegram_required": True,
            },
            {
                "name": "Gabi Tuinaite",
                "slack_username": "gabi",
                "slack_user_id": "U04QGJC7MCU",
                "telegram_username": None,
                "email": "gabi@bitsafe.finance",
                "status": "active",
                "slack_required": True,
                "telegram_required": False,
            },
            {
                "name": "Mayank Sachdev",
                "slack_username": "mayank",
                "slack_user_id": "U091F8WHDC3",
                "telegram_username": "mojo_onchain",
                "email": "mayank@bitsafe.finance",
                "status": "active",
                "slack_required": True,
                "telegram_required": False,
            },
            {
                "name": "Kadeem Clarke",
                "slack_username": "kadeem",
                "slack_user_id": "U08JNLKMH60",
                "telegram_username": None,
                "email": "kadeem@bitsafe.finance",
                "status": "active",
                "slack_required": True,
                "telegram_required": False,
            },
            {
                "name": "Amy Wu",
                "slack_username": "amy",
                "slack_user_id": "U05J9GZJ70E",
                "telegram_username": None,
                "email": "amy@bitsafe.finance",
                "status": "active",
                "slack_required": True,
                "telegram_required": False,
            },
            {
                "name": "Kevin Huet",
                "slack_username": "kevin",
                "slack_user_id": "U09S1JLS6EN",
                "telegram_username": "Sw3zz",
                "email": "kevin@bitsafe.finance",
                "status": "active",
                "slack_required": True,
                "telegram_required": False,
            },
            {
                "name": "Aliya Gordon",
                "slack_username": "aliya",
                "slack_user_id": "U09RZH933NJ",
                "telegram_username": "agordon888",
                "email": "aliya@bitsafe.finance",
                "status": "active",
                "slack_required": True,
                "telegram_required": False,
            },
            {
                "name": "Dave Shin",
                "slack_username": "dave",
                "slack_user_id": "U0997HN7KPE",
                "telegram_username": None,
                "email": "dave@bitsafe.finance",
                "status": "active",
                "slack_required": True,
                "telegram_required": False,
            },
            {
                "name": "Dae Lee",
                "slack_username": "dae",
                "slack_user_id": "U09KR1HKMND",
                "telegram_username": None,
                "email": "dae@bitsafe.finance",
                "status": "active",
                "slack_required": True,
                "telegram_required": False,
            },
        ]

        for member in team_members:
            cursor.execute(
                """
                INSERT INTO employees 
                (name, slack_username, slack_user_id, telegram_username, email, 
                 status, slack_required, telegram_required)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    member["name"],
                    member["slack_username"],
                    member["slack_user_id"],
                    member["telegram_username"],
                    member["email"],
                    member["status"],
                    member["slack_required"],
                    member["telegram_required"],
                ),
            )

        conn.commit()
        conn.close()
        print(f"✅ Seeded {len(team_members)} team members")


if __name__ == "__main__":
    print("🗄️  Initializing database...")
    db = Database()
    print("✅ Database schema created")

    print("\n🌱 Seeding initial data...")
    db.seed_initial_data()
    print("✅ Database ready!")

