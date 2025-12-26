from flask import Flask
from config import Config
from database.db import init_app, init_db, get_db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize database
    init_app(app)

    with app.app_context():
        init_db()

    # Register blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.pomodoro import pomodoro_bp
    from routes.quiz import quiz_bp
    from routes.flashcard import flashcard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(pomodoro_bp, url_prefix='/pomodoro')
    app.register_blueprint(quiz_bp, url_prefix='/quiz')
    app.register_blueprint(flashcard_bp, url_prefix='/flashcard')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
