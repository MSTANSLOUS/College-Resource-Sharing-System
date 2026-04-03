from flask import Blueprint
from flask import render_template



core = Blueprint('core', __name__)

# 3. The dashboard Route
@core.route('/dashboard')
def dashboard():
    return render_template('core/student/dashboard.html')

#the campus_notes rotes
@core.route('/campus_notes')
def campus_notes():
    return render_template('core/student/campus_notes.html')

# the archive routes
@core.route('/cross_campus')
def cross_campus():
    return render_template('core/student/cross_campus.html')

#the vault route
@core.route('/vault')
def vault():
    return render_template('core/student/vault.html')

#the profile route
@core.route('/profile')
def profile():
    return render_template('core/student/profile.html')
