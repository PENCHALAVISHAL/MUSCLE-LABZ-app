import os
from dotenv import load_dotenv

load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_super_secret_key_change_in_production'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'fitness_tracker.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'fitness_tracker.db')

class ProductionConfig(Config):
    DEBUG = False
    # PostgreSQL for production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 