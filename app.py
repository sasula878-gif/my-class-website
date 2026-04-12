import sqlite3
import os
import random
import string
from flask import Flask, render_template, request, url_for, redirect, session

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'anton_super_protected_2026')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

# Секретный код, который ты скажешь одноклассникам завтра
CLASS_INVITE_CODE = "7B_TOP" 

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Таблица пользователей: login, password, role
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  login TEXT UNIQUE NOT NULL, 
                  password TEXT NOT NULL, 
                  role TEXT NOT NULL)''')
    
    # Наши стандартные таблицы
    conn.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, title TEXT NOT NULL, content TEXT NOT NULL)')
    conn.execute('CREATE TABLE IF NOT EXISTS photos (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, url TEXT NOT NULL)')
    conn.execute('CREATE TABLE IF NOT EXISTS knowledge (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL, title TEXT NOT NULL, url TEXT NOT NULL)')
    
    # Создаем админа, если его еще нет
    try:
        conn.execute('INSERT INTO users (login, password, role) VALUES (?, ?, ?)', ('admin', '12345', 'admin'))
    except sqlite3.IntegrityError:
        pass
        
    conn.commit()
    conn.close()

init_db()

# Функция для генерации случайного пароля из 6 символов
def generate_password():
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(6))

@app.route('/')
def index():
    if 'user' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY created DESC').fetchall()
    conn.close()
    return render_template('index.html', user=session['user'], role=session.get('role'), posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form.get('username')
        password_input = request.form.get('password')
        invite_code = request.form.get('invite_code') # Поле для новых учеников

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE login = ?', (login_input,)).fetchone()

        # 1. Если пользователь уже есть — проверяем пароль
        if user:
            if user['password'] == password_input:
                session.permanent = True
                session['user'] = user['login']
                session['role'] = user['role']
                return redirect(url_for('index'))
            else:
                return "Неверный пароль! <a href='/login'>Назад</a>"
        
        # 2. Если пользователя нет, но он ввел правильный код приглашения — регистрируем!
        elif invite_code == CLASS_INVITE_CODE:
            new_password = generate_password()
            conn.execute('INSERT INTO users (login, password, role) VALUES (?, ?, ?)', 
                         (login_input, new_password, 'student'))
            conn.commit()
            conn.close()
            return f"Ты зарегистрирован! Твой логин: <b>{login_input}</b>. Твой пароль: <b style='color:red;'>{new_password}</b>. Запомни его и <a href='/login'>войди</a>."
        
        else:
            return "Пользователь не найден или неверный код приглашения. <a href='/login'>Назад</a>"

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Остальные маршруты (create, gallery, knowledge) остаются такими же...
# Только добавь проверку session.get('role') == 'admin' в декораторах.

@app.route('/create', methods=['GET', 'POST'])
def create():
    if session.get('role') != 'admin': return "Доступ запрещен", 403
    if request.method == 'POST':
        conn = get_db_connection()
        conn.execute('INSERT INTO posts (title, content) VALUES (?, ?)', (request.form['title'], request.form['content']))
        conn.commit(); conn.close()
        return redirect(url_for('index'))
    return render_template('create.html')

@app.route('/gallery')
def gallery():
    if 'user' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    photos = conn.execute('SELECT * FROM photos').fetchall()
    conn.close()
    return render_template('gallery.html', user=session['user'], photos=photos)

@app.route('/add_photo', methods=['GET', 'POST'])
def add_photo():
    if session.get('role') != 'admin': return "Доступ", 403
    if request.method == 'POST':
        conn = get_db_connection()
        conn.execute('INSERT INTO photos (title, url) VALUES (?, ?)', (request.form['title'], request.form['url']))
        conn.commit(); conn.close()
        return redirect(url_for('gallery'))
    return render_template('add_photo.html')

@app.route('/knowledge')
def knowledge():
    if 'user' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    materials = conn.execute('SELECT * FROM knowledge').fetchall()
    conn.close()
    return render_template('knowledge.html', user=session['user'], materials=materials)

@app.route('/add_material', methods=['GET', 'POST'])
def add_material():
    if session.get('role') != 'admin': return "Доступ", 403
    if request.method == 'POST':
        conn = get_db_connection()
        conn.execute('INSERT INTO knowledge (category, title, url) VALUES (?, ?, ?)', (request.form['category'], request.form['title'], request.form['url']))
        conn.commit(); conn.close()
        return redirect(url_for('knowledge'))
    return render_template('add_material.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
