from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from database.db import get_db
from functools import wraps
from datetime import date

main_bp = Blueprint('main', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@main_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    return render_template('welcome.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    user_id = session['user_id']

    # Get today's stats
    today = date.today().isoformat()
    stats = db.execute(
        'SELECT * FROM daily_stats WHERE user_id = ? AND date = ?',
        (user_id, today)
    ).fetchone()

    # Get counts
    deck_count = db.execute(
        'SELECT COUNT(*) as count FROM flashcard_decks WHERE user_id = ?',
        (user_id,)
    ).fetchone()['count']

    quiz_count = db.execute(
        'SELECT COUNT(*) as count FROM quizzes WHERE user_id = ?',
        (user_id,)
    ).fetchone()['count']

    # Get due flashcards count
    due_cards = db.execute('''
        SELECT COUNT(*) as count FROM flashcards f
        JOIN flashcard_decks d ON f.deck_id = d.id
        WHERE d.user_id = ? AND f.next_review_date <= ?
    ''', (user_id, today)).fetchone()['count']

    return render_template('index.html',
        stats=stats,
        deck_count=deck_count,
        quiz_count=quiz_count,
        due_cards=due_cards
    )

@main_bp.route('/api/stats/daily')
@login_required
def daily_stats():
    db = get_db()
    user_id = session['user_id']
    today = date.today().isoformat()

    stats = db.execute(
        'SELECT * FROM daily_stats WHERE user_id = ? AND date = ?',
        (user_id, today)
    ).fetchone()

    if stats:
        return jsonify(dict(stats))
    return jsonify({
        'pomodoro_count': 0,
        'focus_minutes': 0,
        'cards_reviewed': 0,
        'quizzes_taken': 0
    })
