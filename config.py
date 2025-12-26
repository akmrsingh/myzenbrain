import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'myzenbrain-secret-key-change-in-production'
    DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'myzenbrain.db')
