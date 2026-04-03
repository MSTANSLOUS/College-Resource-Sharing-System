from flask import Blueprint, render_template

# 1. Create the Blueprint for Auth
auth = Blueprint('auth', __name__)

# 2. The Login Route
@auth.route('/')
@auth.route('/login')
def login():
    return render_template('auth/login.html')


#the register route
@auth.route('/register')
def register():
    return render_template('auth/register.html')


# 3. The dashboard Route
@auth.route('/dashboard')
def dashboard():
    return render_template('core/student/dashboard.html')

#the campus_notes rotes
@auth.route('/campus_notes')
def campus_notes():
    return render_template('core/student/campus_notes.html')

# the archive routes
@auth.route('/cross_campus')
def cross_campus():
    return render_template('core/student/cross_campus.html')

#the vault route
@auth.route('/vault')
def vault():
    return render_template('core/student/vault.html')

#the profile route
@auth.route('/profile')
def profile():
    return render_template('core/student/profile.html')
