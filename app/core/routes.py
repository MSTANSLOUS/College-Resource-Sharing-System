import os
from flask import Blueprint, render_template, request, redirect, current_app, flash, url_for, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from flask import jsonify
from flask_login import login_user
from werkzeug.security import check_password_hash
from app.models import db, Program, Resource, User, Log, Module, TransferRequest

from datetime import date # Make sure to import date
from app import send_email

core = Blueprint('core', __name__)

def create_log(action, details=None):
    """Helper function to record system activity"""
    log_entry = Log(
        user_id=current_user.id if current_user.is_authenticated else None,
        action=action,
        details=details
    )
    db.session.add(log_entry)
    db.session.commit()




def notify_class_rep(student, user_actions = None):
    """Finds the Rep for the student's campus/program and sends an email"""
    # Note: Ensure 'Message' and 'mail' are imported if you use Flask-Mail
    # For now, we will log the attempt to prevent crashes
    rep = User.query.filter_by(
        is_class_rep=True,
        campus=student.campus,
        program_id=student.program_id
    ).first()

    if rep and rep.email:
        #print(f"Notification logic triggered for Rep: {rep.email}")
        subjects = f"Account Creation"
        message_body = f"Hie class admin am {student.full_name} and i created an account waiting for yout approval"
        # Add your Flask-Mail logic here when ready
        send_email(recipients=rep.email, subject=subjects, massage_body=message_body)

# --- DASHBOARD & PROFILE ---

@core.route('/dashboard')
@login_required
def dashboard():
    pending_students = []

    # If the user is a Class Rep, only show students in their SPECIFIC class
    if current_user.is_class_rep:
        pending_students = User.query.filter_by(
            is_approved=False,
            campus=current_user.campus,
            program_id=current_user.program_id,
            year=current_user.year,  # ADD THIS: Filter by the Rep's year
            semester=current_user.semester  # ADD THIS: Filter by the Rep's semester
        ).all()

    # Fetch recent uploads (Same logic here - filter by year/semester)
    recent_uploads = Resource.query.filter_by(
        campus=current_user.campus,
        target_year=current_user.year,  # Only show notes for their year
        target_semester=current_user.semester  # Only show notes for their semester
    ) \
        .join(Resource.programs) \
        .filter(Program.id == current_user.program_id) \
        .order_by(Resource.id.desc()) \
        .limit(3) \
        .all()

    return render_template('core/student/dashboard.html',
                           pending_students=pending_students,
                           recent_uploads=recent_uploads)





@core.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('fullname')
        current_user.student_id = request.form.get('student_id')
        current_user.phone_number = request.form.get('phone')

        new_year = request.form.get('year')
        new_sem = request.form.get('semester')
        if new_year: current_user.year = int(new_year)
        if new_sem: current_user.semester = int(new_sem)

        req_campus = request.form.get('campus')
        req_prog_id = request.form.get('program_id')

        if (req_campus and req_campus != current_user.campus) or \
           (req_prog_id and int(req_prog_id) != current_user.program_id):

            existing = TransferRequest.query.filter_by(user_id=current_user.id, status='pending').first()
            if not existing:
                new_req = TransferRequest(
                    user_id=current_user.id,
                    target_campus=req_campus or current_user.campus,
                    target_program_id=int(req_prog_id) if req_prog_id else current_user.program_id
                )
                db.session.add(new_req)
                flash('Institutional change request sent to Admin.', 'info')

        db.session.commit()
        create_log("Profile Update", "Updated user profile info")
        flash('Profile updated successfully!')
        return redirect(url_for('core.profile'))

    programs = Program.query.all()
    pending_request = TransferRequest.query.filter_by(user_id=current_user.id, status='pending').first()
    return render_template('core/student/profile.html', user=current_user, programs=programs,
                           pending_request=pending_request)




# --- NOTES & RESOURCES ---

@core.route('/campus_notes')
@login_required
def campus_notes():
    notes = Resource.query.filter_by(campus=current_user.campus) \
        .join(Resource.programs) \
        .filter(Program.id == current_user.program_id) \
        .order_by(Resource.id.desc()) \
        .all()

    grouped_notes = {}
    for note in notes:
        m_name = note.module.name
        if m_name not in grouped_notes:
            grouped_notes[m_name] = []
        grouped_notes[m_name].append(note)

    return render_template('core/student/campus_notes.html', grouped_notes=grouped_notes)



@core.route('/cross_campus')
@login_required
def cross_campus():
    cross_notes = Resource.query.filter(Resource.campus != current_user.campus) \
        .join(Resource.programs) \
        .filter(Program.id == current_user.program_id) \
        .order_by(Resource.id.desc()) \
        .all()

    organized_notes = {}
    for note in cross_notes:
        campus = note.campus
        module_name = note.module.name
        if campus not in organized_notes:
            organized_notes[campus] = {}
        if module_name not in organized_notes[campus]:
            organized_notes[campus][module_name] = []
        organized_notes[campus][module_name].append(note)

    return render_template('core/student/cross_campus.html', organized_notes=organized_notes)




