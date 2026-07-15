from datetime import datetime

from flask import Flask
from config import Config
from app.models import db, User, Program
from flask_login import LoginManager, current_user
from werkzeug.security import generate_password_hash
from flask_mail import Mail, Message
from flask_cors import CORS
from flask_socketio import SocketIO, join_room

login_manager = LoginManager()
mail = Mail()
socketio = SocketIO()

def send_email(recipients, subject, massage_body):
    msg = Message(
        subject=subject,
        sender='musayalous@gmail.com',
        recipients=[recipients],
        body=massage_body,
    )
    mail.send(msg)

def create_app():
    app = Flask(__name__)

    # Config
    app.config.update(
        SESSION_COOKIE_SAMESITE="None",
        SESSION_COOKIE_SECURE=True,
        REMEMBER_COOKIE_SAMESITE="None",
        REMEMBER_COOKIE_SECURE=True
    )
    CORS(app, supports_credentials=True)

    app.config.from_object(Config)
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'musayalous@gmail.com'
    app.config['MAIL_PASSWORD'] = 'etvkgbgnmecmcjgs'

    mail.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # SocketIO with eventlet
    socketio.init_app(app, cors_allowed_origins="*", async_mode='gevent')

    # Blueprints
    from app.auth.routes import auth
    app.register_blueprint(auth)
    from app.core.routes import core
    app.register_blueprint(core)

    @app.context_processor
    def inject_user():
        from flask_login import current_user
        return dict(current_user=current_user)

    @app.after_request
    def add_ngrok_headers(response):
        response.headers['ngrok-skip-browser-warning'] = 'true'
        return response
    

    @app.before_request
    def update_last_activity():
        if current_user.is_authenticated:
            current_user.last_activity = datetime.utcnow()
            db.session.commit()
            

    # ─── SocketIO Connection Handler ───
    @socketio.on('connect')
    def handle_connect(auth=None):
        if current_user.is_authenticated:
            # Student room: for their specific class (program, year, semester)
            join_room(f'student-{current_user.program_id}-{current_user.year}-{current_user.semester}')
            # Admin room
            if current_user.is_admin:
                join_room('admin')
            # Class rep room
            if current_user.is_class_rep:
                join_room(f'rep-{current_user.program_id}-{current_user.year}-{current_user.semester}')
            # Personal room
            join_room(f'user-{current_user.id}')

    # ─── Database seeding ───
    with app.app_context():
        db.create_all()
        programs_list = ['BMIS', 'BBME', 'BAAA-IS', 'BMPR', 'BBFSM']
        for prog_name in programs_list:
            exists = Program.query.filter_by(name=prog_name).first()
            if not exists:
                new_prog = Program(name=prog_name)
                db.session.add(new_prog)
        db.session.commit()

        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            bmis_program = Program.query.filter_by(name='BMIS').first()
            super_user = User(
                full_name="System Super Admin",
                email="admin@gmail.com",
                password_hash=generate_password_hash("admin", method='pbkdf2:sha256'),
                is_admin=True,
                is_approved=True,
                is_class_rep=False,
                campus="System",
                program_id=bmis_program.id
            )
            db.session.add(super_user)
            db.session.commit()

    return app

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


