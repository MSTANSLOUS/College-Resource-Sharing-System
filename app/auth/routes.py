from flask import Blueprint, render_template, request, flash, url_for, redirect
from app.models import db, User, Program
from flask_login import login_user, current_user, logout_user, login_required

# 1. Create the Blueprint for Auth
auth = Blueprint('auth', __name__)

# 2. The Login Route
@auth.route('/', methods=['GET', 'POST'])
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Find the user by email
        user = User.query.filter_by(email=email).first()

        # Check if user exists and password matches
        if not user or user.password_hash != password:
            flash('Invalid email or password.')
            return redirect(url_for('auth.login'))

        # Check if the user has been approved by a Class Rep
        if not user.is_approved:
            flash('Your account is still pending approval by your Class Representative.')
            return redirect(url_for('auth.login'))

        # Log them in via Flask-Login
        login_user(user)
        flash('Successfully logged in!')

        # FIX: Everyone goes straight to the unified dashboard now!
        return redirect(url_for('core.dashboard'))

    # If GET, just show the login page
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
            password_hash=password,
            is_approved=False,
            is_class_rep=False
        )

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Your request has been forwarded to your class rep for approval.')
        return redirect(url_for('auth.login'))

    programs = Program.query.all()
    return render_template('auth/register.html', programs=programs)


@auth.route('/logout')
@login_required  # Keeps non-logged-in users from randomly hitting this endpoint
def logout():
    # 1. This kills the Flask-Login session cookie
    logout_user()

    flash('You have been logged out successfully.')

    # 2. Kick them back to the login page
    return redirect(url_for('auth.login'))