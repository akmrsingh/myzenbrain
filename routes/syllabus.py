from flask import Blueprint, render_template, request, jsonify, session, current_app
from database.db import get_db
from routes.main import login_required
from datetime import date, datetime
import os
import json
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from io import BytesIO

syllabus_bp = Blueprint('syllabus', __name__)

# Initialize Groq client
def get_groq_client():
    try:
        from groq import Groq
        api_key = os.environ.get('GROQ_API_KEY')
        if api_key:
            return Groq(api_key=api_key)
    except Exception as e:
        print(f"Groq init error: {e}")
    return None

@syllabus_bp.route('/')
@login_required
def index():
    db = get_db()
    syllabi = db.execute('''
        SELECT * FROM syllabi WHERE user_id = ? ORDER BY created_at DESC
    ''', (session['user_id'],)).fetchall()

    return render_template('syllabus/index.html', syllabi=syllabi)

@syllabus_bp.route('/create')
@login_required
def create():
    return render_template('syllabus/create.html')

@syllabus_bp.route('/api/parse', methods=['POST'])
@login_required
def parse_syllabus():
    """Parse syllabus from PDF or URL"""
    content = ""
    source_type = request.form.get('source_type', 'text')

    try:
        if source_type == 'pdf' and 'pdf_file' in request.files:
            pdf_file = request.files['pdf_file']
            if pdf_file.filename:
                pdf_reader = PdfReader(BytesIO(pdf_file.read()))
                for page in pdf_reader.pages:
                    content += page.extract_text() or ""

        elif source_type == 'url':
            url = request.form.get('url', '')
            if url:
                headers = {'User-Agent': 'Mozilla/5.0 (compatible; MyZenBrain/1.0)'}
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')

                # Remove scripts and styles
                for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                    tag.decompose()

                content = soup.get_text(separator='\n', strip=True)

        elif source_type == 'text':
            content = request.form.get('text_content', '')

        if not content.strip():
            return jsonify({'error': 'No content extracted'}), 400

        # Limit content length
        content = content[:15000]

        return jsonify({'success': True, 'content': content, 'length': len(content)})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@syllabus_bp.route('/api/generate', methods=['POST'])
