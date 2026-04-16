import sqlite3, os
from flask import Flask, render_template, request, url_for, redirect, session

app = Flask(__name__)
app.secret_key = 'sasha_7b_mega_final_v4'

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Создаем таблицы (если их нет)
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, login TEXT UNIQUE, password TEXT, full_name TEXT, birth_date TEXT, role TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS homework (id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT, task TEXT, deadline TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS schedule (id INTEGER PRIMARY KEY AUTOINCREMENT, lesson_num INTEGER, time_range TEXT, subject TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS photos (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, url TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS knowledge (id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT, title TEXT, url TEXT)')
    
    # СПИСОК ГЛАВНЫХ АККАУНТОВ
    # Роли: admin (ты), teacher (клрук), parent (родители)
    main_users = [
        ('НиколаевскийАА', '54267194360Saha', 'Николаевский А.А.', 'admin'), 
        ('КлРуководитель', 'учитель7б', 'Николаева И.В.', 'teacher'),
        ('Родитель', '7B_parents', 'Уважаемый Родитель', 'parent')
    ]
    
    for l, p, f, r in main_users:
        try:
            # Проверяем, нет ли уже такого логина, чтобы не было ошибок
            conn.execute('INSERT OR IGNORE INTO users (login, password, full_name, role) VALUES (?,?,?,?)', (l, p, f, r))
        except:
            pass
            
    conn.commit()
    conn.close()

# Вызываем создание базы при старте
init_db()

@app.route('/')
def index():
    if 'user' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY id DESC').fetchall()
    hw = conn.execute('SELECT * FROM homework ORDER BY deadline ASC').fetchall()
    sched = conn.execute('SELECT * FROM schedule ORDER BY lesson_num').fetchall()
    bdays = conn.execute('SELECT full_name, birth_date FROM users WHERE birth_date IS NOT NULL').fetchall()
    conn.close()
    return render_template('index.html', role=session.get('role'), posts=posts, homework=hw, schedule=sched, bdays=bdays)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        conn = get_db_connection()
        try:
            # Важно: названия в request.form должны совпадать с именами в HTML
            conn.execute('INSERT INTO users (login, password, full_name, birth_date, role) VALUES (?,?,?,?,?)',
                (request.form['login'], request.form['password'], request.form['fio'], request.form['bday'], 'student'))
            conn.commit()
            return redirect(url_for('login'))
        except Exception as e:
            return f"Ошибка регистрации: {e}"
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Печатаем в консоль Render, что мы вводим (для отладки)
        print(f"Пытаемся войти: {request.form['username']} / {request.form['password']}")
        # ... остальной код входа ...

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
        elif action == 'edit_sched':
            conn.execute('DELETE FROM schedule')
            for i, s in enumerate(request.form.getlist('sub')):
                if s.strip(): conn.execute('INSERT INTO schedule (lesson_num, time_range, subject) VALUES (?,?,?)', (i+1, request.form.getlist('time')[i], s))
        elif action == 'add_photo':
            conn.execute('INSERT INTO photos (title, url) VALUES (?,?)', (request.form['t'], request.form['u']))
        elif action == 'add_kb':
            conn.execute('INSERT INTO knowledge (subject, title, url) VALUES (?,?,?)', (request.form['s'], request.form['t'], request.form['u']))
        conn.commit()
    conn.close()
    return render_template('admin_panel.html')

@app.route('/gallery')
def gallery():
    conn = get_db_connection()
    photos = conn.execute('SELECT * FROM photos ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('gallery.html', photos=photos)

@app.route('/knowledge')
def knowledge():
    conn = get_db_connection()
    kb = conn.execute('SELECT * FROM knowledge').fetchall()
    conn.close()
    return render_template('knowledge.html', kb=kb)

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
