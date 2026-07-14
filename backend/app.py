import csv
import json
import os
import smtplib
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash
from datetime import datetime
from email.mime.text import MIMEText
from flask_jwt_extended import JWTManager
from celery import Celery
from celery.schedules import crontab
from redis import Redis
from sqlalchemy import distinct, func, inspect
from urllib.request import Request, urlopen


# reads simple KEY=VALUE lines from a local .env file (if present) into the
# environment — keeps secrets like the Google Chat webhook URL out of this
# source file, with no extra library needed
def load_env_file(path=".env"):
    if not os.path.exists(path):
        return

    with open(path) as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


load_env_file()

app = Flask(__name__)
CORS(app, supports_credentials=True)
# comes from the .env file so the real key never has to live in source code —
# the fallback below only kicks in if someone forgets to set it, so local
# demos still work out of the box
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///placement.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB cap on any uploaded file (resume / offer letter)
jwt = JWTManager(app)
db = SQLAlchemy(app)

# Celery tasks run outside a real HTTP request, so Flask's url_for(..., _external=True)
# has no request to read the host from — build download links using this instead.
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "http://127.0.0.1:5000")

REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
# Celery (broker+backend on Redis) drives the async/scheduled jobs below: interview reminders, monthly placement reports, and user-triggered CSV exports
celery_app = Celery(app.import_name, broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
celery_app.conf.beat_schedule = {
    "auto-close-expired-jobs": {
        "task": "tasks.auto_close_expired_jobs",
        "schedule": crontab(hour=0, minute=5),
    },
    "send-daily-placement-reminders": {
        "task": "tasks.send_daily_placement_reminders",
        "schedule": crontab(hour=10, minute=0),
    },
    "generate-monthly-placement-report": {
        "task": "tasks.generate_monthly_placement_report",
        "schedule": crontab(hour=9, minute=0, day_of_month=1),
    },
}


# ---------------- HELPERS ----------------

# invalidates the Redis-cached hot dashboard reads (admin stats, company/student lists) so writes never serve stale data
def clear_dashboard_caches():
    redis_client.delete("admin_stats", "companies_list", "admin_all_companies")


def normalize_skills(skills_text):
    if not skills_text:
        return set()

    return {
        skill.strip().lower()
        for skill in skills_text.split(",")
        if skill.strip()
    }


def normalize_branches(branches_text):
    if not branches_text:
        return set()

    return {
        branch.strip().lower()
        for branch in branches_text.split(",")
        if branch.strip()
    }


def normalize_years(years_text):
    if not years_text:
        return set()

    return {
        int(year.strip())
        for year in years_text.split(",")
        if year.strip().isdigit()
    }


ALLOWED_DOCUMENT_EXTENSIONS = {"pdf", "doc", "docx"}


def is_allowed_document(filename):
    if not filename or "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in ALLOWED_DOCUMENT_EXTENSIONS


def student_is_eligible_for_job(student_profile, job):
    # 1. skills — job only cares about this if it lists any skills
    student_skills = normalize_skills(student_profile.skills)
    job_skills = normalize_skills(job.skills)

    if job_skills and not student_skills.intersection(job_skills):
        return False

    # 2. minimum CGPA — job only cares about this if it set one
    if job.min_cgpa is not None:
        if student_profile.cgpa is None or student_profile.cgpa < job.min_cgpa:
            return False

    # 3. branch — job only cares about this if it listed any branches
    job_branches = normalize_branches(job.eligible_branches)
    if job_branches:
        student_branch = (student_profile.department or "").strip().lower()
        if student_branch not in job_branches:
            return False

    # 4. year — job only cares about this if it listed any years
    job_years = normalize_years(job.eligible_years)
    if job_years and student_profile.year not in job_years:
        return False

    return True


def send_notification_message(subject, message, recipients=None, html_message=None, use_webhook=False):
    # use_webhook is opt-in per call — the monthly report must always go to
    # the admin's email, never redirected to chat just because a webhook
    # happens to be configured for the (separate) daily reminders feature
    webhook_url = os.environ.get("REMINDER_WEBHOOK_URL") if use_webhook else None
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    sender_email = os.environ.get("SMTP_FROM", smtp_user or "noreply@example.com")

    if webhook_url:
        payload = json.dumps({
            "text": f"{subject}\n\n{message}",
        }).encode("utf-8")
        request_obj = Request(webhook_url, data=payload, headers={"Content-Type": "application/json"})
        with urlopen(request_obj, timeout=10) as response:
            response.read()
        return {"mode": "webhook", "subject": subject}

    if smtp_host and recipients:
        body = html_message if html_message else message
        mime_message = MIMEText(body, "html" if html_message else "plain", "utf-8")
        mime_message["Subject"] = subject
        mime_message["From"] = sender_email
        mime_message["To"] = ", ".join(recipients)

        with smtplib.SMTP(smtp_host, smtp_port) as smtp_connection:
            if os.environ.get("SMTP_USE_TLS", "true").lower() == "true":
                smtp_connection.starttls()
            if smtp_user and smtp_password:
                smtp_connection.login(smtp_user, smtp_password)
            smtp_connection.sendmail(sender_email, recipients, mime_message.as_string())

        return {"mode": "email", "subject": subject, "recipients": recipients}

    print(f"[{subject}] {message}")
    return {"mode": "console", "subject": subject}


def get_month_bounds(reference_date=None):
    current_date = reference_date or datetime.utcnow()
    month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if current_date.month == 12:
        next_month_start = month_start.replace(year=current_date.year + 1, month=1)
    else:
        next_month_start = month_start.replace(month=current_date.month + 1)

    return month_start, next_month_start


def get_upcoming_deadline_jobs():
    now = datetime.utcnow()

    # every approved, still-open job with a deadline that hasn't passed yet
    # counts as "upcoming" — not just ones within the next couple of days
    return Job.query.filter(
        Job.application_deadline.isnot(None),
        Job.is_approved.is_(True),
        Job.is_closed.is_(False),
        Job.application_deadline >= now,
    ).all()


def close_expired_jobs():
    now = datetime.utcnow()

    expired_jobs = Job.query.filter(
        Job.application_deadline.isnot(None),
        Job.application_deadline < now,
        Job.is_closed.is_(False),
    ).all()

    for job in expired_jobs:
        job.is_closed = True

    if expired_jobs:
        db.session.commit()
        clear_dashboard_caches()

    return len(expired_jobs)


# runs before every single request — this is what makes a job close the
# moment its deadline passes, instead of only when the nightly Celery Beat
# schedule (or the admin's "Close Expired Drives Now" button) happens to run


@app.before_request
def auto_close_expired_jobs_before_request():
    close_expired_jobs()


def ensure_sqlite_schema():
    inspector = inspect(db.engine)
    job_columns = {column["name"] for column in inspector.get_columns("jobs")}
    company_columns = {column["name"] for column in inspector.get_columns("company_profiles")}
    student_columns = {column["name"] for column in inspector.get_columns("student_profiles")}

    with db.engine.begin() as connection:
        if "application_deadline" not in job_columns:
            connection.exec_driver_sql("ALTER TABLE jobs ADD COLUMN application_deadline DATETIME")
        if "min_cgpa" not in job_columns:
            connection.exec_driver_sql("ALTER TABLE jobs ADD COLUMN min_cgpa FLOAT")
        if "eligible_branches" not in job_columns:
            connection.exec_driver_sql("ALTER TABLE jobs ADD COLUMN eligible_branches VARCHAR(200)")
        if "eligible_years" not in job_columns:
            connection.exec_driver_sql("ALTER TABLE jobs ADD COLUMN eligible_years VARCHAR(100)")
        if "hr_contact" not in company_columns:
            connection.exec_driver_sql("ALTER TABLE company_profiles ADD COLUMN hr_contact VARCHAR(100)")
        if "is_profile_complete" not in company_columns:
            connection.exec_driver_sql("ALTER TABLE company_profiles ADD COLUMN is_profile_complete BOOLEAN DEFAULT 0")
            # companies that already filled in their name before this column existed
            # should still count as "complete", not suddenly look unfinished
            connection.exec_driver_sql("UPDATE company_profiles SET is_profile_complete = 1 WHERE company_name IS NOT NULL")
        if "is_profile_complete" not in student_columns:
            connection.exec_driver_sql("ALTER TABLE student_profiles ADD COLUMN is_profile_complete BOOLEAN DEFAULT 0")
            connection.exec_driver_sql("UPDATE student_profiles SET is_profile_complete = 1 WHERE department IS NOT NULL OR skills IS NOT NULL")


def init_db():
    db.create_all()
    ensure_sqlite_schema()

    # this app only ever has one admin, and there's no signup form for it —
    # so the very first time the app starts with an empty database, create
    # that one admin account automatically
    if not User.query.filter_by(role="admin").first():
        admin = User(
            name="Admin",
            email="placementportal.admin@gmail.com",
            password=generate_password_hash("admin123"),
            role="admin",
            is_approved=True
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin created")


# ---------------- SCHEDULED / BACKGROUND JOBS ----------------

@celery_app.task(name="tasks.export_student_applications_csv")
def export_student_applications_csv(student_profile_id):
    with app.app_context():
        profile = StudentProfile.query.get(student_profile_id)

        if not profile:
            return {
                "status": "failed",
                "message": "Student profile not found",
            }

        exports_folder = os.path.join(app.config["UPLOAD_FOLDER"], "exports")
        os.makedirs(exports_folder, exist_ok=True)

        filename = (
            f"student_{profile.user_id}_applications_"
            f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
        )
        file_path = os.path.join(exports_folder, filename)

        applications = Application.query.filter_by(student_id=profile.id).all()

        with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow([
                "Student ID",
                "Company Name",
                "Drive Title",
                "Application Status",
                "Applied At",
            ])

            for application in applications:
                writer.writerow([
                    profile.user_id,
                    application.job.company.company_name if application.job and application.job.company else "",
                    application.job.title if application.job else "",
                    application.status,
                    application.applied_at,
                ])

        return {
            "status": "completed",
            "message": "CSV export is ready",
            "download_url": f"{BACKEND_BASE_URL}/uploads/exports/{filename}",
        }


@celery_app.task(name="tasks.auto_close_expired_jobs")
def auto_close_expired_jobs():
    with app.app_context():
        jobs_closed = close_expired_jobs()
        return {"status": "completed", "jobs_closed": jobs_closed}


@celery_app.task(name="tasks.send_daily_placement_reminders")
def send_daily_placement_reminders():
    with app.app_context():
        upcoming_jobs = get_upcoming_deadline_jobs()

        if not upcoming_jobs:
            return {"status": "completed", "message": "No upcoming deadlines found"}

        reminder_lines = []
        for job in upcoming_jobs:
            deadline_text = job.application_deadline.strftime("%Y-%m-%d") if job.application_deadline else "N/A"
            reminder_lines.append(f"{job.title} at {job.company.company_name} - deadline {deadline_text}")

        reminder_text = "Upcoming placement deadlines:\n" + "\n".join(f"- {line}" for line in reminder_lines)

        # the webhook posts to one shared Google Chat space, not to individual
        # students — so this must be sent once total, not once per student
        # (looping per student was posting the same message N times over)
        send_notification_message(
            "Placement Reminder",
            reminder_text,
            use_webhook=True,
        )

        return {
            "status": "completed",
            "reminders_sent": 1,
            "upcoming_jobs": len(upcoming_jobs),
        }


@celery_app.task(name="tasks.generate_monthly_placement_report")
def generate_monthly_placement_report():
    with app.app_context():
        month_start, next_month_start = get_month_bounds()
        admin_user = User.query.filter_by(role="admin").first()

        drives_conducted = Job.query.filter(
            Job.posted_at >= month_start,
            Job.posted_at < next_month_start,
        ).count()

        applications_submitted = db.session.query(func.count(Application.id)).filter(
            Application.applied_at >= month_start,
            Application.applied_at < next_month_start,
        ).scalar() or 0

        students_applied = db.session.query(func.count(distinct(Application.student_id))).filter(
            Application.applied_at >= month_start,
            Application.applied_at < next_month_start,
        ).scalar() or 0

        students_selected = db.session.query(func.count(distinct(Application.student_id))).filter(
            Application.status == "Selected",
            Application.updated_at.isnot(None),
            Application.updated_at >= month_start,
            Application.updated_at < next_month_start,
        ).scalar() or 0

        # build one row per drive that got at least one application this
        # month — company, drive name, how many applied, and whether
        # anyone from that drive was selected
        month_applications = Application.query.filter(
            Application.applied_at >= month_start,
            Application.applied_at < next_month_start,
        ).all()

        drive_stats = {}
        for application in month_applications:
            job = application.job
            if not job:
                continue

            student_user = application.student.user if application.student else None
            student_name = student_user.name if student_user else "Unknown"

            if job.id not in drive_stats:
                drive_stats[job.id] = {
                    "company_name": job.company.company_name if job.company else "N/A",
                    "job_title": job.title,
                    "applied_names": [],
                    "selected_names": [],
                }

            drive_stats[job.id]["applied_names"].append(student_name)
            if application.status == "Selected":
                drive_stats[job.id]["selected_names"].append(student_name)

        if drive_stats:
            drive_rows_html = "".join(
                f"""
                <tr>
                  <td>{row['company_name']}</td>
                  <td>{row['job_title']}</td>
                  <td>{", ".join(row['applied_names'])}</td>
                  <td>{", ".join(row['selected_names']) if row['selected_names'] else "No"}</td>
                </tr>
                """
                for row in drive_stats.values()
            )
        else:
            drive_rows_html = "<tr><td colspan=\"4\">No drives with applications this month.</td></tr>"

        report_html = f"""
        <html>
          <head>
            <style>
              body {{ font-family: Arial, sans-serif; padding: 24px; }}
              .card {{ border: 1px solid #ddd; padding: 16px; margin-bottom: 12px; }}
              table {{ border-collapse: collapse; width: 100%; }}
              th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
              th {{ background: #f2f2f2; }}
            </style>
          </head>
          <body>
            <h2>Monthly Placement Activity Report</h2>
            <div class="card">
              <p><b>Month:</b> {month_start.strftime('%B %Y')}</p>
              <p><b>Drives Conducted:</b> {drives_conducted}</p>
              <p><b>Applications Submitted:</b> {applications_submitted}</p>
              <p><b>Students Applied:</b> {students_applied}</p>
              <p><b>Students Selected:</b> {students_selected}</p>
            </div>

            <h2>Drive-wise Breakdown</h2>
            <table>
              <tr>
                <th>Company Name</th>
                <th>Drive Name</th>
                <th>Students Applied</th>
                <th>Students Selected</th>
              </tr>
              {drive_rows_html}
            </table>
          </body>
        </html>
        """

        reports_folder = os.path.join(app.config["UPLOAD_FOLDER"], "reports")
        os.makedirs(reports_folder, exist_ok=True)
        report_filename = f"monthly_report_{month_start.strftime('%Y_%m')}.html"
        report_path = os.path.join(reports_folder, report_filename)

        with open(report_path, "w", encoding="utf-8") as report_file:
            report_file.write(report_html)

        if admin_user and admin_user.email:
            send_notification_message(
                f"Monthly Placement Report - {month_start.strftime('%B %Y')}",
                "The monthly placement report is ready.",
                recipients=[admin_user.email],
                html_message=report_html,
            )

        return {
            "status": "completed",
            "report_file": report_filename,
            "report_url": f"{BACKEND_BASE_URL}/uploads/reports/{report_filename}",
            "drives_conducted": drives_conducted,
            "applications_submitted": applications_submitted,
            "students_applied": students_applied,
            "students_selected": students_selected,
        }


# the actual table definitions live in models.py, and every route file
# lives under routes/ — both get imported down here, after everything
# above (app, db, celery_app, the helper functions) already exists, since
# models.py and the route files need to import those from this file
from models import User, StudentProfile, Job, Application

from routes import public_routes, student_routes, company_routes, admin_routes

# makes sure the tables exist and the one admin account is there — this runs
# every time this file is imported (by run.py, by Celery, doesn't matter),
# not just when you run this file directly, so it's always in place
with app.app_context():
    init_db()