@login_required
def generate_content():
    """Generate quizzes and study plan from syllabus using Groq"""
    data = request.get_json()
    syllabus_content = data.get('content', '')
    syllabus_name = data.get('name', 'My Syllabus')
    generate_type = data.get('type', 'all')  # 'quizzes', 'flashcards', 'plan', 'all'

    if not syllabus_content:
        return jsonify({'error': 'No syllabus content provided'}), 400

    client = get_groq_client()
    if not client:
        return jsonify({'error': 'Groq API key not configured. Set GROQ_API_KEY environment variable.'}), 400

    db = get_db()
    user_id = session['user_id']
    results = {'quizzes': [], 'flashcards': [], 'study_plan': None}

    try:
        # Save syllabus first
        cursor = db.execute('''
            INSERT INTO syllabi (user_id, name, content) VALUES (?, ?, ?)
        ''', (user_id, syllabus_name, syllabus_content[:5000]))
        syllabus_id = cursor.lastrowid
        db.commit()

        # Generate quizzes
        if generate_type in ['quizzes', 'all']:
            quiz_prompt = f"""Based on this syllabus/course content, generate 10 quiz questions.

SYLLABUS CONTENT:
{syllabus_content[:8000]}

Return ONLY a valid JSON array with this exact format (no markdown, no explanation):
[
  {{
    "question": "What is...?",
    "type": "multiple_choice",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option A",
    "explanation": "Brief explanation why this is correct"
  }}
]

Include a mix of multiple_choice and true_false questions. For true_false, options should be ["True", "False"]."""

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": quiz_prompt}],
                temperature=0.7,
                max_tokens=3000
            )

            quiz_text = response.choices[0].message.content.strip()
            # Clean up response
            if quiz_text.startswith('```'):
                quiz_text = quiz_text.split('```')[1]
                if quiz_text.startswith('json'):
                    quiz_text = quiz_text[4:]

            try:
                questions = json.loads(quiz_text)

                # Create quiz in database
                cursor = db.execute('''
                    INSERT INTO quizzes (user_id, title, description, subject)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, f"{syllabus_name} - Quiz", f"Auto-generated from syllabus", syllabus_name))
                quiz_id = cursor.lastrowid

                for i, q in enumerate(questions[:10]):
                    q_type = q.get('type', 'multiple_choice')
                    if q_type == 'true_false':
                        q_type = 'true_false'
                    else:
                        q_type = 'multiple_choice'

                    db.execute('''
                        INSERT INTO quiz_questions (quiz_id, question_text, question_type, correct_answer, options, explanation, order_num)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        quiz_id,
                        q.get('question', ''),
                        q_type,
                        q.get('correct_answer', ''),
                        json.dumps(q.get('options', [])),
                        q.get('explanation', ''),
                        i + 1
                    ))

                db.commit()
                results['quizzes'].append({'id': quiz_id, 'title': f"{syllabus_name} - Quiz", 'question_count': len(questions)})

            except json.JSONDecodeError:
                pass

        # Generate flashcards
        if generate_type in ['flashcards', 'all']:
            flashcard_prompt = f"""Based on this syllabus/course content, generate 15 flashcards for key terms and concepts.

SYLLABUS CONTENT:
{syllabus_content[:8000]}

Return ONLY a valid JSON array with this exact format (no markdown, no explanation):
[
  {{
    "front": "Term or question",
    "back": "Definition or answer"
  }}
]"""

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": flashcard_prompt}],
                temperature=0.7,
                max_tokens=2000
            )

            flashcard_text = response.choices[0].message.content.strip()
            if flashcard_text.startswith('```'):
                flashcard_text = flashcard_text.split('```')[1]
                if flashcard_text.startswith('json'):
                    flashcard_text = flashcard_text[4:]

            try:
                cards = json.loads(flashcard_text)

                # Create deck in database
                cursor = db.execute('''
                    INSERT INTO flashcard_decks (user_id, name, description, subject)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, f"{syllabus_name} - Flashcards", "Auto-generated from syllabus", syllabus_name))
                deck_id = cursor.lastrowid

                for card in cards[:15]:
                    db.execute('''
                        INSERT INTO flashcards (deck_id, front, back)
                        VALUES (?, ?, ?)
                    ''', (deck_id, card.get('front', ''), card.get('back', '')))

                db.commit()
                results['flashcards'].append({'id': deck_id, 'name': f"{syllabus_name} - Flashcards", 'card_count': len(cards)})

            except json.JSONDecodeError:
                pass

        # Generate study plan
        if generate_type in ['plan', 'all']:
            plan_prompt = f"""Based on this syllabus, create a study plan with topics and recommended Pomodoro sessions.

SYLLABUS CONTENT:
{syllabus_content[:6000]}

Return ONLY a valid JSON object with this format (no markdown):
{{
  "topics": [
    {{
      "name": "Topic Name",
      "description": "Brief description",
      "estimated_pomodoros": 4,
      "priority": "high"
    }}
  ],
  "total_study_hours": 20,
  "recommended_daily_pomodoros": 4
}}"""

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": plan_prompt}],
                temperature=0.7,
                max_tokens=1500
            )

            plan_text = response.choices[0].message.content.strip()
            if plan_text.startswith('```'):
                plan_text = plan_text.split('```')[1]
                if plan_text.startswith('json'):
                    plan_text = plan_text[4:]

            try:
                study_plan = json.loads(plan_text)
                results['study_plan'] = study_plan

                # Save study plan to syllabus record
                db.execute('''
                    UPDATE syllabi SET study_plan = ? WHERE id = ?
                ''', (json.dumps(study_plan), syllabus_id))
                db.commit()

            except json.JSONDecodeError:
                pass

        return jsonify({
            'success': True,
            'syllabus_id': syllabus_id,
            'results': results
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@syllabus_bp.route('/<int:syllabus_id>')
@login_required
def view(syllabus_id):
    db = get_db()
    syllabus = db.execute(
        'SELECT * FROM syllabi WHERE id = ? AND user_id = ?',
        (syllabus_id, session['user_id'])
    ).fetchone()

    if not syllabus:
        return redirect(url_for('syllabus.index'))

    study_plan = None
    if syllabus['study_plan']:
        try:
            study_plan = json.loads(syllabus['study_plan'])
        except:
            pass

    return render_template('syllabus/view.html', syllabus=syllabus, study_plan=study_plan)

@syllabus_bp.route('/api/syllabus/<int:syllabus_id>', methods=['DELETE'])
@login_required
def delete_syllabus(syllabus_id):
    db = get_db()
    db.execute('DELETE FROM syllabi WHERE id = ? AND user_id = ?', (syllabus_id, session['user_id']))
    db.commit()
    return jsonify({'success': True})
