from flask import Blueprint, render_template, request, flash, url_for, redirect, jsonify
from app.models import db, User, Program
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from app.core.routes import create_log, notify_class_rep
from app import socketio  # <-- Import socketio

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

        if not user.is_active:
            create_log("Blocked Login", f"Deactivated: {user.email}")
            flash('Your account has been deactivated. Contact admin.', 'error')
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

        # ─── SocketIO Events ───
        # Notify all admins
        socketio.emit('new_user_registered', {
            'user_id': new_user.id,
            'full_name': new_user.full_name,
            'email': new_user.email,
            'campus': new_user.campus,
            'program': new_user.program.name,
            'year': new_user.year,
            'semester': new_user.semester,
            'is_approved': new_user.is_approved
        }, room='admin')

        # Notify the class rep room for this specific class
        rep_room = f'rep-{new_user.program_id}-{new_user.year}-{new_user.semester}'
        socketio.emit('new_pending_approval', {
            'user_id': new_user.id,
            'full_name': new_user.full_name,
            'email': new_user.email,
            'campus': new_user.campus,
            'year': new_user.year,
            'semester': new_user.semester
        }, room=rep_room)

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


@auth.route('/api/check-email', methods=['POST'])
def check_email():
    data = request.get_json()
    email = data.get('email', '').strip()
    if not email:
        return jsonify({'valid': False, 'message': 'Email is required.'})
    if not email.endswith('@gmail.com') or '@' not in email:
        return jsonify({'valid': False, 'message': 'Please use a valid Gmail address.'})
    exists = User.query.filter_by(email=email).first() is not None
    if exists:
        return jsonify({'valid': False, 'message': 'This email is already registered.'})
    return jsonify({'valid': True, 'message': 'Email is available.'})


@auth.route('/api/user-status', methods=['POST'])
def user_status():
    data = request.get_json()
    email = data.get('email', '').strip()
    if not email:
        return jsonify({'exists': False, 'message': 'Email required.'})
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'exists': False, 'message': 'No account found.'})
    return jsonify({
        'exists': True,
        'is_approved': user.is_approved,
        'is_admin': user.is_admin,
        'is_active': user.is_active,
        'message': 'Account found.'
    })