@core.route('/vault')
@login_required
def vault():
    return render_template('core/student/vault.html')





@core.route('/upload-resource', methods=['GET', 'POST'])
@login_required
def upload_resource():
    if not current_user.is_class_rep:
        flash('Access denied.')
        return redirect(url_for('core.dashboard'))

    if request.method == 'POST':
        module_id = request.form.get('module_id')
        title = request.form.get('title')
        academic_year = request.form.get('academic_year')
        selected_programs = request.form.getlist('programs')
        file = request.files.get('file')

        if file and file.filename.endswith('.pdf'):
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            file.save(os.path.join(upload_folder, filename))

            new_resource = Resource(
                title=title,
                file_path=f"uploads/{filename}",
                module_id=module_id,
                campus=current_user.campus,
                academic_year=academic_year,
                uploader_id=current_user.id,
                target_year=1, # Default placeholder
                target_semester=1 # Default placeholder
            )

            for prog_id in selected_programs:
                program = Program.query.get(int(prog_id))
                if program:
                    new_resource.programs.append(program)

            db.session.add(new_resource)
            db.session.commit()
            module = Module.query.get(module_id)
            create_log("Resource Upload", f"Uploaded {title} for {module.name}")
            flash('Resource uploaded successfully!')
            return redirect(url_for('core.dashboard'))

    modules = current_user.program.modules.all()
    programs = Program.query.all()
    return render_template('core/class_rep/upload_resource.html', modules=modules, programs=programs)



# --- CLASS REP ACTIONS ---

@core.route('/approve-student/<int:user_id>', methods=['POST'])
@login_required
def approve_student(user_id):
    if not current_user.is_class_rep:
        flash('Access denied.')
        return redirect(url_for('core.dashboard'))

    student = User.query.get_or_404(user_id)
    if student.campus == current_user.campus and student.program_id == current_user.program_id:
        student.is_approved = True
        db.session.commit()
        create_log("Student Approval", f"Approved student: {student.full_name}")
        flash(f'Successfully approved {student.full_name}.')
    else:
        flash('You do not have permission to approve this student.')
    return redirect(url_for('core.dashboard'))





@core.route('/reject-student/<int:user_id>', methods=['POST'])
@login_required
def reject_student(user_id):
    if not current_user.is_class_rep:
        flash('Access denied.')
        return redirect(url_for('core.dashboard'))

    student = User.query.get_or_404(user_id)
    if student.campus == current_user.campus and student.program_id == current_user.program_id:
        student_name = student.full_name
        db.session.delete(student)
        db.session.commit()
        create_log("Registration Rejected", f"Rejected request from: {student_name}")
        flash(f'Ignored registration request from {student_name}.')
    else:
        flash('You do not have permission to reject this student.')
    return redirect(url_for('core.dashboard'))




# --- ADMIN DASHBOARD & ACTIONS ---

@core.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('core.dashboard'))

    # --- PRO LOG CLEANUP ---
    # This deletes all logs where the date is older than today
    today = date.today()
    Log.query.filter(Log.created_at < today).delete()
    db.session.commit()

    # Get filter values from the URL (e.g., /admin/dashboard?year=2)
    year_filter = request.args.get('year', type=int)
    sem_filter = request.args.get('semester', type=int)

    # Start with all users
    user_query = User.query

    # Apply filters if they exist
    if year_filter:
        user_query = user_query.filter_by(year=year_filter)
    if sem_filter:
        user_query = user_query.filter_by(semester=sem_filter)

    all_users = user_query.all()
    all_programs = Program.query.all()
    all_modules = Module.query.all()
    system_logs = Log.query.order_by(Log.created_at.desc()).limit(50).all()
    pending_requests = TransferRequest.query.filter_by(status='pending').all()

    return render_template('core/admin/dashboard.html',
                           users=all_users,
                           logs=system_logs,
                           programs=all_programs,
                           modules=all_modules,
                           requests=pending_requests,
                           current_year=year_filter,    # Pass these back to keep dropdowns selected
                           current_sem=sem_filter)




@core.route('/admin/request/<int:req_id>/<action>')
@login_required
def handle_request(req_id, action):
    if not current_user.is_admin:
        abort(403)

    req = TransferRequest.query.get_or_404(req_id)
    if action == 'approve':
        req.user.campus = req.target_campus
        req.user.program_id = req.target_program_id
        req.status = 'approved'
        create_log("Transfer Approved", f"Approved transfer for {req.user.full_name}")
        flash(f"Approved changes for {req.user.full_name}")
    else:
        req.status = 'rejected'
        flash("Request rejected.")

    db.session.commit()
    return redirect(url_for('core.admin_dashboard'))





