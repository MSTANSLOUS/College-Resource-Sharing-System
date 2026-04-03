import os
from flask import Blueprint, render_template, request, redirect, current_app, flash, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.models import db, Program, Resource, User

core = Blueprint('core', __name__)


# 3. The dashboard Route
@core.route('/dashboard')
@login_required  # Added this to ensure a guest cannot view the dashboard
def dashboard():
    pending_students = []

    # If the logged-in user is a Class Rep, fetch their pending applicants!
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
    return render_template('core/student/campus_notes.html')


# The archive routes
@core.route('/cross_campus')
@login_required
def cross_campus():
    return render_template('core/student/cross_campus.html')


# The vault route
@core.route('/vault')
@login_required
def vault():
    return render_template('core/student/vault.html')


# The profile route
@core.route('/profile')
@login_required
def profile():
    return render_template('core/student/profile.html')


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
        flash(f'Successfully approved {student.full_name}.')
    else:
        flash('You do not have permission to approve this student.')

    # FIX: Redirect back to dashboard instead of a dedicated approvals page!
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
        db.session.delete(student)
        db.session.commit()
        flash(f'Ignored registration request from {student.full_name}.')
    else:
        flash('You do not have permission to reject this student.')

    # FIX: Redirect back to dashboard instead of a dedicated approvals page!
    return redirect(url_for('core.dashboard'))