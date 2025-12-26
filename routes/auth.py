from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db
import uuid

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_guest'] = False
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')

        db = get_db()

        # Check if username exists
        existing = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if existing:
            flash('Username already exists', 'error')
            return render_template('signup.html')

        # Create user
        password_hash = generate_password_hash(password)
        cursor = db.execute(
            'INSERT INTO users (username, email, password_hash, is_guest) VALUES (?, ?, ?, 0)',
            (username, email, password_hash)
        )
        db.commit()

        # Create default pomodoro settings
        db.execute(
            'INSERT INTO pomodoro_settings (user_id) VALUES (?)',
            (cursor.lastrowid,)
        )
        db.commit()

        session['user_id'] = cursor.lastrowid
        session['username'] = username
        session['is_guest'] = False

        return redirect(url_for('main.dashboard'))

    return render_template('signup.html')

@auth_bp.route('/guest')
def guest():
    # Create a temporary guest user
    guest_name = f"Guest_{uuid.uuid4().hex[:8]}"

    db = get_db()
    cursor = db.execute(
        'INSERT INTO users (username, is_guest) VALUES (?, 1)',
        (guest_name,)
    )
    db.commit()

    # Create default pomodoro settings
    db.execute(
        'INSERT INTO pomodoro_settings (user_id) VALUES (?)',
        (cursor.lastrowid,)
    )
    db.commit()

    session['user_id'] = cursor.lastrowid
    session['username'] = guest_name
    session['is_guest'] = True

    return redirect(url_for('main.dashboard'))

@auth_bp.route('/logout')
def logout():
    # If guest, delete their data
    if session.get('is_guest'):
        db = get_db()
        db.execute('DELETE FROM users WHERE id = ?', (session.get('user_id'),))
        db.commit()

    session.clear()
    return redirect(url_for('auth.login'))
