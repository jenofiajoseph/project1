from datetime import datetime
import os
import re
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# File Upload Settings
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Ensure upload directories exist
os.makedirs(os.path.join(app.root_path, UPLOAD_FOLDER, 'staff'), exist_ok=True)
os.makedirs(os.path.join(app.root_path, UPLOAD_FOLDER, 'staff', 'documents'), exist_ok=True)
os.makedirs(os.path.join(app.root_path, UPLOAD_FOLDER, 'student'), exist_ok=True)

db = SQLAlchemy(app)


TIMETABLE_DAYS = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')
TIMETABLE_PERIODS = range(1, 9)


def timetable_periods():
    return [
        {'type': 'period', 'num': 1}, {'type': 'period', 'num': 2},
        {'type': 'break', 'label': 'Break'},
        {'type': 'period', 'num': 3}, {'type': 'period', 'num': 4},
        {'type': 'lunch', 'label': 'Lunch'},
        {'type': 'period', 'num': 5}, {'type': 'period', 'num': 6},
        {'type': 'break', 'label': 'Break'},
        {'type': 'period', 'num': 7}, {'type': 'period', 'num': 8},
    ]


app.jinja_env.globals['timetable_periods'] = timetable_periods

@app.context_processor
def inject_system_settings():
    try:
        entrance_setting = SystemSetting.query.filter_by(key='entrance_exam_enabled').first()
        is_entrance_enabled = entrance_setting.value.lower() == 'true' if entrance_setting else False
        
        study_setting = SystemSetting.query.filter_by(key='study_materials_enabled').first()
        is_study_materials_enabled = study_setting.value.lower() == 'true' if study_setting else False
        
        
        
        video_setting = SystemSetting.query.filter_by(key='study_materials_video_enabled').first()
        is_video_enabled = video_setting.value.lower() == 'true' if video_setting else False
        
        notes_setting = SystemSetting.query.filter_by(key='study_materials_notes_enabled').first()
        is_notes_enabled = notes_setting.value.lower() == 'true' if notes_setting else False
        
        chat_setting = SystemSetting.query.filter_by(key='chat_enabled').first()
        is_chat_enabled = chat_setting.value.lower() == 'true' if chat_setting else False
        
        # Communication module settings
        comm_setting = SystemSetting.query.filter_by(key='communication_enabled').first()
        is_communication_enabled = comm_setting.value.lower() == 'true' if comm_setting else False

        whatsapp_setting = SystemSetting.query.filter_by(key='communication_whatsapp_enabled').first()
        is_communication_whatsapp_enabled = whatsapp_setting.value.lower() == 'true' if whatsapp_setting else False

        email_setting = SystemSetting.query.filter_by(key='communication_email_enabled').first()
        is_communication_email_enabled = email_setting.value.lower() == 'true' if email_setting else False

        circular_setting = SystemSetting.query.filter_by(key='communication_circular_enabled').first()
        is_communication_circular_enabled = circular_setting.value.lower() == 'true' if circular_setting else False

        push_setting = SystemSetting.query.filter_by(key='communication_push_enabled').first()
        is_communication_push_enabled = push_setting.value.lower() == 'true' if push_setting else False

        ann_setting = SystemSetting.query.filter_by(key='communication_announcement_enabled').first()
        is_communication_announcement_enabled = ann_setting.value.lower() == 'true' if ann_setting else False

        notice_setting = SystemSetting.query.filter_by(key='communication_notice_board_enabled').first()
        is_communication_notice_board_enabled = notice_setting.value.lower() == 'true' if notice_setting else False
        
        # Calculate unassigned staff count for the sidebar badge
        unassigned_staff_count = Staff.query.filter_by(role_id=None).count()
        
    except Exception:
        # In case DB is not initialized yet
        is_entrance_enabled = False
        is_study_materials_enabled = False
        
        is_video_enabled = False
        is_notes_enabled = False
        is_chat_enabled = False
        
        is_communication_enabled = False
        is_communication_whatsapp_enabled = False
        is_communication_email_enabled = False
        is_communication_circular_enabled = False
        is_communication_push_enabled = False
        is_communication_announcement_enabled = False
        is_communication_notice_board_enabled = False
        unassigned_staff_count = 0
        
    return dict(
        is_entrance_enabled=is_entrance_enabled, 
        is_study_materials_enabled=is_study_materials_enabled,
        
        is_video_enabled=is_video_enabled,
        is_notes_enabled=is_notes_enabled,
        is_chat_enabled=is_chat_enabled,
        
        is_communication_enabled=is_communication_enabled,
        is_communication_whatsapp_enabled=is_communication_whatsapp_enabled,
        is_communication_email_enabled=is_communication_email_enabled,
        is_communication_circular_enabled=is_communication_circular_enabled,
        is_communication_push_enabled=is_communication_push_enabled,
        is_communication_announcement_enabled=is_communication_announcement_enabled,
        is_communication_notice_board_enabled=is_communication_notice_board_enabled,
        unassigned_staff_count=unassigned_staff_count
    )

# --- Database Models ---

# 1. Admin Model
class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<Admin {self.username}>"

# 2. Academic Year Model
class AcademicYear(db.Model):
    __tablename__ = 'academic_years'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # e.g., "2026-2027"
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_current = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    student_academic_details = db.relationship('StudentAcademicDetail', backref='academic_year', lazy=True)

    def __repr__(self):
        return f"<AcademicYear {self.name}>"

# 2b. Teacher Category Model
class TeacherCategory(db.Model):
    __tablename__ = 'teacher_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    short_form = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return f"<TeacherCategory {self.name}>"

# 2c. Qualification Model
class Qualification(db.Model):
    __tablename__ = 'qualifications'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)

    def __repr__(self):
        return f"<Qualification {self.name}>"

class DegreeLevel(db.Model):
    __tablename__ = 'degree_levels'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    short_form = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return f"<DegreeLevel {self.name}>"

class Specification(db.Model):
    __tablename__ = 'specifications'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    short_form = db.Column(db.String(20), nullable=True)
    degree_level_id = db.Column(db.Integer, db.ForeignKey('degree_levels.id', ondelete='CASCADE'), nullable=False)
    
    degree_level = db.relationship('DegreeLevel', backref='specifications')

    def __repr__(self):
        return f"<Specification {self.name}>"

class MajorSubject(db.Model):
    __tablename__ = 'major_subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    short_form = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return f"<MajorSubject {self.name}>"

# 3. Department Model
class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    short_form = db.Column(db.String(20), nullable=True)
    
    # Relationship
    staff_members = db.relationship('Staff', backref='department', lazy=True)

    def __repr__(self):
        return f"<Department {self.name}>"

# 4. Role Model
class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # Class Teacher, HOD, Receptionist, Librarian
    short_form = db.Column(db.String(20), nullable=True)

    # Relationship
    staff_members = db.relationship('Staff', backref='role', lazy=True)

    def __repr__(self):
        return f"<Role {self.name}>"

# Staff Qualification Model

class StaffExperience(db.Model):
    __tablename__ = 'staff_experiences'
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id', ondelete='CASCADE'), nullable=False)
    experience_type = db.Column(db.String(50), nullable=False)
    experience_years = db.Column(db.Integer, nullable=True)
    previous_work_details = db.Column(db.Text, nullable=True)

class StaffQualification(db.Model):
    __tablename__ = 'staff_qualifications'
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id', ondelete='CASCADE'), nullable=False)
    degree_level = db.Column(db.String(50), nullable=False)  # UG, PG, Extra Curricular, etc.
    specification = db.Column(db.String(100), nullable=True) # B.Sc, M.A, etc.
    major = db.Column(db.String(100), nullable=True)         # Physics, etc.
    college_name = db.Column(db.String(255), nullable=True)
    passing_year = db.Column(db.String(20), nullable=True)
    cgpa_percentage = db.Column(db.String(20), nullable=True)

# 5. Staff Model
class Staff(db.Model):
    __tablename__ = 'staff'
    
    staff_id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=True)
    gender = db.Column(db.String(20), nullable=False)  # Male, Female, Other
    date_of_birth = db.Column(db.Date, nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    teacher_category = db.Column(db.String(50), nullable=True)  # TGT, PGT, PRT, Non-Teaching
    photo = db.Column(db.String(255), nullable=True)
    
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=True)
    
    designation = db.Column(db.String(100), nullable=False)
    
    qualifications = db.relationship('StaffQualification', backref='staff', cascade='all, delete-orphan', lazy=True)
    experiences = db.relationship('StaffExperience', backref='staff', cascade='all, delete-orphan', lazy=True)
    

    experience_level = db.Column(db.String(50), nullable=True)  # Fresher, Experienced
    experience_type = db.Column(db.String(50), nullable=True)   # Industry Experience, Teaching Experience
    experience_years = db.Column(db.Integer, nullable=True)
    previous_work_details = db.Column(db.Text, nullable=True)
    
    # Payment & Documentation
    basic_salary = db.Column(db.Numeric(10, 2), nullable=True)
    aadhar_number = db.Column(db.String(20), nullable=True)
    aadhar_document = db.Column(db.String(255), nullable=True)
    account_holder_name = db.Column(db.String(100), nullable=True)
    bank_name = db.Column(db.String(100), nullable=True)
    account_number = db.Column(db.String(50), nullable=True)
    ifsc_code = db.Column(db.String(20), nullable=True)
    bank_document = db.Column(db.String(255), nullable=True)
    
    joining_date = db.Column(db.Date, nullable=False)
    employment_type = db.Column(db.String(50), nullable=False)  # Permanent, Contract
    status = db.Column(db.String(50), nullable=False, default='Active')  # Active, Inactive, Terminated, Resigned
    
    date_of_termination = db.Column(db.Date, nullable=True)
    termination_reason = db.Column(db.Text, nullable=True)
    relieving_date = db.Column(db.Date, nullable=True)
    
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Staff {self.first_name} {self.last_name or ''}>"

# 6. ClassRoom Model
class ClassRoom(db.Model):
    __tablename__ = 'classes'
    
    class_id = db.Column(db.Integer, primary_key=True)
    academic_year_id = db.Column(db.Integer, db.ForeignKey('academic_years.id'), nullable=False)
    class_name = db.Column(db.String(100), nullable=False) # e.g. LKG, UKG, 1, 2, ..., 12
    display_order = db.Column(db.Integer, nullable=False, default=0)
    capacity = db.Column(db.Integer, nullable=True, default=0)

    __table_args__ = (
        db.UniqueConstraint('academic_year_id', 'class_name', name='uq_academic_year_class'),
    )

    # Relationships
    academic_year = db.relationship('AcademicYear', backref=db.backref('classrooms', lazy=True))
    sections = db.relationship('Section', backref='classroom', cascade='all, delete-orphan', lazy=True)
    student_academic_details = db.relationship('StudentAcademicDetail', backref='classroom', lazy=True)

    def __repr__(self):
        return f"<ClassRoom {self.class_name}>"

# 7. Section Model
class Section(db.Model):
    __tablename__ = 'sections'
    
    section_id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.class_id'), nullable=False)
    academic_year_id = db.Column(db.Integer, db.ForeignKey('academic_years.id'), nullable=False)
    section_name = db.Column(db.String(50), nullable=False) # e.g., A, B, C
    short_form = db.Column(db.String(20), nullable=True)
    short_form = db.Column(db.String(20), nullable=True)

    # Relationships
    academic_year = db.relationship('AcademicYear', backref=db.backref('sections', lazy=True))
    student_academic_details = db.relationship('StudentAcademicDetail', backref='section', lazy=True)

    def __repr__(self):
        return f"<Section {self.section_name} of Class ID {self.class_id}>"

class StudyMaterial(db.Model):
    __tablename__ = 'study_materials'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50)) # e.g., pdf, doc, video, etc.
    
    class_id = db.Column(db.Integer, db.ForeignKey('classes.class_id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.section_id'), nullable=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    class_room = db.relationship('ClassRoom', backref='materials')
    section = db.relationship('Section', backref='materials')
    staff = db.relationship('Staff', backref='materials')

# 8. Student Model (Permanent Info)
class Student(db.Model):
    __tablename__ = 'students'
    
    student_id = db.Column(db.Integer, primary_key=True)
    admission_no = db.Column(db.String(50), unique=True, nullable=False)
    aadhar_no = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=True)
    gender = db.Column(db.String(20), nullable=False) # Male, Female, Other
    date_of_birth = db.Column(db.Date, nullable=False)
    blood_group = db.Column(db.String(20), nullable=True)
    photo = db.Column(db.String(255), nullable=True)
    father_name = db.Column(db.String(150), nullable=False)
    mother_name = db.Column(db.String(150), nullable=False)
    parent_mobile = db.Column(db.String(20), nullable=False)
    parent_email = db.Column(db.String(100), nullable=True)
    address = db.Column(db.Text, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Transfer Student Details
    is_transfer_student = db.Column(db.Boolean, default=False)
    previous_school_name = db.Column(db.String(255), nullable=True)
    previous_school_address = db.Column(db.Text, nullable=True)
    previous_academic_performance = db.Column(db.String(255), nullable=True)
    transfer_certificate_no = db.Column(db.String(100), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    academic_details = db.relationship('StudentAcademicDetail', backref='student', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f"<Student {self.first_name} {self.last_name or ''}>"

# 9. Student Academic Details Model (Academic Year Allocations)
class StudentAcademicDetail(db.Model):
    __tablename__ = 'student_academic_details'
    
    student_academic_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'), nullable=False)
    academic_year_id = db.Column(db.Integer, db.ForeignKey('academic_years.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.class_id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.section_id'), nullable=False)
    roll_no = db.Column(db.String(50), nullable=True)
    student_status = db.Column(db.String(50), nullable=False, default='Active') # Active, Inactive, Suspended, etc.

    def __repr__(self):
        return f"<StudentAcademicDetail StudentID {self.student_id} Year {self.academic_year_id} Class {self.class_id}>"

# 10. Super Admin Model
class SuperAdmin(db.Model):
    __tablename__ = 'super_admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

# Subject management is intentionally additive.  These tables are separate from
# the existing department-based timetable, so the current LMS data is preserved.
class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    department = db.relationship('Department', backref='subjects')


class ClassSubject(db.Model):
    __tablename__ = 'class_subjects'
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.class_id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    classroom = db.relationship('ClassRoom', backref='class_subjects')
    subject = db.relationship('Subject', backref='class_subjects')
    __table_args__ = (db.UniqueConstraint('class_id', 'subject_id', name='uq_class_subject'),)


class StaffSubjectAssignment(db.Model):
    __tablename__ = 'staff_subject_assignments'
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.class_id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.section_id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    staff = db.relationship('Staff', backref='subject_assignments')
    subject = db.relationship('Subject', backref='staff_assignments')
    classroom = db.relationship('ClassRoom', backref='subject_assignments')
    section = db.relationship('Section', backref='subject_assignments')
    __table_args__ = (db.UniqueConstraint('staff_id', 'subject_id', 'class_id', 'section_id', name='uq_staff_subject_class_section'),)


class ClassTeacherAssignment(db.Model):
    __tablename__ = 'class_teacher_assignments'
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.class_id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.section_id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    classroom = db.relationship('ClassRoom', backref='class_teacher_assignments')
    section = db.relationship('Section', backref='class_teacher_assignments')
    staff = db.relationship('Staff', backref='class_teacher_assignments')
    __table_args__ = (db.UniqueConstraint('class_id', 'section_id', name='uq_class_section_teacher'),)

# 11. System Setting Model
class SystemSetting(db.Model):
    __tablename__ = 'system_settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)

# 12. Entrance Exam Model
class EntranceExam(db.Model):
    __tablename__ = 'entrance_exams'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False, default=60)
    assigned_class_id = db.Column(db.Integer, db.ForeignKey('classes.class_id'), nullable=False)
    created_by_staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    questions = db.relationship('ExamQuestion', backref='exam', cascade='all, delete-orphan', lazy=True)
    attempts = db.relationship('StudentExamAttempt', backref='exam', cascade='all, delete-orphan', lazy=True)

# 13. Exam Question Model
class ExamQuestion(db.Model):
    __tablename__ = 'exam_questions'
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('entrance_exams.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    option_d = db.Column(db.String(255), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False) # 'A', 'B', 'C', or 'D'

# 14. Student Exam Attempt Model
class StudentExamAttempt(db.Model):
    __tablename__ = 'student_exam_attempts'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('entrance_exams.id'), nullable=False)
    score = db.Column(db.Integer, nullable=True)
    is_completed = db.Column(db.Boolean, default=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)


# Attendance and timetable tables.  These are additive models: SQLAlchemy's
# create_all() creates only missing tables and never removes existing data.
class Timetable(db.Model):
    __tablename__ = 'timetable'

    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.class_id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.section_id'), nullable=False)
    day = db.Column(db.String(20), nullable=False)
    period_number = db.Column(db.Integer, nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id'), nullable=False)

    classroom = db.relationship('ClassRoom')
    section = db.relationship('Section')
    subject = db.relationship('Department')
    teacher = db.relationship('Staff')

    __table_args__ = (db.UniqueConstraint('class_id', 'section_id', 'day', 'period_number', name='uq_timetable_slot'),)


class StaffAttendance(db.Model):
    __tablename__ = 'staff_attendance'

    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    remarks = db.Column(db.String(255), nullable=True)
    marked_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    staff = db.relationship('Staff')
    __table_args__ = (db.UniqueConstraint('staff_id', 'date', name='uq_staff_attendance_date'),)


class StudentAttendance(db.Model):
    __tablename__ = 'student_attendance'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.class_id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.section_id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    period_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    marked_by = db.Column(db.Integer, db.ForeignKey('staff.staff_id'), nullable=True)
    marked_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    student = db.relationship('Student')
    __table_args__ = (db.UniqueConstraint('student_id', 'date', 'period_number', name='uq_student_attendance_period'),)


class Circular(db.Model):
    __tablename__ = 'circulars'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    attachment_path = db.Column(db.String(255), nullable=True)
    target_audience = db.Column(db.String(100), nullable=False, default='All Students')
    status = db.Column(db.String(50), nullable=False, default='Published') # Published, Draft, Scheduled
    scheduled_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships    
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id', ondelete='CASCADE'), nullable=True)

    # Relationships
    acknowledgements = db.relationship('CircularAcknowledgement', backref='circular', cascade='all, delete-orphan', lazy=True)
    views = db.relationship('CircularView', backref='circular', cascade='all, delete-orphan', lazy=True)
    student = db.relationship('Student', backref='individual_circulars', lazy=True)
    staff = db.relationship('Staff', backref='individual_circulars', lazy=True)

    @property
    def target_count(self):
        try:
            if self.target_audience == 'All Staff':
                return Staff.query.count()
            elif self.target_audience == 'All Students':
                return Student.query.count()
            elif self.target_audience == 'All Students & All Staff':
                return Student.query.count() + Staff.query.count()
            elif self.target_audience.startswith('Class '):
                cname = self.target_audience.replace('Class ', '').strip()
                rooms = ClassRoom.query.filter_by(class_name=cname).all()
                room_ids = [r.class_id for r in rooms]
                if room_ids:
                    return StudentAcademicDetail.query.filter(
                        StudentAcademicDetail.class_id.in_(room_ids),
                        StudentAcademicDetail.student_status == 'Active'
                    ).count()
        except Exception:
            pass
        return 0

    @property
    def ack_count(self):
        try:
            return CircularAcknowledgement.query.filter_by(circular_id=self.id).count()
        except Exception:
            return 0

    @property
    def view_count(self):
        try:
            return CircularView.query.filter_by(circular_id=self.id).count()
        except Exception:
            return 0

    def __repr__(self):
        return f"<Circular {self.title}>"


class CircularAcknowledgement(db.Model):
    __tablename__ = 'circular_acknowledgements'
    
    id = db.Column(db.Integer, primary_key=True)
    circular_id = db.Column(db.Integer, db.ForeignKey('circulars.id', ondelete='CASCADE'), nullable=False)
    user_type = db.Column(db.String(50), nullable=False) # 'staff' or 'student'
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id', ondelete='CASCADE'), nullable=True)
    acknowledged_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', backref='circular_acknowledgements', lazy=True)
    staff = db.relationship('Staff', backref='circular_acknowledgements', lazy=True)


class CircularView(db.Model):
    __tablename__ = 'circular_views'
    
    id = db.Column(db.Integer, primary_key=True)
    circular_id = db.Column(db.Integer, db.ForeignKey('circulars.id', ondelete='CASCADE'), nullable=False)
    user_type = db.Column(db.String(50), nullable=False) # 'staff' or 'student'
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id', ondelete='CASCADE'), nullable=True)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', backref='circular_views', lazy=True)
    staff = db.relationship('Staff', backref='circular_views', lazy=True)


class Announcement(db.Model):
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False, default='General') # General, Academic, Event, Holiday
    target_audience = db.Column(db.String(100), nullable=False, default='All Students')
    status = db.Column(db.String(50), nullable=False, default='Published') # Published, Draft, Scheduled, Archived
    scheduled_date = db.Column(db.DateTime, nullable=True)
    attachment_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Announcement {self.title}>"


class PushNotification(db.Model):
    __tablename__ = 'push_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    target_audience = db.Column(db.String(100), nullable=False, default='All Students')
    status = db.Column(db.String(50), nullable=False, default='Sent') # Sent, Draft, Scheduled
    scheduled_date = db.Column(db.DateTime, nullable=True)
    image_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PushNotification {self.title}>"


class Notice(db.Model):
    __tablename__ = 'notices'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False, default='General') # General, Academic, Event, Holiday
    target_audience = db.Column(db.String(100), nullable=False, default='All Students')
    status = db.Column(db.String(50), nullable=False, default='Published') # Published, Draft, Archived
    publish_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime, nullable=True)
    attachment_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Notice {self.title}>"


