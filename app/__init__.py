from flask import Flask
from config import Config
from app.models import db
from flask_login import LoginManager
from app.models import User

# Initialize LoginManager globally outside the function
login_manager = LoginManager()


def create_app():
    # 1. Create the app instance inside the factory
    app = Flask(__name__)

    # 2. Load the configurations from config.py
    app.config.from_object(Config)

    # 3. Link SQLAlchemy and LoginManager to this specific Flask app
    db.init_app(app)
    login_manager.init_app(app)  # 👈 THIS WAS THE MISSING LINK!

    # Tell Flask-Login where to redirect users who aren't logged in
    login_manager.login_view = 'auth.login'

    # 4. Register the Blueprints (so the web pages work)
    from app.auth.routes import auth
    app.register_blueprint(auth)

    from app.core.routes import core
    app.register_blueprint(core)

    # 5. Global variable injection for Jinja
    @app.context_processor
    def inject_user():
        from flask_login import current_user
        return dict(current_user=current_user)

    # 6. Create the tables automatically
    with app.app_context():
        db.create_all()

    return app


# CRITICAL: This function tells Flask-Login how to load a user from the database by ID
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))