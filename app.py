import sqlite3, os, random, string
from flask import Flask, render_template, request, url_for, redirect, session

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sasha_7b_mega_v3_2026')

# Путь к базе данных
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
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
         login TEXT UNIQUE, password TEXT, full_name TEXT, 
         email TEXT, birth_date TEXT, role TEXT)''')
    
    conn.execute('CREATE TABLE IF NOT EXISTS schedule (id INTEGER PRIMARY KEY AUTOINCREMENT, lesson_num INTEGER, time_range TEXT, subject TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, created TIMESTAMP DEFAULT CURRENT_TIMESTAMP, title TEXT, content TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS homework (id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT, task TEXT, deadline TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS achievements (id INTEGER PRIMARY KEY AUTOINCREMENT, user_login TEXT, title TEXT, icon TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS photos (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, url TEXT)')
    
    # СОЗДАЕМ ТРЕХ ГЛАВНЫХ ГЕРОЕВ
    users_to_add = [
        ('НиколаевскийАА', 'твой_пароль', 'Николаевский А.А.', 'admin'),
        ('КлРуководитель', 'учитель7б', 'Николаева И.В.', 'teacher'),
        ('Родитель', '7B_parents', 'Уважаемый Родитель', 'parent')
    ]
    
    for l, p, f, r in users_to_add:
        try:
            conn.execute('INSERT INTO users (login, password, full_name, role) VALUES (?, ?, ?, ?)', (l, p, f, r))
        except:
            pass
            
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if 'user' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    bdays = conn.execute('SELECT full_name, birth_date FROM users WHERE birth_date IS NOT NULL ORDER BY birth_date').fetchall()
    posts = conn.execute('SELECT * FROM posts ORDER BY created DESC').fetchall()
    sched = conn.execute('SELECT * FROM schedule ORDER BY lesson_num').fetchall()
    hw = conn.execute('SELECT * FROM homework ORDER BY deadline ASC').fetchall()
    conn.close()
    return render_template('index.html', user=session['user'], role=session.get('role'), posts=posts, schedule=sched, homework=hw, bdays=bdays)

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
                return "Регистрация успешна! <a href='/login'>Войти</a>"
            except:
                return "Логин уже занят!"
            finally:
                conn.close()
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

@app.route('/admin_panel', methods=['GET', 'POST'])
def admin_panel():
    if session.get('role') not in ['admin', 'teacher']:
        return "Доступ запрещен!", 403
    conn = get_db_connection()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'edit_sched':
            conn.execute('DELETE FROM schedule')
            subs, times = request.form.getlist('sub'), request.form.getlist('time')
            for i, s in enumerate(subs):
                if s.strip(): conn.execute('INSERT INTO schedule (lesson_num, time_range, subject) VALUES (?,?,?)', (i+1, times[i], s))
        elif action == 'add_hw':
            conn.execute('INSERT INTO homework (subject, task, deadline) VALUES (?,?,?)', (request.form['s'], request.form['t'], request.form['d']))
        elif action == 'add_post':
            conn.execute('INSERT INTO posts (title, content) VALUES (?,?)', (request.form['t'], request.form['c']))
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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
