from flask import Blueprint, render_template, request, jsonify, session
from database.db import get_db
from routes.main import login_required
from datetime import date, datetime, timedelta

flashcard_bp = Blueprint('flashcard', __name__)

@flashcard_bp.route('/')
@login_required
def index():
    db = get_db()
    today = date.today().isoformat()

    decks = db.execute('''
        SELECT d.*,
               COUNT(f.id) as card_count,
               SUM(CASE WHEN f.next_review_date <= ? THEN 1 ELSE 0 END) as due_count
        FROM flashcard_decks d
        LEFT JOIN flashcards f ON d.id = f.deck_id
        WHERE d.user_id = ?
        GROUP BY d.id
        ORDER BY d.updated_at DESC
    ''', (today, session['user_id'])).fetchall()

    return render_template('flashcard/index.html', decks=decks)

@flashcard_bp.route('/create')
@login_required
def create():
    return render_template('flashcard/create.html', deck=None)

@flashcard_bp.route('/edit/<int:deck_id>')
@login_required
def edit(deck_id):
    db = get_db()
    deck = db.execute(
        'SELECT * FROM flashcard_decks WHERE id = ? AND user_id = ?',
        (deck_id, session['user_id'])
    ).fetchone()

    cards = db.execute(
        'SELECT * FROM flashcards WHERE deck_id = ? ORDER BY created_at',
        (deck_id,)
    ).fetchall()

    return render_template('flashcard/create.html', deck=deck, cards=cards)

@flashcard_bp.route('/<int:deck_id>/study')
@login_required
def study(deck_id):
    db = get_db()
    deck = db.execute('SELECT * FROM flashcard_decks WHERE id = ?', (deck_id,)).fetchone()
    return render_template('flashcard/study.html', deck=deck)

# API Routes
@flashcard_bp.route('/api/deck', methods=['POST'])
@login_required
def create_deck():
    data = request.get_json()
    db = get_db()

    cursor = db.execute('''
        INSERT INTO flashcard_decks (user_id, name, description, subject)
        VALUES (?, ?, ?, ?)
    ''', (
        session['user_id'],
        data.get('name', 'Untitled Deck'),
        data.get('description', ''),
        data.get('subject', '')
    ))
    db.commit()

    return jsonify({'id': cursor.lastrowid, 'success': True})

@flashcard_bp.route('/api/deck/<int:deck_id>', methods=['GET'])
@login_required
def get_deck(deck_id):
    db = get_db()
    deck = db.execute('SELECT * FROM flashcard_decks WHERE id = ?', (deck_id,)).fetchone()
    cards = db.execute('SELECT * FROM flashcards WHERE deck_id = ?', (deck_id,)).fetchall()

    return jsonify({
        'deck': dict(deck) if deck else None,
        'cards': [dict(c) for c in cards]
    })

@flashcard_bp.route('/api/deck/<int:deck_id>', methods=['PUT'])
@login_required
def update_deck(deck_id):
    data = request.get_json()
    db = get_db()

    db.execute('''
        UPDATE flashcard_decks SET name = ?, description = ?, subject = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
    ''', (
        data.get('name'),
        data.get('description'),
        data.get('subject'),
        deck_id,
        session['user_id']
    ))
    db.commit()

    return jsonify({'success': True})

@flashcard_bp.route('/api/deck/<int:deck_id>', methods=['DELETE'])
@login_required
def delete_deck(deck_id):
    db = get_db()
    db.execute('DELETE FROM flashcard_decks WHERE id = ? AND user_id = ?', (deck_id, session['user_id']))
    db.commit()
    return jsonify({'success': True})

@flashcard_bp.route('/api/deck/<int:deck_id>/card', methods=['POST'])
@login_required
def add_card(deck_id):
    data = request.get_json()
    db = get_db()

    cursor = db.execute('''
        INSERT INTO flashcards (deck_id, front, back)
        VALUES (?, ?, ?)
    ''', (deck_id, data.get('front'), data.get('back')))
    db.commit()

    return jsonify({'id': cursor.lastrowid, 'success': True})

@flashcard_bp.route('/api/card/<int:card_id>', methods=['PUT'])
@login_required
def update_card(card_id):
    data = request.get_json()
    db = get_db()

    db.execute('''
        UPDATE flashcards SET front = ?, back = ?
        WHERE id = ?
    ''', (data.get('front'), data.get('back'), card_id))
    db.commit()

    return jsonify({'success': True})

@flashcard_bp.route('/api/card/<int:card_id>', methods=['DELETE'])
@login_required
def delete_card(card_id):
    db = get_db()
    db.execute('DELETE FROM flashcards WHERE id = ?', (card_id,))
    db.commit()
    return jsonify({'success': True})

@flashcard_bp.route('/api/deck/<int:deck_id>/due', methods=['GET'])
@login_required
def get_due_cards(deck_id):
    db = get_db()
    today = date.today().isoformat()

    cards = db.execute('''
        SELECT * FROM flashcards
        WHERE deck_id = ? AND next_review_date <= ?
        ORDER BY next_review_date ASC
    ''', (deck_id, today)).fetchall()

    return jsonify([dict(c) for c in cards])

@flashcard_bp.route('/api/card/<int:card_id>/review', methods=['POST'])
@login_required
def review_card(card_id):
    """
    SM-2 Spaced Repetition Algorithm
    Quality: 0-5
    0-1: Complete failure
    2: Correct with difficulty
    3: Correct with hesitation
    4: Correct easily
    5: Perfect, too easy
    """
    data = request.get_json()
    quality = data.get('quality', 3)
    db = get_db()
    user_id = session['user_id']

    card = db.execute('SELECT * FROM flashcards WHERE id = ?', (card_id,)).fetchone()
    if not card:
        return jsonify({'error': 'Card not found'}), 404

    # Get current values
    ease_factor = card['ease_factor']
    interval = card['interval_days']
    repetitions = card['repetitions']

    # Apply SM-2 algorithm
    if quality < 3:
        # Failed - reset
        repetitions = 0
        interval = 1
    else:
        # Success
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = int(interval * ease_factor)

        repetitions += 1

    # Update ease factor
    ease_factor = max(1.3, ease_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))

    # Calculate next review date
    next_review = date.today() + timedelta(days=interval)

    # Update card
    db.execute('''
        UPDATE flashcards SET
            ease_factor = ?,
            interval_days = ?,
            repetitions = ?,
            next_review_date = ?,
            last_reviewed_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (ease_factor, interval, repetitions, next_review.isoformat(), card_id))

    # Log review
    db.execute('''
        INSERT INTO flashcard_reviews (flashcard_id, user_id, quality)
        VALUES (?, ?, ?)
    ''', (card_id, user_id, quality))

    # Update daily stats
    today = date.today().isoformat()
    existing = db.execute(
        'SELECT * FROM daily_stats WHERE user_id = ? AND date = ?',
        (user_id, today)
    ).fetchone()

    if existing:
        db.execute('''
            UPDATE daily_stats SET cards_reviewed = cards_reviewed + 1
            WHERE user_id = ? AND date = ?
        ''', (user_id, today))
    else:
        db.execute('''
            INSERT INTO daily_stats (user_id, date, cards_reviewed)
            VALUES (?, ?, 1)
        ''', (user_id, today))

    db.commit()

    return jsonify({
        'success': True,
        'next_review_date': next_review.isoformat(),
        'interval_days': interval
    })
