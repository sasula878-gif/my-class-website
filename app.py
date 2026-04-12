import sqlite3
import os
from flask import Flask, render_template, request, url_for, redirect, session

app = Flask(__name__)
# Секретный ключ (замени на свой)
app.secret_key = os.environ.get('SECRET_KEY', 'anton_secret_777')

# Настройка путей
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

USERS = {
    "admin": "12345",
    "student": "class2026",
    "teacher": "math_is_cool"
}

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, title TEXT NOT NULL, content TEXT NOT NULL)')
    conn.execute('CREATE TABLE IF NOT EXISTS photos (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, url TEXT NOT NULL)')
    conn.execute('CREATE TABLE IF NOT EXISTS knowledge (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL, title TEXT NOT NULL, url TEXT NOT NULL)')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if 'user' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY created DESC').fetchall()
    conn.close()
    return render_template('index.html', user=session['user'], posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username, password = request.form.get('username'), request.form.get('password')
        if USERS.get(username) == password:
            session.permanent = True
            session['user'] = username
            return redirect(url_for('index'))
        return "Ошибка! <a href='/login'>Назад</a>"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/create', methods=['GET', 'POST'])
def create():
    if session.get('user') != 'admin': return "Доступ", 403
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
    if session.get('user') != 'admin': return "Доступ", 403
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
    if session.get('user') != 'admin': return "Доступ", 403
    if request.method == 'POST':
        conn = get_db_connection()
        conn.execute('INSERT INTO knowledge (category, title, url) VALUES (?, ?, ?)', (request.form['category'], request.form['title'], request.form['url']))
        conn.commit(); conn.close()
        return redirect(url_for('knowledge'))
    return render_template('add_material.html')

if __name__ == '__main__':
    # На компе запускается на 5000 порту, на сервере — на том, который дадут
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)