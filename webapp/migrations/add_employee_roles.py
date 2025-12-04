#!/usr/bin/env python3
"""
Add role column to employees table and populate with current roles
"""

import os
import sys

# Add parent directory to path so we can import database
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Database
from dotenv import load_dotenv

load_dotenv()

# Role mappings based on current team structure
EMPLOYEE_ROLES = {
    "Aki Balogh": "CEO",
    "Gabi Tuinaite": "Head of Product",
    "Kadeem Clarke": "Head of Growth",
    "Amy Wu": "BD",
    "Kevin Huet": "BDR",
    "Aliya Gordon": "BDR",
    "Sarah Flood": "BDR",
    "Mayank Sachdev": "Sales Engineer",
    "Jesse Eisenberg": "CTO",
    "Dave Shin": "Strategy Advisor",
    "Dae Lee": "Sales Advisor",
    "Anna Matusova": "VP Finance & Legal",
}


def main():
    print("=" * 80)
    print("📊 ADDING ROLE COLUMN TO EMPLOYEES TABLE")
    print("=" * 80)

    db = Database()
    conn = db.get_connection()
    cursor = db.get_cursor(conn)

    print("\n1️⃣ Adding role column...")

    try:
        if db.is_postgres:
            # Postgres syntax
            cursor.execute(
                """
                ALTER TABLE employees
                ADD COLUMN IF NOT EXISTS role TEXT
            """
            )
        else:
            # SQLite syntax - check if column exists first
            cursor.execute("PRAGMA table_info(employees)")
            columns = [row[1] for row in cursor.fetchall()]
            if "role" not in columns:
                cursor.execute("ALTER TABLE employees ADD COLUMN role TEXT")

        conn.commit()
        print("   ✅ Role column added")

    except Exception as e:
        print(f"   ⚠️  Column may already exist: {e}")
        conn.rollback()

    print("\n2️⃣ Populating roles for existing employees...")

    for name, role in EMPLOYEE_ROLES.items():
        try:
            if db.is_postgres:
                cursor.execute(
                    "UPDATE employees SET role = %s WHERE name = %s", (role, name)
                )
            else:
                cursor.execute(
                    "UPDATE employees SET role = ? WHERE name = ?", (role, name)
                )

            if cursor.rowcount > 0:
                print(f"   ✅ {name}: {role}")
            else:
                print(f"   ⚠️  {name}: Not found in database")

        except Exception as e:
            print(f"   ❌ {name}: Error - {e}")

    conn.commit()

    print("\n3️⃣ Verifying updates...")
    db.execute_query(cursor, "SELECT name, role FROM employees ORDER BY name")
    employees = cursor.fetchall()

    for emp in employees:
        emp_dict = dict(emp) if not isinstance(emp, dict) else emp
        name = emp_dict.get("name")
        role = emp_dict.get("role") or "Not set"
        print(f"   {name}: {role}")

    conn.close()

    print("\n" + "=" * 80)
    print("✅ Migration complete!")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())

