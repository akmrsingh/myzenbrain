from flask import Blueprint, render_template, request, jsonify, session
from database.db import get_db
from routes.main import login_required
from datetime import date, datetime

pomodoro_bp = Blueprint('pomodoro', __name__)

@pomodoro_bp.route('/')
@login_required
def index():
    return render_template('pomodoro.html')

@pomodoro_bp.route('/api/settings', methods=['GET'])
@login_required
def get_settings():
    db = get_db()
    settings = db.execute(
        'SELECT * FROM pomodoro_settings WHERE user_id = ?',
        (session['user_id'],)
    ).fetchone()

    if settings:
        return jsonify({
            'focus_duration': settings['focus_duration'],
            'short_break_duration': settings['short_break_duration'],
            'long_break_duration': settings['long_break_duration'],
            'sessions_until_long_break': settings['sessions_until_long_break'],
            'auto_start_breaks': bool(settings['auto_start_breaks']),
            'auto_start_focus': bool(settings['auto_start_focus']),
            'sound_enabled': bool(settings['sound_enabled'])
        })

    return jsonify({
        'focus_duration': 25,
        'short_break_duration': 5,
        'long_break_duration': 15,
        'sessions_until_long_break': 4,
        'auto_start_breaks': False,
        'auto_start_focus': False,
        'sound_enabled': True
    })

@pomodoro_bp.route('/api/settings', methods=['PUT'])
@login_required
def update_settings():
    data = request.get_json()
    db = get_db()

    db.execute('''
        UPDATE pomodoro_settings SET
            focus_duration = ?,
            short_break_duration = ?,
            long_break_duration = ?,
            sessions_until_long_break = ?,
            auto_start_breaks = ?,
            auto_start_focus = ?,
            sound_enabled = ?
        WHERE user_id = ?
    ''', (
        data.get('focus_duration', 25),
        data.get('short_break_duration', 5),
        data.get('long_break_duration', 15),
        data.get('sessions_until_long_break', 4),
        data.get('auto_start_breaks', False),
        data.get('auto_start_focus', False),
        data.get('sound_enabled', True),
        session['user_id']
    ))
    db.commit()

    return jsonify({'success': True})

@pomodoro_bp.route('/api/session', methods=['POST'])
@login_required
def log_session():
    data = request.get_json()
    db = get_db()
    user_id = session['user_id']

    # Log the session
    db.execute('''
        INSERT INTO pomodoro_sessions (user_id, session_type, duration_minutes, notes)
        VALUES (?, ?, ?, ?)
    ''', (
        user_id,
        data.get('session_type', 'focus'),
        data.get('duration_minutes', 25),
        data.get('notes', '')
    ))

    # Update daily stats
    today = date.today().isoformat()
    existing = db.execute(
        'SELECT * FROM daily_stats WHERE user_id = ? AND date = ?',
        (user_id, today)
    ).fetchone()

    if existing:
        if data.get('session_type') == 'focus':
            db.execute('''
                UPDATE daily_stats SET
                    pomodoro_count = pomodoro_count + 1,
                    focus_minutes = focus_minutes + ?
                WHERE user_id = ? AND date = ?
            ''', (data.get('duration_minutes', 25), user_id, today))
    else:
        focus_mins = data.get('duration_minutes', 25) if data.get('session_type') == 'focus' else 0
        pomo_count = 1 if data.get('session_type') == 'focus' else 0
        db.execute('''
            INSERT INTO daily_stats (user_id, date, pomodoro_count, focus_minutes)
            VALUES (?, ?, ?, ?)
        ''', (user_id, today, pomo_count, focus_mins))

    db.commit()

    return jsonify({'success': True})

@pomodoro_bp.route('/api/sessions', methods=['GET'])
@login_required
def get_sessions():
    db = get_db()
    sessions_list = db.execute('''
        SELECT * FROM pomodoro_sessions
        WHERE user_id = ?
        ORDER BY completed_at DESC
        LIMIT 20
    ''', (session['user_id'],)).fetchall()

    return jsonify([dict(s) for s in sessions_list])
