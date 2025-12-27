from flask import Blueprint, render_template, request, jsonify, session
from database.db import get_db
from routes.main import login_required
from datetime import date, datetime
import json

quiz_bp = Blueprint('quiz', __name__)

@quiz_bp.route('/')
@login_required
def index():
    db = get_db()
    quizzes = db.execute('''
        SELECT q.*, COUNT(qq.id) as question_count,
               (SELECT MAX(percentage) FROM quiz_attempts WHERE quiz_id = q.id) as best_score
        FROM quizzes q
        LEFT JOIN quiz_questions qq ON q.id = qq.quiz_id
        WHERE q.user_id = ?
        GROUP BY q.id
        ORDER BY q.updated_at DESC
    ''', (session['user_id'],)).fetchall()

    return render_template('quiz/index.html', quizzes=quizzes)

@quiz_bp.route('/create')
@login_required
def create():
    return render_template('quiz/create.html', quiz=None)

@quiz_bp.route('/edit/<int:quiz_id>')
@login_required
def edit(quiz_id):
    db = get_db()
    quiz = db.execute(
        'SELECT * FROM quizzes WHERE id = ? AND user_id = ?',
        (quiz_id, session['user_id'])
    ).fetchone()

    if not quiz:
        return redirect(url_for('quiz.index'))

    questions = db.execute(
        'SELECT * FROM quiz_questions WHERE quiz_id = ? ORDER BY order_num',
        (quiz_id,)
    ).fetchall()

    return render_template('quiz/create.html', quiz=quiz, questions=questions)

