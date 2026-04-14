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
    # Таблицы
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, login TEXT UNIQUE, password TEXT, role TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS schedule (id INTEGER PRIMARY KEY AUTOINCREMENT, lesson_num INTEGER, time_range TEXT, subject TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, created TIMESTAMP DEFAULT CURRENT_TIMESTAMP, title TEXT, content TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS photos (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, url TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS knowledge (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, title TEXT, url TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS achievements (id INTEGER PRIMARY KEY AUTOINCREMENT, user_login TEXT, title TEXT, icon TEXT)')
    
    # ПРЕДУСТАНОВЛЕННЫЕ АККАУНТЫ
    users_to_add = [
        ('НиколаевскийАА', '54267194360Sasha', 'admin'),
        ('КлРуководитель', 'Fybnf2020@', 'admin'),
        ('Родитель', '7B_parents', 'parent')
    ]
    
    for login, pwd, role in users_to_add:
        try:
            conn.execute('INSERT INTO users (login, password, role) VALUES (?, ?, ?)', (login, pwd, role))
        except:
            pass
            
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
        l = request.form.get('username')
        p = request.form.get('password')
        i = request.form.get('invite_code')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE login = ?', (l,)).fetchone()
        
        # Проверка существующего юзера (тебя, учителя или родителя)
        if user and user['password'] == p:
            session['user'] = user['login']
            session['role'] = user['role']
            return redirect(url_for('index'))
            
        # Регистрация нового ученика по коду
        elif i == CLASS_INVITE_CODE:
            pwd = generate_password()
            try:
                conn.execute('INSERT INTO users (login, password, role) VALUES (?, ?, ?)', (l, pwd, 'student'))
                conn.commit()
                conn.close()
                return f"Регистрация успешна! Логин: {l}, Пароль: {pwd}. <a href='/login'>Войти</a>"
            except:
                return "Этот логин уже занят. <a href='/login'>Назад</a>"
        
        return "Неверные данные. <a href='/login'>Назад</a>"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- АДМИН-ФУНКЦИИ (Только role == 'admin') ---

@app.route('/edit_schedule', methods=['GET', 'POST'])
def edit_schedule():
    if session.get('role') != 'admin': return "Доступ только для админа", 403
    conn = get_db_connection()
    if request.method == 'POST':
        conn.execute('DELETE FROM schedule')
        subjects = request.form.getlist('subject')
        times = request.form.getlist('time')
        for idx, sub in enumerate(subjects):
            if sub.strip():
                conn.execute('INSERT INTO schedule (lesson_num, time_range, subject) VALUES (?, ?, ?)', (idx+1, times[idx], sub))
        conn.commit()
        return redirect(url_for('index'))
    sched = conn.execute('SELECT * FROM schedule ORDER BY lesson_num').fetchall()
    return render_template('edit_schedule.html', schedule=sched)

@app.route('/add_photo', methods=['GET', 'POST'])
def add_photo():
    if session.get('role') != 'admin': return "Доступ запрещен", 403
    if request.method == 'POST':
        conn = get_db_connection()
        conn.execute('INSERT INTO photos (title, url) VALUES (?, ?)', (request.form['title'], request.form['url']))
        conn.commit()
        return redirect(url_for('gallery'))
    return render_template('add_photo.html')

@app.route('/add_material', methods=['GET', 'POST'])
def add_material():
    if session.get('role') != 'admin': return "Доступ запрещен", 403
    if request.method == 'POST':
        conn = get_db_connection()
        conn.execute('INSERT INTO knowledge (category, title, url) VALUES (?, ?, ?)', (request.form['category'], request.form['title'], request.form['url']))
        conn.commit()
        return redirect(url_for('knowledge'))
    return render_template('add_material.html')

@app.route('/add_ach', methods=['GET', 'POST'])
def add_ach():
    if session.get('role') != 'admin': return "Доступ запрещен", 403
    if request.method == 'POST':
        conn = get_db_connection()
        conn.execute('INSERT INTO achievements (user_login, title, icon) VALUES (?, ?, ?)', (request.form['login'], request.form['title'], request.form['icon']))
        conn.commit()
        return redirect(url_for('achievements'))
    return render_template('add_ach.html')

# --- ОБЩИЕ СТРАНИЦЫ ---

@app.route('/gallery')
def gallery():
    if 'user' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    photos = conn.execute('SELECT * FROM photos').fetchall()
    return render_template('gallery.html', photos=photos, role=session.get('role'))

@app.route('/knowledge')
def knowledge():
    if 'user' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    mats = conn.execute('SELECT * FROM knowledge').fetchall()
    return render_template('knowledge.html', materials=mats, role=session.get('role'))

@app.route('/achievements')
def achievements():
    if 'user' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    achs = conn.execute('SELECT * FROM achievements').fetchall()
    return render_template('achievements.html', achievements=achs)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
