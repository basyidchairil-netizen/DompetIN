from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
import sqlite3
import os
from datetime import datetime
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

app = Flask(__name__, template_folder='.')

# OpenAI Client - menggunakan API key dari environment variable
def get_openai_client():
    if not HAS_OPENAI:
        raise ValueError("Library 'openai' tidak terinstal. Silakan jalankan 'pip install openai'.")
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return OpenAI(api_key=api_key)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'dompetin.db')

# Database setup
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Users table (simple MVP, assume one user)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    email TEXT
                )''')
    # Transactions table
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY,
                    type TEXT,  -- 'income' or 'expense'
                    amount REAL,
                    category TEXT,
                    date TEXT,
                    description TEXT
                )''')
    # Budgets table with UNIQUE constraint and automatic migration
    c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='budgets'")
    table_sql = c.fetchone()
    if table_sql and 'UNIQUE' not in table_sql[0]:
        # Migrate table to add UNIQUE constraint
        c.execute("CREATE TABLE budgets_new (id INTEGER PRIMARY KEY, category TEXT UNIQUE, amount REAL)")
        c.execute("INSERT OR IGNORE INTO budgets_new (category, amount) SELECT category, amount FROM budgets GROUP BY category")
        c.execute("DROP TABLE budgets")
        c.execute("ALTER TABLE budgets_new RENAME TO budgets")
    else:
        c.execute('''CREATE TABLE IF NOT EXISTS budgets (
                        id INTEGER PRIMARY KEY,
                        category TEXT UNIQUE,
                        amount REAL
                    )''')
    # Saving goals table
    c.execute('''CREATE TABLE IF NOT EXISTS saving_goals (
                    id INTEGER PRIMARY KEY,
                    item_name TEXT,
                    target_amount REAL,
                    current_amount REAL DEFAULT 0,
                    target_date TEXT
                )''')
    # Insert default user if not exists
    c.execute("INSERT OR IGNORE INTO users (id, name, email) VALUES (1, 'User', 'user@example.com')")
    # Insert default budgets
    default_budgets = [
        ('Food/Dining', 1500000),
        ('Transportasi', 450000),
        ('Paket Kuota', 100000),
        ('Shopping & Hiburan', 650000),
        ('Tabungan', 300000)
    ]
    for category, amount in default_budgets:
        c.execute("INSERT OR REPLACE INTO budgets (category, amount) VALUES (?, ?)", (category, amount))
    
    # Insert sample transactions for demonstration
    sample_transactions = [
        # January 2025 - Income
        ('income', 5000000, 'Salary', '2025-01-01', 'Monthly Salary'),
        ('income', 500000, 'Freelance', '2025-01-15', 'Web Development Project'),
        # January 2025 - Expenses
        ('expense', 1500000, 'Food/Dining', '2025-01-03', 'Monthly Groceries'),
        ('expense', 300000, 'Transportasi', '2025-01-05', 'GoJek & Grab'),
        ('expense', 200000, 'Shopping & Hiburan', '2025-01-10', 'Netflix & Spotify'),
        ('expense', 350000, 'Paket Kuota', '2025-01-12', 'Electricity & Water'),
        ('expense', 150000, 'Tabungan', '2025-01-20', 'Miscellaneous'),
        
        # February 2025 - Income
        ('income', 5000000, 'Salary', '2025-02-01', 'Monthly Salary'),
        ('income', 750000, 'Freelance', '2025-02-20', 'App Development'),
        # February 2025 - Expenses
        ('expense', 1400000, 'Food/Dining', '2025-02-04', 'Monthly Groceries'),
        ('expense', 250000, 'Transportasi', '2025-02-08', 'GoJek & Grab'),
        ('expense', 200000, 'Shopping & Hiburan', '2025-02-12', 'Netflix & Spotify'),
        ('expense', 380000, 'Paket Kuota', '2025-02-14', 'Electricity & Water'),
        ('expense', 100000, 'Tabungan', '2025-02-22', 'Miscellaneous'),
        
        # March 2025 - Income
        ('income', 5000000, 'Salary', '2025-03-01', 'Monthly Salary'),
        ('income', 1000000, 'Freelance', '2025-03-18', 'Consulting Project'),
        # March 2025 - Expenses
        ('expense', 1600000, 'Food/Dining', '2025-03-05', 'Monthly Groceries'),
        ('expense', 280000, 'Transportasi', '2025-03-10', 'GoJek & Grab'),
        ('expense', 200000, 'Shopping & Hiburan', '2025-03-15', 'Netflix & Spotify'),
        ('expense', 320000, 'Paket Kuota', '2025-03-18', 'Electricity & Water'),
        ('expense', 200000, 'Tabungan', '2025-03-25', 'Miscellaneous'),
        
        # April 2025 - Income
        ('income', 5500000, 'Salary', '2025-04-01', 'Monthly Salary (Raise)'),
        ('income', 500000, 'Freelance', '2025-04-22', 'Logo Design'),
        # April 2025 - Expenses
        ('expense', 1450000, 'Food/Dining', '2025-04-04', 'Monthly Groceries'),
        ('expense', 220000, 'Transportasi', '2025-04-09', 'GoJek & Grab'),
        ('expense', 200000, 'Shopping & Hiburan', '2025-04-14', 'Netflix & Spotify'),
        ('expense', 400000, 'Paket Kuota', '2025-04-17', 'Electricity & Water'),
        ('expense', 180000, 'Tabungan', '2025-04-26', 'Miscellaneous'),
        
        # May 2025 - Income
        ('income', 5500000, 'Salary', '2025-05-01', 'Monthly Salary'),
        ('income', 800000, 'Freelance', '2025-05-20', 'Website Maintenance'),
        # May 2025 - Expenses
        ('expense', 1550000, 'Food/Dining', '2025-05-04', 'Monthly Groceries'),
        ('expense', 300000, 'Transportasi', '2025-05-10', 'GoJek & Grab'),
        ('expense', 200000, 'Shopping & Hiburan', '2025-05-15', 'Netflix & Spotify'),
        ('expense', 350000, 'Paket Kuota', '2025-05-18', 'Electricity & Water'),
        ('expense', 120000, 'Tabungan', '2025-05-24', 'Miscellaneous'),
        
        # June 2025 - Income
        ('income', 5500000, 'Salary', '2025-06-01', 'Monthly Salary'),
        ('income', 600000, 'Freelance', '2025-06-15', 'Mobile App Project'),
        # June 2025 - Expenses
        ('expense', 1500000, 'Food/Dining', '2025-06-04', 'Monthly Groceries'),
        ('expense', 270000, 'Transportasi', '2025-06-09', 'GoJek & Grab'),
        ('expense', 200000, 'Shopping & Hiburan', '2025-06-14', 'Netflix & Spotify'),
        ('expense', 380000, 'Paket Kuota', '2025-06-17', 'Electricity & Water'),
        ('expense', 160000, 'Tabungan', '2025-06-25', 'Miscellaneous'),
    ]
    
    # Insert sample transactions only if transactions table is empty
    c.execute("SELECT COUNT(*) FROM transactions")
    if c.fetchone()[0] == 0:
        for type_, amount, category, date, description in sample_transactions:
            c.execute("INSERT INTO transactions (type, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
                      (type_, amount, category, date, description))
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
@app.route('/index.html')
def landing():
    return render_template('index.html')

