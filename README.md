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

## License

MIT License - feel free to use this project for learning or personal use.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

---

Built with ❤️ for students everywhere
