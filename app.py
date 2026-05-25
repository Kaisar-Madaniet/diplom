from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime
import os
from io import BytesIO, StringIO
import csv

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ==========================================
# SUPABASE ДЕРЕКҚОРЫНА ҚОСЫЛУ СІЛТЕМЕСІ
# [YOUR-PASSWORD] орнына өз пароліңізді жазыңыз!
# ==========================================
DATABASE_URL = "postgresql://postgres:[7uzeJsKDvPfDqxtg]@db.lnlcftcmdnheylcorrmc.supabase.co:5432/postgres"

def get_db_connection():
    # PostgreSQL-ге қосылу
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)
    return conn

def add_demo_data(user_id, conn, cursor):
    cursor.execute('SELECT id FROM accounts WHERE user_id = %s', (user_id,))
    acc_row = cursor.fetchone()
    if not acc_row: return
    acc_id = acc_row[0]
    
    demo_records = [
        ('2026-05-02', 'Тамақ және Азық-түлік', 12000, 'expense'), ('2026-05-04', 'Көлік және Авто', 3000, 'expense'),
        ('2026-05-07', 'Жалақы', 150000, 'income'), ('2026-05-10', 'Ойын-сауық', 7000, 'expense'),
        ('2026-05-12', 'Байланыс және Интернет', 4000, 'expense'), ('2026-05-15', 'Денсаулық және Дәріхана', 5500, 'expense'),
        ('2026-05-18', 'Тамақ және Азық-түлік', 18000, 'expense'), ('2026-05-22', 'Аударымдар', 25000, 'income'),
        ('2026-05-25', 'Спорт', 10000, 'expense'), ('2026-05-28', 'Тамақ және Азық-түлік', 6000, 'expense'),
        ('2026-04-01', 'Жалақы', 150000, 'income'), ('2026-04-03', 'Тұрғын үй және ТҮКШ', 45000, 'expense'),
        ('2026-04-06', 'Тамақ және Азық-түлік', 14000, 'expense'), ('2026-04-09', 'Киім және Аяқ киім', 25000, 'expense'),
        ('2026-04-12', 'Көлік және Авто', 4500, 'expense'), ('2026-04-15', 'Ойын-сауық', 12000, 'expense'),
        ('2026-04-18', 'Қосымша табыс', 30000, 'income'), ('2026-04-21', 'Тамақ және Азық-түлік', 9000, 'expense'),
        ('2026-04-24', 'Денсаулық және Дәріхана', 3000, 'expense'), ('2026-04-27', 'Байланыс және Интернет', 3500, 'expense'),
        ('2026-03-02', 'Жалақы', 150000, 'income'), ('2026-03-05', 'Тамақ және Азық-түлік', 16000, 'expense'),
        ('2026-03-08', 'Сыйлықтар', 20000, 'expense'), ('2026-03-11', 'Көлік және Авто', 5500, 'expense'),
        ('2026-03-14', 'Тамақ және Азық-түлік', 11000, 'expense'), ('2026-03-17', 'Ойын-сауық', 9000, 'expense'),
        ('2026-03-20', 'Инвестициялар', 50000, 'income'), ('2026-03-23', 'Байланыс және Интернет', 4000, 'expense'),
        ('2026-03-26', 'Денсаулық және Дәріхана', 6000, 'expense'), ('2026-03-29', 'Тамақ және Азық-түлік', 7500, 'expense')
    ]
    for date, cat, amt, t_type in demo_records:
        cursor.execute('INSERT INTO transactions (user_id, account_id, date, category, amount, type, description) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                       (user_id, acc_id, date, cat, amt, t_type, 'Автоматты жазба'))

def add_default_categories(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cats = [
        (user_id, 'Тамақ және Азық-түлік', 'expense'), (user_id, 'Көлік және Авто', 'expense'),
        (user_id, 'Тұрғын үй және ТҮКШ', 'expense'), (user_id, 'Ойын-сауық', 'expense'),
        (user_id, 'Денсаулық және Дәріхана', 'expense'), (user_id, 'Байланыс және Интернет', 'expense'),
        (user_id, 'Киім және Аяқ киім', 'expense'), (user_id, 'Кафе және Мейрамханалар', 'expense'),
        (user_id, 'Білім беру', 'expense'), (user_id, 'Үй жануарлары', 'expense'),
        (user_id, 'Спорт', 'expense'), (user_id, 'Сыйлықтар', 'expense'),
        (user_id, 'Жалақы', 'income'), (user_id, 'Аударымдар', 'income'),
        (user_id, 'Қосымша табыс', 'income'), (user_id, 'Инвестициялар', 'income'),
        (user_id, 'Кэшбэк және Бонустар', 'income')
    ]
    cursor.executemany('INSERT INTO categories (user_id, name, type) VALUES (%s, %s, %s)', cats)
    cursor.execute('INSERT INTO accounts (user_id, name) VALUES (%s, %s)', (user_id, 'Негізгі шот'))
    conn.commit()
    cursor.close()
    conn.close()

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # PostgreSQL үшін SERIAL PRIMARY KEY қолданылады
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username TEXT UNIQUE NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS categories (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL, name TEXT NOT NULL, type TEXT NOT NULL, FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL, name TEXT NOT NULL, FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL, account_id INTEGER NOT NULL DEFAULT 0, date TEXT NOT NULL, category TEXT NOT NULL, amount REAL NOT NULL, type TEXT NOT NULL, description TEXT, FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE)''')
    
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        demo_pass = generate_password_hash('demo')
        # Жаңа қолданушының ID-сін қайтарып алу үшін RETURNING id қолданамыз
        cursor.execute('INSERT INTO users (username, email, password) VALUES (%s, %s, %s) RETURNING id', ('demo', 'demo@mail.ru', demo_pass))
        user_id = cursor.fetchone()[0]
        
        cats = [
            (user_id, 'Тамақ және Азық-түлік', 'expense'), (user_id, 'Көлік және Авто', 'expense'),
            (user_id, 'Тұрғын үй және ТҮКШ', 'expense'), (user_id, 'Ойын-сауық', 'expense'),
            (user_id, 'Денсаулық және Дәріхана', 'expense'), (user_id, 'Байланыс және Интернет', 'expense'),
            (user_id, 'Киім және Аяқ киім', 'expense'), (user_id, 'Кафе және Мейрамханалар', 'expense'),
            (user_id, 'Білім беру', 'expense'), (user_id, 'Үй жануарлары', 'expense'),
            (user_id, 'Спорт', 'expense'), (user_id, 'Сыйлықтар', 'expense'),
            (user_id, 'Жалақы', 'income'), (user_id, 'Аударымдар', 'income'),
            (user_id, 'Қосымша табыс', 'income'), (user_id, 'Инвестициялар', 'income'),
            (user_id, 'Кэшбэк және Бонустар', 'income')
        ]
        cursor.executemany('INSERT INTO categories (user_id, name, type) VALUES (%s, %s, %s)', cats)
        cursor.execute('INSERT INTO accounts (user_id, name) VALUES (%s, %s)', (user_id, 'Негізгі шот'))
        conn.commit()
        
        add_demo_data(user_id, conn, cursor)
        conn.commit()
        
    cursor.close()
    conn.close()

@app.context_processor
def inject_data():
    if 'user_id' in session:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts WHERE user_id = %s', (session['user_id'],))
        accs = cursor.fetchall()
        cursor.close()
        conn.close()
        return {'user_accounts': accs, 'active_account': str(session.get('active_account', 'all'))}
    return {}

@app.route('/set_account', methods=['POST'])
def set_account():
    session['active_account'] = request.form.get('account_id', 'all')
    return redirect(request.referrer or url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_val, password = request.form['login'], request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s OR email = %s', (login_val, login_val))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'], session['username'], session['active_account'] = user['id'], user['username'], 'all'
            return redirect(url_for('index'))
        flash('Қате логин немесе құпиясөз', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username, email, password = request.form['username'], request.form['email'], request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, email, password) VALUES (%s, %s, %s) RETURNING id', (username, email, generate_password_hash(password)))
            user_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            add_default_categories(user_id)
            flash('Тіркелу сәтті аяқталды!', 'success')
            return redirect(url_for('login'))
        except psycopg2.IntegrityError:
            conn.rollback()
            flash('Логин немесе Email бос емес.', 'danger')
        finally:
            if not conn.closed: conn.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.before_request
def require_login():
    allowed = ['login', 'register', 'static']
    if request.endpoint not in allowed and 'user_id' not in session: return redirect(url_for('login'))

def get_filtered_transactions(user_id, date_from, date_to, t_type='all', categories_str='all', acc_id=None):
    if acc_id is None: acc_id = session.get('active_account', 'all')
    if categories_str == 'none': return [] 
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT t.*, coalesce(a.name, 'Өшірілген шот') as acc_name FROM transactions t LEFT JOIN accounts a ON t.account_id = a.id WHERE t.user_id = %s"
    params = [user_id]
    
    if str(acc_id) != 'all':
        query += " AND t.account_id = %s"
        params.append(int(acc_id))
        
    if t_type != 'all': query += " AND t.type = %s"; params.append(t_type)
    if categories_str and categories_str != 'all':
        cats = categories_str.split(',')
        placeholders = ','.join(['%s'] * len(cats))
        query += f" AND t.category IN ({placeholders})"
        params.extend(cats)
    if date_from: query += " AND t.date >= %s"; params.append(date_from)
    if date_to: query += " AND t.date <= %s"; params.append(date_to)
    query += " ORDER BY t.date DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

@app.route('/')
def index():
    user_id = session['user_id']
    rows = get_filtered_transactions(user_id, '', '', 'all', 'all')
    clean_rows = []
    for r in rows:
        d = dict(r)
        d['amount'] = int(d['amount']) if float(d['amount']).is_integer() else d['amount']
        clean_rows.append(d)

    income = sum(r['amount'] for r in clean_rows if r['type'] == 'income')
    expense = sum(r['amount'] for r in clean_rows if r['type'] == 'expense')
    income = int(income) if float(income).is_integer() else round(income, 2)
    expense = int(expense) if float(expense).is_integer() else round(expense, 2)
    balance = income - expense
    balance = int(balance) if float(balance).is_integer() else round(balance, 2)
    
    grouped = {}
    for t in clean_rows: grouped.setdefault(t['date'], []).append(t)
    
    formatted = []
    for d, items in grouped.items():
        try:
            formatted_date = datetime.strptime(d, '%Y-%m-%d').strftime('%d.%m.%Y')
        except ValueError:
            formatted_date = d if d else "Күні жоқ"
            
        day_exp = sum(i['amount'] for i in items if i['type'] == 'expense')
        day_inc = sum(i['amount'] for i in items if i['type'] == 'income')
        day_exp = int(day_exp) if float(day_exp).is_integer() else round(day_exp, 2)
        day_inc = int(day_inc) if float(day_inc).is_integer() else round(day_inc, 2)
        day_bal = int(day_inc - day_exp) if float(day_inc - day_exp).is_integer() else round(day_inc - day_exp, 2)
        formatted.append({'date_str': formatted_date, 'raw_date': d, 'day_expense': day_exp, 'day_income': day_inc, 'day_balance': day_bal, 'items': items})
        
    return render_template('index.html', grouped_transactions=formatted, income=income, expense=expense, balance=balance)

@app.route('/analytics')
def analytics(): return render_template('analytics.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_cat':
            cursor.execute('INSERT INTO categories (user_id, name, type) VALUES (%s, %s, %s)', (user_id, request.form['name'], request.form['type']))
            flash('Санат қосылды', 'success')
        elif action == 'add_acc':
            cursor.execute('INSERT INTO accounts (user_id, name) VALUES (%s, %s)', (user_id, request.form['name']))
            flash('Шот қосылды', 'success')
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('settings'))
        
    cursor.execute('SELECT COUNT(*) FROM categories WHERE user_id = %s', (user_id,))
    if cursor.fetchone()[0] == 0:
        cursor.close()
        conn.close()
        add_default_categories(user_id)
        conn = get_db_connection()
        cursor = conn.cursor()
        
    cursor.execute('SELECT * FROM categories WHERE user_id = %s ORDER BY type, name', (user_id,))
    cats = cursor.fetchall()
    cursor.close()
    conn.close()
    
    expense_cats = [c for c in cats if c['type'] == 'expense']
    income_cats = [c for c in cats if c['type'] == 'income']
    return render_template('settings.html', expense_cats=expense_cats, income_cats=income_cats)

@app.route('/edit_category/<int:id>', methods=['POST'])
def edit_category(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    new_name = request.form['name']
    cursor.execute('SELECT name FROM categories WHERE id = %s AND user_id = %s', (id, session['user_id']))
    old_cat = cursor.fetchone()
    if old_cat:
        old_name = old_cat['name']
        cursor.execute('UPDATE categories SET name = %s WHERE id = %s AND user_id = %s', (new_name, id, session['user_id']))
        cursor.execute('UPDATE transactions SET category = %s WHERE category = %s AND user_id = %s', (new_name, old_name, session['user_id']))
        conn.commit()
        flash('Санат атауы өзгертілді', 'success')
    cursor.close()
    conn.close()
    return redirect(url_for('settings'))

@app.route('/edit_account/<int:id>', methods=['POST'])
def edit_account(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    new_name = request.form['name']
    cursor.execute('UPDATE accounts SET name = %s WHERE id = %s AND user_id = %s', (new_name, id, session['user_id']))
    conn.commit()
    flash('Шот атауы өзгертілді', 'success')
    cursor.close()
    conn.close()
    return redirect(url_for('settings'))

@app.route('/delete_account/<int:id>')
def delete_account(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM accounts WHERE id = %s AND user_id = %s', (id, session['user_id']))
    cursor.execute('UPDATE transactions SET account_id = 0 WHERE account_id = %s AND user_id = %s', (id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    if session.get('active_account') == str(id): session['active_account'] = 'all'
    flash('Шот өшірілді', 'success')
    return redirect(url_for('settings'))

@app.route('/add', methods=['POST'])
def add_transaction():
    conn = get_db_connection()
    cursor = conn.cursor()
    acc_id = request.form.get('account_id', 0)
    cursor.execute('INSERT INTO transactions (user_id, account_id, type, category, amount, date) VALUES (%s, %s, %s, %s, %s, %s)', 
                   (session['user_id'], acc_id, request.form['type'], request.form['category'], float(request.form['amount']), request.form['date']))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['POST'])
def edit_transaction(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    acc_id = request.form.get('account_id', 0)
    cursor.execute('UPDATE transactions SET account_id=%s, type=%s, category=%s, amount=%s, date=%s WHERE id=%s AND user_id=%s', 
                   (acc_id, request.form['type'], request.form['category'], float(request.form['amount']), request.form['date'], id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transactions WHERE id = %s AND user_id = %s', (id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete_category/<int:id>')
def delete_category(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM categories WHERE id = %s AND user_id = %s', (id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('settings'))

@app.route('/api/categories')
def get_categories():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM categories WHERE user_id = %s AND type = %s ORDER BY name', (user_id, request.args.get('type', 'expense')))
    cats = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify([c['name'] for c in cats])

@app.route('/api/stats')
def stats():
    user_id = session['user_id']
    date_from, date_to = request.args.get('date_from', ''), request.args.get('date_to', '')
    t_type, categories_str = request.args.get('type', 'expense'), request.args.get('category', 'all')
    acc_id = request.args.get('account_id', session.get('active_account', 'all'))
    
    all_rows = get_filtered_transactions(user_id, date_from, date_to, 'all', 'all', acc_id)
    total_income = sum(r['amount'] for r in all_rows if r['type'] == 'income')
    total_expense = sum(r['amount'] for r in all_rows if r['type'] == 'expense')
    total_income = int(total_income) if float(total_income).is_integer() else round(total_income, 2)
    total_expense = int(total_expense) if float(total_expense).is_integer() else round(total_expense, 2)
    balance = int(total_income - total_expense) if float(total_income - total_expense).is_integer() else round(total_income - total_expense, 2)
    
    tab_rows = get_filtered_transactions(user_id, date_from, date_to, t_type, categories_str, acc_id)
    cat_sums = {}
    for r in tab_rows: cat_sums[r['category']] = cat_sums.get(r['category'], 0) + r['amount']
    total_tab = sum(cat_sums.values())
    total_tab = int(total_tab) if float(total_tab).is_integer() else round(total_tab, 2)
    
    sorted_cats = sorted(cat_sums.items(), key=lambda x: x[1], reverse=True)
    details = [{"category": c[0], "amount": int(c[1]) if float(c[1]).is_integer() else round(c[1], 2), "percent": int(round((c[1]/total_tab*100) if total_tab>0 else 0, 2)) if float(round((c[1]/total_tab*100) if total_tab>0 else 0, 2)).is_integer() else round((c[1]/total_tab*100) if total_tab>0 else 0, 2)} for c in sorted_cats]
    
    return jsonify({"grand_income": total_income, "grand_expense": total_expense, "grand_balance": balance, "labels": [c[0] for c in sorted_cats], "values": [c[1] for c in sorted_cats], "total": total_tab, "details": details})

@app.route('/api/trend')
def trend():
    user_id = session['user_id']
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    categories_str = request.args.get('category', 'all')
    t_type = request.args.get('type', 'expense')
    account_id = request.args.get('account_id', session.get('active_account', 'all'))
    
    if categories_str == 'none': return jsonify({'labels': [], 'datasets': []})
        
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT date, category, SUM(amount) as total FROM transactions WHERE user_id = %s AND type = %s"
    params = [user_id, t_type]
    
    if str(account_id) != 'all': query += " AND account_id = %s"; params.append(int(account_id))
    if date_from: query += " AND date >= %s"; params.append(date_from)
    if date_to: query += " AND date <= %s"; params.append(date_to)
    
    cats_list = []
    if categories_str != 'all':
        cats_list = categories_str.split(',')
        placeholders = ','.join(['%s'] * len(cats_list))
        query += f" AND category IN ({placeholders})"
        params.extend(cats_list)
        
    query += " GROUP BY date, category ORDER BY date ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    if categories_str == 'all':
        cats_list = list(set([r['category'] for r in rows]))
        
    unique_dates = sorted(list(set([r['date'] for r in rows])))
    datasets_dict = {c: [0]*len(unique_dates) for c in cats_list}
    
    for r in rows:
        d_idx = unique_dates.index(r['date'])
        if r['category'] in datasets_dict:
            datasets_dict[r['category']][d_idx] = r['total']
            
    labels_fmt = []
    for d in unique_dates:
        try:
            labels_fmt.append(datetime.strptime(d, '%Y-%m-%d').strftime('%d.%m'))
        except ValueError:
            labels_fmt.append(d if d else "Күні жоқ")
    
    datasets = []
    colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#14b8a6', '#6366f1']
    for i, c in enumerate(cats_list):
        datasets.append({
            'label': c,
            'data': datasets_dict[c],
            'borderColor': colors[i % len(colors)],
            'backgroundColor': colors[i % len(colors)] + '33',
            'fill': False,
            'tension': 0.4,
            'borderWidth': 3
        })
        
    cursor.close()
    conn.close()
    return jsonify({'labels': labels_fmt, 'datasets': datasets})

def format_kz_date(d_str):
    if not d_str: return ""
    try: return datetime.strptime(d_str, '%Y-%m-%d').strftime('%d.%m.%Y')
    except: return d_str

@app.route('/export/excel')
def export_excel():
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    acc_id = request.args.get('account_id', session.get('active_account', 'all'))
    t_type = request.args.get('type', 'all')
    category = request.args.get('category', 'all')
    calc_mode = request.args.get('calc_mode', 'exact')
    
    rows = get_filtered_transactions(session['user_id'], date_from, date_to, t_type, category, acc_id)
    
    si = StringIO()
    cw = csv.writer(si, delimiter=';')
    cw.writerow(['Күні / Кезең', 'Шот', 'Операция түрі', 'Санат', 'Сома (ТГ)'])
    
    total_sum = 0
    if calc_mode == 'summary':
        summary = {}
        for r in rows:
            cat = r['category']
            if cat not in summary: summary[cat] = {'type': r['type'], 'amount': 0}
            summary[cat]['amount'] += r['amount']
            total_sum += r['amount']
            
        df_fmt = format_kz_date(date_from)
        dt_fmt = format_kz_date(date_to)
        if df_fmt and dt_fmt: date_label = f"{df_fmt} - {dt_fmt}"
        elif df_fmt: date_label = f"{df_fmt} бастап"
        elif dt_fmt: date_label = f"{dt_fmt} дейін"
        else: date_label = "Барлық уақыт"
        
        for cat, data in summary.items():
            amt = int(data['amount']) if float(data['amount']).is_integer() else data['amount']
            cw.writerow([date_label, 'Таңдалған шоттар', 'Кіріс' if data['type']=='income' else 'Шығыс', cat, amt])
    else:
        for r in rows: 
            dt_str = format_kz_date(r['date']) if r['date'] else "Күні жоқ"
            amt = int(r['amount']) if float(r['amount']).is_integer() else r['amount']
            total_sum += amt
            cw.writerow([dt_str, r['acc_name'], 'Кіріс' if r['type']=='income' else 'Шығыс', r['category'], amt])
            
    cw.writerow(['', '', '', 'ЖАЛПЫ СОМА (ИТОГО):', total_sum])
    output = BytesIO()
    output.write(si.getvalue().encode('utf-8-sig'))
    output.seek(0)
    return send_file(output, download_name="Finance_Report.csv", as_attachment=True, mimetype="text/csv")

@app.route('/export/word')
def export_word():
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    acc_id = request.args.get('account_id', session.get('active_account', 'all'))
    t_type = request.args.get('type', 'all')
    category = request.args.get('category', 'all')
    calc_mode = request.args.get('calc_mode', 'exact')
    
    rows = get_filtered_transactions(session['user_id'], date_from, date_to, t_type, category, acc_id)
    
    html = f"<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'><head><meta charset='utf-8'><style>body {{ font-family: 'Times New Roman', Times, serif; font-size: 14pt; color: windowtext; }} h2 {{ text-align: center; font-size: 16pt; font-weight: bold; margin-bottom: 10px; }} .period {{ text-align: center; font-size: 12pt; margin-bottom: 20px; }} table {{ border-collapse: collapse; width: 100%; border: 1pt solid windowtext; }} th, td {{ border: 1pt solid windowtext; padding: 6pt; vertical-align: middle; }} th {{ background-color: #f2f2f2; font-weight: bold; text-align: center; }} .center {{ text-align: center; }} .right {{ text-align: right; font-weight: bold; }}</style></head><body><h2>Қаржылық есеп</h2><div class='period'>Кезең: {format_kz_date(date_from) or 'Басы'} — {format_kz_date(date_to) or 'Соңы'}</div><table><tr><th>Күні / Кезең</th><th>Шот</th><th>Түрі</th><th>Санат</th><th>Сома (ТГ)</th></tr>"
    
    total_sum = 0
    if calc_mode == 'summary':
        summary = {}
        for r in rows:
            cat = r['category']
            if cat not in summary: summary[cat] = {'type': r['type'], 'amount': 0}
            summary[cat]['amount'] += r['amount']
            total_sum += r['amount']
            
        df_fmt = format_kz_date(date_from)
        dt_fmt = format_kz_date(date_to)
        if df_fmt and dt_fmt: date_label = f"{df_fmt} - {dt_fmt}"
        elif df_fmt: date_label = f"{df_fmt} бастап"
        elif dt_fmt: date_label = f"{dt_fmt} дейін"
        else: date_label = "Барлық уақыт"
            
        for cat, data in summary.items():
            amt = int(data['amount']) if float(data['amount']).is_integer() else data['amount']
            t_str = 'Кіріс' if data['type']=='income' else 'Шығыс'
            html += f"<tr><td class='center'>{date_label}</td><td class='center'>Таңдалған шоттар</td><td class='center'>{t_str}</td><td>{cat}</td><td class='right'>{amt}</td></tr>"
    else:
        for r in rows: 
            dt_str = format_kz_date(r['date']) if r['date'] else "Күні жоқ"
            amt = int(r['amount']) if float(r['amount']).is_integer() else r['amount']
            total_sum += amt
            html += f"<tr><td class='center'>{dt_str}</td><td class='center'>{r['acc_name']}</td><td class='center'>{'Кіріс' if r['type']=='income' else 'Шығыс'}</td><td>{r['category']}</td><td class='right'>{amt}</td></tr>"
            
    html += f"<tr><td colspan='4' class='right' style='font-weight:bold;'>ЖАЛПЫ СОМА (ИТОГО):</td><td class='right' style='font-weight:bold;'>{total_sum}</td></tr>"
    html += "</table></body></html>"
    
    output = BytesIO()
    output.write(html.encode('utf-8'))
    output.seek(0)
    return send_file(output, download_name="Finance_Report.doc", as_attachment=True, mimetype="application/msword")

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)