@app.route('/profile')
@app.route('/profile.html')
def profile():
    return render_template('profile.html')

@app.route('/budgetplaning.html')
def budget_planning():
    return render_template('budgetplaning.html')

@app.route('/incomeTracking.html')
def income_tracking():
    return render_template('incomeTracking.html')

@app.route('/analysis.html')
def analysis_page():
    return render_template('analysis.html')

@app.route('/login.html')
def login_page():
    return render_template('login.html')

@app.route('/dashboard')
@app.route('/dashboard.html')
def dashboard():
    # Get total balance
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT SUM(CASE WHEN type='income' THEN amount ELSE -amount END) FROM transactions")
    balance = c.fetchone()[0] or 0
    # Get monthly spending (current month)
    current_month = datetime.now().strftime('%Y-%m')
    c.execute("SELECT category, SUM(amount) FROM transactions WHERE type='expense' AND date LIKE ? GROUP BY category", (current_month + '%',))
    spending = dict(c.fetchall())
    conn.close()
    return render_template('dashboard.html', balance=balance, spending=spending)

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    data = request.json
    type_ = data['type']
    amount = float(data['amount'])
    category = data['category']
    date = data['date']
    description = data['description']
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO transactions (type, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
              (type_, amount, category, date, description))
    # Check budget
    c.execute("SELECT amount FROM budgets WHERE category=?", (category,))
    budget = c.fetchone()
    if budget:
        c.execute("SELECT SUM(amount) FROM transactions WHERE type='expense' AND category=? AND date LIKE ?", (category, datetime.now().strftime('%Y-%m') + '%'))
        spent = c.fetchone()[0] or 0
        if spent > 0.8 * budget[0]:
            nudge = f"Warning: Spending in {category} is nearing budget limit."
        else:
            nudge = None
    else:
        nudge = None
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'nudge': nudge})

