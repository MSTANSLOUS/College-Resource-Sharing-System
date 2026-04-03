from flask import Flask
from config import Config
from app.models import db  # 👈 Grabbing the 'db' from your model file!


def create_app():
    app = Flask(__name__)

    # 1. Load the configurations from config.py
    app.config.from_object(Config)

    # 2. Link SQLAlchemy to this specific Flask app
    db.init_app(app)

    # 3. Register the Blueprints (so the web pages work)
    from app.auth.routes import auth
    app.register_blueprint(auth)
    from app.core.routes import core
    app.register_blueprint(core)

    # 4. ⚠️ THE MAGIC TRICK: This creates the tables automatically!
    with app.app_context():
        # This checks your models.py and creates the 'site.db' file with all tables
        db.create_all()

    return app