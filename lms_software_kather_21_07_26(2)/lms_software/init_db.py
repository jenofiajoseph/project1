import sys
from datetime import datetime, date
from werkzeug.security import generate_password_hash
from app import app, db, Admin, Department, Role, AcademicYear, ClassRoom, Section, SuperAdmin, SystemSetting, EntranceExam, ExamQuestion, StudentExamAttempt, Circular, CircularAcknowledgement, CircularView, Announcement, PushNotification, Notice, WhatsAppLog, EmailLog

def init_database():
    print("Connecting to the database and dropping existing tables...")
    
    with app.app_context():
        try:
            # Drop all tables to perform clean slate migration
            db.drop_all()
            print("Dropped all existing tables.")
            
            # Create all tables according to new models
            db.create_all()
            print("Database schema created successfully.")
            
            # 1. Seed Admin Account
            print("Seeding admin account...")
            hashed_pw = generate_password_hash('admin123')
            admin_user = Admin(username='admin', password_hash=hashed_pw)
            db.session.add(admin_user)
            
            # 1b. Seed Super Admin Account
            print("Seeding super admin account...")
            super_admin_user = SuperAdmin(username='superadmin', password_hash=hashed_pw)
            db.session.add(super_admin_user)
            
            # 1c. Seed System Settings
            print("Seeding system settings...")
            entrance_setting = SystemSetting(key='entrance_exam_enabled', value='false')
            db.session.add(entrance_setting)
            
            # Seed Communication settings (enabled by default for better user evaluation)
            db.session.add(SystemSetting(key='communication_enabled', value='true'))
            db.session.add(SystemSetting(key='communication_whatsapp_enabled', value='false'))
            db.session.add(SystemSetting(key='communication_email_enabled', value='false'))
            db.session.add(SystemSetting(key='communication_circular_enabled', value='true'))
            db.session.add(SystemSetting(key='communication_push_enabled', value='false'))
            db.session.add(SystemSetting(key='communication_announcement_enabled', value='false'))
            db.session.add(SystemSetting(key='communication_notice_board_enabled', value='false'))
            
            # 2. Seed Default Departments
            print("Seeding default departments...")
            departments = [
                Department(name="Tamil"),
                Department(name="English"),
                Department(name="Mathematics"),
                Department(name="Physics"),
                Department(name="Chemistry"),
                Department(name="Botany"),
                Department(name="Zoology"),
                Department(name="Science"),
                Department(name="Social Science"),
                Department(name="Environmental Science"),
                Department(name="Hindi"),
                Department(name="Geography"),
                Department(name="Computer Science"),
                Department(name="Commerce"),
                Department(name="History"),
                Department(name="Accountancy"),
                Department(name="Economics"),
                Department(name="Business Studies"),
                Department(name="Political Science"),
                Department(name="Administration"),
                Department(name="Library"),
                Department(name="Reception"),
                Department(name="IT Support"),
                Department(name="Accounts")
            ]
            db.session.add_all(departments)
            
            # 3. Seed Default Roles
            print("Seeding default roles...")
            roles = [
                Role(name="Principal"),
                Role(name="HOD"),
                Role(name="Class Teacher"),
                Role(name="Librarian"),
                Role(name="Receptionist")
            ]
            db.session.add_all(roles)
            
            # 4. Seed Default Academic Year
            print("Seeding default academic year...")
            academic_year = AcademicYear(
                name="2026-2027",
                start_date=date(2026, 6, 1),
                end_date=date(2027, 4, 30),
                is_current=True
            )
            db.session.add(academic_year)
            db.session.flush() # flush to get academic_year.id
            
            # 5. Seed Default Classes & Sections
            print("Seeding default classes and sections...")
            class_names = ["LKG", "UKG", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
            classrooms = []
            
            for index, name in enumerate(class_names):
                classroom = ClassRoom(class_name=name, display_order=index + 1, academic_year_id=academic_year.id)
                classrooms.append(classroom)
                db.session.add(classroom)
            
            db.session.flush() # Flush to get class_ids
            
            # Seed A & B sections for all classes
            for classroom in classrooms:
                section_a = Section(class_id=classroom.class_id, section_name="A", academic_year_id=academic_year.id)
                section_b = Section(class_id=classroom.class_id, section_name="B", academic_year_id=academic_year.id)
                db.session.add_all([section_a, section_b])

            # Seed WhatsApp Logs (3 Draft, 1 Sent)
            print("Seeding WhatsApp logs...")
            db.session.add_all([
                WhatsAppLog(recipient="All Teachers", message="Reminder: Staff review meeting tomorrow.", status="Sent"),
                WhatsAppLog(recipient="Class 10-A Parents", message="Draft: Midterm exams report cards update.", status="Draft"),
                WhatsAppLog(recipient="Class 12-B Students", message="Draft: Physics quiz scheduled for Friday.", status="Draft"),
                WhatsAppLog(recipient="All Parents", message="Draft: Sports day registration reminder.", status="Draft")
            ])
            
            # Seed Email Logs (1 Draft, 1 Sent)
            print("Seeding Email logs...")
            db.session.add_all([
                EmailLog(recipient="principal@school.com", subject="Academic Performance Audit", message="audit report text", status="Sent"),
                EmailLog(recipient="teachers@school.com", subject="Draft: Annual Workshop Guidelines", message="guidelines text", status="Draft")
            ])
            
            # Seed Circulars (3 Draft, 2 Scheduled, 2 Published -> 5 pending)
            print("Seeding Circulars...")
            db.session.add_all([
                Circular(title="Annual Sports Meet 2026", description="Detailed guidelines for the sports meet.", target_audience="All Students, Staff & Parents", status="Published"),
                Circular(title="Quarterly Fees Structure", description="Fees details for the second quarter.", target_audience="All Parents", status="Published"),
                Circular(title="Draft: Science Exhibition Guidelines", description="Science exhibition registration.", target_audience="All Students", status="Draft"),
                Circular(title="Draft: National Day Celebration", description="Independence day events list.", target_audience="All Students & All Staff", status="Draft"),
                Circular(title="Draft: Special Lecture Series", description="Guest lecture timetable.", target_audience="All Staff", status="Draft"),
                Circular(title="Scheduled: Parent-Teacher Meeting", description="Scheduled PTM for October.", target_audience="All Parents", status="Scheduled", scheduled_date=datetime(2026, 10, 15, 10, 0)),
                Circular(title="Scheduled: Staff Training Program", description="Professional development workshop.", target_audience="All Staff", status="Scheduled", scheduled_date=datetime(2026, 11, 1, 9, 30))
            ])
            
            # Seed Announcements (2 Draft, 1 Published -> 2 pending)
            print("Seeding Announcements...")
            db.session.add_all([
                Announcement(title="Mid-Term Exams Timetable", description="Class 6-12 midterm exams schedule.", category="Academic", target_audience="All Students", status="Published"),
                Announcement(title="Draft: Library Books Return", description="Return borrowed books before next week.", category="General", target_audience="All Students", status="Draft"),
                Announcement(title="Draft: Holiday Notice - Diwali", description="School holiday announcement.", category="Holiday", target_audience="All Students, Staff & Parents", status="Draft")
            ])
            
            # Seed Push Notifications (2 Sent -> 0 pending)
            print("Seeding Push Notifications...")
            db.session.add_all([
                PushNotification(title="Exam Fees Due Reminder", message="Please pay exam fees before July 30.", target_audience="All Parents", status="Sent"),
                PushNotification(title="Urgent: School Bus Delay", message="Route 4 bus is delayed by 20 minutes.", target_audience="All Parents", status="Sent")
            ])
            
            # Seed Notices (1 Draft, 1 Published -> 1 pending)
            print("Seeding Notices...")
            db.session.add_all([
                Notice(title="Notice: Inter-School Debate competition", description="Debate competition rules.", category="Event", target_audience="All Students", status="Published"),
                Notice(title="Draft: Revision Timetable Notice", description="Revision classes schedule.", category="Academic", target_audience="All Students", status="Draft")
            ])
            
            db.session.commit()
            print("\nDatabase initialized and seeded successfully!")
            print("Default Admin Account:")
            print("  Username: admin")
            print("  Password: admin123 (hashed in database)")
            print(f"Seeded {len(departments)} departments, {len(roles)} roles, {len(class_names)} classes, and sections A/B.")
            
        except Exception as e:
            db.session.rollback()
            print(f"\nError during database initialization: {e}", file=sys.stderr)
            print("Please make sure PostgreSQL is running and your DATABASE_URL in .env is correct.", file=sys.stderr)
            sys.exit(1)

if __name__ == '__main__':
    init_database()
