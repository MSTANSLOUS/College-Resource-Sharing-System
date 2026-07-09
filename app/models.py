from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Helper tables
resource_programs = db.Table('resource_programs',
                             db.Column('resource_id', db.Integer, db.ForeignKey('resource.id'), primary_key=True),
                             db.Column('program_id', db.Integer, db.ForeignKey('program.id'), primary_key=True)
                             )

module_programs = db.Table('module_programs',
                           db.Column('module_id', db.Integer, db.ForeignKey('module.id'), primary_key=True),
                           db.Column('program_id', db.Integer, db.ForeignKey('program.id'), primary_key=True)
                           )

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    campus = db.Column(db.String(50), nullable=False)
    student_id = db.Column(db.String(20), nullable=True)
    phone_number = db.Column(db.String(15), nullable=True)
    year = db.Column(db.Integer, default=1)
    semester = db.Column(db.Integer, default=1)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    is_class_rep = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tour_completed = db.Column(db.Boolean, default=False)

class TransferRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    target_campus = db.Column(db.String(50))
    target_program_id = db.Column(db.Integer, db.ForeignKey('program.id'))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='transfer_requests')

class Program(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    users = db.relationship('User', backref='program', lazy=True)

class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=True)
    programs = db.relationship('Program', secondary=module_programs, backref=db.backref('modules', lazy='dynamic'))
    resources = db.relationship('Resource', backref='module', lazy=True)

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    file_path = db.Column(db.String(200), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), nullable=False)
    campus = db.Column(db.String(50), nullable=False)
    target_year = db.Column(db.Integer, nullable=False)
    target_semester = db.Column(db.Integer, nullable=False)
    academic_year = db.Column(db.String(20), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uploader = db.relationship('User', backref='uploaded_resources')
    programs = db.relationship('Program', secondary=resource_programs, backref=db.backref('resources', lazy='dynamic'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='logs')