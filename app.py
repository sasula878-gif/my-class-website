import sqlite3, os, random, string
from flask import Flask, render_template, request, url_for, redirect, session

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sasha_7b_dev_2026_super')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')
CLASS_INVITE_CODE = "7B_TOP"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, login TEXT UNIQUE, password TEXT, role TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS schedule (id INTEGER PRIMARY KEY, lesson_num INTEGER, time_range TEXT, subject TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, created TIMESTAMP DEFAULT CURRENT_TIMESTAMP, title TEXT, content TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS photos (id INTEGER PRIMARY KEY, title TEXT, url TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS knowledge (id INTEGER PRIMARY KEY, category TEXT, title TEXT, url TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS achievements (id INTEGER PRIMARY KEY, user_login TEXT, title TEXT, icon TEXT)')
    # НОВЫЕ ТАБЛИЦЫ
    conn.execute('CREATE TABLE IF NOT EXISTS homework (id INTEGER PRIMARY KEY, subject TEXT, task TEXT, deadline TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS birthdays (id INTEGER PRIMARY KEY, name TEXT, date TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS cloud_files (id INTEGER PRIMARY KEY, title TEXT, url TEXT)')
    
    users_to_add = [('НиколаевскийАА', '54267194360Sasha', 'admin'), ('КлРуководитель', 'Fybnf2020@', 'admin'), ('Родитель', '7B_parents', 'parent')]
    for l, p, r in users_to_add:
        try: conn.execute('INSERT INTO users (login, password, role) VALUES (?, ?, ?)', (l, p, r))
        except: pass
    conn.commit(); conn.close()

init_db()

@app.route('/')
def index():
    if 'user' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY created DESC').fetchall()
    sched = conn.execute('SELECT * FROM schedule ORDER BY lesson_num').fetchall()
    hw = conn.execute('SELECT * FROM homework').fetchall()
    bdays = conn.execute('SELECT * FROM birthdays ORDER BY date').fetchall()
    conn.close()
    return render_template('index.html', user=session['user'], role=session.get('role'), posts=posts, schedule=sched, homework=hw, birthdays=bdays)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        l, p, i = request.form.get('username'), request.form.get('password'), request.form.get('invite_code')
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE login = ?', (l,)).fetchone()
        if user and user['password'] == p:
            session['user'], session['role'] = user['login'], user['role']
            return redirect(url_for('index'))
        elif i == CLASS_INVITE_CODE:
            pwd = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
            try:
                conn.execute('INSERT INTO users (login, password, role) VALUES (?, ?, ?)', (l, pwd, 'student'))
                conn.commit(); conn.close()
                return f"Логин: {l}, Пароль: {pwd}. <a href='/login'>Войти</a>"
            except: return "Логин занят."
        return "Ошибка!"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

# --- АДМИН-ПАНЕЛЬ ---
@app.route('/admin_panel', methods=['GET', 'POST'])
def admin_panel():
    if session.get('role') != 'admin': return "Доступ запрещен", 403
    conn = get_db_connection()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_hw':
            conn.execute('INSERT INTO homework (subject, task, deadline) VALUES (?, ?, ?)', (request.form['subject'], request.form['task'], request.form['deadline']))
        elif action == 'add_post':
            conn.execute('INSERT INTO posts (title, content) VALUES (?, ?)', (request.form['title'], request.form['content']))
        elif action == 'add_bday':
            conn.execute('INSERT INTO birthdays (name, date) VALUES (?, ?)', (request.form['name'], request.form['date']))
        elif action == 'add_file':
            conn.execute('INSERT INTO cloud_files (title, url) VALUES (?, ?)', (request.form['title'], request.form['url']))
        conn.commit()
    return render_template('admin_panel.html')

# --- СТРАНИЦЫ ---
@app.route('/gallery')
def gallery():
    conn = get_db_connection()
    photos = conn.execute('SELECT * FROM photos').fetchall()
    return render_template('gallery.html', photos=photos, role=session.get('role'))

@app.route('/knowledge')
def knowledge():
    conn = get_db_connection()
    mats = conn.execute('SELECT * FROM knowledge').fetchall()
    files = conn.execute('SELECT * FROM cloud_files').fetchall()
    return render_template('knowledge.html', materials=mats, files=files, role=session.get('role'))

@app.route('/achievements')
def achievements():
    conn = get_db_connection()
    achs = conn.execute('SELECT * FROM achievements').fetchall()
    return render_template('achievements.html', achievements=achs)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
