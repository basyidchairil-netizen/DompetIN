from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
import sqlite3
import os
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import google.generativeai as genai
    HAS_GEMINI = True
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
except ImportError:
    HAS_GEMINI = False

app = Flask(__name__, template_folder='.')
app.secret_key = 'dompetin_secret_key_123' # Required for session management
from flask import session

# Jinja Filter untuk Format Rupiah
@app.template_filter('fmt_rupiah')
def fmt_rupiah(value):
    if value is None:
        return "Rp 0"
    try:
        # Format as Rp 1.234.567
        return f"Rp {int(value):,}".replace(',', '.')
    except (ValueError, TypeError):
        return f"Rp {value}"

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
                    description TEXT,
                    notes TEXT DEFAULT ''
                )''')
    
    # Check if 'notes' column exists in transactions
    c.execute("PRAGMA table_info(transactions)")
    columns = [col[1] for col in c.fetchall()]
    if 'notes' not in columns:
        c.execute("ALTER TABLE transactions ADD COLUMN notes TEXT DEFAULT ''")
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
                    item_name TEXT NOT NULL,
                    target_amount REAL NOT NULL,
                    current_amount REAL DEFAULT 0,
                    target_date TEXT NOT NULL,
                    created_date TEXT,
                    notes TEXT
                )''')
    
    # Migration: Check for missing columns in saving_goals
    c.execute("PRAGMA table_info(saving_goals)")
    cols = [col[1] for col in c.fetchall()]
    if 'created_date' not in cols:
        c.execute("ALTER TABLE saving_goals ADD COLUMN created_date TEXT")
    if 'notes' not in cols:
        c.execute("ALTER TABLE saving_goals ADD COLUMN notes TEXT")
    if 'current_amount' not in cols and 'current_savings' in cols:
        c.execute("ALTER TABLE saving_goals RENAME COLUMN current_savings TO current_amount")
    if 'target_amount' not in cols and 'target_price' in cols:
        c.execute("ALTER TABLE saving_goals RENAME COLUMN target_price TO target_amount")
    if 'target_date' not in cols and 'deadline_date' in cols:
        c.execute("ALTER TABLE saving_goals RENAME COLUMN deadline_date TO target_date")

    # Settings table
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )''')
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('total_budget', '3000000')")
    # Smart saving goals table
    c.execute('''CREATE TABLE IF NOT EXISTS smart_saving_goals (
                    id INTEGER PRIMARY KEY,
                    item_name TEXT NOT NULL,
                    target_price REAL NOT NULL,
                    current_savings REAL DEFAULT 0,
                    deadline_date TEXT NOT NULL,
                    created_date TEXT NOT NULL,
                    notes TEXT
                )''')
    # Smart saving daily logs
    c.execute('''CREATE TABLE IF NOT EXISTS smart_saving_logs (
                    id INTEGER PRIMARY KEY,
                    goal_id INTEGER NOT NULL,
                    log_date TEXT NOT NULL,
                    amount_saved REAL DEFAULT 0,
                    daily_spending REAL DEFAULT 0,
                    FOREIGN KEY (goal_id) REFERENCES smart_saving_goals(id)
                )''')
    # Insert default user if not exists
    c.execute("INSERT OR IGNORE INTO users (id, name, email) VALUES (1, 'User', 'user@example.com')")
    # Insert default budgets
    default_budgets = [
        ('food', 1500000),
        ('transport', 450000),
        ('bills', 100000),
        ('entertainment', 650000),
        ('savings', 300000)
    ]
    for category, amount in default_budgets:
        c.execute("INSERT OR REPLACE INTO budgets (category, amount) VALUES (?, ?)", (category, amount))
    
    conn.commit()
    conn.close()

init_db()

@app.context_processor
def inject_global_data():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    current_month = datetime.now().strftime('%Y-%m')
    
    # All-time balance
    c.execute("SELECT COALESCE(SUM(CASE WHEN type='income' THEN amount ELSE -amount END), 0) FROM transactions")
    balance = c.fetchone()[0]

    # Current month income
    c.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='income' AND date LIKE ?", (current_month + '%',))
    monthly_income = c.fetchone()[0]

    # Current month expenses
    c.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='expense' AND date LIKE ?", (current_month + '%',))
    monthly_expense = c.fetchone()[0]
    
    # Today's metrics
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='income' AND date = ?", (today,))
    today_income = c.fetchone()[0]
    
    c.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='expense' AND date = ?", (today,))
    today_expense = c.fetchone()[0]
    
    # Category spent for the month
    c.execute("SELECT category, COALESCE(SUM(amount), 0) FROM transactions WHERE type='expense' AND date LIKE ? GROUP BY category", (current_month + '%',))
    category_spent = dict(c.fetchall())
    
    # Total budget strictly mirrors monthly income
    total_budget = monthly_income

    # Dynamic Budget Allocation percentages
    CATEGORY_PERCENTAGES = {
        'food': 0.30,
        'transport': 0.10,
        'bills': 0.05,
        'entertainment': 0.15,
        'shopping': 0.10,
        'savings': 0.30
    }

    # Calculate category budgets based on total_budget
    category_budgets = {}
    for cat, percent in CATEGORY_PERCENTAGES.items():
        category_budgets[cat] = int(total_budget * percent)

    # Transactions for current month
    c.execute("SELECT id, type, description, amount, category, date FROM transactions WHERE date LIKE ? ORDER BY date DESC", (current_month + '%',))
    transactions = [
        {'id': row[0], 'type': row[1], 'description': row[2], 'amount': row[3], 'category': row[4], 'date': row[5]}
        for row in c.fetchall()
    ]

    # Weekly spending pattern (current week)
    now = datetime.now()
    start_of_week = now - timedelta(days=now.weekday())
    weekly_spending = []
    for i in range(7):
        day = start_of_week + timedelta(days=i)
        day_str = day.strftime('%Y-%m-%d')
        c.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='expense' AND date = ?", (day_str,))
        weekly_spending.append(c.fetchone()[0])

    # Category comparison for analysis (using the dynamic budgets)
    analysis_categories = [
        {'key': 'category_food', 'db_key': 'food', 'color': '#f97316', 'name': 'Food'},
        {'key': 'category_transport', 'db_key': 'transport', 'color': '#3b82f6', 'name': 'Transport'},
        {'key': 'category_entertainment', 'db_key': 'entertainment', 'color': '#ec4899', 'name': 'Entertainment'},
        {'key': 'category_bills', 'db_key': 'bills', 'color': '#8b5cf6', 'name': 'Bills'},
        {'key': 'category_shopping', 'db_key': 'shopping', 'color': '#14b8a6', 'name': 'Shopping'},
        {'key': 'category_savings', 'db_key': 'savings', 'color': '#10b981', 'name': 'Savings'}
    ]
    
    category_comparison = []
    for cat in analysis_categories:
        spent = category_spent.get(cat['db_key'], 0)
        budget = category_budgets.get(cat['db_key'], 0)
        category_comparison.append({
            'key': cat['key'],
            'name': cat['name'],
            'color': cat['color'],
            'spent': spent,
            'budget': budget
        })

    conn.close()
    # Date variables
    now = datetime.now()
    months_id = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    days_id = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    
    current_date_formatted = f"{days_id[now.weekday()] if now.weekday() < 7 else ''}, {now.day} {months_id[now.month]} {now.year}"
    current_month_name = months_id[now.month]
    current_year = now.year

    global_data = {
        'total_balance': balance,
        'monthly_income': monthly_income,
        'monthly_expense': monthly_expense,
        'today_income': today_income,
        'today_expense': today_expense,
        'total_budget': total_budget,
        'monthly_savings': monthly_income - monthly_expense,
        'category_spent': category_spent,
        'category_budgets': category_budgets,
        'transactions': transactions,
        'current_date_formatted': current_date_formatted,
        'current_month_name': current_month_name,
        'current_year': current_year,
        'weekly_spending': weekly_spending,
        'category_comparison': category_comparison
    }
    return dict(global_data=global_data)

@app.route('/')
@app.route('/index.html')
def landing():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    if email and password:
        session['logged_in'] = True
        session['user_email'] = email
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Invalid credentials"}), 401

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))

@app.route('/profile')
@app.route('/profile.html')
def profile():
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    return render_template('profile.html')

@app.route('/budgetplaning.html')
@app.route('/budgetplaning')
@app.route('/budget_planning')
def budget_planning():
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    return render_template('budgetplaning.html')

@app.route('/incomeTracking.html')
def income_tracking():
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    current_month = datetime.now().strftime('%Y-%m')
    c.execute("SELECT id, type, description, amount, category, date, notes FROM transactions WHERE date LIKE ? ORDER BY date DESC", (current_month + '%',))
    transactions = [
        {'id': row[0], 'type': row[1], 'desc': row[2], 'amount': row[3], 'category': row[4], 'date': row[5], 'notes': row[6]}
        for row in c.fetchall()
    ]
    conn.close()
    return render_template('incomeTracking.html', transactions=transactions)

@app.route('/smart_saving.html')
@app.route('/smart_saving')
def smart_saving_page():
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    return render_template('smart_saving.html')

@app.route('/analysis.html')
def analysis_page():
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    return render_template('analysis.html')

@app.route('/login.html')
def login_page():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
@app.route('/dashboard.html')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COALESCE(SUM(CASE WHEN type='income' THEN amount ELSE -amount END), 0) FROM transactions")
    balance = c.fetchone()[0]
    conn.close()
    return render_template('dashboard.html', balance=balance)

@app.route('/reset_data', methods=['POST'])
def reset_data():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM transactions")
        c.execute("UPDATE budgets SET amount = 0")
        c.execute("DELETE FROM smart_saving_goals")
        c.execute("DELETE FROM smart_saving_logs")
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "All data has been reset."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    try:
        data = request.json
        type_ = data['type']
        amount = float(data['amount'])
        category = data['category']
        date_str = data['date']
        description = data['description']
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO transactions (type, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
                  (type_, amount, category, date_str, description))
        
        nudge = None
        if type_ == 'expense':
            # Check budget limit
            c.execute("SELECT amount FROM budgets WHERE category=?", (category,))
            budget_row = c.fetchone()
            if budget_row and budget_row[0] > 0:
                limit = budget_row[0]
                current_month = datetime.now().strftime('%Y-%m')
                c.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='expense' AND category=? AND date LIKE ?", (category, current_month + '%'))
                total_spent = c.fetchone()[0]
                
                if total_spent > limit:
                    nudge = f"Warning: You have exceeded the budget for {category}!"
                elif total_spent > 0.8 * limit:
                    nudge = f"Note: You have used more than 80% of your {category} budget."
        
        conn.commit()
        conn.close()
        return jsonify({"success": True, "nudge": nudge})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/get_spending')
def get_spending():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    current_month = datetime.now().strftime('%Y-%m')
    c.execute("SELECT category, COALESCE(SUM(amount), 0) FROM transactions WHERE type='expense' AND date LIKE ? GROUP BY category", (current_month + '%',))
    spending = dict(c.fetchall())
    conn.close()
    return jsonify(spending)

@app.route('/api/total_budget', methods=['GET', 'POST'])
def api_total_budget():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if request.method == 'POST':
        data = request.json
        new_amount = float(data.get('amount', 0))
        c.execute("INSERT OR REPLACE INTO budgets (category, amount) VALUES ('TOTAL_BUDGET', ?)", (new_amount,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    else:
        c.execute("SELECT amount FROM budgets WHERE category='TOTAL_BUDGET'")
        row = c.fetchone()
        total_budget = float(row[0]) if row else 0
        conn.close()
        return jsonify({'total_budget': total_budget})

@app.route('/api/budgets', methods=['GET', 'POST'])
def api_budgets():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if request.method == 'POST':
        data = request.json
        category = data.get('category')
        amount = data.get('amount')
        if category and amount is not None:
            c.execute("INSERT OR REPLACE INTO budgets (category, amount) VALUES (?, ?)", (category, amount))
            conn.commit()
        conn.close()
        return jsonify({'success': True})
    else:
        c.execute("SELECT category, amount FROM budgets")
        budgets = dict(c.fetchall())
        conn.close()
        return jsonify(budgets)

@app.route('/api/summary')
def api_summary():
    """Unified summary endpoint for dashboard and other pages."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    current_month = datetime.now().strftime('%Y-%m')

    # All-time balance
    c.execute("SELECT COALESCE(SUM(CASE WHEN type='income' THEN amount ELSE -amount END), 0) FROM transactions")
    balance = c.fetchone()[0]

    # Current month income
    c.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='income' AND date LIKE ?", (current_month + '%',))
    monthly_income = c.fetchone()[0]

    # Current month expenses
    c.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='expense' AND date LIKE ?", (current_month + '%',))
    monthly_expense = c.fetchone()[0]

    # Monthly net savings
    monthly_savings = monthly_income - monthly_expense

    # Saving rate
    saving_rate = round((monthly_savings / monthly_income * 100), 1) if monthly_income > 0 else 0

    # Spending by category this month
    c.execute("SELECT category, SUM(amount) FROM transactions WHERE type='expense' AND date LIKE ? GROUP BY category ORDER BY SUM(amount) DESC", (current_month + '%',))
    spending_by_category = [{'category': r[0], 'amount': r[1]} for r in c.fetchall()]

    # Top spending category
    top_category = spending_by_category[0]['category'] if spending_by_category else None

    # Last 5 transactions
    c.execute("SELECT id, type, amount, category, date, description FROM transactions ORDER BY date DESC, id DESC LIMIT 5")
    recent = [{'id': r[0], 'type': r[1], 'amount': r[2], 'category': r[3], 'date': r[4], 'desc': r[5] or ''} for r in c.fetchall()]

    conn.close()
    return jsonify({
        'balance': balance,
        'monthly_income': monthly_income,
        'monthly_expense': monthly_expense,
        'monthly_savings': monthly_savings,
        'saving_rate': saving_rate,
        'spending_by_category': spending_by_category,
        'top_category': top_category,
        'recent_transactions': recent,
        'current_month': current_month
    })

@app.route('/get_transactions')
def get_transactions():
    date = request.args.get('date')
    month = request.args.get('month')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    if month:
        c.execute("SELECT id, type, amount, category, date, description FROM transactions WHERE date LIKE ? ORDER BY date DESC", (month + '%',))
    else:
        # Default to today if neither date nor month provided
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        c.execute("SELECT id, type, amount, category, date, description FROM transactions WHERE date=? ORDER BY id DESC", (date,))
    
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

# ==================== Smart Saving API ====================

def calculate_required_daily_savings(target_price, current_savings, deadline_date_str):
    """Calculate required daily savings to reach goal by deadline."""
    try:
        deadline = datetime.strptime(deadline_date_str, '%Y-%m-%d').date()
        today = date.today()
        remaining_days = (deadline - today).days
        if remaining_days <= 0:
            return 0, 0
        amount_needed = max(0, target_price - current_savings)
        required_daily = amount_needed / remaining_days
        return required_daily, remaining_days
    except Exception:
        return 0, 0

@app.route('/update_total_budget', methods=['POST'])
def update_total_budget():
    try:
        # Handle both JSON and Form data
        if request.is_json:
            data = request.json
        else:
            data = request.form
            
        amount = float(data.get('amount', 0))
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO budgets (category, amount) VALUES ('TOTAL_BUDGET', ?)", (amount,))
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('total_budget', ?)", (str(amount),))
        conn.commit()
        conn.close()
        
        if request.is_json:
            return jsonify({'success': True})
        return redirect(url_for('budget_planning'))
    except Exception as e:
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        return f"Error: {str(e)}", 500

@app.route('/add_category', methods=['POST'])
def add_category():
    try:
        if request.is_json:
            data = request.json
        else:
            data = request.form
            
        name = data.get('category_name')
        percentage = float(data.get('percentage', 0))
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO budgets (category, amount) VALUES (?, ?)", (name, percentage))
        conn.commit()
        conn.close()
        
        if request.is_json:
            return jsonify({'success': True})
        return redirect(url_for('budget_planning'))
    except Exception as e:
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        return f"Error: {str(e)}", 500

@app.route('/add_saving_goal', methods=['POST'])
def add_saving_goal():
    try:
        if request.is_json:
            data = request.json
        else:
            data = request.form
            
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        created_date = datetime.now().strftime('%Y-%m-%d')
        
        # Mapping form names to db columns
        item_name = data.get('item_name')
        target_amount = float(data.get('target_amount', 0))
        current_amount = float(data.get('current_amount', 0))
        target_date = data.get('target_date')
        notes = data.get('notes', '')
        
        c.execute(
            "INSERT INTO saving_goals (item_name, target_amount, current_amount, target_date, created_date, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (item_name, target_amount, current_amount, target_date, created_date, notes)
        )
        conn.commit()
        conn.close()
        
        if request.is_json:
            return jsonify({'success': True})
        return redirect(url_for('smart_saving'))
    except Exception as e:
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        return f"Error: {str(e)}", 500

@app.route('/api/smart_goals', methods=['GET', 'POST'])
def smart_goals():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        if request.method == 'POST':
            data = request.json
            if not data:
                return jsonify({'success': False, 'error': 'No data provided'}), 400
            
            created_date = date.today().isoformat()
            c.execute(
                "INSERT INTO saving_goals (item_name, target_amount, current_amount, target_date, created_date, notes) VALUES (?, ?, ?, ?, ?, ?)",
                (data.get('item_name', 'Unnamed'), 
                 float(data.get('target_amount', 0)), 
                 float(data.get('current_amount', 0)),
                 data.get('target_date', date.today().isoformat()), 
                 created_date, 
                 data.get('notes', ''))
            )
            conn.commit()
            goal_id = c.lastrowid
            return jsonify({'success': True, 'id': goal_id})
        else:
            c.execute("SELECT id, item_name, target_amount, current_amount, target_date, created_date, notes FROM saving_goals ORDER BY id DESC")
            rows = c.fetchall()
            goals = []
            for row in rows:
                required_daily, remaining_days = calculate_required_daily_savings(row[2], row[3], row[4])
                progress = (row[3] / row[2] * 100) if row[2] > 0 else 0
                goals.append({
                    'id': row[0],
                    'item_name': row[1],
                    'target_amount': row[2],
                    'current_amount': row[3],
                    'target_date': row[4],
                    'created_date': row[5],
                    'notes': row[6],
                    'required_daily': round(required_daily, 0),
                    'remaining_days': remaining_days,
                    'progress_pct': round(progress, 1)
                })
            return jsonify(goals)
    except Exception as e:
        print(f"Error in /api/smart_goals: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/smart_goals/<int:goal_id>', methods=['GET', 'DELETE', 'PATCH'])
def manage_smart_goal(goal_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if request.method == 'DELETE':
        c.execute("DELETE FROM saving_goals WHERE id=?", (goal_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    elif request.method == 'PATCH':
        data = request.json
        if 'add_amount' in data:
            c.execute("UPDATE saving_goals SET current_amount = current_amount + ? WHERE id=?", (float(data['add_amount']), goal_id))
            conn.commit()
        conn.close()
        return jsonify({'success': True})
    else:
        c.execute("SELECT * FROM saving_goals WHERE id=?", (goal_id,))
        goal = c.fetchone()
        conn.close()
        return jsonify(goal)

@app.route('/api/smart_saving_stats')
def smart_saving_stats():
    """Returns today's spending, monthly avg income, and active goal calculations."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        today_str = date.today().isoformat()
        current_month = datetime.now().strftime('%Y-%m')

        # Today's spending
        c.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='expense' AND date=?", (today_str,))
        today_spending = c.fetchone()[0]

        # Today's income
        c.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='income' AND date=?", (today_str,))
        today_income = c.fetchone()[0]

        # Monthly avg daily income (current month)
        c.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='income' AND date LIKE ?", (current_month + '%',))
        monthly_income = c.fetchone()[0]
        days_in_month = datetime.now().day
        avg_daily_income = monthly_income / days_in_month if days_in_month > 0 else 0

        # All active goals with computed fields
        c.execute("SELECT id, item_name, target_amount, current_amount, target_date FROM saving_goals ORDER BY id DESC")
        rows = c.fetchall()
        
        goals = []
        for row in rows:
            required_daily, remaining_days = calculate_required_daily_savings(row[2], row[3], row[4])
            # Logika Status: Jika (Net Income Hari Ini) < Target Tabungan Harian, maka At Risk/Boros
            # Net Income hari ini = today_income - today_spending
            net_income = today_income - today_spending
            at_risk = net_income < required_daily
            
            safe_to_spend = max(0, avg_daily_income - required_daily)
            extra_needed = 0
            if at_risk and remaining_days > 1:
                # Selisih yang harus ditutupi
                deficit = required_daily - net_income
                extra_needed = deficit / (remaining_days - 1)
                
            goals.append({
                'id': row[0],
                'item_name': row[1],
                'target_amount': row[2],
                'current_amount': row[3],
                'target_date': row[4],
                'required_daily': round(required_daily, 0),
                'remaining_days': remaining_days,
                'progress_pct': round((row[3] / row[2] * 100) if row[2] > 0 else 0, 1),
                'safe_to_spend': round(safe_to_spend, 0),
                'at_risk': at_risk,
                'extra_needed': round(extra_needed, 0)
            })

        return jsonify({
            'today_spending': today_spending,
            'today_income': today_income,
            'avg_daily_income': round(avg_daily_income, 0),
            'goals': goals
        })
    except Exception as e:
        print(f"Error in /api/smart_saving_stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/smart_saving_logs/<int:goal_id>')
def smart_saving_logs(goal_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT log_date, amount_saved, daily_spending FROM smart_saving_logs WHERE goal_id=? ORDER BY log_date DESC LIMIT 30", (goal_id,))
    rows = c.fetchall()
    conn.close()
    return jsonify([{'date': r[0], 'saved': r[1], 'spent': r[2]} for r in rows])



@app.route('/api/saving_goals', methods=['GET', 'POST'])
def saving_goals():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if request.method == 'POST':
        data = request.json
        # Only use existing columns: item_name, target_amount, current_amount, target_date
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

# ==================== Gemini AI Chat API ====================
@app.route('/api/chat', methods=['POST'])
def chat():
    """AI Financial Advisor endpoint using Google Gemini (Primary API)"""
    try:
        if not HAS_GEMINI:
            return jsonify({"success": False, "error": "Gemini library not installed"}), 500
            
        data = request.json
        messages = data.get('messages', [])
        
        # Get financial context from database
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # 1. Total Balance
        c.execute("SELECT COALESCE(SUM(CASE WHEN type='income' THEN amount ELSE -amount END), 0) FROM transactions")
        balance = c.fetchone()[0]
        
        # 2. Monthly Stats
        current_month = datetime.now().strftime('%Y-%m')
        c.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='income' AND date LIKE ?", (current_month + '%',))
        monthly_income = c.fetchone()[0]
        
        c.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='expense' AND date LIKE ?", (current_month + '%',))
        monthly_expense = c.fetchone()[0]
        
        # 3. Category Breakdown
        c.execute("SELECT category, SUM(amount) FROM transactions WHERE type='expense' AND date LIKE ? GROUP BY category", (current_month + '%',))
        categories = c.fetchall()
        category_info = ", ".join([f"{cat}: Rp {amt:,.0f}" for cat, amt in categories])
        
        # 4. Saving Goals
        c.execute("SELECT item_name, target_amount, current_amount FROM saving_goals")
        goals = c.fetchall()
        goals_info = ", ".join([f"{name} (Target: Rp {target:,.0f}, Terkumpul: Rp {current:,.0f})" for name, target, current in goals])
        
        conn.close()
        
        # Construct Expert System Instruction
        system_instruction = f"""Kamu adalah Dompetin AI, asisten perencana keuangan yang cerdas dan tegas.

KONTEKS DATA USER (DATABASE):
- Saldo Saat Ini: Rp {balance:,.0f}
- Pemasukan Bulan Ini: Rp {monthly_income:,.0f}
- Pengeluaran Bulan Ini: Rp {monthly_expense:,.0f}
- Rincian Pengeluaran Kategori: {category_info if category_info else 'Belum ada pengeluaran'}
- Tujuan Tabungan: {goals_info if goals_info else 'Belum ada tujuan tabungan'}

ATURAN KETAT:
1. Jawablah dengan sangat singkat dan langsung ke intinya (maksimal 2-3 kalimat santai).
2. JANGAN PERNAH mengarang angka. HANYA berikan saran berdasarkan data user di atas. Jika data tidak ada, katakan data belum tersedia.
3. Jika user hanya menyapa (seperti 'hi', 'halo', 'p', atau salam), balaslah dengan singkat: 'Halo! Ada data pengeluaran atau budget yang ingin kita evaluasi hari ini?'
4. Gunakan Bahasa Indonesia yang santai tapi tegas.
5. Gunakan maksimal 1 emoji per jawaban."""

        # Configure Gemini Model with System Instruction
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_instruction
        )
        
        # Map history for Gemini (user/model)
        history = []
        if len(messages) > 1:
            for m in messages[:-1]:
                # Map role: 'assistant' to 'model' for Gemini
                role = "user" if m['role'] == "user" else "model"
                content = m.get('content', '')
                if content:
                    history.append({"role": role, "parts": [content]})
            
        chat_session = model.start_chat(history=history)
        
        # Send the latest user message
        last_message = messages[-1]['content'] if messages else "Halo"
        response = chat_session.send_message(last_message)
        
        # Robust text extraction
        ai_text = ""
        try:
            ai_text = response.text
        except Exception:
            if response.candidates:
                ai_text = response.candidates[0].content.parts[0].text
        
        if not ai_text:
            ai_text = "Maaf, saya tidak bisa memberikan jawaban saat ini."

        return jsonify({
            "success": True,
            "response": ai_text
        })
        
    except Exception as e:
        print(f"Gemini AI Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
