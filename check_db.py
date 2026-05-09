import sqlite3
import os

db_path = 'dompetin.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='saving_goals'")
    table_exists = c.fetchone()
    if table_exists:
        print("Table 'saving_goals' exists.")
        c.execute("PRAGMA table_info(saving_goals)")
        columns = c.fetchall()
        for col in columns:
            print(col)
    else:
        print("Table 'saving_goals' does NOT exist.")
    conn.close()
else:
    print(f"File {db_path} not found.")
