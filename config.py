import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'myzenbrain-secret-key-change-in-production'
    DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'myzenbrain.db')
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
