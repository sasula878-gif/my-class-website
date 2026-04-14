import sqlite3, os, random, string
from flask import Flask, render_template, request, url_for, redirect, session
import smtplib # Для почты
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sasha_ultra_2026')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
CLASS_INVITE_CODE = "7B_TOP"

# Настройки почты (для отправки кодов)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "sasula878@gmail.com" 
SENDER_PASSWORD = "owjc yzky sugr qvpv" # Нужен пароль приложения, а не от почты

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Таблица юзеров стала больше
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
         login TEXT UNIQUE, password TEXT, full_name TEXT, 
         email TEXT, birth_date TEXT, role TEXT)''')
    
    conn.execute('CREATE TABLE IF NOT EXISTS schedule (id INTEGER PRIMARY KEY, lesson_num INTEGER, time_range TEXT, subject TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, created TIMESTAMP DEFAULT CURRENT_TIMESTAMP, title TEXT, content TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS homework (id INTEGER PRIMARY KEY, subject TEXT, task TEXT, deadline TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS achievements (id INTEGER PRIMARY KEY, user_login TEXT, title TEXT, icon TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS photos (id INTEGER PRIMARY KEY, title TEXT, url TEXT)')
    
    # СОЗДАЕМ ТРЕХ ГЛАВНЫХ ГЕРОЕВ
    users_to_add = [
        ('НиколаевскийАА', '54267194360Sasha', 'Николаевский А.А.', 'admin'),
        ('КлРуководитель', 'Fybnf2020@', 'teacher'),
        ('Родитель', '7B_parents', 'parent')
    ]
init_db()

# --- ЛОГИКА ПОЧТЫ ---
def send_confirm_email(receiver_email, code):
    msg = MIMEText(f"Твой код для регистрации на сайте 7Б: {code}")
    msg['Subject'] = 'Код подтверждения 7Б'
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"Ошибка почты: {e}")

@app.route('/')
def index():
    if 'user' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    # Берем всех именинников
    bdays = conn.execute('SELECT full_name, birth_date FROM users WHERE birth_date IS NOT NULL').fetchall()
    posts = conn.execute('SELECT * FROM posts ORDER BY created DESC').fetchall()
    sched = conn.execute('SELECT * FROM schedule ORDER BY lesson_num').fetchall()
    hw = conn.execute('SELECT * FROM homework').fetchall()
    conn.close()
    return render_template('index.html', user=session['user'], role=session.get('role'), 
                           posts=posts, schedule=sched, homework=hw, bdays=bdays)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fio = request.form.get('fio')
        email = request.form.get('email')
        login = request.form.get('login')
        pwd = request.form.get('password')
        bday = request.form.get('bday')
        invite = request.form.get('invite')

        if invite == CLASS_INVITE_CODE:
            conn = get_db_connection()
            try:
                conn.execute('INSERT INTO users (login, password, full_name, email, birth_date, role) VALUES (?, ?, ?, ?, ?, ?)',
                             (login, pwd, fio, email, bday, 'student'))
                conn.commit()
                # Тут можно вызвать send_confirm_email, если настроил SMTP
                return "Регистрация успешна! <a href='/login'>Войти</a>"
            except: return "Логин уже занят!"
            finally: conn.close()
        return "Неверный код приглашения!"
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        l, p = request.form.get('username'), request.form.get('password')
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE login = ? AND password = ?', (l, p)).fetchone()
        if user:
            session['user'], session['role'] = user['login'], user['role']
            return redirect(url_for('index'))
        return "Ошибка входа!"
    return render_template('login.html')

# --- МЕГА-АДМИНКА ---
@app.route('/admin_panel', methods=['GET', 'POST'])
def admin_panel():
    if session.get('role') != 'admin': return "Уйди, разбойник!", 403
    conn = get_db_connection()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'edit_sched':
            conn.execute('DELETE FROM schedule')
            subs = request.form.getlist('sub')
            times = request.form.getlist('time')
            for i, s in enumerate(subs):
                if s: conn.execute('INSERT INTO schedule (lesson_num, time_range, subject) VALUES (?,?,?)', (i+1, times[i], s))
        elif action == 'add_post':
            conn.execute('INSERT INTO posts (title, content) VALUES (?,?)', (request.form['t'], request.form['c']))
        elif action == 'del_post':
            conn.execute('DELETE FROM posts WHERE id = ?', (request.form['id'],))
        elif action == 'add_hw':
            conn.execute('INSERT INTO homework (subject, task, deadline) VALUES (?,?,?)', (request.form['s'], request.form['t'], request.form['d']))
        elif action == 'add_ach':
            conn.execute('INSERT INTO achievements (user_login, title, icon) VALUES (?,?,?)', (request.form['l'], request.form['t'], request.form['i']))
        conn.commit()
    
    posts = conn.execute('SELECT * FROM posts').fetchall()
    sched = conn.execute('SELECT * FROM schedule').fetchall()
    conn.close()
    return render_template('admin_panel.html', posts=posts, sched=sched)

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

@app.route('/gallery')
def gallery():
    conn = get_db_connection(); photos = conn.execute('SELECT * FROM photos').fetchall()
    return render_template('gallery.html', photos=photos, role=session.get('role'))

@app.route('/achievements')
def achievements():
    conn = get_db_connection(); achs = conn.execute('SELECT * FROM achievements').fetchall()
    return render_template('achievements.html', achievements=achs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