@app.route('/get_spending')
def get_spending():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    current_month = datetime.now().strftime('%Y-%m')
    c.execute("SELECT category, SUM(amount) FROM transactions WHERE type='expense' AND date LIKE ? GROUP BY category", (current_month + '%',))
    spending = dict(c.fetchall())
    conn.close()
    return jsonify(spending)

@app.route('/get_transactions')
def get_transactions():
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, type, amount, category, date, description FROM transactions WHERE date=?", (date,))
    rows = c.fetchall()
    conn.close()
    
    transactions = []
    for row in rows:
        transactions.append({
            'id': row[0],
            'type': row[1],
            'amount': row[2],
            'category': row[3],
            'date': row[4],
            'desc': row[5] if row[5] else '',
            'notes': ''
        })
    return jsonify(transactions)

@app.route('/academy')
def academy():
    articles = [
        {'title': 'Understanding Budgeting', 'content': 'Budgeting is key to financial health...', 'read_more': 'Full article here.'},
        {'title': 'Saving for the Future', 'content': 'Start saving early...', 'read_more': 'Full article here.'}
    ]
    return render_template('academy.html', articles=articles)

@app.route('/get_profile_stats')
def get_profile_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get total transactions count
    c.execute("SELECT COUNT(*) FROM transactions")
    total_transactions = c.fetchone()[0] or 0
    
    # Get total income and expenses
    c.execute("SELECT SUM(amount) FROM transactions WHERE type='income'")
    total_income = c.fetchone()[0] or 0
    
    c.execute("SELECT SUM(amount) FROM transactions WHERE type='expense'")
    total_expense = c.fetchone()[0] or 0
    
    # Calculate total savings (income - expense)
    total_savings = total_income - total_expense
    
    # Calculate average saving rate
    if total_income > 0:
        avg_saving_rate = round((total_savings / total_income) * 100, 1)
    else:
        avg_saving_rate = 0
    
    # Get active months (count distinct months with transactions)
    c.execute("SELECT DISTINCT substr(date, 1, 7) FROM transactions ORDER BY date")
    distinct_months = c.fetchall()
    active_months = len(distinct_months)
    
    conn.close()
    
    return jsonify({
        'total_transactions': total_transactions,
        'total_savings': total_savings,
        'total_income': total_income,
        'total_expense': total_expense,
        'avg_saving_rate': avg_saving_rate,
        'active_months': active_months
    })

