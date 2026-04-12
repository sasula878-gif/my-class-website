import sqlite3
import os
import random
import string
from flask import Flask, render_template, request, url_for, redirect, session

app = Flask(__name__)
# Твой секретный ключ для сессий
app.secret_key = os.environ.get('SECRET_KEY', 'sasha_super_dev_7b_2026')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

# Код для регистрации одноклассников
CLASS_INVITE_CODE = "7B_TOP" 

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # 1. Таблица пользователей
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  login TEXT UNIQUE NOT NULL, 
                  password TEXT NOT NULL, 
                  role TEXT NOT NULL)''')
    
    # 2. Таблица расписания
    conn.execute('''CREATE TABLE IF NOT EXISTS schedule 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  lesson_num INTEGER, 
                  time_range TEXT, 
                  subject TEXT)''')
    
    # 3. Таблицы для контента
    conn.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, title TEXT NOT NULL, content TEXT NOT NULL)')
    conn.execute('CREATE TABLE IF NOT EXISTS photos (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, url TEXT NOT NULL)')
    conn.execute('CREATE TABLE IF NOT EXISTS knowledge (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL, title TEXT NOT NULL, url TEXT NOT NULL)')
    
    # Создаем тебя (админа) и других стартовых юзеров
    # Смени 'твой_пароль' на тот, который хочешь!
    admins = [
        ('НиколаевскийАА', '54267194360Sasha', 'admin'),
        ('КлРуководитель', 'Fybnf2020@', 'admin'),
        ('Родитель', '7B_parents', 'parent')
    ]
    
    for login, pwd, role in admins:
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

# --- ГЛАВНАЯ ---
@app.route('/')
def index():
    if 'user' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY created DESC').fetchall()
    sched = conn.execute('SELECT * FROM schedule ORDER BY lesson_num').fetchall()
    conn.close()
    return render_template('index.html', user=session['user'], role=session.get('role'), posts=posts, schedule=sched)

# --- ВХОД И РЕГИСТРАЦИЯ ---
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
            return "Неверный пароль! <a href='/login'>Назад</a>"
        
        elif invite_code == CLASS_INVITE_CODE:
            new_pwd = generate_password()
            conn.execute('INSERT INTO users (login, password, role) VALUES (?, ?, ?)', 
                         (login_input, new_pwd, 'student'))
            conn.commit()
            conn.close()
            return f"Аккаунт создан! Твой логин: <b>{login_input}</b>, пароль: <b style='color:red;'>{new_pwd}</b>. <a href='/login'>Войти</a>"
        
        return "Пользователь не найден. <a href='/login'>Назад</a>"
    
    return render_template('login.html')
