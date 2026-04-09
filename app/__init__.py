from flask import Flask

from config import Config

from app.models import db, User, Program

from flask_login import LoginManager

from werkzeug.security import generate_password_hash

from flask_mail import Mail

from flask_cors import CORS # Import this

# Initialize LoginManager globally outside the function
login_manager = LoginManager()

# Initialize Mail
mail = Mail()

def create_app():
    # 1. Create the app instance inside the factory
    app = Flask(__name__)

    # Add these lines to your Flask config
    app.config.update(
        SESSION_COOKIE_SAMESITE="None",  # Allows cookie to be sent across different origins
        SESSION_COOKIE_SECURE=True,  # Required when SameSite is "None"
        REMEMBER_COOKIE_SAMESITE="None",
        REMEMBER_COOKIE_SECURE=True
    )

    # This allows your Android app to communicate with your Ngrok link
    # supports_credentials=True is needed so the session cookie works
    CORS(app, supports_credentials=True)

    # 2. Load the configurations from config.py and mail
    app.config.from_object(Config)
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'musayalous@gmail.com'
    app.config['MAIL_PASSWORD'] = 'hoexnlwpoecigkbf'

    mail.init_app(app=app)


    # 3. Link SQLAlchemy and LoginManager to this specific Flask app
    db.init_app(app)
    login_manager.init_app(app=app)

    # Tell Flask-Login where to redirect users who aren't logged in
    login_manager.login_view = 'auth.login'

    # 4. Register the Blueprints (so the web pages work)
    from app.auth.routes import auth
    app.register_blueprint(blueprint=auth)

    from app.core.routes import core
    app.register_blueprint(blueprint=core)

    # 5. Global variable injection for Jinja
    @app.context_processor
    def inject_user():
        from flask_login import current_user
        return dict(current_user=current_user)

    # 6. Create the tables and seed default data automatically
    # (Fixed the indentation here so it lines up with the rest of the function)
    with app.app_context():
        db.create_all()

        # 1. SEED YOUR ACTUAL PROGRAMS FIRST
        programs_list = ['BMIS', 'BBME', 'BAAA-IS', 'BMPR', 'BBFSM']
        for prog_name in programs_list:
            exists = Program.query.filter_by(name=prog_name).first()
            if not exists:
                new_prog = Program(name=prog_name)
                db.session.add(new_prog)

        # Save the programs so we can grab one for the admin!
        db.session.commit()

        # 2. NOW CREATE THE SUPER ADMIN
        admin = User.query.filter_by(is_admin=True).first()

        if not admin:
            # Grab the BMIS program we just created to keep the database happy!
            bmis_program = Program.query.filter_by(name='BMIS').first()

            print("No Super Admin found. Creating one now...")
            super_user = User(
                full_name="System Super Admin",
                email="admin@gmail.com",
                # Upgraded to secure hash instead of plain text "admin"
                password_hash=generate_password_hash("admin"),
                is_admin=True,
                is_approved=True,
                is_class_rep=False,
                campus="System",
                program_id=bmis_program.id
            )
            db.session.add(super_user)
            db.session.commit()
            print("Super Admin created successfully!")

    return app


# CRITICAL: This function tells Flask-Login how to load a user from the database by ID
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))