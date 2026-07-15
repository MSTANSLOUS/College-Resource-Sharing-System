import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Secret key – use environment variable in production, fallback for local
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-12345'

    # Database – use PostgreSQL if DATABASE_URL is set, otherwise SQLite
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Render provides DATABASE_URL with 'postgres://', SQLAlchemy expects 'postgresql://'
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'database.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False