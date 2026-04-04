from flask import Blueprint, render_template, request, flash, url_for, redirect
from app.models import db, User, Program
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash

# 1. IMPORT THE LOGGER FROM CORE!
from app.core.routes import create_log

# Create the Blueprint for Auth
auth = Blueprint('auth', __name__)


# 2. The Login Route
@auth.route('/', methods=['GET', 'POST'])
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        # Check if user exists and securely check the password hash
        if not user or not check_password_hash(user.password_hash, password):
            # 📝 LOG: Failed Login Attempt
            # (No user_id since they failed, details will store the email attempted)
            create_log("Failed Login", f"Failed attempt with email: {email}")

            flash('Invalid email or password.')
            return redirect(url_for('auth.login'))

        # Security Wall: Check if approved
        if not user.is_approved and not user.is_admin:
            # 📝 LOG: Blocked unapproved user
            create_log("Blocked Login", f"Unapproved user tried to log in: {user.email}")

            flash('Your account is still pending approval by your Class Representative.')
            return redirect(url_for('auth.login'))

        # Log them in via Flask-Login
        login_user(user)

        # 📝 LOG: Successful Login
        create_log("User Login", f"{user.full_name} logged in successfully")

        flash('Successfully logged in!')

        # REDIRECT PROTOCOL
        if user.is_admin:
            return redirect(url_for('core.admin_dashboard'))

        return redirect(url_for('core.dashboard'))

    return render_template('auth/login.html')


# The register route
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        campus = request.form.get('campus')
        program_id = request.form.get('program')
        password = request.form.get('password')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Gmail address is already registered.')
            return redirect(url_for('auth.register'))

        new_user = User(
            full_name=fullname,
            email=email,
            campus=campus,
            program_id=program_id,
            password_hash=generate_password_hash(password),
            is_approved=False,
            is_class_rep=False
        )

        db.session.add(new_user)
        db.session.commit()

        # 📝 LOG: New Registration Request
        # (Using new_user.id since commit just generated it!)
        create_log("Registration Request", f"New sign-up request from: {fullname} ({email})")

        flash('Registration successful! Your request has been forwarded to your class rep for approval.')
        return redirect(url_for('auth.login'))

    programs = Program.query.all()
    return render_template('auth/register.html', programs=programs)


@auth.route('/logout')
@login_required
def logout():
    # Grab name before we kill the session
    user_name = current_user.full_name

    # 📝 LOG: Logout
    create_log("User Logout", f"{user_name} logged out")

    logout_user()
    flash('You have been logged out successfully.')
    return redirect(url_for('auth.login'))