@app.route('/get_monthly_income')
def get_monthly_income():
    """Get total income for the current month"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    current_month = datetime.now().strftime('%Y-%m')
    c.execute("SELECT SUM(amount) FROM transactions WHERE type='income' AND date LIKE ?", (current_month + '%',))
    monthly_income = c.fetchone()[0] or 0
    conn.close()
    return jsonify({'monthly_income': monthly_income})

@app.route('/get_income_by_month')
def get_income_by_month():
    """Get income for a specific month"""
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT SUM(amount) FROM transactions WHERE type='income' AND date LIKE ?", (month + '%',))
    monthly_income = c.fetchone()[0] or 0
    conn.close()
    return jsonify({'monthly_income': monthly_income})

@app.route('/api/saving_goals', methods=['GET', 'POST'])
def saving_goals():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if request.method == 'POST':
        data = request.json
        c.execute("INSERT INTO saving_goals (item_name, target_amount, current_amount, target_date) VALUES (?, ?, ?, ?)",
                  (data['item_name'], data['target_amount'], data.get('current_amount', 0), data['target_date']))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    else:
        c.execute("SELECT id, item_name, target_amount, current_amount, target_date FROM saving_goals")
        rows = c.fetchall()
        conn.close()
        goals = []
        for row in rows:
            goals.append({
                'id': row[0],
                'item_name': row[1],
                'target_amount': row[2],
                'current_amount': row[3],
                'target_date': row[4]
            })
        return jsonify(goals)

@app.route('/api/saving_goals/<int:goal_id>', methods=['DELETE', 'PATCH'])
def manage_saving_goal(goal_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if request.method == 'DELETE':
        c.execute("DELETE FROM saving_goals WHERE id=?", (goal_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    elif request.method == 'PATCH':
        data = request.json
        c.execute("UPDATE saving_goals SET current_amount = current_amount + ? WHERE id=?", (data['add_amount'], goal_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

@app.route('/api/budgets', methods=['GET', 'POST'])
def manage_budgets():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if request.method == 'POST':
        data = request.json
        # Check if category exists
        c.execute("SELECT id FROM budgets WHERE category=?", (data['category'],))
        row = c.fetchone()
        if row:
            c.execute("UPDATE budgets SET amount=? WHERE category=?", (data['amount'], data['category']))
        else:
            c.execute("INSERT INTO budgets (category, amount) VALUES (?, ?)", (data['category'], data['amount']))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    else:
        c.execute("SELECT category, amount FROM budgets")
        rows = c.fetchall()
        conn.close()
        return jsonify(dict(rows))

@app.route('/api/total_budget', methods=['GET', 'POST'])
def manage_total_budget():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if request.method == 'POST':
        data = request.json
        c.execute("INSERT OR REPLACE INTO budgets (category, amount) VALUES ('TOTAL_BUDGET', ?)", (data['amount'],))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    else:
        c.execute("SELECT amount FROM budgets WHERE category='TOTAL_BUDGET'")
        row = c.fetchone()
        conn.close()
        return jsonify({'total_budget': row[0] if row else 3000000})

# ==================== OpenAI Chat API ====================
@app.route('/api/chat', methods=['POST'])
def chat():
    """OpenAI Chat Completion endpoint - replaces Ollama"""
    try:
        data = request.json
        messages = data.get('messages', [])
        
        # Get financial context from database
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get recent transactions summary
        c.execute("SELECT SUM(CASE WHEN type='income' THEN amount ELSE -amount END) FROM transactions")
        balance = c.fetchone()[0] or 0
        
        c.execute("SELECT SUM(amount) FROM transactions WHERE type='income'")
        total_income = c.fetchone()[0] or 0
        
        c.execute("SELECT SUM(amount) FROM transactions WHERE type='expense'")
        total_expense = c.fetchone()[0] or 0
        
        c.execute("SELECT category, SUM(amount) as total FROM transactions WHERE type='expense' GROUP BY category ORDER BY total DESC")
        expenses_by_category = c.fetchall()
        
        conn.close()
        
        # Build system message with financial context
        expense_breakdown = ", ".join([f"{cat}: Rp {amt:,.0f}" for cat, amt in expenses_by_category])
        
        system_message = f"""Anda adalah asisten AI Dompetin yang ahli dalam keuangan personal. 
Anda membantu pengguna mengelola keuangan mereka dengan memberikan saran yang helpful dan friendly.

Data keuangan user:
- Total Balance: Rp {balance:,.0f}
- Total Pemasukan: Rp {total_income:,.0f}
- Total Pengeluaran: Rp {total_expense:,.0f}
- Pengeluaran per kategori: {expense_breakdown}

Selalu jawab dalam Bahasa Indonesia yang natural dan gunakan emoji yang sesuai. 
Berikan saran yang praktis dan actionable."""
        
        # Add system message at the beginning
        full_messages = [{"role": "system", "content": system_message}] + messages
        
        # Call OpenAI API
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=full_messages,
            temperature=0.7,
            max_tokens=500
        )
        
        # Return the response
        return jsonify({
            "response": response.choices[0].message.content,
            "success": True
        })
        
    except ValueError as e:
        return jsonify({"error": str(e), "success": False}), 500
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}", "success": False}), 500

if __name__ == '__main__':
    app.run(debug=True)
