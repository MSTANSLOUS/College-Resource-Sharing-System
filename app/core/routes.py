import os
from flask import Blueprint, render_template, request, redirect, current_app, flash, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.models import db, Program, Resource, User, Log

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


# 3. The dashboard Route
@core.route('/dashboard')
@login_required
def dashboard():
    pending_students = []

    if current_user.is_class_rep:
        pending_students = User.query.filter_by(
            is_approved=False,
            campus=current_user.campus,
            program_id=current_user.program_id
        ).all()

    return render_template('core/student/dashboard.html', pending_students=pending_students)


# The campus_notes routes
@core.route('/campus_notes')
@login_required
def campus_notes():
    notes = Resource.query.filter_by(campus=current_user.campus) \
        .join(Resource.programs) \
        .filter(Program.id == current_user.program_id) \
        .order_by(Resource.id.desc()) \
        .all()

    return render_template('core/student/campus_notes.html', notes=notes)


# The archive routes
@core.route('/cross_campus')
@login_required
def cross_campus():
    cross_notes = Resource.query.filter(Resource.campus != current_user.campus) \
        .join(Resource.programs) \
        .filter(Program.id == current_user.program_id) \
        .order_by(Resource.id.desc()) \
        .all()

    return render_template('core/student/cross_campus.html', cross_notes=cross_notes)


# The vault route
@core.route('/vault')
@login_required
def vault():
    return render_template('core/student/vault.html')


@core.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        student_id_val = request.form.get('student_id')
        phone = request.form.get('phone')
        campus = request.form.get('campus')
        program_id = request.form.get('program')

        current_user.full_name = fullname
        current_user.student_id = student_id_val
        current_user.phone_number = phone
        current_user.campus = campus
        current_user.program_id = program_id

        db.session.commit()

        # 📝 LOG: Profile Updated
        create_log("Profile Update", f"Updated profile details")

        flash('Profile updated successfully!')
        return redirect(url_for('core.profile'))

    programs = Program.query.all()
    return render_template('core/student/profile.html', user=current_user, programs=programs)


@core.route('/upload-resource', methods=['GET', 'POST'])
@login_required
def upload_resource():
    if not current_user.is_class_rep:
        flash('Access denied. Only Class Representatives can upload resources.')
        return redirect(url_for('core.dashboard'))

    if request.method == 'POST':
        module_name = request.form.get('module_name')
        title = request.form.get('title')
        semester = request.form.get('semester')
        academic_year = request.form.get('academic_year')
        selected_programs = request.form.getlist('programs')
        file = request.files.get('file')

        if not file or file.filename == '':
            flash('No file selected.')
            return redirect(request.url)

        if file and file.filename.endswith('.pdf'):
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)

            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)

            new_resource = Resource(
                title=title,
                file_path=f"uploads/{filename}",
                module_name=module_name,
                campus=current_user.campus,
                academic_year=academic_year,
                uploader_id=current_user.id
            )

            for prog_id in selected_programs:
                program = Program.query.get(int(prog_id))
                if program:
                    new_resource.programs.append(program)

            db.session.add(new_resource)
            db.session.commit()

            # 📝 LOG: File Uploaded
            create_log("Resource Upload", f"Uploaded module resource: {title} ({module_name})")

            flash('Resource successfully uploaded and mapped!')
            return redirect(url_for('core.dashboard'))
        else:
            flash('Invalid file type. Please upload a PDF.')

    programs = Program.query.all()
    return render_template('core/class_rep/upload_resource.html', programs=programs)


# 2. Action: Approve the Student
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

        # 📝 LOG: Student Approved
        create_log("Student Approval", f"Approved student: {student.full_name}")

        flash(f'Successfully approved {student.full_name}.')
    else:
        flash('You do not have permission to approve this student.')

    return redirect(url_for('core.dashboard'))


# 3. Action: Reject/Delete the Student
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

        # 📝 LOG: Request Rejected
        create_log("Registration Rejected", f"Rejected request from: {student_name}")

        flash(f'Ignored registration request from {student_name}.')
    else:
        flash('You do not have permission to reject this student.')

    return redirect(url_for('core.dashboard'))


# The Super Admin Route
@core.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('core.dashboard'))

    all_users = User.query.all()
    system_logs = Log.query.order_by(Log.created_at.desc()).limit(50).all()

    return render_template('core/admin/dashboard.html', users=all_users, logs=system_logs)


# ACTION: Promote to Rep
@core.route('/admin/make-rep/<int:user_id>', methods=['POST'])
@login_required
def make_rep(user_id):
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('core.dashboard'))

    user = User.query.get_or_404(user_id)
    user.is_class_rep = True
    db.session.commit()

    # 📝 LOG: Role Change
    create_log("Role Change", f"Promoted {user.full_name} to Class Representative")

    flash(f'{user.full_name} is now a Class Representative!')
    return redirect(url_for('core.admin_dashboard'))