from flask import Blueprint, render_template, request, flash, url_for, redirect
from app.models import db, User, Program
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from app.core.routes import create_log, notify_class_rep


auth = Blueprint('auth', __name__)

@auth.route('/')
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            create_log("Failed Login", f"Email: {email}")
            flash('Invalid email or password.')
            return redirect(url_for('auth.login'))

        if not user.is_approved and not user.is_admin:
            create_log("Blocked Login", f"Unapproved: {user.email}")
            flash('Account pending approval by Class Rep.')
            return redirect(url_for('auth.login'))

        login_user(user)
        create_log("User Login", f"{user.full_name} logged in")
        return redirect(url_for('core.admin_dashboard' if user.is_admin else 'core.dashboard'))

    return render_template('auth/login.html')


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
            return redirect(url_for('auth.register'))

        new_user = User(
            full_name=request.form.get('fullname'),
            email=email,
            campus=request.form.get('campus'),
            program_id=request.form.get('program'),
            year=int(request.form.get('year')),
            semester=int(request.form.get('semester')),
            password_hash=generate_password_hash(request.form.get('password')),
            is_approved=False
        )

        db.session.add(new_user)
        db.session.commit()

        notify_class_rep(student=new_user, user_actions=f"{new_user.email} created an account and is waiting for your approval")
        create_log("Registration Request", f"New sign-up: {new_user.full_name}")
        flash('Registration successful! Waiting for Rep approval.')
        return redirect(url_for('auth.login'))

    programs = Program.query.all()
    return render_template('auth/register.html', programs=programs)


@auth.route('/logout')
@login_required
def logout():

    create_log("User Logout", f"{current_user.full_name} logged out")

    logout_user()
    return redirect(url_for('auth.login'))