from flask import Blueprint
from flask import render_template
from flask import request
from flask import flash
from flask import url_for
from flask import redirect
from sqlalchemy.orm.attributes import register_descriptor

from app.models import db
from app.models import User
from app.models import Program

from werkzeug.security import generate_password_hash

# 1. Create the Blueprint for Auth
auth = Blueprint('auth', __name__)

# 2. The Login Route
@auth.route('/')
@auth.route('/login')
def login():
    return render_template('auth/login.html')


#the register route
@auth.route('/register', methods = ['GET', 'POST'])
def register():
    # ONLY process data if the form was actually submitted via POST
    if request.method == 'POST':
        # 1. Grab form data from your clean non-scrolling UI
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        campus = request.form.get('campus')
        program_id = request.form.get('program')  # This will be the ID of the program
        password = request.form.get('password')

        # 2. Basic check to see if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Gmail address is already registered.')
            return redirect(url_for('auth.register'))

        # 3. Hash the password securely (Uncomment this when you're ready for security!)
        # hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # 4. Create the new user object
        new_user = User(
            full_name=fullname,
            email=email,
            campus=campus,
            program_id=program_id,
            password_hash=password, # Swapping to hashed_password later is highly recommended!
            is_approved=False,  # Explicitly keeping them blocked as per Module 1
            is_class_rep=False  # Defaulting them to standard students
        )

        # 5. Push to database
        db.session.add(new_user)
        db.session.commit()

        # 6. Redirect them or show a success message
        flash('Registration successful! Your request has been forwarded to your class rep for approval.')
        return redirect(url_for('auth.login'))

    # This part only runs during a GET request (When they just land on the page)
    # Query all programs from the database for the dropdown
    programs = Program.query.all()

    return render_template('auth/register.html', programs=programs)