class WhatsAppLog(db.Model):
    __tablename__ = 'whatsapp_logs'
    id = db.Column(db.Integer, primary_key=True)
    recipient = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Sent') # 'Draft', 'Sent'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<WhatsAppLog to {self.recipient}>"


class EmailLog(db.Model):
    __tablename__ = 'email_logs'
    id = db.Column(db.Integer, primary_key=True)
    recipient = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Sent') # 'Draft', 'Sent'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<EmailLog to {self.recipient}>"


# --- Helper Functions ---
def parse_date(date_str):
    if not date_str or date_str.strip() == '':
        return None
    try:
        return datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
    except ValueError:
        return None


# --- Application Routes ---

@app.route('/')
def index():
    if session.get('admin_logged_in'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('admin_logged_in'):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash("Please fill in both fields.", "danger")
            return render_template('admin/login.html')

        admin = Admin.query.filter_by(username=username).first()

        if admin and check_password_hash(admin.password_hash, password):
            session['admin_logged_in'] = True
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            flash("Welcome back, Administrator! Login successful.", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password.", "danger")

    return render_template('admin/login.html')


@app.route('/dashboard')
def dashboard():
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    return render_template('admin/dashboard.html', admin_username=session.get('admin_username'))


# --- Academic Years Routes ---

@app.route('/academic-years', methods=['GET', 'POST'])
def academic_years():
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        start_date_str = request.form.get('start_date', '')
        end_date_str = request.form.get('end_date', '')
        is_current = 'is_current' in request.form
        
        start_date = parse_date(start_date_str)
        end_date = parse_date(end_date_str)
        
        years_in_name = [int(y) for y in re.findall(r'\b\d{4}\b', name)]
        
        if not name or not start_date or not end_date:
            flash("Please fill in all required fields correctly.", "danger")
        elif not re.match(r'^[\d-]+$', name):
            flash("Academic Year Name can only contain numbers and hyphens (e.g. 2026-2027).", "danger")
        elif start_date >= end_date:
            flash("End Date must be after Start Date.", "danger")
        elif years_in_name and (start_date.year < min(years_in_name) or end_date.year > max(years_in_name)):
            flash(f"Start and End dates must fall within the years specified in the name ({min(years_in_name)}-{max(years_in_name)}).", "danger")
        else:
            existing = AcademicYear.query.filter_by(name=name).first()
            if existing:
                flash(f"Academic Year '{name}' already exists.", "danger")
            else:
                if is_current:
                    db.session.query(AcademicYear).update({AcademicYear.is_current: False})
                
                new_year = AcademicYear(
                    name=name,
                    start_date=start_date,
                    end_date=end_date,
                    is_current=is_current
                )
                db.session.add(new_year)
                db.session.commit()
                flash("Academic Year created successfully!", "success")
                return redirect(url_for('academic_years'))
                
    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    
    query = AcademicYear.query
    if search_query:
        query = query.filter(AcademicYear.name.ilike(f'%{search_query}%'))
        
    pagination = query.order_by(AcademicYear.start_date.desc()).paginate(page=page, per_page=10, error_out=False)
    
    return render_template('admin/academic_years.html', 
                           years=pagination.items, 
                           pagination=pagination,
                           search_query=search_query,
                           admin_username=session.get('admin_username'))

@app.route('/academic-years/edit/<int:year_id>', methods=['GET', 'POST'])
def edit_academic_year(year_id):
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    year = AcademicYear.query.get_or_404(year_id)
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        start_date_str = request.form.get('start_date', '')
        end_date_str = request.form.get('end_date', '')
        is_current = 'is_current' in request.form
        
        start_date = parse_date(start_date_str)
        end_date = parse_date(end_date_str)
        
        years_in_name = [int(y) for y in re.findall(r'\b\d{4}\b', name)]
        
        if not name or not start_date or not end_date:
            flash("Please fill in all required fields correctly.", "danger")
        elif not re.match(r'^[\d-]+$', name):
            flash("Academic Year Name can only contain numbers and hyphens (e.g. 2026-2027).", "danger")
        elif start_date >= end_date:
            flash("End Date must be after Start Date.", "danger")
        elif years_in_name and (start_date.year < min(years_in_name) or end_date.year > max(years_in_name)):
            flash(f"Start and End dates must fall within the years specified in the name ({min(years_in_name)}-{max(years_in_name)}).", "danger")
        else:
            existing = AcademicYear.query.filter(AcademicYear.name == name, AcademicYear.id != year_id).first()
            if existing:
                flash(f"Academic Year '{name}' already exists.", "danger")
            else:
                if is_current and not year.is_current:
                    db.session.query(AcademicYear).update({AcademicYear.is_current: False})
                
                year.name = name
                year.start_date = start_date
                year.end_date = end_date
                year.is_current = is_current
                
                db.session.commit()
                flash("Academic Year updated successfully!", "success")
                return redirect(url_for('academic_years'))
                
    return render_template('admin/academic_year_edit.html', year=year, admin_username=session.get('admin_username'))

@app.route('/academic-years/delete/<int:year_id>', methods=['POST'])
def delete_academic_year(year_id):
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    year = AcademicYear.query.get_or_404(year_id)
    
    if year.is_current:
        flash("Cannot delete the currently active academic year.", "danger")
    else:
        db.session.delete(year)
        db.session.commit()
        flash("Academic Year deleted successfully.", "success")
        
    return redirect(url_for('academic_years'))

# --- Staff Settings Routes ---

@app.route('/admin/teacher_categories')
def teacher_categories():
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    categories = TeacherCategory.query.order_by(TeacherCategory.name).all()
    return render_template('admin/teacher_categories.html', categories=categories, admin_username=session.get('admin_username'))

@app.route('/admin/teacher_categories/add', methods=['POST'])
def add_teacher_category():
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    name = request.form.get('name', '').strip()
    short_form = request.form.get('short_form', '').strip().upper()
    if not short_form:
        short_form = None
    if name:
        if not TeacherCategory.query.filter_by(name=name).first():
            db.session.add(TeacherCategory(name=name, short_form=short_form))
            db.session.commit()
            flash("Teacher Category added successfully.", "success")
        else:
            flash("Teacher Category already exists.", "danger")
    return redirect(url_for('teacher_categories'))

@app.route('/admin/teacher_categories/delete/<int:id>', methods=['POST'])
def delete_teacher_category(id):
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    cat = TeacherCategory.query.get_or_404(id)
    db.session.delete(cat)
    db.session.commit()
    flash("Teacher Category deleted.", "success")
    return redirect(url_for('teacher_categories'))


@app.route('/admin/departments')
def departments():
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    departments = Department.query.order_by(Department.name).all()
    return render_template('admin/departments.html', departments=departments, admin_username=session.get('admin_username'))

@app.route('/admin/departments/add', methods=['POST'])
def add_department():
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    name = request.form.get('name', '').strip()
    short_form = request.form.get('short_form', '').strip().upper()
    if not short_form:
        short_form = None

    if name:
        if not Department.query.filter_by(name=name).first():
            db.session.add(Department(name=name, short_form=short_form))
            db.session.commit()
            flash("Department added successfully.", "success")
        else:
            flash("Department already exists.", "danger")
    return redirect(url_for('departments'))

@app.route('/admin/departments/delete/<int:id>', methods=['POST'])
def delete_department(id):
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    dept = Department.query.get_or_404(id)
    if dept.staff_members:
        flash("Cannot delete department because it has staff members assigned to it.", "danger")
        return redirect(url_for('departments'))
    db.session.delete(dept)
    db.session.commit()
    flash("Department deleted.", "success")
    return redirect(url_for('departments'))


# --- Dynamic Setup Routes ---

@app.route('/admin/roles')
def roles():
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    roles = Role.query.order_by(Role.name).all()
    return render_template('admin/roles.html', roles=roles, admin_username=session.get('admin_username'))

@app.route('/admin/roles/add', methods=['POST'])
def add_role():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
        
    name = request.form.get('name', '').strip()
    short_form = request.form.get('short_form', '').strip().upper()
    if not short_form:
        short_form = None
    
    if not name:
        flash("Role Name is required.", "danger")
        return redirect(url_for('roles'))
        
    existing_role = Role.query.filter_by(name=name).first()
    if existing_role:
        flash(f"Role '{name}' already exists.", "warning")
        return redirect(url_for('roles'))
        
    new_role = Role(name=name)
    db.session.add(new_role)
    db.session.commit()
    
    flash(f"Role '{name}' added successfully!", "success")
    return redirect(url_for('roles'))

@app.route('/admin/roles/delete/<int:id>', methods=['POST'])
def delete_role(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
        
    role = Role.query.get_or_404(id)
    name = role.name
    
    try:
        db.session.delete(role)
        db.session.commit()
        flash(f"Role '{name}' deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Cannot delete Role '{name}' as it might be assigned to staff members.", "danger")
        
    return redirect(url_for('roles'))

@app.route('/admin/degree_levels')
def degree_levels():
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    degree_levels = DegreeLevel.query.order_by(DegreeLevel.name).all()
    return render_template('admin/degree_levels.html', degree_levels=degree_levels, admin_username=session.get('admin_username'))

@app.route('/admin/degree_levels/add', methods=['POST'])
def add_degree_level():
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    name = request.form.get('name', '').strip()
    short_form = request.form.get('short_form', '').strip().upper()
    if not short_form:
        short_form = None
    if name:
        if not DegreeLevel.query.filter_by(name=name).first():
            db.session.add(DegreeLevel(name=name, short_form=short_form))
            db.session.commit()
            flash("Degree Level added successfully.", "success")
        else:
            flash("Degree Level already exists.", "danger")
    return redirect(url_for('degree_levels'))

@app.route('/admin/degree_levels/delete/<int:id>', methods=['POST'])
def delete_degree_level(id):
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    obj = DegreeLevel.query.get_or_404(id)
    if obj.specifications:
        flash("Cannot delete degree level because it has specifications assigned to it.", "danger")
        return redirect(url_for('degree_levels'))
    db.session.delete(obj)
    db.session.commit()
    flash("Degree Level deleted.", "success")
    return redirect(url_for('degree_levels'))

@app.route('/admin/specifications')
def specifications():
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    specifications = Specification.query.join(DegreeLevel).order_by(DegreeLevel.name, Specification.name).all()
    degree_levels = DegreeLevel.query.order_by(DegreeLevel.name).all()
    return render_template('admin/specifications.html', specifications=specifications, degree_levels=degree_levels, admin_username=session.get('admin_username'))

@app.route('/admin/specifications/add', methods=['POST'])
def add_specification():
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    name = request.form.get('name', '').strip()
    short_form = request.form.get('short_form', '').strip().upper()
    if not short_form:
        short_form = None
    degree_level_id = request.form.get('degree_level_id')
    if name and degree_level_id:
        if not Specification.query.filter_by(name=name, degree_level_id=degree_level_id).first():
            db.session.add(Specification(name=name, degree_level_id=degree_level_id, short_form=short_form))
            db.session.commit()
            flash("Specification added successfully.", "success")
        else:
            flash("Specification already exists for this degree level.", "danger")
    else:
        flash("Please provide all required fields.", "warning")
    return redirect(url_for('specifications'))

@app.route('/admin/specifications/delete/<int:id>', methods=['POST'])
def delete_specification(id):
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    obj = Specification.query.get_or_404(id)
    db.session.delete(obj)
    db.session.commit()
    flash("Specification deleted.", "success")
    return redirect(url_for('specifications'))

@app.route('/admin/major_subjects')
def major_subjects():
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    major_subjects = MajorSubject.query.order_by(MajorSubject.name).all()
    return render_template('admin/major_subjects.html', major_subjects=major_subjects, admin_username=session.get('admin_username'))

@app.route('/admin/major_subjects/add', methods=['POST'])
def add_major_subject():
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    name = request.form.get('name', '').strip()
    short_form = request.form.get('short_form', '').strip().upper()
    if not short_form:
        short_form = None
    if name:
        if not MajorSubject.query.filter_by(name=name).first():
            db.session.add(MajorSubject(name=name, short_form=short_form))
            db.session.commit()
            flash("Major / Subject added successfully.", "success")
        else:
            flash("Major / Subject already exists.", "danger")
    return redirect(url_for('major_subjects'))

@app.route('/admin/major_subjects/delete/<int:id>', methods=['POST'])
def delete_major_subject(id):
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    obj = MajorSubject.query.get_or_404(id)
    db.session.delete(obj)
    db.session.commit()
    flash("Major / Subject deleted.", "success")
    return redirect(url_for('major_subjects'))



@app.route('/admin/qualifications')
def qualifications():
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    qualifications = Qualification.query.order_by(Qualification.name).all()
    degree_levels = DegreeLevel.query.order_by(DegreeLevel.name).all()
    specifications = Specification.query.order_by(Specification.name).all()
    major_subjects = MajorSubject.query.order_by(MajorSubject.name).all()
    return render_template('admin/qualifications.html', qualifications=qualifications, admin_username=session.get('admin_username'))

@app.route('/admin/qualifications/add', methods=['POST'])
def add_qualification():
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    name = request.form.get('name', '').strip()
    if name:
        if not Qualification.query.filter_by(name=name).first():
            db.session.add(Qualification(name=name))
            db.session.commit()
            flash("Qualification added successfully.", "success")
        else:
            flash("Qualification already exists.", "danger")
    return redirect(url_for('qualifications'))

@app.route('/admin/qualifications/delete/<int:id>', methods=['POST'])
def delete_qualification(id):
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    qual = Qualification.query.get_or_404(id)
    db.session.delete(qual)
    db.session.commit()
    flash("Qualification deleted.", "success")
    return redirect(url_for('qualifications'))



# --- Staff Management Routes ---

@app.route('/admin/assign_role')
def assign_role():
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    staff_members = Staff.query.order_by(Staff.first_name).all()
    roles = Role.query.order_by(Role.name).all()
    
    return render_template('admin/assign_role.html', 
                           staff_members=staff_members, 
                           roles=roles,
                           admin_username=session.get('admin_username'))

@app.route('/admin/assign_role/<int:staff_id>', methods=['POST'])
def assign_role_post(staff_id):
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    staff = Staff.query.get_or_404(staff_id)
    role_id = request.form.get('role_id')
    
    if role_id:
        selected_role = Role.query.get(int(role_id))
        if selected_role and selected_role.name == 'HOD':
            existing_hod = Staff.query.join(Role).filter(Staff.department_id == staff.department_id, Role.name == 'HOD', Staff.staff_id != staff.staff_id).first()
            if existing_hod:
                flash(f"Department already has a HOD ({existing_hod.first_name}). Only one HOD allowed per department.", "danger")
                return redirect(url_for('assign_role'))
                
        staff.role_id = int(role_id)
        db.session.commit()
        flash(f"Role updated successfully for {staff.first_name}.", "success")
    else:
        flash("Please select a valid role.", "danger")
        
    return redirect(url_for('assign_role'))

@app.route('/staff')
def staff_list():
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    all_staff = Staff.query.order_by(Staff.staff_id.desc()).all()
    return render_template('admin/staff_list.html', staff_members=all_staff, admin_username=session.get('admin_username'))


@app.route('/staff/register', methods=['GET', 'POST'])
def register_staff():
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    departments = Department.query.order_by(Department.name).all()
    roles = Role.query.order_by(Role.name).all()
    categories = TeacherCategory.query.order_by(TeacherCategory.name).all()
    qualifications = Qualification.query.order_by(Qualification.name).all()
    degree_levels = DegreeLevel.query.order_by(DegreeLevel.name).all()
    specifications = Specification.query.order_by(Specification.name).all()
    major_subjects = MajorSubject.query.order_by(MajorSubject.name).all()
    
    if request.method == 'POST':
        employee_id = request.form.get('employee_id', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip() or None
        gender = request.form.get('gender', '')
        date_of_birth_str = request.form.get('date_of_birth', '')
        mobile = request.form.get('mobile', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        
        department_id = request.form.get('department_id')
        role_id = None
        
        designation = request.form.get('designation', '').strip()
        
        experience_level = request.form.get('experience_level', 'Fresher')
        joining_date_str = request.form.get('joining_date', '')
        employment_type = request.form.get('employment_type', '')
        status = request.form.get('status', 'Active')
        
        date_of_termination_str = request.form.get('date_of_termination', '')
        termination_reason = request.form.get('termination_reason', '').strip() or None
        relieving_date_str = request.form.get('relieving_date', '')
        
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        teacher_category = request.form.get('teacher_category', '').strip() or None
        
        basic_salary_str = request.form.get('basic_salary', '').strip()
        basic_salary = float(basic_salary_str) if basic_salary_str else None
        aadhar_number = request.form.get('aadhar_number', '').strip() or None
        account_holder_name = request.form.get('account_holder_name', '').strip() or None
        bank_name = request.form.get('bank_name', '').strip() or None
        account_number = request.form.get('account_number', '').strip() or None
        ifsc_code = request.form.get('ifsc_code', '').strip() or None
        
        photo_filename = None
        photo_file = request.files.get('photo')
        if photo_file and photo_file.filename != '':
            filename = secure_filename(photo_file.filename)
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            photo_filename = f"staff_{employee_id}.{ext}" if ext else f"staff_{employee_id}"
            photo_file.save(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], 'staff', photo_filename))
            
        aadhar_document = None
        aadhar_file = request.files.get('aadhar_document')
        if aadhar_file and aadhar_file.filename != '':
            filename = secure_filename(aadhar_file.filename)
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            aadhar_document = f"staff_{employee_id}_aadhar.{ext}" if ext else f"staff_{employee_id}_aadhar"
            aadhar_file.save(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], 'staff', 'documents', aadhar_document))
            
        bank_document = None
        bank_file = request.files.get('bank_document')
        if bank_file and bank_file.filename != '':
            filename = secure_filename(bank_file.filename)
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            bank_document = f"staff_{employee_id}_bank.{ext}" if ext else f"staff_{employee_id}_bank"
            bank_file.save(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], 'staff', 'documents', bank_document))
        
        if not (employee_id and first_name and gender and date_of_birth_str and mobile 
                and email and address and department_id and designation 
                and joining_date_str and employment_type and status and username and password):
            flash("Please fill in all required fields.", "danger")
            return render_template('admin/register_staff.html', departments=departments, roles=roles, categories=categories, qualifications=qualifications, degree_levels=degree_levels, specifications=specifications, major_subjects=major_subjects, admin_username=session.get('admin_username'))
            
        if not mobile.isdigit() or len(mobile) != 10:
            flash("Mobile number must be exactly 10 digits.", "danger")
            return render_template('admin/register_staff.html', departments=departments, roles=roles, categories=categories, qualifications=qualifications, degree_levels=degree_levels, specifications=specifications, major_subjects=major_subjects, admin_username=session.get('admin_username'))
            
        dup_employee = Staff.query.filter_by(employee_id=employee_id).first()
        if dup_employee:
            flash(f"Staff member with Employee ID '{employee_id}' already exists.", "danger")
            return render_template('admin/register_staff.html', departments=departments, roles=roles, categories=categories, qualifications=qualifications, degree_levels=degree_levels, specifications=specifications, major_subjects=major_subjects, admin_username=session.get('admin_username'))
            
        dup_username = Staff.query.filter_by(username=username).first()
        if dup_username:
            flash(f"Username '{username}' is already taken.", "danger")
            return render_template('admin/register_staff.html', departments=departments, roles=roles, categories=categories, qualifications=qualifications, degree_levels=degree_levels, specifications=specifications, major_subjects=major_subjects, admin_username=session.get('admin_username'))

        dob = parse_date(date_of_birth_str)
        if not dob:
            flash("Invalid date of birth format.", "danger")
            return render_template('admin/register_staff.html', departments=departments, roles=roles, categories=categories, qualifications=qualifications, degree_levels=degree_levels, specifications=specifications, major_subjects=major_subjects, admin_username=session.get('admin_username'))
            
        today = datetime.now().date()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 18:
            flash("Staff member must be at least 18 years old.", "danger")
            return render_template('admin/register_staff.html', departments=departments, roles=roles, categories=categories, qualifications=qualifications, degree_levels=degree_levels, specifications=specifications, major_subjects=major_subjects, admin_username=session.get('admin_username'))

        joining_date = parse_date(joining_date_str)
        date_of_termination = parse_date(date_of_termination_str)
        relieving_date = parse_date(relieving_date_str)
        
        

        hashed_pw = generate_password_hash(password)
        
        try:
            new_staff = Staff(
                employee_id=employee_id,
                first_name=first_name,
                last_name=last_name,
                gender=gender,
                date_of_birth=dob,
                mobile=mobile,
                email=email,
                address=address,
                teacher_category=teacher_category,
                photo=photo_filename,
                department_id=int(department_id),
                
                designation=designation,
                
                joining_date=joining_date,
                employment_type=employment_type,
                status=status,
            basic_salary=basic_salary,
            aadhar_number=aadhar_number,
            aadhar_document=aadhar_document,
            account_holder_name=account_holder_name,
            bank_name=bank_name,
            account_number=account_number,
            ifsc_code=ifsc_code,
            bank_document=bank_document,
                date_of_termination=date_of_termination,
                termination_reason=termination_reason,
                relieving_date=relieving_date,
                username=username,
                password_hash=hashed_pw
            )
            db.session.add(new_staff)
            db.session.commit()
            
            # Process Qualifications
            degree_levels = request.form.getlist('degree_level[]')
            specifications = request.form.getlist('specification[]')
            majors = request.form.getlist('major[]')
            college_names = request.form.getlist('college_name[]')
            passing_years = request.form.getlist('passing_year[]')
            cgpa_percentages = request.form.getlist('cgpa_percentage[]')
            
            for i in range(len(degree_levels)):
                if degree_levels[i].strip():
                    qual = StaffQualification(
                        staff_id=new_staff.staff_id,
                        degree_level=degree_levels[i].strip(),
                        specification=specifications[i].strip() if i < len(specifications) and specifications[i].strip() else None,
                        major=majors[i].strip() if i < len(majors) and majors[i].strip() else None,
                        college_name=college_names[i].strip() if i < len(college_names) and college_names[i].strip() else None,
                        passing_year=passing_years[i].strip() if i < len(passing_years) and passing_years[i].strip() else None,
                        cgpa_percentage=cgpa_percentages[i].strip() if i < len(cgpa_percentages) and cgpa_percentages[i].strip() else None
                    )
                    db.session.add(qual)
            db.session.commit()

            flash(f"Staff member {first_name} registered successfully!", "success")
            return redirect(url_for('staff_list'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error registering staff member: {str(e)}", "danger")
            
    return render_template('admin/register_staff.html', departments=departments, roles=roles, categories=categories, qualifications=qualifications, degree_levels=degree_levels, specifications=specifications, major_subjects=major_subjects, admin_username=session.get('admin_username'))


@app.route('/staff/edit/<int:staff_id>', methods=['GET', 'POST'])
def edit_staff(staff_id):
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    staff = Staff.query.get_or_404(staff_id)
    departments = Department.query.order_by(Department.name).all()
    roles = Role.query.order_by(Role.name).all()
    categories = TeacherCategory.query.order_by(TeacherCategory.name).all()
    qualifications = Qualification.query.order_by(Qualification.name).all()
    degree_levels = DegreeLevel.query.order_by(DegreeLevel.name).all()
    specifications = Specification.query.order_by(Specification.name).all()
    major_subjects = MajorSubject.query.order_by(MajorSubject.name).all()
    
    if request.method == 'POST':
        employee_id = request.form.get('employee_id', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip() or None
        gender = request.form.get('gender', '')
        date_of_birth_str = request.form.get('date_of_birth', '')
        mobile = request.form.get('mobile', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        
        teacher_category = request.form.get('teacher_category', '').strip() or None
        department_id = request.form.get('department_id')
        role_id = None
        
        designation = request.form.get('designation', '').strip()
        
        experience_level = request.form.get('experience_level', 'Fresher')
        experience_types = request.form.getlist('experience_type[]')
        experience_year_values = request.form.getlist('experience_years[]')
        previous_work_details = request.form.getlist('previous_work_details[]')
        degree_level_values = request.form.getlist('degree_level[]')
        specification_values = request.form.getlist('specification[]')
        major_values = request.form.getlist('major[]')
        college_name_values = request.form.getlist('college_name[]')
        passing_year_values = request.form.getlist('passing_year[]')
        cgpa_percentage_values = request.form.getlist('cgpa_percentage[]')
        joining_date_str = request.form.get('joining_date', '')
        employment_type = request.form.get('employment_type', '')
        status = request.form.get('status', 'Active')
        
        date_of_termination_str = request.form.get('date_of_termination', '')
        termination_reason = request.form.get('termination_reason', '').strip() or None
        relieving_date_str = request.form.get('relieving_date', '')
        
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        basic_salary_str = request.form.get('basic_salary', '').strip()
        basic_salary = float(basic_salary_str) if basic_salary_str else None
        aadhar_number = request.form.get('aadhar_number', '').strip() or None
        account_holder_name = request.form.get('account_holder_name', '').strip() or None
        bank_name = request.form.get('bank_name', '').strip() or None
        account_number = request.form.get('account_number', '').strip() or None
        ifsc_code = request.form.get('ifsc_code', '').strip() or None
        
        photo_file = request.files.get('photo')
        if photo_file and photo_file.filename != '':
            filename = secure_filename(photo_file.filename)
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            photo_filename = f"staff_{employee_id}.{ext}" if ext else f"staff_{employee_id}"
            photo_file.save(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], 'staff', photo_filename))
            staff.photo = photo_filename
            
        aadhar_file = request.files.get('aadhar_document')
        if aadhar_file and aadhar_file.filename != '':
            filename = secure_filename(aadhar_file.filename)
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            aadhar_document = f"staff_{employee_id}_aadhar.{ext}" if ext else f"staff_{employee_id}_aadhar"
            aadhar_file.save(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], 'staff', 'documents', aadhar_document))
            staff.aadhar_document = aadhar_document
            
        bank_file = request.files.get('bank_document')
        if bank_file and bank_file.filename != '':
            filename = secure_filename(bank_file.filename)
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            bank_document = f"staff_{employee_id}_bank.{ext}" if ext else f"staff_{employee_id}_bank"
            bank_file.save(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], 'staff', 'documents', bank_document))
            staff.bank_document = bank_document
        
        if not (employee_id and first_name and gender and date_of_birth_str and mobile 
                and email and address and department_id and designation 
                and joining_date_str and employment_type and status and username):
            flash("Please fill in all required fields.", "danger")
            return render_template('admin/edit_staff.html', staff=staff, departments=departments, roles=roles, categories=categories, qualifications=qualifications, degree_levels=degree_levels, specifications=specifications, major_subjects=major_subjects, admin_username=session.get('admin_username'))
            
        if not mobile.isdigit() or len(mobile) != 10:
            flash("Mobile number must be exactly 10 digits.", "danger")
            return render_template('admin/edit_staff.html', staff=staff, departments=departments, roles=roles, categories=categories, qualifications=qualifications, degree_levels=degree_levels, specifications=specifications, major_subjects=major_subjects, admin_username=session.get('admin_username'))
            
        dup_employee = Staff.query.filter(Staff.employee_id == employee_id, Staff.staff_id != staff_id).first()
        if dup_employee:
            flash(f"Staff member with Employee ID '{employee_id}' already exists.", "danger")
            return render_template('admin/edit_staff.html', staff=staff, departments=departments, roles=roles, categories=categories, qualifications=qualifications, degree_levels=degree_levels, specifications=specifications, major_subjects=major_subjects, admin_username=session.get('admin_username'))
            
        dup_username = Staff.query.filter(Staff.username == username, Staff.staff_id != staff_id).first()
        if dup_username:
            flash(f"Username '{username}' is already taken.", "danger")
            return render_template('admin/edit_staff.html', staff=staff, departments=departments, roles=roles, categories=categories, qualifications=qualifications, degree_levels=degree_levels, specifications=specifications, major_subjects=major_subjects, admin_username=session.get('admin_username'))

        dob = parse_date(date_of_birth_str)
        if not dob:
            flash("Invalid date of birth format.", "danger")
            return render_template('admin/edit_staff.html', staff=staff, departments=departments, roles=roles, categories=categories, qualifications=qualifications, degree_levels=degree_levels, specifications=specifications, major_subjects=major_subjects, admin_username=session.get('admin_username'))
            
        today = datetime.now().date()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 18:
            flash("Staff member must be at least 18 years old.", "danger")
            return render_template('admin/edit_staff.html', staff=staff, departments=departments, roles=roles, categories=categories, qualifications=qualifications, degree_levels=degree_levels, specifications=specifications, major_subjects=major_subjects, admin_username=session.get('admin_username'))

        joining_date = parse_date(joining_date_str)
        date_of_termination = parse_date(date_of_termination_str)
        relieving_date = parse_date(relieving_date_str)
        
        
        
        try:
            staff.employee_id = employee_id
            staff.first_name = first_name
            staff.last_name = last_name
            staff.gender = gender
            staff.date_of_birth = dob
            staff.mobile = mobile
            staff.email = email
            staff.address = address
            staff.teacher_category = teacher_category
            staff.department_id = int(department_id)
            
            staff.designation = designation
            staff.experience_level = experience_level
            # Replace the editable detail rows atomically so removed rows do not
            # remain attached to the staff member.
            staff.experiences.clear()
            if experience_level == 'Experienced':
                for index, experience_type in enumerate(experience_types):
                    experience_type = experience_type.strip()
                    if not experience_type:
                        continue
                    years_value = experience_year_values[index].strip() if index < len(experience_year_values) else ''
                    try:
                        experience_years = int(years_value) if years_value else None
                    except ValueError:
                        raise ValueError('Experience years must be a whole number.')
                    staff.experiences.append(StaffExperience(
                        experience_type=experience_type,
                        experience_years=experience_years,
                        previous_work_details=(previous_work_details[index].strip() if index < len(previous_work_details) and previous_work_details[index].strip() else None)
                    ))
            # Preserve the legacy fields for existing reports that still read them.
            first_experience = staff.experiences[0] if staff.experiences else None
            staff.experience_type = first_experience.experience_type if first_experience else None
            staff.experience_years = first_experience.experience_years if first_experience else None
            staff.previous_work_details = first_experience.previous_work_details if first_experience else None

            staff.qualifications.clear()
            for index, degree_level in enumerate(degree_level_values):
                degree_level = degree_level.strip()
                if not degree_level:
                    continue
                staff.qualifications.append(StaffQualification(
                    degree_level=degree_level,
                    specification=(specification_values[index].strip() if index < len(specification_values) and specification_values[index].strip() else None),
                    major=(major_values[index].strip() if index < len(major_values) and major_values[index].strip() else None),
                    college_name=(college_name_values[index].strip() if index < len(college_name_values) and college_name_values[index].strip() else None),
                    passing_year=(passing_year_values[index].strip() if index < len(passing_year_values) and passing_year_values[index].strip() else None),
                    cgpa_percentage=(cgpa_percentage_values[index].strip() if index < len(cgpa_percentage_values) and cgpa_percentage_values[index].strip() else None)
                ))
            staff.joining_date = joining_date
            staff.employment_type = employment_type
            staff.status = status
            staff.basic_salary = basic_salary
            staff.aadhar_number = aadhar_number
            staff.account_holder_name = account_holder_name
            staff.bank_name = bank_name
            staff.account_number = account_number
            staff.ifsc_code = ifsc_code
            staff.date_of_termination = date_of_termination
            staff.termination_reason = termination_reason
            staff.relieving_date = relieving_date
            staff.username = username
            
            if password:
                staff.password_hash = generate_password_hash(password)
                
            db.session.commit()
            flash(f"Staff member {first_name} updated successfully!", "success")
            return redirect(url_for('staff_list'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating staff member: {str(e)}", "danger")
            
    return render_template('admin/edit_staff.html', staff=staff, departments=departments, roles=roles, categories=categories, qualifications=qualifications, degree_levels=degree_levels, specifications=specifications, major_subjects=major_subjects, admin_username=session.get('admin_username'))


# --- Classes & Sections Management Routes ---

@app.route('/classes', methods=['GET', 'POST'])
def classes():
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    all_years = AcademicYear.query.order_by(AcademicYear.start_date.desc()).all()
    active_year = next((y for y in all_years if y.is_current), None)
    
    selected_year_id = request.args.get('year_id', type=int)
    if not selected_year_id and active_year:
        selected_year_id = active_year.id
        
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_class':
            class_name = request.form.get('class_name', '').strip()
            display_order_str = request.form.get('display_order', '0')
            capacity_str = request.form.get('capacity', '0')
            
            if not class_name:
                flash("Class Name is required.", "danger")
            else:
                existing = ClassRoom.query.filter_by(class_name=class_name, academic_year_id=selected_year_id).first()
                if existing:
                    flash(f"Class '{class_name}' already exists in the selected academic year.", "danger")
                else:
                    try:
                        display_order = int(display_order_str)
                    except ValueError:
                        display_order = 0
                        
                    try:
                        capacity = int(capacity_str)
                    except ValueError:
                        capacity = 0
                    
                    new_class = ClassRoom(class_name=class_name, display_order=display_order, capacity=capacity, academic_year_id=selected_year_id)
                    db.session.add(new_class)
                    db.session.commit()
                    flash(f"Class '{class_name}' created successfully!", "success")
                    return redirect(url_for('classes', year_id=selected_year_id))
                    
        elif action == 'edit_class':
            class_id = request.form.get('class_id', type=int)
            class_name = request.form.get('class_name', '').strip()
            display_order_str = request.form.get('display_order', '0')
            capacity_str = request.form.get('capacity', '0')
            
            if class_id and class_name:
                cls_obj = ClassRoom.query.get(class_id)
                if cls_obj:
                    existing = ClassRoom.query.filter(ClassRoom.class_name == class_name, ClassRoom.academic_year_id == cls_obj.academic_year_id, ClassRoom.class_id != class_id).first()
                    if existing:
                        flash(f"Class name '{class_name}' is already taken in this academic year.", "danger")
                    else:
                        cls_obj.class_name = class_name
                        try:
                            cls_obj.display_order = int(display_order_str)
                        except ValueError:
                            pass
                        try:
                            cls_obj.capacity = int(capacity_str)
                        except ValueError:
                            pass
                        db.session.commit()
                        flash("Class updated successfully.", "success")
            return redirect(url_for('classes', year_id=selected_year_id))
                    
        elif action == 'add_section':
            class_id = request.form.get('class_id')
            section_name = request.form.get('section_name', '').strip()
            academic_year_id = request.form.get('academic_year_id')
            
            if not class_id or not section_name or not academic_year_id:
                flash("Please fill in Class, Section Name, and Academic Year.", "danger")
            else:
                # Check for duplicate section in the same class and academic year
                existing = Section.query.filter_by(class_id=int(class_id), section_name=section_name, academic_year_id=int(academic_year_id)).first()
                if existing:
                    flash(f"Section '{section_name}' already exists in this class for the selected year.", "danger")
                else:
                    new_section = Section(class_id=int(class_id), section_name=section_name, academic_year_id=int(academic_year_id))
                    db.session.add(new_section)
                    db.session.commit()
                    flash(f"Section '{section_name}' added successfully!", "success")
                    return redirect(url_for('classes', year_id=academic_year_id))
                    
        elif action == 'edit_section':
            section_id = request.form.get('section_id', type=int)
            section_name = request.form.get('section_name', '').strip()
            
            if section_id and section_name:
                sec_obj = Section.query.get(section_id)
                if sec_obj:
                    existing = Section.query.filter(Section.class_id == sec_obj.class_id, Section.academic_year_id == sec_obj.academic_year_id, Section.section_name == section_name, Section.section_id != section_id).first()
                    if existing:
                        flash(f"Section '{section_name}' already exists in this class.", "danger")
                    else:
                        sec_obj.section_name = section_name
                        db.session.commit()
                        flash("Section updated successfully.", "success")
            return redirect(url_for('classes', year_id=selected_year_id))
                    
        elif action == 'delete_class':
            class_id = request.form.get('class_id', type=int)
            if class_id:
                cls_obj = ClassRoom.query.get(class_id)
                if cls_obj:
                    try:
                        db.session.delete(cls_obj)
                        db.session.commit()
                        flash(f"Class '{cls_obj.class_name}' deleted successfully.", "success")
                    except IntegrityError:
                        db.session.rollback()
                        flash(f"Cannot delete class '{cls_obj.class_name}' because there are students or other records tied to it.", "danger")
            return redirect(url_for('classes', year_id=selected_year_id))
            
        elif action == 'delete_section':
            section_id = request.form.get('section_id', type=int)
            if section_id:
                sec_obj = Section.query.get(section_id)
                if sec_obj:
                    try:
                        db.session.delete(sec_obj)
                        db.session.commit()
                        flash(f"Section '{sec_obj.section_name}' deleted successfully.", "success")
                    except IntegrityError:
                        db.session.rollback()
                        flash(f"Cannot delete section '{sec_obj.section_name}' because there are students or other records tied to it.", "danger")
            return redirect(url_for('classes', year_id=selected_year_id))

    all_classes = ClassRoom.query.filter_by(academic_year_id=selected_year_id).order_by(ClassRoom.display_order, ClassRoom.class_name).all()
    # For rendering, we will let the template filter sections by the selected year
    
    return render_template('admin/classes.html', 
                           classrooms=all_classes, 
                           all_years=all_years,
                           selected_year_id=selected_year_id,
                           admin_username=session.get('admin_username'))


# --- Student Management Routes ---

@app.route('/students')
def students_list():
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    # Join queries to fetch students along with their class, section and status for current/any academic year
    students_query = db.session.query(
        Student, StudentAcademicDetail, ClassRoom, Section, AcademicYear
    ).join(
        StudentAcademicDetail, Student.student_id == StudentAcademicDetail.student_id
    ).join(
        ClassRoom, StudentAcademicDetail.class_id == ClassRoom.class_id
    ).join(
        Section, StudentAcademicDetail.section_id == Section.section_id
    ).join(
        AcademicYear, StudentAcademicDetail.academic_year_id == AcademicYear.id
    ).order_by(
        ClassRoom.display_order, Section.section_name, StudentAcademicDetail.roll_no, Student.first_name
    ).all()
    
    return render_template('admin/students_list.html', student_records=students_query, admin_username=session.get('admin_username'))


@app.route('/students/register', methods=['GET', 'POST'])
def register_student():
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    academic_years = AcademicYear.query.order_by(AcademicYear.name.desc()).all()
    classrooms = ClassRoom.query.order_by(ClassRoom.display_order, ClassRoom.class_name).all()
    sections = Section.query.order_by(Section.section_name).all()
    
    if request.method == 'POST':
        # 1. Student permanent info
        admission_no = request.form.get('admission_no', '').strip()
        aadhar_no = request.form.get('aadhar_no', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip() or None
        gender = request.form.get('gender', '')
        date_of_birth_str = request.form.get('date_of_birth', '')
        blood_group = request.form.get('blood_group', '').strip() or None
        photo = None  # To be added later if file upload requested
        father_name = request.form.get('father_name', '').strip()
        mother_name = request.form.get('mother_name', '').strip()
        parent_mobile = request.form.get('parent_mobile', '').strip()
        parent_email = request.form.get('parent_email', '').strip() or None
        address = request.form.get('address', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        photo_filename = None
        photo_file = request.files.get('photo')
        if photo_file and photo_file.filename != '':
            filename = secure_filename(photo_file.filename)
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            photo_filename = f"student_{admission_no}.{ext}" if ext else f"student_{admission_no}"
            photo_file.save(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], 'student', photo_filename))
        
        # Transfer Student info
        is_transfer_student = request.form.get('is_transfer_student') == 'on'
        previous_school_name = request.form.get('previous_school_name', '').strip() if is_transfer_student else None
        previous_school_address = request.form.get('previous_school_address', '').strip() if is_transfer_student else None
        previous_academic_performance = request.form.get('previous_academic_performance', '').strip() if is_transfer_student else None
        transfer_certificate_no = request.form.get('transfer_certificate_no', '').strip() if is_transfer_student else None
        
        # 2. Student academic details
        academic_year_id = request.form.get('academic_year_id')
        class_id = request.form.get('class_id')
        section_id = request.form.get('section_id')
        roll_no = request.form.get('roll_no', '').strip() or None
        student_status = request.form.get('student_status', 'Active')
        
        # Validation checks
        if not (admission_no and aadhar_no and first_name and gender and date_of_birth_str and father_name 
                and mother_name and parent_mobile and address and username and password 
                and academic_year_id and class_id and section_id and student_status):
            flash("Please fill in all required fields.", "danger")
            return render_template('admin/register_student.html', academic_years=academic_years, classrooms=classrooms, sections=sections, admin_username=session.get('admin_username'))
            
        if not parent_mobile.isdigit() or len(parent_mobile) != 10:
            flash("Parent Mobile number must be exactly 10 digits.", "danger")
            return render_template('admin/register_student.html', academic_years=academic_years, classrooms=classrooms, sections=sections, admin_username=session.get('admin_username'))

        if not aadhar_no.isdigit() or len(aadhar_no) != 12:
            flash("Aadhar number must be exactly 12 digits.", "danger")
            return render_template('admin/register_student.html', academic_years=academic_years, classrooms=classrooms, sections=sections, admin_username=session.get('admin_username'))

        # Check unique constraint on aadhar_no
        dup_aadhar = Student.query.filter_by(aadhar_no=aadhar_no).first()
        if dup_aadhar:
            flash(f"Student with Aadhar No '{aadhar_no}' already exists.", "danger")
            return render_template('admin/register_student.html', academic_years=academic_years, classrooms=classrooms, sections=sections, admin_username=session.get('admin_username'))

        dob = parse_date(date_of_birth_str)
        if not dob:
            flash("Invalid date of birth format.", "danger")
            return render_template('admin/register_student.html', academic_years=academic_years, classrooms=classrooms, sections=sections, admin_username=session.get('admin_username'))
        
        # Calculate age
        today = datetime.now().date()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 3:
            flash("Student must be at least 3 years old for admission.", "danger")
            return render_template('admin/register_student.html', academic_years=academic_years, classrooms=classrooms, sections=sections, admin_username=session.get('admin_username'))

        # Check uniqueness constraints
        dup_admission = Student.query.filter_by(admission_no=admission_no).first()
        if dup_admission:
            flash(f"Student with Admission No '{admission_no}' already exists.", "danger")
            return render_template('admin/register_student.html', academic_years=academic_years, classrooms=classrooms, sections=sections, admin_username=session.get('admin_username'))
            
        dup_username = Student.query.filter_by(username=username).first()
        if dup_username:
            flash(f"Username '{username}' is already taken.", "danger")
            return render_template('admin/register_student.html', academic_years=academic_years, classrooms=classrooms, sections=sections, admin_username=session.get('admin_username'))

        hashed_pw = generate_password_hash(password)
        
        try:
            # Create master student entry
            new_student = Student(
                admission_no=admission_no,
                aadhar_no=aadhar_no,
                first_name=first_name,
                last_name=last_name,
                gender=gender,
                date_of_birth=dob,
                blood_group=blood_group,
                photo=photo_filename,
                father_name=father_name,
                mother_name=mother_name,
                parent_mobile=parent_mobile,
                parent_email=parent_email,
                address=address,
                username=username,
                password_hash=hashed_pw,
                is_transfer_student=is_transfer_student,
                previous_school_name=previous_school_name,
                previous_school_address=previous_school_address,
                previous_academic_performance=previous_academic_performance,
                transfer_certificate_no=transfer_certificate_no
            )
            db.session.add(new_student)
            db.session.flush() # Flushes database transactions to get new_student.student_id
            
            # Create academic detail entry
            academic_detail = StudentAcademicDetail(
                student_id=new_student.student_id,
                academic_year_id=int(academic_year_id),
                class_id=int(class_id),
                section_id=int(section_id),
                roll_no=roll_no,
                student_status=student_status
            )
            db.session.add(academic_detail)
            db.session.commit()
            
            flash(f"Student {first_name} admitted successfully!", "success")
            return redirect(url_for('students_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error registering student: {str(e)}", "danger")
            
    return render_template('admin/register_student.html', academic_years=academic_years, classrooms=classrooms, sections=sections, admin_username=session.get('admin_username'))


@app.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    student = Student.query.get_or_404(student_id)
    academic_detail = StudentAcademicDetail.query.filter_by(student_id=student_id).first()
    
    academic_years = AcademicYear.query.order_by(AcademicYear.name.desc()).all()
    classrooms = ClassRoom.query.order_by(ClassRoom.display_order, ClassRoom.class_name).all()
    sections = Section.query.order_by(Section.section_name).all()
    
    if request.method == 'POST':
        admission_no = request.form.get('admission_no', '').strip()
        aadhar_no = request.form.get('aadhar_no', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip() or None
        gender = request.form.get('gender', '')
        date_of_birth_str = request.form.get('date_of_birth', '')
        blood_group = request.form.get('blood_group', '').strip() or None
        father_name = request.form.get('father_name', '').strip()
        mother_name = request.form.get('mother_name', '').strip()
        parent_mobile = request.form.get('parent_mobile', '').strip()
        parent_email = request.form.get('parent_email', '').strip() or None
        address = request.form.get('address', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        photo_file = request.files.get('photo')
        if photo_file and photo_file.filename != '':
            filename = secure_filename(photo_file.filename)
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            photo_filename = f"student_{admission_no}.{ext}" if ext else f"student_{admission_no}"
            photo_file.save(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], 'student', photo_filename))
            student.photo = photo_filename
        
        # Transfer Student info
        is_transfer_student = request.form.get('is_transfer_student') == 'on'
        previous_school_name = request.form.get('previous_school_name', '').strip() if is_transfer_student else None
        previous_school_address = request.form.get('previous_school_address', '').strip() if is_transfer_student else None
        previous_academic_performance = request.form.get('previous_academic_performance', '').strip() if is_transfer_student else None
        transfer_certificate_no = request.form.get('transfer_certificate_no', '').strip() if is_transfer_student else None
        
        academic_year_id = request.form.get('academic_year_id')
        class_id = request.form.get('class_id')
        section_id = request.form.get('section_id')
        roll_no = request.form.get('roll_no', '').strip() or None
        student_status = request.form.get('student_status', 'Active')
        
        if not (admission_no and aadhar_no and first_name and gender and date_of_birth_str and father_name 
                and mother_name and parent_mobile and address and username 
                and academic_year_id and class_id and section_id and student_status):
            flash("Please fill in all required fields.", "danger")
            return render_template('admin/edit_student.html', student=student, academic_detail=academic_detail, academic_years=academic_years, classrooms=classrooms, sections=sections, admin_username=session.get('admin_username'))
            
        if not parent_mobile.isdigit() or len(parent_mobile) != 10:
            flash("Parent Mobile number must be exactly 10 digits.", "danger")
            return render_template('admin/edit_student.html', student=student, academic_detail=academic_detail, academic_years=academic_years, classrooms=classrooms, sections=sections, admin_username=session.get('admin_username'))

        if not aadhar_no.isdigit() or len(aadhar_no) != 12:
            flash("Aadhar number must be exactly 12 digits.", "danger")
            return render_template('admin/edit_student.html', student=student, academic_detail=academic_detail, academic_years=academic_years, classrooms=classrooms, sections=sections, admin_username=session.get('admin_username'))

        # Check unique constraint on aadhar_no excluding self
        dup_aadhar = Student.query.filter(Student.aadhar_no == aadhar_no, Student.student_id != student_id).first()
        if dup_aadhar:
            flash(f"Student with Aadhar No '{aadhar_no}' already exists.", "danger")
            return render_template('admin/edit_student.html', student=student, academic_detail=academic_detail, academic_years=academic_years, classrooms=classrooms, sections=sections, admin_username=session.get('admin_username'))

        dob = parse_date(date_of_birth_str)
        if not dob:
            flash("Invalid date of birth format.", "danger")
            return render_template('admin/edit_student.html', student=student, academic_detail=academic_detail, academic_years=academic_years, classrooms=classrooms, sections=sections, admin_username=session.get('admin_username'))
            
        today = datetime.now().date()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 3:
            flash("Student must be at least 3 years old for admission.", "danger")
            return render_template('admin/edit_student.html', student=student, academic_detail=academic_detail, academic_years=academic_years, classrooms=classrooms, sections=sections, admin_username=session.get('admin_username'))

        dup_admission = Student.query.filter(Student.admission_no == admission_no, Student.student_id != student_id).first()
        if dup_admission:
            flash(f"Student with Admission No '{admission_no}' already exists.", "danger")
            return render_template('admin/edit_student.html', student=student, academic_detail=academic_detail, academic_years=academic_years, classrooms=classrooms, sections=sections, admin_username=session.get('admin_username'))
            
        dup_username = Student.query.filter(Student.username == username, Student.student_id != student_id).first()
        if dup_username:
            flash(f"Username '{username}' is already taken.", "danger")
            return render_template('admin/edit_student.html', student=student, academic_detail=academic_detail, academic_years=academic_years, classrooms=classrooms, sections=sections, admin_username=session.get('admin_username'))

        try:
            student.admission_no = admission_no
            student.aadhar_no = aadhar_no
            student.first_name = first_name
            student.last_name = last_name
            student.gender = gender
            student.date_of_birth = dob
            student.blood_group = blood_group
            student.father_name = father_name
            student.mother_name = mother_name
            student.parent_mobile = parent_mobile
            student.parent_email = parent_email
            student.address = address
            student.username = username
            
            student.is_transfer_student = is_transfer_student
            student.previous_school_name = previous_school_name
            student.previous_school_address = previous_school_address
            student.previous_academic_performance = previous_academic_performance
            student.transfer_certificate_no = transfer_certificate_no
            
            if password:
                student.password_hash = generate_password_hash(password)
                
            if not academic_detail:
                academic_detail = StudentAcademicDetail(student_id=student_id)
                db.session.add(academic_detail)
                
            academic_detail.academic_year_id = int(academic_year_id)
            academic_detail.class_id = int(class_id)
            academic_detail.section_id = int(section_id)
            academic_detail.roll_no = roll_no
            academic_detail.student_status = student_status
            
            db.session.commit()
            flash(f"Student {first_name} updated successfully!", "success")
            return redirect(url_for('students_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating student: {str(e)}", "danger")
            
    return render_template('admin/edit_student.html', student=student, academic_detail=academic_detail, academic_years=academic_years, classrooms=classrooms, sections=sections, admin_username=session.get('admin_username'))


@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('login'))


# --- Student Portal Routes ---

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if session.get('student_logged_in'):
        return redirect(url_for('student_dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        student = Student.query.filter_by(username=username).first()
        
        if student and check_password_hash(student.password_hash, password):
            session['student_logged_in'] = True
            session['student_id'] = student.student_id
            session['student_username'] = student.username
            
            # Fetch academic details for the current year
            academic_year = AcademicYear.query.filter_by(is_current=True).first()
            if academic_year:
                academic_detail = StudentAcademicDetail.query.filter_by(
                    student_id=student.student_id,
                    academic_year_id=academic_year.id
                ).first()
                if academic_detail:
                    session['student_class_id'] = academic_detail.class_id
            
            flash("Logged in successfully!", "success")
            return redirect(url_for('student_dashboard'))
        else:
            flash("Invalid username or password.", "danger")
            
    return render_template('student/login.html')

@app.route('/student/dashboard')
def student_dashboard():
    if not session.get('student_logged_in'):
        return redirect(url_for('student_login'))
        
    student_id = session.get('student_id')
    class_id = session.get('student_class_id')
    
    # Check for pending entrance exam
    pending_exam = None
    completed_attempts = []
    
    # Fetch all completed attempts for this student
    completed_attempts = StudentExamAttempt.query.filter_by(student_id=student_id, is_completed=True).all()
    
    if class_id:
        # Is entrance exam globally enabled?
        entrance_setting = SystemSetting.query.filter_by(key='entrance_exam_enabled').first()
        if entrance_setting and entrance_setting.value.lower() == 'true':
            # Check for active exam assigned to this class
            active_exam = EntranceExam.query.filter_by(assigned_class_id=class_id, is_active=True).first()
            if active_exam:
                # Check if the student has already completed it
                attempt = StudentExamAttempt.query.filter_by(student_id=student_id, exam_id=active_exam.id).first()
                if not attempt or not attempt.is_completed:
                    pending_exam = active_exam

    return render_template('student/dashboard.html', pending_exam=pending_exam, completed_attempts=completed_attempts)

@app.route('/student/exam/<int:exam_id>')
def student_take_exam(exam_id):
    if not session.get('student_logged_in'):
        return redirect(url_for('student_login'))
        
    student_id = session.get('student_id')
    exam = EntranceExam.query.get_or_404(exam_id)
    
    # Create an attempt record if it doesn't exist
    attempt = StudentExamAttempt.query.filter_by(student_id=student_id, exam_id=exam_id).first()
    if not attempt:
        attempt = StudentExamAttempt(student_id=student_id, exam_id=exam_id)
        db.session.add(attempt)
        db.session.commit()
        
    if attempt.is_completed:
        flash("You have already completed this exam.", "info")
        return redirect(url_for('student_exam_result', exam_id=exam_id))
        
    # We could calculate remaining time based on attempt.started_at + duration_minutes.
    # For simplicity, we'll pass duration_minutes and let client side handle countdown, 
    # but a secure implementation would check the timestamp difference on submit.
    return render_template('student/take_exam.html', exam=exam, attempt=attempt)

@app.route('/student/exam/<int:exam_id>/submit', methods=['POST'])
def student_submit_exam(exam_id):
    if not session.get('student_logged_in'):
        return redirect(url_for('student_login'))
        
    student_id = session.get('student_id')
    attempt = StudentExamAttempt.query.filter_by(student_id=student_id, exam_id=exam_id).first()
    
    if not attempt or attempt.is_completed:
        return redirect(url_for('student_dashboard'))
        
    exam = EntranceExam.query.get_or_404(exam_id)
    questions = ExamQuestion.query.filter_by(exam_id=exam.id).all()
    
    # Calculate score
    score = 0
    for q in questions:
        selected_option = request.form.get(f'question_{q.id}')
        if selected_option and selected_option == q.correct_option:
            score += 1
            
    attempt.score = score
    attempt.is_completed = True
    attempt.completed_at = datetime.utcnow()
    db.session.commit()
    
    flash("Exam submitted successfully!", "success")
    return redirect(url_for('student_exam_result', exam_id=exam.id))

@app.route('/student/exam/<int:exam_id>/result')
def student_exam_result(exam_id):
    if not session.get('student_logged_in'):
        return redirect(url_for('student_login'))
        
    student_id = session.get('student_id')
    exam = EntranceExam.query.get_or_404(exam_id)
    attempt = StudentExamAttempt.query.filter_by(student_id=student_id, exam_id=exam_id).first()
    
    if not attempt or not attempt.is_completed:
        return redirect(url_for('student_dashboard'))
        
    return render_template('student/exam_result.html', exam=exam, attempt=attempt)

@app.route('/student/profile')
def student_profile():
    if not session.get('student_logged_in'):
        return redirect(url_for('student_login'))
        
    student = Student.query.get(session.get('student_id'))
    
    academic_detail = StudentAcademicDetail.query.filter_by(
        student_id=student.student_id,
        student_status='Active'
    ).order_by(StudentAcademicDetail.academic_year_id.desc()).first()
    
    class_name = "N/A"
    section_name = "N/A"
    roll_no = "N/A"
    
    if academic_detail:
        classroom = ClassRoom.query.get(academic_detail.class_id)
        if classroom:
            class_name = classroom.class_name
        section = Section.query.get(academic_detail.section_id)
        if section:
            section_name = section.section_name
        if academic_detail.roll_no:
            roll_no = academic_detail.roll_no
            
    return render_template('student/profile.html', student=student, class_name=class_name, section_name=section_name, roll_no=roll_no)

@app.route('/student/logout')
def student_logout():
    session.pop('student_logged_in', None)
    session.pop('student_id', None)
    session.pop('student_username', None)
    session.pop('student_class_id', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('student_login'))


# --- Super Admin Portal Routes ---

@app.route('/superadmin/login', methods=['GET', 'POST'])
def superadmin_login():
    if session.get('superadmin_logged_in'):
        return redirect(url_for('superadmin_dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        superadmin = SuperAdmin.query.filter_by(username=username).first()
        
        if superadmin and check_password_hash(superadmin.password_hash, password):
            session['superadmin_logged_in'] = True
            session['superadmin_id'] = superadmin.id
            session['superadmin_username'] = superadmin.username
            flash("Logged in successfully to Super Admin Portal!", "success")
            return redirect(url_for('superadmin_dashboard'))
        else:
            flash("Invalid username or password.", "danger")
            
    return render_template('superadmin/login.html')

@app.route('/superadmin/dashboard')
def superadmin_dashboard():
    if not session.get('superadmin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('superadmin_login'))
        
    entrance_setting = SystemSetting.query.filter_by(key='entrance_exam_enabled').first()
    is_entrance_enabled = entrance_setting.value.lower() == 'true' if entrance_setting else False
    
    study_setting = SystemSetting.query.filter_by(key='study_materials_enabled').first()
    is_study_materials_enabled = study_setting.value.lower() == 'true' if study_setting else False
    
    return render_template('superadmin/dashboard.html', superadmin_username=session.get('superadmin_username'), is_entrance_enabled=is_entrance_enabled, is_study_materials_enabled=is_study_materials_enabled)

@app.route('/superadmin/toggle_study_materials', methods=['POST'])
def superadmin_toggle_study_materials():
    if not session.get('superadmin_logged_in'):
        return redirect(url_for('superadmin_login'))
        
    study_setting = SystemSetting.query.filter_by(key='study_materials_enabled').first()
    if not study_setting:
        study_setting = SystemSetting(key='study_materials_enabled', value='false')
        db.session.add(study_setting)
        
    current_val = study_setting.value.lower() == 'true'
    study_setting.value = 'false' if current_val else 'true'
    
    db.session.commit()
    status = "enabled" if study_setting.value == 'true' else "disabled"
    flash(f"Study Materials are now {status} globally.", "success")
    return redirect(url_for('superadmin_dashboard'))

@app.route('/superadmin/toggle_exam', methods=['POST'])



@app.route('/superadmin/toggle_video', methods=['POST'])
def superadmin_toggle_video():
    if not session.get('superadmin_logged_in'): return redirect(url_for('superadmin_login'))
    setting = SystemSetting.query.filter_by(key='study_materials_video_enabled').first()
    if not setting:
        setting = SystemSetting(key='study_materials_video_enabled', value='false')
        db.session.add(setting)
    setting.value = 'false' if setting.value.lower() == 'true' else 'true'
    db.session.commit()
    flash(f"Video Materials are now {'enabled' if setting.value == 'true' else 'disabled'}.", "success")
    return redirect(url_for('superadmin_dashboard'))

@app.route('/superadmin/toggle_notes', methods=['POST'])
def superadmin_toggle_notes():
    if not session.get('superadmin_logged_in'): return redirect(url_for('superadmin_login'))
    setting = SystemSetting.query.filter_by(key='study_materials_notes_enabled').first()
    if not setting:
        setting = SystemSetting(key='study_materials_notes_enabled', value='false')
        db.session.add(setting)
    setting.value = 'false' if setting.value.lower() == 'true' else 'true'
    db.session.commit()
    flash(f"Notes Materials are now {'enabled' if setting.value == 'true' else 'disabled'}.", "success")
    return redirect(url_for('superadmin_dashboard'))

@app.route('/superadmin/toggle_chat', methods=['POST'])
def superadmin_toggle_chat():
    if not session.get('superadmin_logged_in'): return redirect(url_for('superadmin_login'))
    setting = SystemSetting.query.filter_by(key='chat_enabled').first()
    if not setting:
        setting = SystemSetting(key='chat_enabled', value='false')
        db.session.add(setting)
    setting.value = 'false' if setting.value.lower() == 'true' else 'true'
    db.session.commit()
    flash(f"Chat Feature is now {'enabled' if setting.value == 'true' else 'disabled'}.", "success")
    return redirect(url_for('superadmin_dashboard'))

@app.route('/superadmin/toggle_exam', methods=['POST'])
def superadmin_toggle_exam():
    if not session.get('superadmin_logged_in'):
        return redirect(url_for('superadmin_login'))
        
    entrance_setting = SystemSetting.query.filter_by(key='entrance_exam_enabled').first()
    if not entrance_setting:
        entrance_setting = SystemSetting(key='entrance_exam_enabled', value='false')
        db.session.add(entrance_setting)
        
    current_val = entrance_setting.value.lower() == 'true'
    entrance_setting.value = 'false' if current_val else 'true'
    
    db.session.commit()
    status = "enabled" if entrance_setting.value == 'true' else "disabled"
    flash(f"Entrance Exams are now {status} globally.", "success")
    return redirect(url_for('superadmin_dashboard'))

@app.route('/superadmin/toggle_communication', methods=['POST'])
def superadmin_toggle_communication():
    if not session.get('superadmin_logged_in'):
        return redirect(url_for('superadmin_login'))
    setting = SystemSetting.query.filter_by(key='communication_enabled').first()
    if not setting:
        setting = SystemSetting(key='communication_enabled', value='false')
        db.session.add(setting)
    setting.value = 'false' if setting.value.lower() == 'true' else 'true'
    db.session.commit()
    status = "enabled" if setting.value == 'true' else "disabled"
    flash(f"Communication Module is now {status} globally.", "success")
    return redirect(url_for('superadmin_dashboard'))

@app.route('/superadmin/toggle_communication_whatsapp', methods=['POST'])
def superadmin_toggle_communication_whatsapp():
    if not session.get('superadmin_logged_in'): return redirect(url_for('superadmin_login'))
    setting = SystemSetting.query.filter_by(key='communication_whatsapp_enabled').first()
    if not setting:
        setting = SystemSetting(key='communication_whatsapp_enabled', value='false')
        db.session.add(setting)
    setting.value = 'false' if setting.value.lower() == 'true' else 'true'
    db.session.commit()
    flash(f"WhatsApp channel is now {'enabled' if setting.value == 'true' else 'disabled'}.", "success")
    return redirect(url_for('superadmin_dashboard'))

@app.route('/superadmin/toggle_communication_email', methods=['POST'])
def superadmin_toggle_communication_email():
    if not session.get('superadmin_logged_in'): return redirect(url_for('superadmin_login'))
    setting = SystemSetting.query.filter_by(key='communication_email_enabled').first()
    if not setting:
        setting = SystemSetting(key='communication_email_enabled', value='false')
        db.session.add(setting)
    setting.value = 'false' if setting.value.lower() == 'true' else 'true'
    db.session.commit()
    flash(f"Email channel is now {'enabled' if setting.value == 'true' else 'disabled'}.", "success")
    return redirect(url_for('superadmin_dashboard'))

@app.route('/superadmin/toggle_communication_circular', methods=['POST'])
def superadmin_toggle_communication_circular():
    if not session.get('superadmin_logged_in'): return redirect(url_for('superadmin_login'))
    setting = SystemSetting.query.filter_by(key='communication_circular_enabled').first()
    if not setting:
        setting = SystemSetting(key='communication_circular_enabled', value='false')
        db.session.add(setting)
    setting.value = 'false' if setting.value.lower() == 'true' else 'true'
    db.session.commit()
    flash(f"Circular channel is now {'enabled' if setting.value == 'true' else 'disabled'}.", "success")
    return redirect(url_for('superadmin_dashboard'))

@app.route('/superadmin/toggle_communication_push', methods=['POST'])
def superadmin_toggle_communication_push():
    if not session.get('superadmin_logged_in'): return redirect(url_for('superadmin_login'))
    setting = SystemSetting.query.filter_by(key='communication_push_enabled').first()
    if not setting:
        setting = SystemSetting(key='communication_push_enabled', value='false')
        db.session.add(setting)
    setting.value = 'false' if setting.value.lower() == 'true' else 'true'
    db.session.commit()
    flash(f"Push Notification channel is now {'enabled' if setting.value == 'true' else 'disabled'}.", "success")
    return redirect(url_for('superadmin_dashboard'))

@app.route('/superadmin/toggle_communication_announcement', methods=['POST'])
def superadmin_toggle_communication_announcement():
    if not session.get('superadmin_logged_in'): return redirect(url_for('superadmin_login'))
    setting = SystemSetting.query.filter_by(key='communication_announcement_enabled').first()
    if not setting:
        setting = SystemSetting(key='communication_announcement_enabled', value='false')
        db.session.add(setting)
    setting.value = 'false' if setting.value.lower() == 'true' else 'true'
    db.session.commit()
    flash(f"Announcement channel is now {'enabled' if setting.value == 'true' else 'disabled'}.", "success")
    return redirect(url_for('superadmin_dashboard'))

@app.route('/superadmin/toggle_communication_notice_board', methods=['POST'])
def superadmin_toggle_communication_notice_board():
    if not session.get('superadmin_logged_in'): return redirect(url_for('superadmin_login'))
    setting = SystemSetting.query.filter_by(key='communication_notice_board_enabled').first()
    if not setting:
        setting = SystemSetting(key='communication_notice_board_enabled', value='false')
        db.session.add(setting)
    setting.value = 'false' if setting.value.lower() == 'true' else 'true'
    db.session.commit()
    flash(f"Notice Board channel is now {'enabled' if setting.value == 'true' else 'disabled'}.", "success")
    return redirect(url_for('superadmin_dashboard'))

@app.route('/superadmin/logout')
def superadmin_logout():
    session.pop('superadmin_logged_in', None)
    session.pop('superadmin_id', None)
    session.pop('superadmin_username', None)
    flash("You have logged out of the Super Admin Portal.", "info")
    return redirect(url_for('superadmin_login'))


# --- Staff Portal Routes ---

@app.route('/staff/login', methods=['GET', 'POST'])
def staff_portal_login():
    if session.get('staff_logged_in'):
        return redirect(url_for('staff_portal_dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template('staff/login.html')
            
        staff = Staff.query.filter_by(username=username).first()
        
        if staff and check_password_hash(staff.password_hash, password):
            # Check if active
            if staff.status != 'Active':
                flash("Your account status is not Active. Please contact administrator.", "danger")
                return render_template('staff/login.html')
                
            session['staff_logged_in'] = True
            session['staff_id'] = staff.staff_id
            session['staff_username'] = staff.username
            session['staff_name'] = f"{staff.first_name} {staff.last_name or ''}".strip()
            flash("Logged in successfully to Staff Portal!", "success")
            return redirect(url_for('staff_portal_dashboard'))
        else:
            flash("Invalid username or password.", "danger")
            
    return render_template('staff/login.html')


@app.route('/staff/dashboard')
def staff_portal_dashboard():
    if not session.get('staff_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('staff_portal_login'))
        
    staff = Staff.query.get(session.get('staff_id'))
    if not staff:
        session.clear()
        return redirect(url_for('staff_portal_login'))
        
    return render_template('staff/dashboard.html', staff=staff)


@app.route('/staff/profile')
def staff_portal_profile():
    if not session.get('staff_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('staff_portal_login'))
        
    staff = Staff.query.get(session.get('staff_id'))
    if not staff:
        session.clear()
        return redirect(url_for('staff_portal_login'))
        
    return render_template('staff/profile.html', staff=staff)


# --- Staff Entrance Exam Routes ---

@app.route('/staff/exams')
def staff_exams_list():
    if not session.get('staff_logged_in'):
        return redirect(url_for('staff_portal_login'))
        
    exams = EntranceExam.query.filter_by(created_by_staff_id=session.get('staff_id')).all()
    return render_template('staff/exams_list.html', exams=exams)

@app.route('/staff/exams/create', methods=['GET', 'POST'])
def staff_exams_create():
    if not session.get('staff_logged_in'):
        return redirect(url_for('staff_portal_login'))
        
    if request.method == 'POST':
        title = request.form.get('title')
        duration = request.form.get('duration')
        class_id = request.form.get('class_id')
        
        new_exam = EntranceExam(
            title=title,
            duration_minutes=int(duration),
            assigned_class_id=class_id,
            created_by_staff_id=session.get('staff_id')
        )
        db.session.add(new_exam)
        db.session.commit()
        flash("Entrance Exam created successfully!", "success")
        return redirect(url_for('staff_exams_list'))
        
    classrooms = ClassRoom.query.order_by(ClassRoom.display_order).all()
    return render_template('staff/create_exam.html', classrooms=classrooms)

@app.route('/staff/exams/<int:exam_id>/questions', methods=['GET', 'POST'])
def staff_exams_questions(exam_id):
    if not session.get('staff_logged_in'):
        return redirect(url_for('staff_portal_login'))
        
    exam = EntranceExam.query.get_or_404(exam_id)
    if exam.created_by_staff_id != session.get('staff_id'):
        flash("Unauthorized access.", "danger")
        return redirect(url_for('staff_exams_list'))
        
    if request.method == 'POST':
        q_text = request.form.get('question_text')
        opt_a = request.form.get('option_a')
        opt_b = request.form.get('option_b')
        opt_c = request.form.get('option_c')
        opt_d = request.form.get('option_d')
        correct = request.form.get('correct_option')
        
        new_q = ExamQuestion(
            exam_id=exam.id, question_text=q_text,
            option_a=opt_a, option_b=opt_b, option_c=opt_c, option_d=opt_d,
            correct_option=correct
        )
        db.session.add(new_q)
        db.session.commit()
        flash("Question added successfully!", "success")
        return redirect(url_for('staff_exams_questions', exam_id=exam.id))
        
    questions = ExamQuestion.query.filter_by(exam_id=exam.id).all()
    return render_template('staff/manage_questions.html', exam=exam, questions=questions)

@app.route('/staff/exams/<int:exam_id>/results')
def staff_exams_results(exam_id):
    if not session.get('staff_logged_in'):
        return redirect(url_for('staff_portal_login'))
        
    exam = EntranceExam.query.get_or_404(exam_id)
    if exam.created_by_staff_id != session.get('staff_id'):
        flash("Unauthorized access.", "danger")
        return redirect(url_for('staff_exams_list'))
        
    attempts = StudentExamAttempt.query.filter_by(exam_id=exam.id).all()
    return render_template('staff/exam_results.html', exam=exam, attempts=attempts)



@app.route('/staff/logout')
def staff_portal_logout():
    session.pop('staff_logged_in', None)
    session.pop('staff_id', None)
    session.pop('staff_username', None)
    session.pop('staff_name', None)
    flash("You have logged out of the Staff Portal.", "info")
    return redirect(url_for('staff_portal_login'))



@app.route('/staff/change_password', methods=['POST'])
def staff_change_password():
    if not session.get('staff_logged_in'):
        return redirect(url_for('staff_login'))
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('staff_portal_profile'))
        
    staff = Staff.query.get(session.get('staff_id'))
    if not staff or not check_password_hash(staff.password_hash, current_password):
        flash('Incorrect current password.', 'danger')
        return redirect(url_for('staff_portal_profile'))
        
    staff.password_hash = generate_password_hash(new_password)
    db.session.commit()
    flash('Password updated successfully.', 'success')
    return redirect(url_for('staff_portal_profile'))

@app.route('/student/change_password', methods=['POST'])
def student_change_password():
    if not session.get('student_logged_in'):
        return redirect(url_for('student_login'))
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('student_profile'))
        
    student = Student.query.get(session.get('student_id'))
    if not student or not check_password_hash(student.password_hash, current_password):
        flash('Incorrect current password.', 'danger')
        return redirect(url_for('student_profile'))
        
    student.password_hash = generate_password_hash(new_password)
    db.session.commit()
    flash('Password updated successfully.', 'success')
    return redirect(url_for('student_profile'))

# --- Study Materials Routes ---

@app.route('/staff/study_materials')
def staff_study_materials_base():
    return redirect(url_for('staff_study_materials', category='docs'))

@app.route('/staff/study_materials/<category>', methods=['GET', 'POST'])
def staff_study_materials(category):
    if category not in ['video', 'docs', 'chat']:
        return redirect(url_for('staff_study_materials', category='docs'))
    if not session.get('staff_logged_in'):
        return redirect(url_for('staff_login'))
        
    study_setting = SystemSetting.query.filter_by(key='study_materials_enabled').first()
    is_study_materials_enabled = study_setting.value.lower() == 'true' if study_setting else False
    
    if not is_study_materials_enabled:
        flash("Study Materials feature is currently disabled by the Super Admin.", "warning")
        return redirect(url_for('staff_dashboard'))
        
    staff_id = session.get('staff_id')
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        class_id = request.form.get('class_id')
        section_id = request.form.get('section_id')
        file = request.files.get('material_file')
        
        if not title or not class_id or not file or file.filename == '':
            flash("Please provide a title, class, and select a file.", "danger")
            return redirect(url_for('staff_study_materials', category=category))
            
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        import os
        
        vid_set = SystemSetting.query.filter_by(key='study_materials_video_enabled').first()
        not_set = SystemSetting.query.filter_by(key='study_materials_notes_enabled').first()
        
        vid_enabled = vid_set.value.lower() == 'true' if vid_set else False
        not_enabled = not_set.value.lower() == 'true' if not_set else False
        
        if file_ext in ['mp4', 'mkv', 'avi']:
            if not vid_enabled:
                flash("Video uploads are currently disabled by the Super Admin.", "danger")
                return redirect(url_for('staff_study_materials', category=category))
            
            file.seek(0, os.SEEK_END)
            file_length = file.tell()
            file.seek(0)
            if file_length > 15 * 1024 * 1024:
                flash("Video files must be strictly under 15MB.", "danger")
                return redirect(url_for('staff_study_materials', category=category))
                
        if file_ext in ['pdf', 'doc', 'docx', 'txt', 'ppt', 'pptx', 'xls', 'xlsx'] and not not_enabled:
            flash("Notes & Document uploads are currently disabled.", "danger")
            return redirect(url_for('staff_study_materials', category=category))
            
        upload_folder = os.path.join(app.root_path, 'static', 'uploads', 'study_materials')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            
        file_path = os.path.join('static', 'uploads', 'study_materials', filename)
        file.save(os.path.join(app.root_path, file_path))
        
        new_material = StudyMaterial(
            title=title,
            description=description,
            file_path=file_path,
            file_type=file_ext,
            class_id=int(class_id),
            section_id=int(section_id) if section_id else None,
            staff_id=staff_id
        )
        db.session.add(new_material)
        db.session.commit()
        flash("Study material uploaded successfully!", "success")
        return redirect(url_for('staff_study_materials', category=category))
        
    query = StudyMaterial.query.filter_by(staff_id=staff_id)
    if category == 'video':
        query = query.filter(StudyMaterial.file_type.in_(['mp4', 'mkv', 'avi']))
    elif category == 'docs':
        query = query.filter(StudyMaterial.file_type.in_(['pdf', 'doc', 'docx', 'txt', 'ppt', 'pptx', 'xls', 'xlsx']))
    else:
        query = query.filter(StudyMaterial.file_type == 'none') # Chat placeholder for now
    materials = query.order_by(StudyMaterial.uploaded_at.desc()).all()
    classes = ClassRoom.query.all()
    sections = Section.query.all()
    
    return render_template('staff/study_materials.html', materials=materials, classes=classes, sections=sections, is_study_materials_enabled=is_study_materials_enabled, category=category)

@app.route('/staff/study_materials/delete/<int:material_id>', methods=['POST'])
def staff_delete_study_material(material_id):
    if not session.get('staff_logged_in'):
        return redirect(url_for('staff_login'))
        
    material = StudyMaterial.query.get_or_404(material_id)
    if material.file_type in ['mp4', 'mkv', 'avi']:
        category = 'video'
    elif material.file_type in ['pdf', 'doc', 'docx', 'txt', 'ppt', 'pptx', 'xls', 'xlsx']:
        category = 'docs'
    else:
        category = 'chat'
        
    if material.staff_id != session.get('staff_id'):
        flash("Unauthorized to delete this material.", "danger")
        return redirect(url_for('staff_study_materials', category=category))
        
    db.session.delete(material)
    db.session.commit()
    flash("Study material deleted successfully.", "info")
    return redirect(url_for('staff_study_materials', category=category))

@app.route('/student/study_materials')
def student_study_materials_base():
    return redirect(url_for('student_study_materials', category='docs'))

@app.route('/student/study_materials/<category>')
def student_study_materials(category):
    if category not in ['video', 'docs', 'chat']:
        return redirect(url_for('student_study_materials', category='docs'))
    if not session.get('student_logged_in'):
        return redirect(url_for('student_login'))
        
    study_setting = SystemSetting.query.filter_by(key='study_materials_enabled').first()
    is_study_materials_enabled = study_setting.value.lower() == 'true' if study_setting else False
    
    if not is_study_materials_enabled:
        flash("Study Materials feature is currently disabled.", "warning")
        return redirect(url_for('student_dashboard'))
        
    student_id = session.get('student_id')
    student = Student.query.get(student_id)
    academic_detail = StudentAcademicDetail.query.filter_by(student_id=student_id).order_by(StudentAcademicDetail.academic_year_id.desc()).first()
    
    if academic_detail:
        query = StudyMaterial.query.filter_by(class_id=academic_detail.class_id).filter((StudyMaterial.section_id == academic_detail.section_id) | (StudyMaterial.section_id == None))
        
        if category == 'video':
            query = query.filter(StudyMaterial.file_type.in_(['mp4', 'mkv', 'avi']))
        elif category == 'docs':
            query = query.filter(StudyMaterial.file_type.in_(['pdf', 'doc', 'docx', 'txt', 'ppt', 'pptx', 'xls', 'xlsx']))
        else:
            query = query.filter(StudyMaterial.file_type == 'none')
            
        materials = query.order_by(StudyMaterial.uploaded_at.desc()).all()
    else:
        materials = []
        
    return render_template('student/study_materials.html', materials=materials, student=student, is_study_materials_enabled=is_study_materials_enabled, category=category)


# --- Attendance and timetable routes ---
def _admin_required():
    return session.get('admin_logged_in')


@app.route('/staff-attendance', methods=['GET', 'POST'])
@app.route('/staff-attendance/submit', methods=['POST'], endpoint='submit_admin_staff_attendance')
def admin_staff_attendance():
    if not _admin_required():
        flash('Access denied. Please log in first.', 'warning')
        return redirect(url_for('login'))
    today = datetime.today().date()
    if request.method == 'POST':
        for staff in Staff.query.filter_by(status='Active').all():
            status = request.form.get(f'status_{staff.staff_id}')
            if status in ('Present', 'Absent'):
                record = StaffAttendance.query.filter_by(staff_id=staff.staff_id, date=today).first()
                if record:
                    record.status = status
                else:
                    db.session.add(StaffAttendance(staff_id=staff.staff_id, date=today, status=status))
        db.session.commit()
        flash('Staff attendance saved successfully.', 'success')
        return redirect(url_for('admin_staff_attendance'))
    staff_members = Staff.query.filter_by(status='Active').order_by(Staff.first_name).all()
    records = {record.staff_id: record for record in StaffAttendance.query.filter_by(date=today).all()}
    return render_template('admin/staff_attendance.html', staff_members=staff_members,
                           attendance_map=records, selected_date=today,
                           departments=Department.query.order_by(Department.name).all(),
                           selected_department_id=None, page=1, per_page=10,
                           total_records=len(staff_members), total_pages=1)


@app.route('/admin/timetable', methods=['GET', 'POST'])
def admin_timetable():
    if not _admin_required():
        flash('Access denied. Please log in first.', 'warning')
        return redirect(url_for('login'))
    classes = ClassRoom.query.order_by(ClassRoom.display_order, ClassRoom.class_name).all()
    class_section_id = request.values.get('class_section_id', '')
    class_id = request.values.get('class_id', type=int)
    section_id = request.values.get('section_id', type=int)
    if class_section_id and not (class_id and section_id):
        try:
            class_id, section_id = (int(value) for value in class_section_id.split('_', 1))
        except ValueError:
            class_id = section_id = None
    if request.method == 'POST' and class_id and section_id:
        Timetable.query.filter_by(class_id=class_id, section_id=section_id).delete()
        for day in TIMETABLE_DAYS:
            for period in TIMETABLE_PERIODS:
                subject_id = request.form.get(f'subject_{day}_{period}', type=int)
                teacher_id = request.form.get(f'teacher_{day}_{period}', type=int)
                if subject_id and teacher_id:
                    db.session.add(Timetable(class_id=class_id, section_id=section_id, day=day, period_number=period, subject_id=subject_id, teacher_id=teacher_id))
        db.session.commit()
        flash('Timetable saved successfully.', 'success')
        return redirect(url_for('admin_timetable', class_id=class_id, section_id=section_id))
    sections = Section.query.filter_by(class_id=class_id).order_by(Section.section_name).all() if class_id else []
    entries = Timetable.query.filter_by(class_id=class_id, section_id=section_id).all() if class_id and section_id else []
    grid = {(entry.day, entry.period_number): entry for entry in entries}
    grid_data = {day: {period: None for period in TIMETABLE_PERIODS} for day in TIMETABLE_DAYS}
    for entry in entries:
        grid_data[entry.day][entry.period_number] = {'subject': entry.subject.name, 'teacher': f"{entry.teacher.first_name} {entry.teacher.last_name or ''}".strip()}
    classroom = ClassRoom.query.get(class_id) if class_id else None
    section = Section.query.get(section_id) if section_id else None
    active_tab = request.args.get('tab', 'student')
    selected_staff_id = request.args.get('staff_id', type=int) if active_tab == 'teacher' else None
    selected_teacher = Staff.query.get(selected_staff_id) if selected_staff_id else None
    teacher_grid = {day: {period: [] for period in TIMETABLE_PERIODS} for day in TIMETABLE_DAYS}
    if selected_teacher:
        for entry in Timetable.query.filter_by(teacher_id=selected_teacher.staff_id).all():
            teacher_grid[entry.day][entry.period_number].append({
                'subject': entry.subject.name,
                'class_name': entry.classroom.class_name,
                'section_name': entry.section.section_name,
            })
    return render_template('admin/timetable.html', active_tab=active_tab,
                           classrooms=classes, teachers=Staff.query.filter_by(status='Active').order_by(Staff.first_name).all(),
                           selected_class_id=class_id, selected_section_id=section_id,
                           selected_class_name=classroom.class_name if classroom else '',
                           selected_section_name=section.section_name if section else '',
                           sat_alt_day=None, grid_data=grid_data, selected_staff_id=selected_staff_id,
                           selected_teacher_name=f"{selected_teacher.first_name} {selected_teacher.last_name or ''}".strip() if selected_teacher else '',
                           teacher_grid=teacher_grid)


@app.route('/staff/timetable')
def staff_timetable():
    if not session.get('staff_logged_in'):
        return redirect(url_for('staff_portal_login'))
    staff_id = session.get('staff_id')
    entries = Timetable.query.filter_by(teacher_id=staff_id).all()
    teacher_grid = {day: {period: [] for period in TIMETABLE_PERIODS} for day in TIMETABLE_DAYS}
    for entry in entries:
        teacher_grid[entry.day][entry.period_number].append({
            'subject': entry.subject.name,
            'class_name': entry.classroom.class_name,
            'section_name': entry.section.section_name,
        })
    return render_template('staff/timetable.html', teacher_grid=teacher_grid)


@app.route('/admin/timetable/edit/<int:class_id>/<int:section_id>', methods=['GET', 'POST'])
def admin_timetable_edit(class_id, section_id):
    if not _admin_required():
        return redirect(url_for('login'))
    classroom = ClassRoom.query.get_or_404(class_id)
    section = Section.query.get_or_404(section_id)
    if request.method == 'POST':
        Timetable.query.filter_by(class_id=class_id, section_id=section_id).delete()
        for day in TIMETABLE_DAYS:
            for period in TIMETABLE_PERIODS:
                subject_id = request.form.get(f'subject_{day}_{period}', type=int)
                teacher_id = request.form.get(f'teacher_{day}_{period}', type=int)
                if subject_id and teacher_id:
                    db.session.add(Timetable(class_id=class_id, section_id=section_id,
                                              day=day, period_number=period,
                                              subject_id=subject_id, teacher_id=teacher_id))
        db.session.commit()
        flash('Timetable updated successfully.', 'success')
        return redirect(url_for('admin_timetable', tab='student', class_section_id=f'{class_id}_{section_id}'))
    existing_entries = {day: {period: None for period in TIMETABLE_PERIODS} for day in TIMETABLE_DAYS}
    for entry in Timetable.query.filter_by(class_id=class_id, section_id=section_id).all():
        existing_entries[entry.day][entry.period_number] = entry
    saturday_config = type('SaturdayConfigView', (), {'alternative_day': 'None'})()
    return render_template('admin/timetable_edit.html', classroom=classroom, section=section,
                           departments=Department.query.order_by(Department.name).all(),
                           teachers=Staff.query.filter_by(status='Active').order_by(Staff.first_name).all(),
                           saturday_config=saturday_config, existing_entries=existing_entries)


@app.route('/admin/timetable/teacher_edit/<int:staff_id>')
def admin_timetable_teacher_edit(staff_id):
    """Compatibility endpoint used by the imported lms_without_env UI."""
    if not _admin_required():
        return redirect(url_for('login'))
    return redirect(url_for('admin_timetable', tab='teacher', staff_id=staff_id))


@app.route('/student/timetable')
def student_timetable():
    if not session.get('student_logged_in'):
        return redirect(url_for('student_login'))
    detail = StudentAcademicDetail.query.filter_by(student_id=session['student_id']).order_by(StudentAcademicDetail.academic_year_id.desc()).first()
    entries = Timetable.query.filter_by(class_id=detail.class_id, section_id=detail.section_id).all() if detail else []
    grid_data = {day: {period: None for period in TIMETABLE_PERIODS} for day in TIMETABLE_DAYS}
    for entry in entries:
        grid_data[entry.day][entry.period_number] = {
            'subject': entry.subject.name,
            'teacher': f"{entry.teacher.first_name} {entry.teacher.last_name or ''}".strip(),
        }
    return render_template('student/timetable.html', grid_data=grid_data,
                           class_name=detail.classroom.class_name if detail else '',
                           section_name=detail.section.section_name if detail else '',
                           sat_alt_day=None)


@app.route('/staff/attendance', methods=['GET', 'POST'])
@app.route('/staff/attendance/submit', methods=['POST'], endpoint='staff_attendance_submit')
def staff_attendance():
    if not session.get('staff_logged_in'):
        return redirect(url_for('staff_portal_login'))
    class_section_id = request.values.get('class_section_id', '')
    class_id = request.values.get('class_id', type=int)
    section_id = request.values.get('section_id', type=int)
    if class_section_id and not (class_id and section_id):
        try:
            class_id, section_id = (int(value) for value in class_section_id.split('_', 1))
        except ValueError:
            class_id = section_id = None
    period = request.values.get('period_number', type=int) or request.values.get('period', default=1, type=int)
    today = datetime.today().date()
    classes = ClassRoom.query.order_by(ClassRoom.display_order, ClassRoom.class_name).all()
    sections = Section.query.filter_by(class_id=class_id).order_by(Section.section_name).all() if class_id else []
    details = StudentAcademicDetail.query.filter_by(class_id=class_id, section_id=section_id, student_status='Active').all() if class_id and section_id else []
    if request.method == 'POST' and details:
        for detail in details:
            status = request.form.get(f'status_{detail.student_id}')
            if status in ('Present', 'Absent', 'Late', 'Late Entry'):
                record = StudentAttendance.query.filter_by(student_id=detail.student_id, date=today, period_number=period).first()
                if record:
                    record.status = status
                else:
                    db.session.add(StudentAttendance(student_id=detail.student_id, class_id=class_id, section_id=section_id, date=today, period_number=period, status=status, marked_by=session.get('staff_id')))
        db.session.commit()
        flash('Student attendance saved successfully.', 'success')
        return redirect(url_for('staff_attendance', class_id=class_id, section_id=section_id, period=period))
    records = {record.student_id: record for record in StudentAttendance.query.filter_by(class_id=class_id, section_id=section_id, date=today, period_number=period).all()} if details else {}
    students_data = []
    for detail in details:
        record = records.get(detail.student_id)
        students_data.append({
            'student_id': detail.student_id,
            'roll_no': detail.roll_no,
            'name': f"{detail.student.first_name} {detail.student.last_name or ''}".strip(),
            'gender': detail.student.gender,
            'status': record.status if record else None,
        })
    classroom = ClassRoom.query.get(class_id) if class_id else None
    section = Section.query.get(section_id) if section_id else None
    return render_template('staff/attendance.html', classrooms=classes,
                           class_section_id=class_section_id or (f'{class_id}_{section_id}' if class_id and section_id else ''),
                           selected_class_name=classroom.class_name if classroom else '',
                           selected_section_name=section.section_name if section else '',
                           selected_date=today, date_str=today.strftime('%Y-%m-%d'),
                           period_number=period, students_data=students_data,
                           page=1, per_page=10, total_records=len(students_data), total_pages=1)


# --- Additive subject, curriculum and teacher assignment routes ---
def _active_class_sections():
    return [(room, section) for room in ClassRoom.query.order_by(ClassRoom.display_order, ClassRoom.class_name).all()
            for section in sorted(room.sections, key=lambda item: item.section_name)]


@app.route('/admin/subjects', methods=['GET', 'POST'])
def admin_subjects():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        name, code = request.form.get('name', '').strip(), request.form.get('code', '').strip().upper()
        department_id = request.form.get('department_id', type=int)
        if not name or not code:
            flash('Please enter a subject name and code.', 'danger')
        elif Subject.query.filter((Subject.name == name) | (Subject.code == code)).first():
            flash('Subject name or code already exists.', 'danger')
        else:
            db.session.add(Subject(name=name, code=code, department_id=department_id))
            db.session.commit()
            flash('Subject added successfully.', 'success')
        return redirect(url_for('admin_subjects'))
    return render_template('admin/subjects.html', subjects=Subject.query.order_by(Subject.name).all(),
                           departments=Department.query.order_by(Department.name).all())


@app.route('/admin/subjects/edit/<int:subject_id>', methods=['POST'])
def edit_subject(subject_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    subject = Subject.query.get_or_404(subject_id)
    name, code = request.form.get('name', '').strip(), request.form.get('code', '').strip().upper()
    duplicate = Subject.query.filter(Subject.id != subject_id, (Subject.name == name) | (Subject.code == code)).first()
    if not name or not code or duplicate:
        flash('Use a unique subject name and code.', 'danger')
    else:
        subject.name, subject.code = name, code
        subject.department_id = request.form.get('department_id', type=int)
        db.session.commit()
        flash('Subject updated successfully.', 'success')
    return redirect(url_for('admin_subjects'))


@app.route('/admin/subjects/delete/<int:id>', methods=['POST'])
def delete_subject(id):
    """Remove only the selected subject and its subject-specific mappings."""
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    subject = Subject.query.get_or_404(id)
    StaffSubjectAssignment.query.filter_by(subject_id=id).delete()
    ClassSubject.query.filter_by(subject_id=id).delete()
    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted successfully.', 'success')
    return redirect(url_for('admin_subjects'))


@app.route('/admin/subjects/assign-staff', methods=['GET', 'POST'])
def assign_subject_staff():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    return render_template('admin/assign_subject_staff.html',
                           staff_members=Staff.query.filter_by(status='Active').order_by(Staff.first_name).all())


@app.route('/admin/subjects/assign-staff/<int:staff_id>', methods=['GET', 'POST'])
def admin_assign_subject_to_staff(staff_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    staff = Staff.query.get_or_404(staff_id)
    classrooms = ClassRoom.query.order_by(ClassRoom.display_order).all()
    teacher_category = (staff.teacher_category or '').strip().upper()
    if 'PPT' in teacher_category or 'PRE-PRIMARY' in teacher_category or 'PRE PRIMARY' in teacher_category:
        allowed_class_names = {'LKG', 'UKG'}
        classrooms = [room for room in classrooms if room.class_name.strip().upper() in allowed_class_names]
    elif 'PRT' in teacher_category or 'PRIMARY TEACHER' in teacher_category:
        allowed_class_names = {'1', '2', '3', '4', '5'}
        classrooms = [room for room in classrooms if room.class_name.strip() in allowed_class_names]
    elif 'TGT' in teacher_category:
        allowed_class_names = {'6', '7', '8', '9', '10'}
        classrooms = [room for room in classrooms if room.class_name.strip() in allowed_class_names]
    elif 'PGT' in teacher_category:
        allowed_class_names = {'11', '12'}
        classrooms = [room for room in classrooms if room.class_name.strip() in allowed_class_names]
    allowed_class_ids = {room.class_id for room in classrooms}

    if request.method == 'POST':
        assignment_count = StaffSubjectAssignment.query.filter_by(staff_id=staff_id).count()
        subject_id = request.form.get('subject_id', type=int)
        class_section = request.form.get('class_section_id', '')
        try:
            class_id, section_id = (int(value) for value in class_section.split('_', 1))
        except (ValueError, AttributeError):
            class_id = section_id = None
        if assignment_count >= 8:
            flash('A teacher can have a maximum of 8 subject assignments. Remove an assignment before adding another.', 'warning')
        elif not all((subject_id, class_id, section_id)):
            flash('Please select a subject and class section.', 'danger')
        elif class_id not in allowed_class_ids:
            flash('This class is not available for the selected teacher category.', 'danger')
        elif StaffSubjectAssignment.query.filter_by(staff_id=staff_id, subject_id=subject_id, class_id=class_id, section_id=section_id).first():
            flash('This subject-class combination is already assigned.', 'warning')
        else:
            db.session.add(StaffSubjectAssignment(staff_id=staff_id, subject_id=subject_id, class_id=class_id, section_id=section_id))
            db.session.commit(); flash('Subject assigned successfully.', 'success')
        return redirect(url_for('admin_assign_subject_to_staff', staff_id=staff_id))
    return render_template('admin/assign_subject_to_staff.html', staff=staff,
                           subjects=Subject.query.order_by(Subject.name).all(),
                           departments=Department.query.order_by(Department.name).all(),
                           classrooms=classrooms,
                           existing_assignments=StaffSubjectAssignment.query.filter_by(staff_id=staff_id).all())


@app.route('/admin/subjects/assign-staff/delete/<int:assignment_id>', methods=['POST'])
def admin_delete_subject_assignment(assignment_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    assignment = StaffSubjectAssignment.query.get_or_404(assignment_id)
    staff_id = assignment.staff_id
    db.session.delete(assignment)
    db.session.commit()
    flash('Assignment removed successfully.', 'success')
    return redirect(url_for('admin_assign_subject_to_staff', staff_id=staff_id))


@app.route('/admin/class-teacher', methods=['GET', 'POST'])
def assign_class_teacher():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        class_section = request.form.get('class_section_id', '')
        try:
            class_id, section_id = (int(value) for value in class_section.split('_', 1))
        except (ValueError, AttributeError):
            class_id = section_id = None
        staff_id = request.form.get('staff_id', type=int)
        assignment = ClassTeacherAssignment.query.filter_by(class_id=class_id, section_id=section_id).first()
        if not all((class_id, section_id, staff_id)):
            flash('Select a class, section and teacher.', 'danger')
        elif not Section.query.filter_by(section_id=section_id, class_id=class_id).first():
            flash('The selected section does not belong to that class.', 'danger')
        elif assignment:
            assignment.staff_id, assignment.assigned_at = staff_id, datetime.utcnow()
            db.session.commit(); flash('Class teacher updated successfully.', 'success')
        else:
            db.session.add(ClassTeacherAssignment(class_id=class_id, section_id=section_id, staff_id=staff_id))
            db.session.commit(); flash('Class teacher assigned successfully.', 'success')
        return redirect(url_for('assign_class_teacher'))
    classrooms = ClassRoom.query.order_by(ClassRoom.display_order, ClassRoom.class_name).all()
    assignment_map = {(item.class_id, item.section_id): item for item in ClassTeacherAssignment.query.all()}
    return render_template('admin/assign_class_teacher.html', classrooms=classrooms,
                           staff_members=Staff.query.filter_by(status='Active').order_by(Staff.first_name).all(),
                           assignment_map=assignment_map)


@app.route('/admin/class-teacher/remove/<int:assignment_id>', methods=['POST'])
def remove_class_teacher(assignment_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    db.session.delete(ClassTeacherAssignment.query.get_or_404(assignment_id))
    db.session.commit()
    flash('Class teacher assignment removed.', 'success')
    return redirect(url_for('assign_class_teacher'))


@app.route('/admin/assign-subject-teacher')
def assign_subject_teacher():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    classrooms = ClassRoom.query.order_by(ClassRoom.display_order, ClassRoom.class_name).all()
    assignments_by_class = {}
    for assignment in StaffSubjectAssignment.query.all():
        assignments_by_class.setdefault(assignment.class_id, []).append(assignment)

    assignment_groups = []
    for classroom in classrooms:
        assignments = assignments_by_class.get(classroom.class_id, [])
        if assignments:
            assignments.sort(key=lambda item: (
                item.section.section_name if item.section else '',
                item.subject.name.lower(),
                item.staff.first_name.lower()
            ))
            section_groups = []
            for section in classroom.sections:
                section_assignments = [item for item in assignments if item.section_id == section.section_id]
                if section_assignments:
                    section_groups.append({'section': section, 'assignments': section_assignments})
            if not classroom.sections:
                section_groups.append({'section': None, 'assignments': assignments})
            assignment_groups.append({'classroom': classroom, 'assignments': assignments, 'section_groups': section_groups})

    class_categories = [
        ('LKG', {'LKG'}), ('UKG', {'UKG'}),
        ('Classes 1-5', {'1', '2', '3', '4', '5'}),
        ('Classes 6-8', {'6', '7', '8'}),
        ('Classes 9-10', {'9', '10'}), ('Classes 11-12', {'11', '12'}),
    ]
    assignment_navigation_groups = [
        {'name': category_name, 'classes': [group for group in assignment_groups if group['classroom'].class_name in class_names]}
        for category_name, class_names in class_categories
    ]
    assignment_navigation_groups = [group for group in assignment_navigation_groups if group['classes']]
    return render_template('admin/assign_subject_teacher_curriculum.html',
                           assignment_groups=assignment_groups,
                           assignment_navigation_groups=assignment_navigation_groups,
                           total_assignments=sum(len(group['assignments']) for group in assignment_groups))

    if request.method == 'POST':
        class_name, subject_name = request.form.get('class_name'), request.form.get('subject_name')
        section_id, staff_id = request.form.get('section_id', type=int), request.form.get('staff_id')
        classroom = ClassRoom.query.filter_by(class_name=class_name).first()
        subject = Subject.query.filter_by(name=subject_name).first()
        if classroom and subject and section_id:
            current = StaffSubjectAssignment.query.filter_by(class_id=classroom.class_id, section_id=section_id, subject_id=subject.id).first()
            if staff_id == 'REMOVE':
                if current: db.session.delete(current)
            elif staff_id and staff_id.isdigit():
                if current: current.staff_id = int(staff_id)
                else: db.session.add(StaffSubjectAssignment(staff_id=int(staff_id), subject_id=subject.id, class_id=classroom.class_id, section_id=section_id))
            db.session.commit(); flash('Subject teacher assignment updated.', 'success')
        return redirect(url_for('assign_subject_teacher'))
    curriculum_groups = [
        {'category_name': 'LKG', 'classes': ['LKG']}, {'category_name': 'UKG', 'classes': ['UKG']},
        {'category_name': 'Classes 1–5', 'classes': ['1','2','3','4','5']},
        {'category_name': 'Classes 6–8', 'classes': ['6','7','8']},
        {'category_name': 'Classes 9–10', 'classes': ['9','10']},
    ]
    classrooms = ClassRoom.query.order_by(ClassRoom.display_order, ClassRoom.class_name).all()
    class_map = {room.class_name: room for room in classrooms}
    all_subjects = Subject.query.order_by(Subject.name).all()
    class_subjects_map = {}
    for record in ClassSubject.query.all(): class_subjects_map.setdefault(record.class_id, []).append(record.subject)
    assignment_map = {(item.class_id, item.section_id, item.subject_id): item for item in StaffSubjectAssignment.query.all()}
    staff_members = Staff.query.filter_by(status='Active').order_by(Staff.first_name).all()
    subject_staff_map = {subject.name: staff_members for subject in all_subjects}
    return render_template('admin/assign_subject_teacher_curriculum.html', curriculum_groups=curriculum_groups,
                           class_map=class_map, all_subjects=all_subjects, class_subjects_map=class_subjects_map,
                           assignment_map=assignment_map, staff_members=staff_members, subject_staff_map=subject_staff_map)


@app.route('/admin/subjects/add-class-subject', methods=['POST'])
def add_class_subject():
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    class_id, subject_id = request.form.get('class_id', type=int), request.form.get('subject_id', type=int)
    if class_id and subject_id and not ClassSubject.query.filter_by(class_id=class_id, subject_id=subject_id).first():
        db.session.add(ClassSubject(class_id=class_id, subject_id=subject_id)); db.session.commit(); flash('Subject added to class.', 'success')
    return redirect(url_for('assign_subject_teacher'))


@app.route('/admin/subjects/delete-class-subject/<int:class_id>/<int:subject_id>', methods=['POST'])
def delete_class_subject(class_id, subject_id):
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    StaffSubjectAssignment.query.filter_by(class_id=class_id, subject_id=subject_id).delete()
    ClassSubject.query.filter_by(class_id=class_id, subject_id=subject_id).delete()
    db.session.commit(); flash('Subject removed from class.', 'success')
    return redirect(url_for('assign_subject_teacher'))


@app.route('/admin/subjects/remove-teacher/<int:assignment_id>', methods=['POST'])
def remove_subject_teacher(assignment_id):
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    db.session.delete(StaffSubjectAssignment.query.get_or_404(assignment_id))
    db.session.commit(); flash('Teacher removed.', 'success')
    return redirect(url_for('assign_subject_teacher'))


@app.route('/staff/my-class')
def staff_my_class():
    if not session.get('staff_logged_in'):
        return redirect(url_for('staff_portal_login'))
    assignment = ClassTeacherAssignment.query.filter_by(staff_id=session.get('staff_id')).first()
    details = StudentAcademicDetail.query.filter_by(class_id=assignment.class_id, section_id=assignment.section_id).all() if assignment else []
    return render_template('staff/my_class.html', assignment=assignment, details=details)


@app.route('/staff/assigned-classes')
def staff_assigned_classes():
    if not session.get('staff_logged_in'):
        return redirect(url_for('staff_portal_login'))
    return render_template('staff/assigned_classes.html', assignments=StaffSubjectAssignment.query.filter_by(staff_id=session.get('staff_id')).all())


def _student_detail():
    return StudentAcademicDetail.query.filter_by(student_id=session.get('student_id')).order_by(StudentAcademicDetail.academic_year_id.desc()).first()


@app.route('/student/class-teacher')
def student_class_teacher():
    if not session.get('student_logged_in'):
        return redirect(url_for('student_login'))
    detail = _student_detail()
    assignment = ClassTeacherAssignment.query.filter_by(class_id=detail.class_id, section_id=detail.section_id).first() if detail else None
    return render_template('student/class_teacher.html', assignment=assignment)


@app.route('/student/assigned-teachers')
def student_assigned_teachers():
    if not session.get('student_logged_in'):
        return redirect(url_for('student_login'))
    detail = _student_detail()
    assignments = StaffSubjectAssignment.query.filter_by(class_id=detail.class_id, section_id=detail.section_id).all() if detail else []
    return render_template('student/assigned_teachers.html', assignments=assignments)


@app.route('/student/assigned-subjects')
def student_assigned_subjects():
    if not session.get('student_logged_in'):
        return redirect(url_for('student_login'))
    detail = _student_detail()
    assignments = StaffSubjectAssignment.query.filter_by(class_id=detail.class_id, section_id=detail.section_id).all() if detail else []
    return render_template('student/assigned_subjects.html', assignments=assignments)


@app.route('/admin/communication/circulars', methods=['GET', 'POST'])
def admin_circulars():
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    circulars_upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'circulars')
    os.makedirs(circulars_upload_dir, exist_ok=True)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        target_audience = request.form.get('target_audience', 'All Students').strip()
        status = request.form.get('status', 'Published').strip()
        scheduled_date_str = request.form.get('scheduled_date', '').strip()
        attachment_file = request.files.get('attachment')
        
        if not title:
            flash("Circular Title is required.", "danger")
        else:
            student_id_val = request.form.get('student_id')
            staff_id_val = request.form.get('staff_id')
            student_id = None
            staff_id = None
            
            if target_audience == 'Individual Student':
                if not student_id_val:
                    flash("Please select a student for Individual Student target audience.", "danger")
                    return redirect(url_for('admin_circulars'))
                student_id = int(student_id_val)
            elif target_audience == 'Individual Staff':
                if not staff_id_val:
                    flash("Please select a staff member for Individual Staff target audience.", "danger")
                    return redirect(url_for('admin_circulars'))
                staff_id = int(staff_id_val)

            attachment_path = None
            if attachment_file and attachment_file.filename != '':
                filename = secure_filename(attachment_file.filename)
                timestamp = int(datetime.utcnow().timestamp())
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                saved_filename = f"circular_{timestamp}.{ext}" if ext else f"circular_{timestamp}"
                
                attachment_relative_path = os.path.join('uploads', 'circulars', saved_filename)
                attachment_file.save(os.path.join(app.root_path, 'static', attachment_relative_path))
                attachment_path = attachment_relative_path

            scheduled_date = None
            if status == 'Scheduled' and scheduled_date_str:
                try:
                    scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%dT%H:%M')
                except ValueError:
                    try:
                        scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        scheduled_date = datetime.utcnow()
                
            try:
                new_circular = Circular(
                    title=title,
                    description=description,
                    attachment_path=attachment_path,
                    target_audience=target_audience,
                    status=status,
                    scheduled_date=scheduled_date,
                    student_id=student_id,
                    staff_id=staff_id
                )
                db.session.add(new_circular)
                db.session.commit()
                flash(f"Circular '{title}' saved as {status} successfully!", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Error creating circular: {str(e)}", "danger")
                
            return redirect(url_for('admin_circulars'))
            
    search_query = request.args.get('search', '').strip()
    active_filter = request.args.get('filter', 'all').strip().lower()

    query = Circular.query
    if active_filter == 'published':
        query = query.filter_by(status='Published')
    elif active_filter == 'draft':
        query = query.filter_by(status='Draft')
    elif active_filter == 'scheduled':
        query = query.filter_by(status='Scheduled')

    if search_query:
        query = query.filter(
            (Circular.title.like(f"%{search_query}%")) | 
            (Circular.description.like(f"%{search_query}%")) |
            (Circular.target_audience.like(f"%{search_query}%"))
        )
        
    circulars_list = query.order_by(Circular.created_at.desc()).all()
    classrooms = ClassRoom.query.order_by(ClassRoom.display_order, ClassRoom.class_name).all()
    students = Student.query.order_by(Student.first_name, Student.last_name).all()
    staffs = Staff.query.order_by(Staff.first_name, Staff.last_name).all()
    
    # Calculate Dashboard Stats
    total_circulars = Circular.query.count()
    
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    published_today = Circular.query.filter_by(status='Published').filter(Circular.created_at >= today_start).count()
    
    draft_circulars = Circular.query.filter_by(status='Draft').count()
    scheduled_circulars = Circular.query.filter_by(status='Scheduled').count()
    total_views = CircularView.query.count()

    stats = {
        'total': total_circulars,
        'published_today': published_today,
        'drafts': draft_circulars,
        'scheduled': scheduled_circulars,
        'views': total_views
    }

    return render_template('admin/circulars.html',
                           circulars=circulars_list,
                           classrooms=classrooms,
                           students=students,
                           staffs=staffs,
                           search_query=search_query,
                           active_filter=active_filter,
                           stats=stats,
                           admin_username=session.get('admin_username'))

@app.route('/admin/communication/circulars/delete/<int:circular_id>', methods=['POST'])
def delete_circular(circular_id):
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    circular = Circular.query.get_or_404(circular_id)
    try:
        if circular.attachment_path:
            full_file_path = os.path.join(app.root_path, 'static', circular.attachment_path)
            if os.path.exists(full_file_path):
                os.remove(full_file_path)
                
        db.session.delete(circular)
        db.session.commit()
        flash("Circular deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting circular: {str(e)}", "danger")
        
    return redirect(url_for('admin_circulars'))


@app.route('/admin/communication/announcements', methods=['GET', 'POST'])
def admin_announcements():
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    announcements_upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'announcements')
    os.makedirs(announcements_upload_dir, exist_ok=True)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', 'General').strip()
        description = request.form.get('description', '').strip()
        target_audience = request.form.get('target_audience', 'All Students').strip()
        status = request.form.get('status', 'Published').strip()
        scheduled_date_str = request.form.get('scheduled_date', '').strip()
        attachment_file = request.files.get('attachment')
        
        if not title:
            flash("Announcement Title is required.", "danger")
        else:
            attachment_path = None
            if attachment_file and attachment_file.filename != '':
                filename = secure_filename(attachment_file.filename)
                timestamp = int(datetime.utcnow().timestamp())
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                saved_filename = f"announcement_{timestamp}.{ext}" if ext else f"announcement_{timestamp}"
                
                attachment_relative_path = os.path.join('uploads', 'announcements', saved_filename)
                attachment_file.save(os.path.join(app.root_path, 'static', attachment_relative_path))
                attachment_path = attachment_relative_path

            scheduled_date = None
            if status == 'Scheduled' and scheduled_date_str:
                try:
                    scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%dT%H:%M')
                except ValueError:
                    try:
                        scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        scheduled_date = datetime.utcnow()
                
            try:
                new_announcement = Announcement(
                    title=title,
                    category=category,
                    description=description,
                    attachment_path=attachment_path,
                    target_audience=target_audience,
                    status=status,
                    scheduled_date=scheduled_date
                )
                db.session.add(new_announcement)
                db.session.commit()
                flash(f"Announcement '{title}' saved as {status} successfully!", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Error creating announcement: {str(e)}", "danger")
                
            return redirect(url_for('admin_announcements'))
            
    search_query = request.args.get('search', '').strip()
    active_category = request.args.get('category', '').strip()
    active_status = request.args.get('status', '').strip()

    query = Announcement.query
    if active_status:
        query = query.filter_by(status=active_status)
    if active_category:
        query = query.filter_by(category=active_category)

    if search_query:
        query = query.filter(
            (Announcement.title.like(f"%{search_query}%")) | 
            (Announcement.description.like(f"%{search_query}%"))
        )
        
    announcements_list = query.order_by(Announcement.created_at.desc()).all()
    classrooms = ClassRoom.query.order_by(ClassRoom.display_order, ClassRoom.class_name).all()
    
    return render_template('admin/announcements.html',
                           announcements=announcements_list,
                           classrooms=classrooms,
                           search_query=search_query,
                           active_category=active_category,
                           active_status=active_status,
                           admin_username=session.get('admin_username'))


@app.route('/admin/communication/announcements/<int:announcement_id>', methods=['GET'])
def get_announcement_json(announcement_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    announcement = Announcement.query.get_or_404(announcement_id)
    return jsonify({
        'id': announcement.id,
        'title': announcement.title,
        'category': announcement.category,
        'description': announcement.description,
        'target_audience': announcement.target_audience,
        'status': announcement.status,
        'scheduled_date': announcement.scheduled_date.strftime('%Y-%m-%dT%H:%M') if announcement.scheduled_date else '',
        'attachment_path': announcement.attachment_path,
        'created_at': announcement.created_at.strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/admin/communication/announcements/edit/<int:announcement_id>', methods=['POST'])
def edit_announcement(announcement_id):
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    announcement = Announcement.query.get_or_404(announcement_id)
    title = request.form.get('title', '').strip()
    category = request.form.get('category', 'General').strip()
    description = request.form.get('description', '').strip()
    target_audience = request.form.get('target_audience', 'All Students').strip()
    status = request.form.get('status', 'Published').strip()
    scheduled_date_str = request.form.get('scheduled_date', '').strip()
    attachment_file = request.files.get('attachment')
    
    if not title:
        flash("Announcement Title is required.", "danger")
    else:
        try:
            announcement.title = title
            announcement.category = category
            announcement.description = description
            announcement.target_audience = target_audience
            announcement.status = status
            
            if attachment_file and attachment_file.filename != '':
                # remove old attachment
                if announcement.attachment_path:
                    old_path = os.path.join(app.root_path, 'static', announcement.attachment_path)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                filename = secure_filename(attachment_file.filename)
                timestamp = int(datetime.utcnow().timestamp())
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                saved_filename = f"announcement_{timestamp}.{ext}" if ext else f"announcement_{timestamp}"
                
                attachment_relative_path = os.path.join('uploads', 'announcements', saved_filename)
                attachment_file.save(os.path.join(app.root_path, 'static', attachment_relative_path))
                announcement.attachment_path = attachment_relative_path
                
            scheduled_date = None
            if status == 'Scheduled' and scheduled_date_str:
                try:
                    scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%dT%H:%M')
                except ValueError:
                    try:
                        scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        scheduled_date = datetime.utcnow()
            announcement.scheduled_date = scheduled_date
            
            db.session.commit()
            flash("Announcement updated successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating announcement: {str(e)}", "danger")
            
    return redirect(url_for('admin_announcements'))


@app.route('/admin/communication/announcements/delete/<int:announcement_id>', methods=['POST'])
def delete_announcement(announcement_id):
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    announcement = Announcement.query.get_or_404(announcement_id)
    try:
        if announcement.attachment_path:
            full_file_path = os.path.join(app.root_path, 'static', announcement.attachment_path)
            if os.path.exists(full_file_path):
                os.remove(full_file_path)
                
        db.session.delete(announcement)
        db.session.commit()
        flash("Announcement deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting announcement: {str(e)}", "danger")
        
    return redirect(url_for('admin_announcements'))


@app.route('/admin/communication/push', methods=['GET', 'POST'])
def admin_push_notifications():
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    push_upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'push')
    os.makedirs(push_upload_dir, exist_ok=True)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        message = request.form.get('message', '').strip()
        target_audience = request.form.get('target_audience', 'All Students').strip()
        status = request.form.get('status', 'Sent').strip()
        scheduled_date_str = request.form.get('scheduled_date', '').strip()
        image_file = request.files.get('image')
        
        if not title or not message:
            flash("Notification Title and Message are required.", "danger")
        else:
            image_path = None
            if image_file and image_file.filename != '':
                filename = secure_filename(image_file.filename)
                timestamp = int(datetime.utcnow().timestamp())
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                saved_filename = f"push_{timestamp}.{ext}" if ext else f"push_{timestamp}"
                
                image_relative_path = os.path.join('uploads', 'push', saved_filename)
                image_file.save(os.path.join(app.root_path, 'static', image_relative_path))
                image_path = image_relative_path

            scheduled_date = None
            if status == 'Scheduled' and scheduled_date_str:
                try:
                    scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%dT%H:%M')
                except ValueError:
                    try:
                        scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        scheduled_date = datetime.utcnow()
                
            try:
                new_push = PushNotification(
                    title=title,
                    message=message,
                    target_audience=target_audience,
                    status=status,
                    scheduled_date=scheduled_date,
                    image_path=image_path
                )
                db.session.add(new_push)
                db.session.commit()
                flash(f"Push Notification '{title}' saved as {status} successfully!", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Error creating push notification: {str(e)}", "danger")
                
            return redirect(url_for('admin_push_notifications'))
            
    search_query = request.args.get('search', '').strip()
    active_status = request.args.get('status', '').strip()

    query = PushNotification.query
    if active_status:
        query = query.filter_by(status=active_status)

    if search_query:
        query = query.filter(
            (PushNotification.title.like(f"%{search_query}%")) | 
            (PushNotification.message.like(f"%{search_query}%"))
        )
        
    notifications_list = query.order_by(PushNotification.created_at.desc()).all()
    
    return render_template('admin/push_notifications.html',
                           notifications=notifications_list,
                           search_query=search_query,
                           active_status=active_status,
                           admin_username=session.get('admin_username'))


@app.route('/admin/communication/push/<int:notification_id>', methods=['GET'])
def get_push_json(notification_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    notification = PushNotification.query.get_or_404(notification_id)
    return jsonify({
        'id': notification.id,
        'title': notification.title,
        'message': notification.message,
        'target_audience': notification.target_audience,
        'status': notification.status,
        'scheduled_date': notification.scheduled_date.strftime('%Y-%m-%dT%H:%M') if notification.scheduled_date else '',
        'image_path': notification.image_path,
        'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/admin/communication/push/edit/<int:notification_id>', methods=['POST'])
def edit_push_notification(notification_id):
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    notification = PushNotification.query.get_or_404(notification_id)
    title = request.form.get('title', '').strip()
    message = request.form.get('message', '').strip()
    target_audience = request.form.get('target_audience', 'All Students').strip()
    status = request.form.get('status', 'Sent').strip()
    scheduled_date_str = request.form.get('scheduled_date', '').strip()
    image_file = request.files.get('image')
    
    if not title or not message:
        flash("Notification Title and Message are required.", "danger")
    else:
        try:
            notification.title = title
            notification.message = message
            notification.target_audience = target_audience
            notification.status = status
            
            if image_file and image_file.filename != '':
                # remove old image
                if notification.image_path:
                    old_path = os.path.join(app.root_path, 'static', notification.image_path)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                filename = secure_filename(image_file.filename)
                timestamp = int(datetime.utcnow().timestamp())
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                saved_filename = f"push_{timestamp}.{ext}" if ext else f"push_{timestamp}"
                
                image_relative_path = os.path.join('uploads', 'push', saved_filename)
                image_file.save(os.path.join(app.root_path, 'static', image_relative_path))
                notification.image_path = image_relative_path
                
            scheduled_date = None
            if status == 'Scheduled' and scheduled_date_str:
                try:
                    scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%dT%H:%M')
                except ValueError:
                    try:
                        scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        scheduled_date = datetime.utcnow()
            notification.scheduled_date = scheduled_date
            
            db.session.commit()
            flash("Push Notification updated successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating push notification: {str(e)}", "danger")
            
    return redirect(url_for('admin_push_notifications'))


@app.route('/admin/communication/push/delete/<int:notification_id>', methods=['POST'])
def delete_push_notification(notification_id):
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    notification = PushNotification.query.get_or_404(notification_id)
    try:
        if notification.image_path:
            full_file_path = os.path.join(app.root_path, 'static', notification.image_path)
            if os.path.exists(full_file_path):
                os.remove(full_file_path)
                
        db.session.delete(notification)
        db.session.commit()
        flash("Push Notification deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting push notification: {str(e)}", "danger")
        
    return redirect(url_for('admin_push_notifications'))


@app.route('/admin/communication/notices', methods=['GET', 'POST'])
def admin_notices():
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    notice_upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'notices')
    os.makedirs(notice_upload_dir, exist_ok=True)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'General').strip()
        target_audience = request.form.get('target_audience', 'All Students').strip()
        status = request.form.get('status', 'Published').strip()
        publish_date_str = request.form.get('publish_date', '').strip()
        expiry_date_str = request.form.get('expiry_date', '').strip()
        attachment_file = request.files.get('attachment')
        
        if not title or not description:
            flash("Notice Title and Description are required.", "danger")
        else:
            attachment_path = None
            if attachment_file and attachment_file.filename != '':
                filename = secure_filename(attachment_file.filename)
                timestamp = int(datetime.utcnow().timestamp())
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                saved_filename = f"notice_{timestamp}.{ext}" if ext else f"notice_{timestamp}"
                
                relative_path = os.path.join('uploads', 'notices', saved_filename)
                attachment_file.save(os.path.join(app.root_path, 'static', relative_path))
                attachment_path = relative_path

            publish_date = datetime.utcnow()
            if publish_date_str:
                try:
                    publish_date = datetime.strptime(publish_date_str, '%Y-%m-%dT%H:%M')
                except ValueError:
                    pass

            expiry_date = None
            if expiry_date_str:
                try:
                    expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%dT%H:%M')
                except ValueError:
                    pass
                
            try:
                new_notice = Notice(
                    title=title,
                    description=description,
                    category=category,
                    target_audience=target_audience,
                    status=status,
                    publish_date=publish_date,
                    expiry_date=expiry_date,
                    attachment_path=attachment_path
                )
                db.session.add(new_notice)
                db.session.commit()
                flash(f"Notice '{title}' created successfully!", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Error creating notice: {str(e)}", "danger")
                
            return redirect(url_for('admin_notices'))
            
    search_query = request.args.get('search', '').strip()
    active_category = request.args.get('category', '').strip()
    active_status = request.args.get('status', '').strip()

    query = Notice.query
    if active_category:
        query = query.filter_by(category=active_category)
    if active_status:
        query = query.filter_by(status=active_status)

    if search_query:
        query = query.filter(
            (Notice.title.like(f"%{search_query}%")) | 
            (Notice.description.like(f"%{search_query}%"))
        )
        
    notices_list = query.order_by(Notice.publish_date.desc()).all()
    
    return render_template('admin/notices.html',
                           notices=notices_list,
                           search_query=search_query,
                           active_category=active_category,
                           active_status=active_status,
                           admin_username=session.get('admin_username'))


@app.route('/admin/communication/notices/<int:notice_id>', methods=['GET'])
def get_notice_json(notice_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    notice = Notice.query.get_or_404(notice_id)
    return jsonify({
        'id': notice.id,
        'title': notice.title,
        'description': notice.description,
        'category': notice.category,
        'target_audience': notice.target_audience,
        'status': notice.status,
        'publish_date': notice.publish_date.strftime('%Y-%m-%dT%H:%M') if notice.publish_date else '',
        'expiry_date': notice.expiry_date.strftime('%Y-%m-%dT%H:%M') if notice.expiry_date else '',
        'attachment_path': notice.attachment_path,
        'created_at': notice.created_at.strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/admin/communication/notices/edit/<int:notice_id>', methods=['POST'])
def edit_notice(notice_id):
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    notice = Notice.query.get_or_404(notice_id)
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    category = request.form.get('category', 'General').strip()
    target_audience = request.form.get('target_audience', 'All Students').strip()
    status = request.form.get('status', 'Published').strip()
    publish_date_str = request.form.get('publish_date', '').strip()
    expiry_date_str = request.form.get('expiry_date', '').strip()
    attachment_file = request.files.get('attachment')
    
    if not title or not description:
        flash("Notice Title and Description are required.", "danger")
    else:
        try:
            notice.title = title
            notice.description = description
            notice.category = category
            notice.target_audience = target_audience
            notice.status = status
            
            if attachment_file and attachment_file.filename != '':
                # remove old attachment
                if notice.attachment_path:
                    old_path = os.path.join(app.root_path, 'static', notice.attachment_path)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                filename = secure_filename(attachment_file.filename)
                timestamp = int(datetime.utcnow().timestamp())
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                saved_filename = f"notice_{timestamp}.{ext}" if ext else f"notice_{timestamp}"
                
                relative_path = os.path.join('uploads', 'notices', saved_filename)
                attachment_file.save(os.path.join(app.root_path, 'static', relative_path))
                notice.attachment_path = relative_path
                
            if publish_date_str:
                try:
                    notice.publish_date = datetime.strptime(publish_date_str, '%Y-%m-%dT%H:%M')
                except ValueError:
                    pass

            if expiry_date_str:
                try:
                    notice.expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%dT%H:%M')
                except ValueError:
                    pass
            else:
                notice.expiry_date = None
            
            db.session.commit()
            flash("Notice updated successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating notice: {str(e)}", "danger")
            
    return redirect(url_for('admin_notices'))


@app.route('/admin/communication/notices/delete/<int:notice_id>', methods=['POST'])
def delete_notice(notice_id):
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    notice = Notice.query.get_or_404(notice_id)
    try:
        if notice.attachment_path:
            full_file_path = os.path.join(app.root_path, 'static', notice.attachment_path)
            if os.path.exists(full_file_path):
                os.remove(full_file_path)
                
        db.session.delete(notice)
        db.session.commit()
        flash("Notice deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting notice: {str(e)}", "danger")
        
    return redirect(url_for('admin_notices'))


@app.route('/admin/communication/badge_counts', methods=['GET'])
def get_badge_counts():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Calculate counts of Draft/Scheduled items
    circular_count = Circular.query.filter(Circular.status.in_(['Draft', 'Scheduled'])).count()
    announcement_count = Announcement.query.filter(Announcement.status.in_(['Draft', 'Scheduled'])).count()
    push_count = PushNotification.query.filter(PushNotification.status.in_(['Draft', 'Scheduled'])).count()
    notice_count = Notice.query.filter(Notice.status == 'Draft').count()
    whatsapp_count = WhatsAppLog.query.filter_by(status='Draft').count()
    email_count = EmailLog.query.filter_by(status='Draft').count()
    
    # Get latest 5 communication activities for bell icon dropdown
    activities = []
    
    # Circulars
    circulars = Circular.query.order_by(Circular.created_at.desc()).limit(5).all()
    for c in circulars:
        activities.append({
            'type': 'Circular',
            'icon': 'fa-file-lines',
            'color': 'text-primary',
            'title': f"New Circular: {c.title}",
            'time': c.created_at,
            'url': url_for('admin_circulars')
        })
        
    # Announcements
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(5).all()
    for a in announcements:
        activities.append({
            'type': 'Announcement',
            'icon': 'fa-bullhorn',
            'color': 'text-info',
            'title': f"New Announcement: {a.title}",
            'time': a.created_at,
            'url': url_for('admin_announcements')
        })
        
    # Push notifications
    pushes = PushNotification.query.order_by(PushNotification.created_at.desc()).limit(5).all()
    for p in pushes:
        activities.append({
            'type': 'Push Notification',
            'icon': 'fa-bell',
            'color': 'text-warning',
            'title': f"Push Notification: {p.title}",
            'time': p.created_at,
            'url': url_for('admin_push_notifications')
        })
        
    # Notices
    notices = Notice.query.order_by(Notice.created_at.desc()).limit(5).all()
    for n in notices:
        activities.append({
            'type': 'Notice Board',
            'icon': 'fa-clipboard-list',
            'color': 'text-success',
            'title': f"New Notice Board Post: {n.title}",
            'time': n.created_at,
            'url': url_for('admin_notices')
        })
        
    # WhatsApp logs
    whatsapps = WhatsAppLog.query.order_by(WhatsAppLog.created_at.desc()).limit(5).all()
    for w in whatsapps:
        activities.append({
            'type': 'WhatsApp',
            'icon': 'fa-whatsapp',
            'color': 'text-success-emphasis',
            'title': f"WhatsApp sent to {w.recipient}",
            'time': w.created_at,
            'url': url_for('admin_whatsapp')
        })
        
    # Email logs
    emails = EmailLog.query.order_by(EmailLog.created_at.desc()).limit(5).all()
    for e in emails:
        activities.append({
            'type': 'Email',
            'icon': 'fa-envelope',
            'color': 'text-danger',
            'title': f"Email sent to {e.recipient}",
            'time': e.created_at,
            'url': url_for('admin_email')
        })
        
    # Sort activities by time desc and take top 5
    activities.sort(key=lambda x: x['time'], reverse=True)
    top_activities = activities[:5]
    
    # Format ISO strings
    for act in top_activities:
        act['time'] = act['time'].isoformat()
        
    return jsonify({
        'whatsapp': whatsapp_count,
        'email': email_count,
        'circular': circular_count,
        'push': push_count,
        'announcement': announcement_count,
        'notice': notice_count,
        'activities': top_activities
    })


@app.route('/admin/communication/whatsapp', methods=['GET', 'POST'])
def admin_whatsapp():
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    # Check if enabled
    setting = SystemSetting.query.filter_by(key='communication_whatsapp_enabled').first()
    is_enabled = setting.value.lower() == 'true' if setting else False
    if not is_enabled:
        flash("WhatsApp communication channel is currently disabled.", "warning")
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        recipient = request.form.get('recipient', '').strip()
        message = request.form.get('message', '').strip()
        status = request.form.get('status', 'Sent').strip()
        
        if not recipient or not message:
            flash("Recipient and Message are required.", "danger")
        else:
            try:
                new_log = WhatsAppLog(recipient=recipient, message=message, status=status)
                db.session.add(new_log)
                db.session.commit()
                flash(f"WhatsApp message saved as {status} successfully!", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Error creating WhatsApp log: {str(e)}", "danger")
            return redirect(url_for('admin_whatsapp'))
            
    search_query = request.args.get('search', '').strip()
    active_status = request.args.get('status', '').strip()
    
    query = WhatsAppLog.query
    if active_status:
        query = query.filter_by(status=active_status)
    if search_query:
        query = query.filter(
            (WhatsAppLog.recipient.like(f"%{search_query}%")) |
            (WhatsAppLog.message.like(f"%{search_query}%"))
        )
        
    logs = query.order_by(WhatsAppLog.created_at.desc()).all()
    return render_template('admin/whatsapp.html',
                           logs=logs,
                           search_query=search_query,
                           active_status=active_status,
                           admin_username=session.get('admin_username'))


@app.route('/admin/communication/whatsapp/delete/<int:log_id>', methods=['POST'])
def delete_whatsapp_log(log_id):
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    log = WhatsAppLog.query.get_or_404(log_id)
    try:
        db.session.delete(log)
        db.session.commit()
        flash("WhatsApp log deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting WhatsApp log: {str(e)}", "danger")
    return redirect(url_for('admin_whatsapp'))


@app.route('/admin/communication/email', methods=['GET', 'POST'])
def admin_email():
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    # Check if enabled
    setting = SystemSetting.query.filter_by(key='communication_email_enabled').first()
    is_enabled = setting.value.lower() == 'true' if setting else False
    if not is_enabled:
        flash("Email communication channel is currently disabled.", "warning")
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        recipient = request.form.get('recipient', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        status = request.form.get('status', 'Sent').strip()
        
        if not recipient or not subject or not message:
            flash("Recipient, Subject, and Message are required.", "danger")
        else:
            try:
                new_log = EmailLog(recipient=recipient, subject=subject, message=message, status=status)
                db.session.add(new_log)
                db.session.commit()
                flash(f"Email saved as {status} successfully!", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Error creating Email log: {str(e)}", "danger")
            return redirect(url_for('admin_email'))
            
    search_query = request.args.get('search', '').strip()
    active_status = request.args.get('status', '').strip()
    
    query = EmailLog.query
    if active_status:
        query = query.filter_by(status=active_status)
    if search_query:
        query = query.filter(
            (EmailLog.recipient.like(f"%{search_query}%")) |
            (EmailLog.subject.like(f"%{search_query}%")) |
            (EmailLog.message.like(f"%{search_query}%"))
        )
        
    logs = query.order_by(EmailLog.created_at.desc()).all()
    return render_template('admin/email.html',
                           logs=logs,
                           search_query=search_query,
                           active_status=active_status,
                           admin_username=session.get('admin_username'))


@app.route('/admin/communication/email/delete/<int:log_id>', methods=['POST'])
def delete_email_log(log_id):
    if not session.get('admin_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))
        
    log = EmailLog.query.get_or_404(log_id)
    try:
        db.session.delete(log)
        db.session.commit()
        flash("Email log deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting Email log: {str(e)}", "danger")
    return redirect(url_for('admin_email'))


@app.route('/staff/communication/circulars')
def staff_circulars():
    if not session.get('staff_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('staff_portal_login'))
        
    staff_id = session.get('staff_id')
    staff = Staff.query.get(staff_id)
    if not staff:
        session.clear()
        return redirect(url_for('staff_portal_login'))

    circulars_list = Circular.query.filter(
        Circular.status == 'Published',
        db.or_(
            Circular.target_audience.in_(['All Staff', 'All Students & All Staff']),
            db.and_(Circular.target_audience == 'Individual Staff', Circular.staff_id == staff_id)
        )
    ).order_by(Circular.created_at.desc()).all()

    # Log Unique Views
    for circ in circulars_list:
        existing_view = CircularView.query.filter_by(
            circular_id=circ.id,
            user_type='staff',
            staff_id=staff_id
        ).first()
        if not existing_view:
            db.session.add(CircularView(
                circular_id=circ.id,
                user_type='staff',
                staff_id=staff_id
            ))
    db.session.commit()

    # Get Acknowledged IDs
    acknowledged_ids = [
        ack.circular_id for ack in CircularAcknowledgement.query.filter_by(
            user_type='staff',
            staff_id=staff_id
        ).all()
    ]

    return render_template('staff/circulars.html',
                           circulars=circulars_list,
                           acknowledged_ids=acknowledged_ids,
                           staff=staff)


@app.route('/student/communication/circulars')
def student_circulars():
    if not session.get('student_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('student_login'))
        
    student_id = session.get('student_id')
    student = Student.query.get(student_id)
    if not student:
        session.clear()
        return redirect(url_for('student_login'))

    detail = _student_detail()
    classroom = ClassRoom.query.get(detail.class_id) if detail else None
    
    target_audiences = ['All Students', 'All Students & All Staff']
    if classroom:
        target_audiences.append(f"Class {classroom.class_name}")

    circulars_list = Circular.query.filter(
        Circular.status == 'Published',
        db.or_(
            Circular.target_audience.in_(target_audiences),
            db.and_(Circular.target_audience == 'Individual Student', Circular.student_id == student_id)
        )
    ).order_by(Circular.created_at.desc()).all()

    # Log Unique Views
    for circ in circulars_list:
        existing_view = CircularView.query.filter_by(
            circular_id=circ.id,
            user_type='student',
            student_id=student_id
        ).first()
        if not existing_view:
            db.session.add(CircularView(
                circular_id=circ.id,
                user_type='student',
                student_id=student_id
            ))
    db.session.commit()

    # Get Acknowledged IDs
    acknowledged_ids = [
        ack.circular_id for ack in CircularAcknowledgement.query.filter_by(
            user_type='student',
            student_id=student_id
        ).all()
    ]

    return render_template('student/circulars.html',
                           circulars=circulars_list,
                           acknowledged_ids=acknowledged_ids,
                           student=student)


@app.route('/communication/circular/<int:circular_id>/acknowledge', methods=['POST'])
def acknowledge_circular(circular_id):
    if session.get('student_logged_in'):
        student_id = session.get('student_id')
        existing = CircularAcknowledgement.query.filter_by(
            circular_id=circular_id,
            user_type='student',
            student_id=student_id
        ).first()
        if not existing:
            db.session.add(CircularAcknowledgement(
                circular_id=circular_id,
                user_type='student',
                student_id=student_id
            ))
            db.session.commit()
            flash("Circular acknowledged successfully.", "success")
        return redirect(url_for('student_circulars'))

    elif session.get('staff_logged_in'):
        staff_id = session.get('staff_id')
        existing = CircularAcknowledgement.query.filter_by(
            circular_id=circular_id,
            user_type='staff',
            staff_id=staff_id
        ).first()
        if not existing:
            db.session.add(CircularAcknowledgement(
                circular_id=circular_id,
                user_type='staff',
                staff_id=staff_id
            ))
            db.session.commit()
            flash("Circular acknowledged successfully.", "success")
        return redirect(url_for('staff_circulars'))

    else:
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('login'))


@app.route('/student/communication/announcements')
def student_announcements():
    if not session.get('student_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('student_login'))
        
    student_id = session.get('student_id')
    student = Student.query.get(student_id)
    if not student:
        session.clear()
        return redirect(url_for('student_login'))

    detail = _student_detail()
    classroom = ClassRoom.query.get(detail.class_id) if detail else None
    
    target_audiences = ['All Students', 'All Students & All Staff']
    if classroom:
        target_audiences.append(f"Class {classroom.class_name}")

    announcements_list = Announcement.query.filter(
        Announcement.status == 'Published',
        Announcement.target_audience.in_(target_audiences)
    ).order_by(Announcement.created_at.desc()).all()

    return render_template('student/announcements.html',
                           announcements=announcements_list,
                           student=student)


@app.route('/staff/communication/announcements')
def staff_announcements():
    if not session.get('staff_logged_in'):
        flash("Access denied. Please log in first.", "warning")
        return redirect(url_for('staff_portal_login'))
        
    staff_id = session.get('staff_id')
    staff = Staff.query.get(staff_id)
    if not staff:
        session.clear()
        return redirect(url_for('staff_portal_login'))

    announcements_list = Announcement.query.filter(
        Announcement.status == 'Published',
        Announcement.target_audience.in_(['All Staff', 'All Students & All Staff'])
    ).order_by(Announcement.created_at.desc()).all()

    return render_template('staff/announcements.html',
                           announcements=announcements_list,
                           staff=staff)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='127.0.0.1', port=9090, debug=True)
