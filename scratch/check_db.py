import sqlite3
import os

DB_PATH = r"c:\Users\LENOVO\Downloads\ecosurv (2)\ecosurv\ecosurv\dompetin.db"

def check_db():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("--- smart_saving_goals ---")
    c.execute("SELECT * FROM smart_saving_goals")
    rows = c.fetchall()
    for row in rows:
        print(row)
        
    print("\n--- budgets ---")
    c.execute("SELECT * FROM budgets")
    rows = c.fetchall()
    for row in rows:
        print(row)
        
    conn.close()

if __name__ == "__main__":
    check_db()
