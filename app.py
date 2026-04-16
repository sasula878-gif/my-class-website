import sqlite3, os
from flask import Flask, render_template, request, url_for, redirect, session

app = Flask(__name__)
app.secret_key = 'sasha_7b_fix'

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, login TEXT UNIQUE, password TEXT, full_name TEXT, birth_date TEXT, role TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS homework (id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT, task TEXT, deadline TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS schedule (id INTEGER PRIMARY KEY AUTOINCREMENT, lesson_num INTEGER, time_range TEXT, subject TEXT)')
    
    # Твои доступы
    users = [('НиколаевскийАА', '54267194360Sasha', 'Николаевский А.А.', 'admin'), 
             ('КлРуководитель', 'учитель7б', 'Николаева И.В.', 'teacher'),
             ('Родитель', '7B_parents', 'Родитель', 'parent')]
    for l, p, f, r in users:
        try: conn.execute('INSERT INTO users (login, password, full_name, role) VALUES (?,?,?,?)', (l,p,f,r))
        except: pass
    conn.commit(); conn.close()

init_db()

@app.route('/')
def index():
    if 'user' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts').fetchall()
    hw = conn.execute('SELECT * FROM homework').fetchall()
    bdays = conn.execute('SELECT full_name, birth_date FROM users WHERE birth_date IS NOT NULL').fetchall()
    conn.close()
    return render_template('index.html', role=session.get('role'), posts=posts, homework=hw, bdays=bdays)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE login=? AND password=?', (request.form['username'], request.form['password'])).fetchone()
        if user:
            session['user'], session['role'] = user['login'], user['role']
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/admin_panel', methods=['GET', 'POST'])
def admin_panel():
    if session.get('role') not in ['admin', 'teacher']: return "Нет доступа", 403
    conn = get_db_connection()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_hw':
            conn.execute('INSERT INTO homework (subject, task, deadline) VALUES (?,?,?)', (request.form['s'], request.form['t'], request.form['d']))
        elif action == 'add_post':
            conn.execute('INSERT INTO posts (title, content) VALUES (?,?)', (request.form['t'], request.form['c']))
        conn.commit()
    conn.close()
    return render_template('admin_panel.html')

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
