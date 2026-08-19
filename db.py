from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from enum import Enum

db = SQLAlchemy()

class UserRole(Enum):
    ADMIN = 'admin'
    TEACHER = 'teacher'
    STUDENT = 'student'

class StudentStatus(Enum):
    ACTIVE = '在读'
    SUSPENDED = '休学'
    WITHDRAWN = '退学'
    GRADUATED = '毕业'
    COMPLETED = '结业'

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=UserRole.STUDENT.value)
    real_name = db.Column(db.String(80))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if not self.role:
            self.role = UserRole.STUDENT.value

    def is_admin(self):
        return self.role == UserRole.ADMIN.value

    def is_teacher(self):
        return self.role == UserRole.TEACHER.value

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Major(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    department = db.relationship('Department', backref=db.backref('majors', lazy=True))

class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    grade_id = db.Column(db.Integer, db.ForeignKey('grade.id'), nullable=False)
    major_id = db.Column(db.Integer, db.ForeignKey('major.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 班主任
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    grade = db.relationship('Grade', backref=db.backref('classes', lazy=True))
    major = db.relationship('Major', backref=db.backref('classes', lazy=True))
    teacher = db.relationship('User', backref=db.backref('classes', lazy=True))

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    age = db.Column(db.Integer)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))
    status = db.Column(db.String(20), nullable=False, default=StudentStatus.ACTIVE.value)
    admission_date = db.Column(db.Date, nullable=False)
    graduation_date = db.Column(db.Date)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('student_profile', uselist=False))
    class_ = db.relationship('Class', backref=db.backref('students', lazy=True))

class StudentStatusChange(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    old_status = db.Column(db.String(20), nullable=False)
    new_status = db.Column(db.String(20), nullable=False)
    change_reason = db.Column(db.Text, nullable=False)
    effective_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    student = db.relationship('Student', backref=db.backref('status_changes', lazy=True))
    creator = db.relationship('User', backref=db.backref('status_changes_created', lazy=True))

class MajorTransfer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    old_class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    new_major_id = db.Column(db.Integer, db.ForeignKey('major.id'), nullable=False)
    new_class_id = db.Column(db.Integer, db.ForeignKey('class.id'))
    transfer_reason = db.Column(db.Text, nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='待审核')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    reject_reason = db.Column(db.Text)

    student = db.relationship('Student', backref=db.backref('transfers', lazy=True))
    old_class = db.relationship('Class', foreign_keys=[old_class_id])
    new_major = db.relationship('Major', foreign_keys=[new_major_id])
    new_class = db.relationship('Class', foreign_keys=[new_class_id])
    approver = db.relationship('User', backref=db.backref('transfers_approved', lazy=True))
