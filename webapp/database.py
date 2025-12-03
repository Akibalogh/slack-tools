"""
Database setup and models for Admin Panel
"""

import os
from pathlib import Path

import psycopg2
import psycopg2.extras


class Database:
    def __init__(self, db_url=None):
        """Initialize database connection"""
        if db_url is None:
            # Use Heroku DATABASE_URL or local sqlite fallback
            db_url = os.environ.get("DATABASE_URL")
            if not db_url:
                # Local development fallback (though we now prefer Postgres)
                project_root = Path(__file__).parent.parent
                db_path = project_root / "data" / "admin_panel.db"
                db_url = f"file:{db_path}"

        # Fix for Heroku postgres:// -> postgresql://
        if db_url and db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)

        self.db_url = db_url
        self.is_postgres = db_url and db_url.startswith("postgresql://")
        self.init_db()

    def get_connection(self):
        """Get database connection"""
        if self.is_postgres:
            conn = psycopg2.connect(self.db_url)
            return conn
        else:
            # Fallback to sqlite for local dev
            import sqlite3

            conn = sqlite3.connect(self.db_url.replace("file:", ""))
            conn.row_factory = sqlite3.Row
            return conn

    def get_cursor(self, conn):
        """Get a cursor with appropriate row factory"""
        if self.is_postgres:
            return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            return conn.cursor()

    def param_placeholder(self):
        """Get the correct parameter placeholder for the database type"""
        return "%s" if self.is_postgres else "?"

    def execute_query(self, cursor, query, params=None):
        """Execute a query with the correct parameter placeholder"""
        if self.is_postgres:
            # Replace ? with %s for Postgres
            query = query.replace("?", "%s")
            # Replace CURRENT_TIMESTAMP with NOW() for Postgres
            query = query.replace("CURRENT_TIMESTAMP", "NOW()")
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

    def safe_execute(self, query, params=None, fetch_one=False, fetch_all=False):
        """
        Execute a query with automatic transaction handling and error recovery.
        Returns: result of query if fetch_one or fetch_all is True, None otherwise
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = self.get_cursor(conn) if self.is_postgres else conn.cursor()
            self.execute_query(cursor, query, params)

            result = None
            if fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()

            conn.commit()
            return result
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()

    def init_db(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = self.get_cursor(conn) if self.is_postgres else conn.cursor()

        if self.is_postgres:
            # Postgres-specific schema
            # Employees table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS employees (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    slack_username TEXT,
                    slack_user_id TEXT,
                    telegram_username TEXT,
                    email TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    slack_required BOOLEAN DEFAULT TRUE,
                    telegram_required BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """
            )

            # Audit runs table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_runs (
                    id SERIAL PRIMARY KEY,
                    run_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TIMESTAMP DEFAULT NOW(),
                    completed_at TIMESTAMP,
                    slack_channels_total INTEGER,
                    slack_channels_complete INTEGER,
                    telegram_groups_total INTEGER,
                    telegram_groups_complete INTEGER,
                    report_path TEXT,
                    error_message TEXT
                )
            """
            )

            # Audit findings table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_findings (
                    id SERIAL PRIMARY KEY,
                    audit_run_id INTEGER NOT NULL,
                    platform TEXT NOT NULL,
                    channel_name TEXT NOT NULL,
                    channel_id TEXT,
                    missing_members TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    FOREIGN KEY (audit_run_id) REFERENCES audit_runs(id)
                )
            """
            )

            # Offboarding tasks table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS offboarding_tasks (
                    id SERIAL PRIMARY KEY,
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
                    created_at TIMESTAMP DEFAULT NOW(),
                    FOREIGN KEY (employee_id) REFERENCES employees(id)
                )
            """
            )

            # Telegram audit status table (single row to track current status across workers)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS telegram_audit_status (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    status TEXT NOT NULL DEFAULT 'idle',
                    message TEXT DEFAULT '',
                    error TEXT,
                    code TEXT,
                    password TEXT,
                    session_string TEXT,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """
            )

            # Insert initial row if it doesn't exist (Postgres syntax)
            self.execute_query(
                cursor,
                """
                INSERT INTO telegram_audit_status (id, status, message)
                VALUES (1, 'idle', '')
                ON CONFLICT (id) DO NOTHING
            """,
            )

        else:
            # SQLite-specific schema (local dev fallback)
            # Employees table
            cursor.execute(
                """
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
            """
            )

            # Audit runs table
            cursor.execute(
                """
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
            """
            )

            # Audit findings table
            cursor.execute(
                """
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
            """
            )

            # Offboarding tasks table
            cursor.execute(
                """
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
            """
            )

            # Telegram audit status table (single row to track current status across workers)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS telegram_audit_status (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    status TEXT NOT NULL DEFAULT 'idle',
                    message TEXT DEFAULT '',
                    error TEXT,
                    code TEXT,
                    password TEXT,
                    session_string TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Insert initial row if it doesn't exist (SQLite syntax)
            cursor.execute(
                """
                INSERT OR IGNORE INTO telegram_audit_status (id, status, message)
                VALUES (1, 'idle', '')
            """
            )

        conn.commit()
        conn.close()

    def seed_initial_data(self):
        """Seed database with current team members"""
        conn = self.get_connection()
        cursor = self.get_cursor(conn) if self.is_postgres else conn.cursor()

        # Check if already seeded
        cursor.execute("SELECT COUNT(*) as count FROM employees")
        row = cursor.fetchone()
        count = row["count"] if isinstance(row, dict) else row[0]
        if count > 0:
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
                "telegram_username": "gabitui",
                "email": "gabi@bitsafe.finance",
                "status": "active",
                "slack_required": True,
                "telegram_required": True,
            },
            {
                "name": "Mayank Sachdev",
                "slack_username": "mayank",
                "slack_user_id": "U091F8WHDC3",
                "telegram_username": "mojo_onchain",
                "email": "mayank@bitsafe.finance",
                "status": "active",
                "slack_required": True,
                "telegram_required": True,
            },
            {
                "name": "Kadeem Clarke",
                "slack_username": "kadeem",
                "slack_user_id": "U08JNLKMH60",
                "telegram_username": "kadeemclarke",
                "email": "kadeem@bitsafe.finance",
                "status": "active",
                "slack_required": True,
                "telegram_required": True,
            },
            {
                "name": "Amy Wu",
                "slack_username": "amy",
                "slack_user_id": "U05J9GZJ70E",
                "telegram_username": "NonFungibleAmy",
                "email": "amy@bitsafe.finance",
                "status": "active",
                "slack_required": True,
                "telegram_required": True,
            },
            {
                "name": "Kevin Huet",
                "slack_username": "kevin",
                "slack_user_id": "U09S1JLS6EN",
                "telegram_username": "Sw3zz",
                "email": "kevin@bitsafe.finance",
                "status": "active",
                "slack_required": True,
                "telegram_required": True,
            },
            {
                "name": "Aliya Gordon",
                "slack_username": "aliya",
                "slack_user_id": "U09RZH933NJ",
                "telegram_username": "agordon888",
                "email": "aliya@bitsafe.finance",
                "status": "active",
                "slack_required": True,
                "telegram_required": True,
            },
            {
                "name": "Dave Shin",
                "slack_username": "dave",
                "slack_user_id": "U0997HN7KPE",
                "telegram_username": "shin_novation",
                "email": "dave@bitsafe.finance",
                "status": "active",
                "slack_required": True,
                "telegram_required": False,
            },
            {
                "name": "Dae Lee",
                "slack_username": "dae",
                "slack_user_id": "U09KR1HKMND",
                "telegram_username": "Dae_L",
                "email": "dae@bitsafe.finance",
                "status": "active",
                "slack_required": True,
                "telegram_required": False,
            },
            {
                "name": "Jesse Eisenberg",
                "slack_username": "jesse",
                "slack_user_id": "U05G2HFEAQD",
                "telegram_username": "j_eisenberg",
                "email": "jesse@bitsafe.finance",
                "status": "active",
                "slack_required": True,
                "telegram_required": True,
            },
            {
                "name": "Sarah Flood",
                "slack_username": "sarah",
                "slack_user_id": "UXXXXXXXX",  # TODO: Get actual Slack user ID
                "telegram_username": "sfl00d",
                "email": "sarah@bitsafe.finance",
                "status": "active",
                "slack_required": True,
                "telegram_required": True,
            },
        ]

        for member in team_members:
            if self.is_postgres:
                cursor.execute(
                    """
                    INSERT INTO employees 
                    (name, slack_username, slack_user_id, telegram_username, email, 
                     status, slack_required, telegram_required)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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
            else:
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
