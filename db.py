import os
import sqlite3
from contextlib import contextmanager

# Local development with SQLite
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SQLITE_PATH = os.path.join(BASE_DIR, 'database.db')

print(f"[DB] Using SQLite at {SQLITE_PATH}")

def get_db():
    """
    Returns a connection object.
    Usage: conn = get_db(); c = conn.cursor()
    """
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_conn():
    """Context manager that yields a (conn, cursor) tuple and auto-commits/closes."""
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        yield conn, cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

def init_db():
    """Create all tables if they don't exist (idempotent)."""
    with get_conn() as (conn, c):
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY, name TEXT, email TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY, type TEXT, amount REAL,
                        category TEXT, date TEXT, description TEXT,
                        notes TEXT DEFAULT '')''')
        c.execute('''CREATE TABLE IF NOT EXISTS budgets (
                        id INTEGER PRIMARY KEY, category TEXT UNIQUE, amount REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS saving_goals (
                        id INTEGER PRIMARY KEY, item_name TEXT NOT NULL,
                        target_amount REAL NOT NULL, current_amount REAL DEFAULT 0,
                        target_date TEXT NOT NULL, created_date TEXT, notes TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS smart_saving_goals (
                        id INTEGER PRIMARY KEY, item_name TEXT NOT NULL,
                        target_price REAL NOT NULL, current_savings REAL DEFAULT 0,
                        deadline_date TEXT NOT NULL, created_date TEXT NOT NULL, notes TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS smart_saving_logs (
                        id INTEGER PRIMARY KEY, goal_id INTEGER NOT NULL,
                        log_date TEXT NOT NULL, amount_saved REAL DEFAULT 0,
                        daily_spending REAL DEFAULT 0,
                        FOREIGN KEY (goal_id) REFERENCES smart_saving_goals(id))''')

        # Seed default data
        c.execute("INSERT OR IGNORE INTO users (id, name, email) VALUES (1, 'User', 'user@example.com')")
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('total_budget', '3000000')")

        default_budgets = [
            ('food', 1500000), ('transport', 450000), ('bills', 100000),
            ('entertainment', 650000), ('savings', 300000)
        ]
        for cat, amt in default_budgets:
            c.execute("INSERT OR REPLACE INTO budgets (category, amount) VALUES (?, ?)", (cat, amt))
