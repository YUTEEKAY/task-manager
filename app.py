from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from database import init_db, get_db
from datetime import datetime
import bcrypt
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'supersecretkey')
csrf = CSRFProtect(app)
init_db()

LOGIN_ATTEMPTS = {}

def login_rate_limited(username):
    attempts = LOGIN_ATTEMPTS.get(username, {'count': 0, 'last': None})
    if attempts['count'] >= 5 and (datetime.now() - attempts['last']).seconds < 300:
        return True
    return False

def reset_login_attempt(username):
    LOGIN_ATTEMPTS[username] = {'count': 0, 'last': None}

def increment_login_attempt(username):
    attempts = LOGIN_ATTEMPTS.get(username, {'count': 0, 'last': None})
    attempts['count'] += 1
    attempts['last'] = datetime.now()
    LOGIN_ATTEMPTS[username] = attempts

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']

        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for('register'))

        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT id FROM sqlUsers WHERE username = ?", (username,))
        if cursor.fetchone():
            flash("Username already exists.", "danger")
            return redirect(url_for('register'))

        cursor.execute("SELECT id FROM sqlUsers WHERE email = ?", (email,))
        if cursor.fetchone():
            flash("Email already registered.", "danger")
            return redirect(url_for('register'))

        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        cursor.execute(
            "INSERT INTO sqlUsers (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (username, email, password_hash, datetime.now())
        )
        db.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        if login_rate_limited(username):
            flash("Too many login attempts. Please try again later.", "danger")
            return redirect(url_for('login'))

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, password_hash FROM sqlUsers WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[1]):
            session['user_id'] = user[0]
            reset_login_attempt(username)
            return redirect(url_for('dashboard'))
        else:
            increment_login_attempt(username)
            flash("Invalid credentials.", "danger")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, title, description, priority, completed, due_date, created_at FROM Tasks WHERE user_id = ? ORDER BY due_date ASC",
        (user_id,)
    )
    tasks = cursor.fetchall()
    return render_template('dashboard.html', tasks=tasks)

@app.route('/add_task', methods=['POST'])
@login_required
@csrf.exempt
def add_task():
    title = request.form['title'].strip()
    description = request.form['description'].strip()
    priority = request.form['priority']
    due_date = request.form['due_date']

    if not title or priority not in ['High', 'Medium', 'Low']:
        flash("Title and priority are required.", "danger")
        return redirect(url_for('dashboard'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO Tasks (user_id, title, description, priority, completed, due_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (session['user_id'], title, description, priority, False, due_date, datetime.now())
    )
    db.commit()
    flash("Task added.", "success")
    return redirect(url_for('dashboard'))

@app.route('/update_task/<int:task_id>', methods=['POST'])
@login_required
@csrf.exempt
def update_task(task_id):
    title = request.form['title'].strip()
    description = request.form['description'].strip()
    priority = request.form['priority']
    due_date = request.form['due_date']
    completed = request.form.get('completed', 'off') == 'on'

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE Tasks SET title=?, description=?, priority=?, completed=?, due_date=? WHERE id=? AND user_id=?",
        (title, description, priority, completed, due_date, task_id, session['user_id'])
    )
    db.commit()
    flash("Task updated.", "success")
    return redirect(url_for('dashboard'))

@app.route('/delete_task/<int:task_id>', methods=['POST'])
@login_required
@csrf.exempt
def delete_task(task_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM Tasks WHERE id=? AND user_id=?", (task_id, session['user_id']))
    db.commit()
    flash("Task deleted.", "success")
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
