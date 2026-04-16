import sqlite3, os, random, string
from flask import Flask, render_template, request, url_for, redirect, session

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sasha_7b_legend_2026')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Пользователи: логин, пароль, ФИО, почта, ДР, роль
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
         login TEXT UNIQUE, password TEXT, full_name TEXT, 
         email TEXT, birth_date TEXT, role TEXT)''')
    
    conn.execute('CREATE TABLE IF NOT EXISTS schedule (id INTEGER PRIMARY KEY, lesson_num INTEGER, time_range TEXT, subject TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, created TIMESTAMP DEFAULT CURRENT_TIMESTAMP, title TEXT, content TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS homework (id INTEGER PRIMARY KEY, subject TEXT, task TEXT, deadline TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS achievements (id INTEGER PRIMARY KEY, user_login TEXT, title TEXT, icon TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS photos (id INTEGER PRIMARY KEY, title TEXT, url TEXT)')
    
    # ОСНОВНЫЕ АККАУНТЫ
    users_to_add = [
        ('НиколаевскийАА', '54267194360Sasha', 'Николаевский А.А.', 'admin'),
        ('КлРуководитель', 'Fybnf2020@', 'Николаева И.В.', 'teacher'),
        ('Родитель', '7B_parents', 'Уважаемый Родитель', 'parent')
    ]
    for l, p, f, r in users_to_add:
        try: conn.execute('INSERT INTO users (login, password, full_name, role) VALUES (?,?,?,?)', (l,p,f,r))
        except: pass
    conn.commit(); conn.close()

init_db()

@app.route('/')
def index():
    if 'user' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY created DESC').fetchall()
    sched = conn.execute('SELECT * FROM schedule ORDER BY lesson_num').fetchall()
    hw = conn.execute('SELECT * FROM homework ORDER BY deadline ASC').fetchall()
    bdays = conn.execute('SELECT full_name, birth_date FROM users WHERE birth_date IS NOT NULL ORDER BY birth_date').fetchall()
    conn.close()
    return render_template('index.html', user=session['user'], role=session.get('role'), posts=posts, schedule=sched, homework=hw, bdays=bdays)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (login, password, full_name, email, birth_date, role) VALUES (?,?,?,?,?,?)',
                (request.form['login'], request.form['password'], request.form['fio'], request.form['email'], request.form['bday'], 'student'))
            conn.commit()
            return redirect(url_for('login'))
        except: return "Ошибка! Возможно, логин занят."
        finally: conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE login = ? AND password = ?', (request.form['username'], request.form['password'])).fetchone()
        if user:
            session['user'], session['role'] = user['login'], user['role']
            return redirect(url_for('index'))
        return "Неверный вход!"
    return render_template('login.html')

@app.route('/admin_panel', methods=['GET', 'POST'])
def admin_panel():
    if session.get('role') not in ['admin', 'teacher']: return "Доступ закрыт!", 403
    conn = get_db_connection()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'edit_sched':
            conn.execute('DELETE FROM schedule')
            for i, s in enumerate(request.form.getlist('sub')):
                if s.strip(): conn.execute('INSERT INTO schedule (lesson_num, time_range, subject) VALUES (?,?,?)', (i+1, request.form.getlist('time')[i], s))
        elif action == 'add_hw':
            conn.execute('INSERT INTO homework (subject, task, deadline) VALUES (?,?,?)', (request.form['s'], request.form['t'], request.form['d']))
        elif action == 'add_post':
            conn.execute('INSERT INTO posts (title, content) VALUES (?,?)', (request.form['t'], request.form['c']))
        elif action == 'add_ach':
            conn.execute('INSERT INTO achievements (user_login, title, icon) VALUES (?,?,?)', (request.form['l'], request.form['t'], request.form['i']))
        conn.commit()
    posts = conn.execute('SELECT * FROM posts').fetchall()
    conn.close()
    return render_template('admin_panel.html', posts=posts)

@app.route('/gallery')
def gallery():
    conn = get_db_connection(); photos = conn.execute('SELECT * FROM photos').fetchall()
    return render_template('gallery.html', photos=photos, role=session.get('role'))

@app.route('/achievements')
def achievements():
    conn = get_db_connection(); achs = conn.execute('SELECT * FROM achievements').fetchall()
    return render_template('achievements.html', achievements=achs)

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
