import sqlite3
import os

DB_PATH = 'dompetin.db'

def check_db():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("--- Transactions ---")
    c.execute("SELECT * FROM transactions")
    rows = c.fetchall()
    for r in rows:
        print(r)
        
    print("\n--- Summary Stats ---")
    c.execute("SELECT type, SUM(amount) FROM transactions GROUP BY type")
    print(c.fetchall())
    
    conn.close()

if __name__ == "__main__":
    check_db()
