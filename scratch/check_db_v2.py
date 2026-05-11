import sqlite3
import os

DB_PATH = r"c:\Users\LENOVO\Downloads\ecosurv (2)\ecosurv\ecosurv\dompetin.db"

def check_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("--- saving_goals ---")
    try:
        c.execute("SELECT * FROM saving_goals")
        rows = c.fetchall()
        for row in rows:
            print(row)
    except Exception as e:
        print(f"Error: {e}")
        
    print("\n--- transactions today ---")
    from datetime import date
    today_str = date.today().isoformat()
    c.execute("SELECT * FROM transactions WHERE date=?", (today_str,))
    rows = c.fetchall()
    for row in rows:
        print(row)
        
    conn.close()

if __name__ == "__main__":
    check_db()