@quiz_bp.route('/<int:quiz_id>/take')
@login_required
def take(quiz_id):
    db = get_db()
    quiz = db.execute('SELECT * FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
    questions_raw = db.execute(
        'SELECT * FROM quiz_questions WHERE quiz_id = ? ORDER BY order_num',
        (quiz_id,)
    ).fetchall()

    # Parse options JSON for each question
    questions = []
    for q in questions_raw:
        q_dict = dict(q)
        try:
            q_dict['options_list'] = json.loads(q['options']) if q['options'] else []
        except:
            q_dict['options_list'] = []
        questions.append(q_dict)

    return render_template('quiz/take.html', quiz=quiz, questions=questions)

# API Routes
@quiz_bp.route('/api/quiz', methods=['POST'])
@login_required
def create_quiz():
    data = request.get_json()
    db = get_db()

    cursor = db.execute('''
        INSERT INTO quizzes (user_id, title, description, subject)
        VALUES (?, ?, ?, ?)
    ''', (
        session['user_id'],
        data.get('title', 'Untitled Quiz'),
        data.get('description', ''),
        data.get('subject', '')
    ))
    db.commit()

    return jsonify({'id': cursor.lastrowid, 'success': True})

@quiz_bp.route('/api/quiz/<int:quiz_id>', methods=['GET'])
@login_required
def get_quiz(quiz_id):
    db = get_db()
    quiz = db.execute('SELECT * FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
    questions = db.execute(
        'SELECT * FROM quiz_questions WHERE quiz_id = ? ORDER BY order_num',
        (quiz_id,)
    ).fetchall()

    return jsonify({
        'quiz': dict(quiz) if quiz else None,
        'questions': [dict(q) for q in questions]
    })

@quiz_bp.route('/api/quiz/<int:quiz_id>', methods=['PUT'])
@login_required
def update_quiz(quiz_id):
    data = request.get_json()
    db = get_db()

    db.execute('''
        UPDATE quizzes SET title = ?, description = ?, subject = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
    ''', (
        data.get('title'),
        data.get('description'),
        data.get('subject'),
        quiz_id,
        session['user_id']
    ))
    db.commit()

    return jsonify({'success': True})

@quiz_bp.route('/api/quiz/<int:quiz_id>', methods=['DELETE'])
@login_required
def delete_quiz(quiz_id):
    db = get_db()
    db.execute('DELETE FROM quizzes WHERE id = ? AND user_id = ?', (quiz_id, session['user_id']))
    db.commit()
    return jsonify({'success': True})

@quiz_bp.route('/api/quiz/<int:quiz_id>/question', methods=['POST'])
@login_required
def add_question(quiz_id):
    data = request.get_json()
    db = get_db()

    # Get next order number
    max_order = db.execute(
        'SELECT MAX(order_num) as max_order FROM quiz_questions WHERE quiz_id = ?',
        (quiz_id,)
    ).fetchone()['max_order'] or 0

    cursor = db.execute('''
        INSERT INTO quiz_questions (quiz_id, question_text, question_type, correct_answer, options, explanation, points, order_num)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        quiz_id,
        data.get('question_text'),
        data.get('question_type', 'multiple_choice'),
        data.get('correct_answer'),
        json.dumps(data.get('options', [])),
        data.get('explanation', ''),
        data.get('points', 1),
        max_order + 1
    ))
    db.commit()

    return jsonify({'id': cursor.lastrowid, 'success': True})

@quiz_bp.route('/api/question/<int:question_id>', methods=['PUT'])
@login_required
def update_question(question_id):
    data = request.get_json()
    db = get_db()

    db.execute('''
        UPDATE quiz_questions SET
            question_text = ?,
            question_type = ?,
            correct_answer = ?,
            options = ?,
            explanation = ?,
            points = ?
        WHERE id = ?
    ''', (
        data.get('question_text'),
        data.get('question_type'),
        data.get('correct_answer'),
        json.dumps(data.get('options', [])),
        data.get('explanation', ''),
        data.get('points', 1),
        question_id
    ))
    db.commit()

    return jsonify({'success': True})

@quiz_bp.route('/api/question/<int:question_id>', methods=['DELETE'])
@login_required
def delete_question(question_id):
    db = get_db()
    db.execute('DELETE FROM quiz_questions WHERE id = ?', (question_id,))
    db.commit()
    return jsonify({'success': True})

@quiz_bp.route('/api/quiz/<int:quiz_id>/submit', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    data = request.get_json()
    answers = data.get('answers', {})
    time_taken = data.get('time_taken', 0)

    db = get_db()
    questions = db.execute(
        'SELECT * FROM quiz_questions WHERE quiz_id = ?',
        (quiz_id,)
    ).fetchall()

    score = 0
    total_points = 0
    results = []

    for q in questions:
        total_points += q['points']
        user_answer = answers.get(str(q['id']), '').strip().lower()
        correct_answer = q['correct_answer'].strip().lower()

        is_correct = user_answer == correct_answer

        if is_correct:
            score += q['points']

        results.append({
            'question_id': q['id'],
            'correct': is_correct,
            'user_answer': answers.get(str(q['id']), ''),
            'correct_answer': q['correct_answer'],
            'explanation': q['explanation']
        })

    percentage = (score / total_points * 100) if total_points > 0 else 0

    # Save attempt
    db.execute('''
        INSERT INTO quiz_attempts (quiz_id, user_id, score, total_points, percentage, time_taken_seconds, answers)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        quiz_id,
        session['user_id'],
        score,
        total_points,
        percentage,
        time_taken,
        json.dumps(answers)
    ))

    # Update daily stats
    today = date.today().isoformat()
    user_id = session['user_id']

    existing = db.execute(
        'SELECT * FROM daily_stats WHERE user_id = ? AND date = ?',
        (user_id, today)
    ).fetchone()

    if existing:
        new_avg = ((existing['average_quiz_score'] * existing['quizzes_taken']) + percentage) / (existing['quizzes_taken'] + 1)
        db.execute('''
            UPDATE daily_stats SET quizzes_taken = quizzes_taken + 1, average_quiz_score = ?
            WHERE user_id = ? AND date = ?
        ''', (new_avg, user_id, today))
    else:
        db.execute('''
            INSERT INTO daily_stats (user_id, date, quizzes_taken, average_quiz_score)
            VALUES (?, ?, 1, ?)
        ''', (user_id, today, percentage))

    db.commit()

    return jsonify({
        'score': score,
        'total_points': total_points,
        'percentage': percentage,
        'results': results
    })
