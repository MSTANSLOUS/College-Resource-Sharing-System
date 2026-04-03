import os

# Get the base directory of this folder
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Secret key for forms (we will keep it simple for now)
    SECRET_KEY = 'dev-secret-key-12345'

    # 💾 Database Setup: This creates a file called 'site.db' in your instance folder
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'site.db')

    # Stops Flask from raising warning messages
    SQLALCHEMY_TRACK_MODIFICATIONS = False