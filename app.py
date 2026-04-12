import sqlite3
import os
import random
import string
from flask import Flask, render_template, request, url_for, redirect, session

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sasha_top_dev_2026')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

CLASS_INVITE_CODE = "7B_TOP" 

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Таблица пользователей
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  login TEXT UNIQUE NOT NULL, 
                  password TEXT NOT NULL, 
                  role TEXT NOT NULL)''')
    
    # Таблица расписания
    conn.execute('''CREATE TABLE IF NOT EXISTS schedule 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  lesson_num INTEGER, 
                  time_range TEXT, 
                  subject TEXT)''')
    
    conn.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, title TEXT NOT NULL, content TEXT NOT NULL)')
    conn.execute('CREATE TABLE IF NOT EXISTS photos (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, url TEXT NOT NULL)')
    conn.execute('CREATE TABLE IF NOT EXISTS knowledge (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL, title TEXT NOT NULL, url TEXT NOT NULL)')
    
    # ТВОЯ АДМИНКА И КЛАССНЫЙ РУКОВОДИТЕЛЬ
    users_to_add = [
        ('НиколаевскийАА', '54267194360Sasha', 'admin'),
        ('КлРуководитель', 'Fybnf2020@', 'admin'),
        ('Родитель', '7B_parents', 'parent') # Общий вход для родителей
    ]
    
    for login, pwd, role in users_to_add:
        try:
            conn.execute('INSERT INTO users (login, password, role) VALUES (?, ?, ?)', (login, pwd, role))
        except sqlite3.IntegrityError:
            pass
            
    conn.commit()
    conn.close()

init_db()

def generate_password():
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(6))

@app.route('/')
def index():
    if 'user' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY created DESC').fetchall()
    # Загружаем расписание из базы
    sched = conn.execute('SELECT * FROM schedule ORDER BY lesson_num').fetchall()
    conn.close()
    return render_template('index.html', user=session['user'], role=session.get('role'), posts=posts, schedule=sched)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form.get('username')
        password_input = request.form.get('password')
        invite_code = request.form.get('invite_code')

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE login = ?', (login_input,)).fetchone()

        if user:
            if user['password'] == password_input:
                session.permanent = True
                session['user'] = user['login']
                session['role'] = user['role']
                return redirect(url_for('index'))
            return "Ошибка пароля! <a href='/login'>Назад</a>"
        
        elif invite_code == CLASS_INVITE_CODE:
            new_pwd = generate_password()
            conn.execute('INSERT INTO users (login, password, role) VALUES (?, ?, ?)', 
                         (login_input, new_pwd, 'student'))
            conn.commit(); conn.close()
            return f"Аккаунт создан! Твой пароль: <b>{new_pwd}</b>. <a href='/login'>Войти</a>"
        
        return "Неверные данные. <a href='/login'>Назад</a>"
    return render_template('login.html')

# МАРШРУТ ДЛЯ РЕДАКТИРОВАНИЯ РАСПИСАНИЯ
@app.route('/edit_schedule', methods=['GET', 'POST'])
def edit_schedule():
    if session.get('role') != 'admin': return "Нет прав", 403
    conn = get_db_connection()
    if request.method == 'POST':
        # Очищаем старое расписание и записываем новое
        conn.execute('DELETE FROM schedule')
        lessons = request.form.getlist('subject')
        times = request.form.getlist('time')
        for i, subject in enumerate(lessons):
            if subject.strip():
                conn.execute('INSERT INTO schedule (lesson_num, time_range, subject) VALUES (?, ?, ?)',
                             (i+1, times[i], subject))
        conn.commit(); conn.close()
        return redirect(url_for('index'))
    
    sched = conn.execute('SELECT * FROM schedule ORDER BY lesson_num').fetchall()
    conn.close()
    return render_template('edit_schedule.html', schedule=sched)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Пути для постов, фото и базы знаний (с проверкой role == 'admin')...
# [ОСТАЛЬНОЙ КОД БЕЗ ИЗМЕНЕНИЙ]

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
