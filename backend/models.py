# All the database tables for this app live here.
# "db" itself is created in app.py, not here — this file just imports it and
# uses it to describe each table, so the whole app shares the exact same
# database connection instead of accidentally creating a second one.
from datetime import datetime
from app import db


# ---------------- USER ----------------
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # store hashed password
    role = db.Column(db.String(20), nullable=False)  # admin / student / company

    phone = db.Column(db.String(15))
    is_active = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # one user → one student profile
    student_profile = db.relationship(
        "StudentProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete"
    )

    # one user → one company profile
    company_profile = db.relationship(
        "CompanyProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete"
    )


# ---------------- STUDENT PROFILE ----------------
class StudentProfile(db.Model):
    __tablename__ = "student_profiles"

    id = db.Column(db.Integer, primary_key=True)

    # one-to-one → must be unique
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        unique=True
    )

    department = db.Column(db.String(100))
    year = db.Column(db.Integer)
    cgpa = db.Column(db.Float)

    skills = db.Column(db.String(200))  # simple for now (comma separated)
    resume = db.Column(db.String(200))

    placement_status = db.Column(db.String(50), default="Not Placed")

    # this row is created empty at registration — flips to True once the
    # student actually fills in and submits their profile
    is_profile_complete = db.Column(db.Boolean, default=False)

    # relation back to user
    user = db.relationship("User", back_populates="student_profile")

    # one student → many applications
    applications = db.relationship(
        "Application",
        back_populates="student",
        cascade="all, delete"
    )


# ---------------- COMPANY PROFILE ----------------
class CompanyProfile(db.Model):
    __tablename__ = "company_profiles"

    id = db.Column(db.Integer, primary_key=True)

    # one-to-one → must be unique
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        unique=True
    )

    company_name = db.Column(db.String(150))
    industry = db.Column(db.String(100))
    website = db.Column(db.String(150))
    location = db.Column(db.String(100))
    company_size = db.Column(db.String(50))
    hr_contact = db.Column(db.String(100))

    # this row is created empty at registration — flips to True once the
    # company actually fills in and submits their profile
    is_profile_complete = db.Column(db.Boolean, default=False)

    # relation back to user
    user = db.relationship("User", back_populates="company_profile")

    # one company → many jobs
    jobs = db.relationship(
        "Job",
        back_populates="company",
        cascade="all, delete"
    )


# ---------------- JOB ----------------
class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("company_profiles.id"),
        nullable=False
    )

    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)

    skills = db.Column(db.String(200), nullable=False)
    experience = db.Column(db.String(50))
    salary = db.Column(db.String(50))
    benefits = db.Column(db.String(300))

    location = db.Column(db.String(100))
    job_type = db.Column(db.String(50), default="Full-time")
    application_deadline = db.Column(db.DateTime)

    # eligibility criteria (all optional — if a company leaves one blank,
    # that criterion just isn't checked for students)
    min_cgpa = db.Column(db.Float)
    eligible_branches = db.Column(db.String(200))  # comma separated, e.g. "CSE, ECE"
    eligible_years = db.Column(db.String(100))     # comma separated, e.g. "3, 4"

    is_approved = db.Column(db.Boolean, default=False)
    is_closed = db.Column(db.Boolean, default=False)

    posted_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_blacklisted = db.Column(db.Boolean, default=False)
    # relation
    company = db.relationship("CompanyProfile", back_populates="jobs")

    # one job → many applications
    applications = db.relationship(
        "Application",
        back_populates="job",
        cascade="all, delete"
    )


# ---------------- APPLICATION ----------------
class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)

    job_id = db.Column(
        db.Integer,
        db.ForeignKey("jobs.id"),
        nullable=False
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("student_profiles.id"),
        nullable=False
    )

    status = db.Column(db.String(50), default="Applied")

    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime)

    remarks = db.Column(db.Text)

    # interview details
    interview_datetime = db.Column(db.DateTime)
    interview_mode = db.Column(db.String(50))  # Online / Offline
    interview_link = db.Column(db.String(300))
    interview_location = db.Column(db.String(200))

    feedback = db.Column(db.Text)
    offer_letter = db.Column(db.String(200))

    # relations
    job = db.relationship("Job", back_populates="applications")
    student = db.relationship("StudentProfile", back_populates="applications")