@core.route('/admin/add-module', methods=['POST'])
@login_required
def add_module():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('core.dashboard'))

    name = request.form.get('name', '').strip()
    code = request.form.get('code', '').strip().upper()
    program_ids = request.form.getlist('programs')

    if not name or not code or not program_ids:
        flash('Error: Module Name, Code, and at least one Program are required!')
        return redirect(url_for('core.admin_dashboard'))

    existing = Module.query.filter_by(code=code).first()
    if existing:
        flash(f'Error: Module code "{code}" is already used by "{existing.name}".')
        return redirect(url_for('core.admin_dashboard'))

    try:
        new_module = Module(name=name, code=code)
        for p_id in program_ids:
            prog = Program.query.get(int(p_id))
            if prog:
                new_module.programs.append(prog)
        db.session.add(new_module)
        db.session.commit()
        create_log("Module Created", f"Admin registered module: {name} ({code})")
        flash(f'Module {name} registered successfully!')
    except Exception as e:
        db.session.rollback()
        flash('Something went wrong.')
        print(f"Database Error: {e}")

    return redirect(url_for('core.admin_dashboard'))




@core.route('/admin/make-rep/<int:user_id>', methods=['POST'])
@login_required
def make_rep(user_id):
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('core.dashboard'))

    user = User.query.get_or_404(user_id)
    user.is_class_rep = True
    db.session.commit()
    create_log("Role Change", f"Promoted {user.full_name} to Class Representative")
    flash(f'{user.full_name} is now a Class Representative!')
    return redirect(url_for('core.admin_dashboard'))


@core.route('/admin/remove-rep/<int:user_id>', methods=['POST'])
@login_required
def remove_rep(user_id):
    if not current_user.is_admin:
        flash('Access denied.', 'error')  # Added 'error' category for red styling
        return redirect(url_for('core.dashboard'))

    # STANDARD SQLALCHEMY WAY
    user = User.query.get_or_404(user_id)

    user.is_class_rep = False
    db.session.commit()

    # Good job on the log!
    create_log("Role Change", f"Removed {user.full_name} from being Class Representative")

    flash(f'{user.full_name} is no longer a Class Representative!', 'info')
    return redirect(url_for('core.admin_dashboard'))


@core.route('/admin/delete-module/<int:module_id>', methods=['POST'])
@login_required
def delete_module(module_id):
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('core.dashboard'))

    module = Module.query.get_or_404(module_id)

    # Check if the module has resources
    if module.resources:
        flash(f'Cannot delete "{module.name}" because it contains resources. Delete the notes first!', 'error')
        return redirect(url_for('core.admin_dashboard'))

    module_name = module.name
    db.session.delete(module)
    db.session.commit()

    create_log("Database Change", f"Deleted Module: {module_name}")
    flash(f'Module "{module_name}" removed successfully.', 'info')

    return redirect(url_for('core.admin_dashboard'))



@core.route('/notes/delete/<int:note_id>', methods=['POST'])
@login_required
def delete_note(note_id):
    # 1. Fetch the note or 404 if it's missing
    note = Resource.query.get_or_404(note_id)

    # 2. SECURITY CHECK: Ensure it's a Rep and THEY are the owner
    if not current_user.is_class_rep or current_user.id != note.user_id:
        flash('Permission denied. You can only delete your own uploads.', 'error')
        return redirect(url_for('core.notes'))

    try:
        # 3. DELETE THE PHYSICAL FILE FROM THE FOLDER
        # This finds the exact path on your Kali machine
        file_path = os.path.join(current_app.root_path, 'static', note.file_path)

        if os.path.exists(file_path):
            os.remove(file_path)  # Boom. File is gone from the folder.

        # 4. DELETE THE RECORD FROM THE DATABASE
        db.session.delete(note)
        db.session.commit()

        # 5. LOG THE ACTION
        create_log("File Removed", f"Rep {current_user.full_name} deleted: {note.title}")
        flash('File deleted successfully. You can now upload the correct version!', 'info')

    except Exception as e:
        db.session.rollback()
        print(f"Delete Error: {e}")
        flash('Something went wrong while removing the file.', 'error')

    return redirect(url_for('core.notes'))





"""AI LOGIC HERE BELOW THE ENDPOINTS """

@core.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if user:
        if check_password_hash(user.password_hash, password):
            if user.is_approved:
                # 1. Use remember=True to make the cookie persistent
                login_user(user, remember=True)

                response = jsonify({"status": "success", "message": "Welcome!"})

                # 2. Ngrok skip header (for the app)
                response.headers.add("ngrok-skip-browser-warning", "true")

                # 3. CRITICAL: Manual Cookie Header (if SESSION_COOKIE settings are failing)
                # This ensures the cookie is sent back with 'None' SameSite policy
                response.set_cookie('session', request.cookies.get('session', ''),
                                    samesite='None', secure=True)

                return response, 200
            else:
                return jsonify({"status": "error", "message": "Account pending approval"}), 403
        else:
            return jsonify({"status": "error", "message": "Incorrect password"}), 401

    return jsonify({"status": "error", "message": "User not found"}), 404


@core.route('/api/v1/student-context', methods=['GET'])
@login_required
def get_student_context():
    active_modules = current_user.program.modules.all()
    modules_list = [{"name": m.name, "code": m.code} for m in active_modules]

    response = jsonify({
        "student_name": current_user.full_name,
        "modules": modules_list
    })
    # Tell Ngrok NOT to show the warning page to the Android app
    response.headers.add("ngrok-skip-browser-warning", "true")
    return response
