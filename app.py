import sqlite3
import os
import random
import string
from flask import Flask, render_template, request, url_for, redirect, session

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sasha_7b_dev_2026_secure')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')
CLASS_INVITE_CODE = "7B_TOP"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Пользователи
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, login TEXT UNIQUE, password TEXT, role TEXT)')
    # Расписание
    conn.execute('CREATE TABLE IF NOT EXISTS schedule (id INTEGER PRIMARY KEY AUTOINCREMENT, lesson_num INTEGER, time_range TEXT, subject TEXT)')
    # Посты/Новости
    conn.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, created TIMESTAMP DEFAULT CURRENT_TIMESTAMP, title TEXT, content TEXT)')
    # Галерея
    conn.execute('CREATE TABLE IF NOT EXISTS photos (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, url TEXT)')
    # База знаний
    conn.execute('CREATE TABLE IF NOT EXISTS knowledge (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, title TEXT, url TEXT)')
    # АЧИВКИ (Новое!)
    conn.execute('CREATE TABLE IF NOT EXISTS achievements (id INTEGER PRIMARY KEY AUTOINCREMENT, user_login TEXT, title TEXT, icon TEXT)')
    
    # Твой аккаунт (Админ)
    try:
        conn.execute('INSERT INTO users (login, password, role) VALUES (?, ?, ?)', ('НиколаевскийАА', 'твой_пароль', 'admin'))
    except: pass
    conn.commit()
    conn.close()

init_db()

def generate_password():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))

@app.route('/')
def index():
    if 'user' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY created DESC').fetchall()
    sched = conn.execute('SELECT * FROM schedule ORDER BY lesson_num').fetchall()
    conn.close()
    return render_template('index.html', user=session['user'], role=session.get('role'), posts=posts, schedule=sched)

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
            pwd = generate_password()
            conn.execute('INSERT INTO users (login, password, role) VALUES (?, ?, ?)', (l, pwd, 'student'))
            conn.commit(); conn.close()
            return f"Логин: {l}, Пароль: {pwd}. Запомни! <a href='/login'>Войти</a>"
        return "Ошибка! <a href='/login'>Назад</a>"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- ФУНКЦИИ УПРАВЛЕНИЯ (Админ) ---
@app.route('/edit_schedule', methods=['GET', 'POST'])
def edit_schedule():
    if session.get('role') != 'admin': return "Нет доступа", 403
    conn = get_db_connection()
    if request.method == 'POST':
        conn.execute('DELETE FROM schedule')
        for i, sub in enumerate(request.form.getlist('subject')):
            if sub.strip():
                conn.execute('INSERT INTO schedule (lesson_num, time_range, subject) VALUES (?, ?, ?)', (i+1, request.form.getlist('time')[i], sub))
        conn.commit(); return redirect(url_for('index'))
    sched = conn.execute('SELECT * FROM schedule ORDER BY lesson_num').fetchall()
    return render_template('edit_schedule.html', schedule=sched)

@app.route('/gallery')
def gallery():
    if 'user' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    photos = conn.execute('SELECT * FROM photos').fetchall()
    return render_template('gallery.html', photos=photos, role=session.get('role'))

@app.route('/add_photo', methods=['GET', 'POST'])
def add_photo():
    if session.get('role') != 'admin': return "Нет доступа", 403
    if request.method == 'POST':
        conn = get_db_connection()
        conn.execute('INSERT INTO photos (title, url) VALUES (?, ?)', (request.form['title'], request.form['url']))
        conn.commit(); return redirect(url_for('gallery'))
    return render_template('add_photo.html')

@app.route('/knowledge')
def knowledge():
    if 'user' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    mats = conn.execute('SELECT * FROM knowledge').fetchall()
    return render_template('knowledge.html', materials=mats, role=session.get('role'))

@app.route('/add_material', methods=['GET', 'POST'])
def add_material():
    if session.get('role') != 'admin': return "Нет доступа", 403
    if request.method == 'POST':
        conn = get_db_connection()
        conn.execute('INSERT INTO knowledge (category, title, url) VALUES (?, ?, ?)', (request.form['category'], request.form['title'], request.form['url']))
        conn.commit(); return redirect(url_for('knowledge'))
    return render_template('add_material.html')

# --- АЧИВКИ (НОВОЕ) ---
@app.route('/achievements')
def achievements():
    if 'user' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    achs = conn.execute('SELECT * FROM achievements').fetchall()
    return render_template('achievements.html', achievements=achs)

@app.route('/add_ach', methods=['GET', 'POST'])
def add_ach():
    if session.get('role') != 'admin': return "Нет доступа", 403
    if request.method == 'POST':
        conn = get_db_connection()
        conn.execute('INSERT INTO achievements (user_login, title, icon) VALUES (?, ?, ?)', (request.form['login'], request.form['title'], request.form['icon']))
        conn.commit(); return redirect(url_for('achievements'))
    return render_template('add_ach.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
