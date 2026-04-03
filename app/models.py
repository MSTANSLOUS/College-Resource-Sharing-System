from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Helper table for the Many-to-Many relationship (Module 3)
# This allows one resource to belong to multiple programs!
resource_programs = db.Table('resource_programs',
                             db.Column('resource_id', db.Integer, db.ForeignKey('resource.id'), primary_key=True),
                             db.Column('program_id', db.Integer, db.ForeignKey('program.id'), primary_key=True)
                             )


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)  # For secure login

    # MCA Specifics
    campus = db.Column(db.String(50), nullable=False)  # Lilongwe, Blantyre, Mzuzu
    student_id = db.Column(db.String(20), nullable=True)  # Filled out in Profile update
    phone_number = db.Column(db.String(15), nullable=True)  # Filled out in Profile update

    # Relationships
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'), nullable=False)

    # Roles and Approvals (Module 1)
    is_approved = db.Column(db.Boolean, default=False)
    is_class_rep = db.Column(db.Boolean, default=False)  # True for reps, False for students

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Program(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # e.g., BMIS, BBME

    # Relationships
    users = db.relationship('User', backref='program', lazy=True)


class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)  # e.g., Business Statistics Notes
    file_path = db.Column(db.String(200), nullable=False)  # Where the PDF is stored on Render
    module_name = db.Column(db.String(100), nullable=False)

    # Target Audience & Location
    campus = db.Column(db.String(50), nullable=False)  # The campus this note belongs to
    academic_year = db.Column(db.String(20), nullable=False)  # e.g., "2025/2026"
    is_archived = db.Column(db.Boolean, default=False)  # False for dashboard, True for Vault

    # Who uploaded it?
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Many-to-Many Relationship (Maps to multiple programs)
    programs = db.relationship('Program', secondary=resource_programs, backref=db.backref('resources', lazy='dynamic'))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)