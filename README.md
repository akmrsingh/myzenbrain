# MyZenBrain

A modern study app with AI-powered quiz generation, flashcards with spaced repetition, and Pomodoro timer.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

### Pomodoro Timer
- Customizable focus and break durations
- Session tracking and statistics
- Browser notifications
- Keyboard shortcuts (Space to start/pause)

### Flashcards
- Create decks and cards
- **Spaced Repetition (SM-2 algorithm)** for optimal learning
- Flip animation study mode
- Track mastery per deck

### Quizzes
- Multiple choice, True/False, and Short answer questions
- Score tracking and history
- Explanations for correct answers

### AI Syllabus (Powered by Groq)
- Upload PDF or paste website URL
- Auto-generate quizzes (10 questions)
- Auto-generate flashcards (15 cards)
- Create study plans with Pomodoro estimates

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/akmrsingh/myzenbrain.git
cd myzenbrain
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
```bash
cp .env.example .env
```

Edit `.env` and add your Groq API key (get one free at https://console.groq.com):
```
GROQ_API_KEY=your-groq-api-key
SECRET_KEY=your-secret-key
```

### 4. Run the app
```bash
python app.py
```

Open http://localhost:5000 in your browser.

## Project Structure

```
myzenbrain/
├── app.py                 # Main Flask application
├── config.py              # Configuration and environment variables
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not in git)
├── .env.example           # Template for environment variables
│
├── database/
│   ├── db.py              # Database helpers
│   └── schema.sql         # SQLite schema
│
├── routes/
│   ├── auth.py            # Login, signup, guest mode
│   ├── main.py            # Dashboard
│   ├── pomodoro.py        # Pomodoro timer API
│   ├── quiz.py            # Quiz API
│   ├── flashcard.py       # Flashcard API
│   └── syllabus.py        # AI syllabus generation
│
├── static/
│   ├── css/style.css      # Stylesheet
│   └── js/                # JavaScript files
│
└── templates/             # HTML templates
```

## Tech Stack

- **Backend:** Python, Flask
- **Database:** SQLite
- **AI:** Groq (Llama 3.1)
- **Frontend:** HTML, CSS, JavaScript
- **Icons:** Font Awesome

## Screenshots

### Dashboard
Clean dashboard with study statistics and quick access to all modules.

### Pomodoro Timer
Focus timer with customizable durations and session tracking.

### Flashcards
Study mode with flip animation and spaced repetition ratings.

### AI Syllabus
Upload a syllabus and auto-generate study materials.

## API Endpoints

| Module | Endpoint | Method | Description |
|--------|----------|--------|-------------|
| Auth | `/login` | GET/POST | User login |
| Auth | `/signup` | GET/POST | User registration |
| Auth | `/guest` | GET | Continue as guest |
| Pomodoro | `/pomodoro/api/settings` | GET/PUT | Timer settings |
| Pomodoro | `/pomodoro/api/session` | POST | Log session |
| Quiz | `/quiz/api/quiz` | POST | Create quiz |
| Quiz | `/quiz/api/quiz/<id>/submit` | POST | Submit answers |
| Flashcard | `/flashcard/api/deck` | POST | Create deck |
| Flashcard | `/flashcard/api/card/<id>/review` | POST | Submit review |
| Syllabus | `/syllabus/api/parse` | POST | Parse PDF/URL |
| Syllabus | `/syllabus/api/generate` | POST | Generate content |

## Development Guide

### Setting Up Development Environment

```bash
# Clone the repo
git clone https://github.com/akmrsingh/myzenbrain.git
cd myzenbrain

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run in development mode
python app.py
```

### Database

The app uses SQLite. The database file (`myzenbrain.db`) is auto-created on first run.

**Reset database:**
```bash
rm myzenbrain.db
python app.py
```

**Schema location:** `database/schema.sql`

### Adding New Features

#### Adding a New Route/Module

1. Create route file in `routes/`:
```python
# routes/mymodule.py
from flask import Blueprint, render_template
from routes.main import login_required

mymodule_bp = Blueprint('mymodule', __name__)

@mymodule_bp.route('/')
@login_required
def index():
    return render_template('mymodule/index.html')
```

2. Register in `app.py`:
```python
from routes.mymodule import mymodule_bp
app.register_blueprint(mymodule_bp, url_prefix='/mymodule')
```

3. Add to navigation in `templates/base.html`

#### Adding Database Tables

1. Add table definition to `database/schema.sql`
2. Delete `myzenbrain.db` to recreate

### Code Style

- Python: Follow PEP 8
- HTML: Use Jinja2 templates, extend `base.html`
- CSS: Use CSS variables defined in `:root`
- JavaScript: Use vanilla JS, no frameworks required

### Key Files to Know

| File | Purpose |
|------|---------|
| `app.py` | App factory, blueprint registration |
| `config.py` | Environment variables, configuration |
| `database/db.py` | Database connection helpers |
| `routes/main.py` | `login_required` decorator |
| `templates/base.html` | Base template with navigation |
| `static/css/style.css` | All styles, CSS variables |

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | For AI features | Get from console.groq.com |
| `SECRET_KEY` | Recommended | Flask session secret |

### Common Tasks

**Add a new page:**
1. Create route in appropriate `routes/*.py`
2. Create template in `templates/`
3. Add navigation link in `base.html`

**Modify styles:**
- Edit `static/css/style.css`
- Use existing CSS variables for consistency

**Add API endpoint:**
- Add to appropriate route file
- Use `@login_required` decorator
- Return JSON with `jsonify()`

## Contributing

### How to Contribute

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Commit: `git commit -m "Add my feature"`
5. Push: `git push origin feature/my-feature`
6. Open a Pull Request

### Guidelines

- Keep code simple and readable
- Test your changes locally
- Update README if adding new features
- Follow existing code patterns

### Ideas for Contributions

- [ ] Add more quiz question types
- [ ] Implement study streaks
- [ ] Add dark mode toggle
- [ ] Export/import flashcard decks
- [ ] Add progress charts
- [ ] Mobile responsive improvements

## License

MIT License - feel free to use this project for learning or personal use.

---

Built with ❤️ for students everywhere
