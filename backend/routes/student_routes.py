# Everything a logged-in student can do: profile, browsing companies and
# drives, applying, tracking applications, resume upload, and CSV export.
#
# "app" and "db" come from app.py, not created here — see public_routes.py
# for why. The helper functions and the export Celery task also live in
# app.py, so they're imported from there the same way.
import json
import os
from datetime import datetime

from flask import request, jsonify, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from celery.result import AsyncResult

from app import (
    app,
    db,
    celery_app,
    redis_client,
    clear_dashboard_caches,
    is_allowed_document,
    student_is_eligible_for_job,
    export_student_applications_csv,
)
from models import User, StudentProfile, CompanyProfile, Job, Application


@app.route("/student/get_profile", methods=["GET"])
@jwt_required()
def get_student_profile():
    user_id = get_jwt_identity()

    user = User.query.filter_by(id=user_id).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    profile = StudentProfile.query.filter_by(user_id=user_id).first()

    if not profile or not profile.is_profile_complete:
        return jsonify({"message": "Profile not found"}), 404

    return jsonify({
        "id": profile.id,
        "user_name": user.name,
        "phone": user.phone,
        "department": profile.department,
        "year": profile.year,
        "cgpa": profile.cgpa,
        "skills": profile.skills,
        "resume": profile.resume,
        "placement_status": profile.placement_status
    }), 200


@app.route("/student/create_profile", methods=["POST"])
@jwt_required()
def create_student_profile():
    user_id = get_jwt_identity()

    # the profile row already exists (created empty at registration) —
    # just fill it in instead of creating a new one
    profile = StudentProfile.query.filter_by(user_id=user_id).first()

    if profile.is_profile_complete:
        return jsonify({"message": "Profile already exists"}), 400

    data = request.get_json()

    profile.department = data.get("department")
    profile.year = data.get("year")
    profile.cgpa = data.get("cgpa")
    profile.skills = data.get("skills")
    profile.is_profile_complete = True

    db.session.commit()
    clear_dashboard_caches()

    return jsonify({"message": "Profile created successfully"}), 201


@app.route("/student/edit_profile", methods=["POST"])
@jwt_required()
def edit_student_profile():
    user_id = get_jwt_identity()

    profile = StudentProfile.query.filter_by(user_id=user_id).first()

    if not profile:
        return jsonify({"message": "Profile not found"}), 404

    data = request.get_json()

    profile.department = data.get("department", profile.department)
    profile.year = data.get("year", profile.year)
    profile.cgpa = data.get("cgpa", profile.cgpa)
    profile.skills = data.get("skills", profile.skills)

    # phone lives on the User record, not the student profile
    if "phone" in data:
        profile.user.phone = data.get("phone")

    db.session.commit()

    return jsonify({"message": "Profile updated successfully"}), 200


@app.route("/student/companies", methods=["GET"])
@jwt_required()
def get_all_companies():
    query = request.args.get("q", "").strip()

    # only the full, unfiltered list is cached — search results are cheap
    # enough to compute fresh every time, same as the admin search endpoints
    if not query:
        cached = redis_client.get("companies_list")
        if cached:
            return jsonify(json.loads(cached))

    # only show companies that have actually filled in their profile —
    # every company gets an empty row at registration, so without this
    # filter students would see blank, unfinished company entries.
    # Also hide companies the admin has blocked entirely.
    companies_query = (
        CompanyProfile.query
        .join(User, CompanyProfile.user_id == User.id)
        .filter(
            CompanyProfile.is_profile_complete.is_(True),
            User.is_active.is_(True),
        )
    )

    if query:
        companies_query = companies_query.filter(
            (
                CompanyProfile.company_name.ilike(f"%{query}%") |
                CompanyProfile.industry.ilike(f"%{query}%") |
                CompanyProfile.location.ilike(f"%{query}%")
            )
        )

    companies = companies_query.all()

    company_list = []

    for c in companies:
        company_list.append({
            "id": c.id,
            "company_name": c.company_name,
            "industry": c.industry,
            "website": c.website,
            "location": c.location,
            "company_size": c.company_size
        })

    if not query:
        # cache for 60 seconds so it expires and stays fresh
        redis_client.setex("companies_list", 60, json.dumps(company_list))

    return jsonify(company_list)


@app.route("/student/available_jobs", methods=["GET"])
@jwt_required()
def get_available_jobs():
    query = request.args.get("q", "").strip()

    # need the student's own profile to work out which jobs they're eligible for
    user_id = get_jwt_identity()
    student_profile = StudentProfile.query.filter_by(user_id=user_id).first()

    # a job should only be "available" if it's approved, still open, not
    # individually blocked by the admin, AND its company isn't blocked either
    jobs_query = (
        Job.query
        .join(CompanyProfile)
        .join(User, CompanyProfile.user_id == User.id)
        .filter(
            Job.is_approved.is_(True),
            Job.is_closed.is_(False),
            Job.is_blacklisted.is_(False),
            User.is_active.is_(True),
        )
    )

    if query:
        jobs_query = jobs_query.filter(
            (
                Job.title.ilike(f"%{query}%") |
                Job.skills.ilike(f"%{query}%") |
                Job.location.ilike(f"%{query}%") |
                CompanyProfile.company_name.ilike(f"%{query}%")
            )
        )

    jobs = jobs_query.all()

    job_list = []

    for job in jobs:
        job_list.append({
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "skills": job.skills,
            "experience": job.experience,
            "salary": job.salary,
            "location": job.location,
            "job_type": job.job_type,
            "application_deadline": job.application_deadline,
            "company_name": job.company.company_name,
            "posted_at": job.posted_at,
            "min_cgpa": job.min_cgpa,
            "eligible_branches": job.eligible_branches,
            "eligible_years": job.eligible_years,
            "is_eligible": student_is_eligible_for_job(student_profile, job) if student_profile else True
        })

    return jsonify(job_list)


@app.route("/student/apply/<int:job_id>", methods=["POST"])
@jwt_required()
def apply_for_job(job_id):
    user_id = get_jwt_identity()

    profile = StudentProfile.query.filter_by(user_id=user_id).first()

    if not profile:
        return jsonify({"message": "Create your profile before applying"}), 400

    job = Job.query.filter_by(id=job_id).first()

    if not job:
        return jsonify({"message": "Job not found"}), 404

    if job.is_closed:
        return jsonify({"message": "This job is closed"}), 400

    if job.is_blacklisted:
        return jsonify({"message": "This job has been blocked by the admin"}), 400

    if not job.is_approved:
        return jsonify({"message": "Job is not approved yet"}), 400

    if job.application_deadline and datetime.utcnow() > job.application_deadline:
        return jsonify({"message": "Application deadline has passed"}), 400

    if not student_is_eligible_for_job(profile, job):
        return jsonify({"message": "You do not meet the eligibility requirements for this job"}), 400

    # one Application row per (student, job); its status field is the full history: Applied -> Shortlisted -> Interview -> Offer -> Rejected/Placed
    already_applied = Application.query.filter_by(job_id=job_id, student_id=profile.id).first()

    if already_applied:
        return jsonify({"message": "Already applied for this job"}), 400

    application = Application(
        job_id=job_id,
        student_id=profile.id,
        status="Applied",
        applied_at=datetime.utcnow()
    )

    db.session.add(application)
    db.session.commit()
    clear_dashboard_caches()

    return jsonify({"message": "Applied successfully"}), 201


@app.route("/student/my_applications", methods=["GET"])
@jwt_required()
def get_my_applications():
    user_id = get_jwt_identity()

    profile = StudentProfile.query.filter_by(user_id=user_id).first()

    if not profile:
        return jsonify([])

    applications = Application.query.filter_by(student_id=profile.id).all()

    app_list = []

    for a in applications:
        # offer_letter is stored as a relative file path — build the same
        # full download URL that the company side already gets
        offer_letter_url = None
        if a.offer_letter:
            offer_letter_url = url_for('uploaded_file', filename=a.offer_letter.replace("uploads/", ""), _external=True)

        app_list.append({
            "id": a.id,
            "job_id": a.job_id,
            "job_title": a.job.title,
            "company_name": a.job.company.company_name,
            "job_type": a.job.job_type if a.job else None,
            "job_location": a.job.location if a.job else None,
            "is_job_closed": a.job.is_closed if a.job else None,
            "is_job_blacklisted": a.job.is_blacklisted if a.job else None,
            "status": a.status,
            "applied_at": a.applied_at,
            "remarks": a.remarks,
            "interview_datetime": a.interview_datetime,
            "interview_mode": a.interview_mode,
            "interview_link": a.interview_link,
            "interview_location": a.interview_location,
            "feedback": a.feedback,
            "offer_letter": offer_letter_url
        })

    return jsonify(app_list)


@app.route("/student/company_details/<int:company_id>", methods=["GET"])
@jwt_required()
def get_company_details(company_id):
    company = CompanyProfile.query.filter_by(id=company_id).first()

    # a blocked company should be invisible everywhere on the student side,
    # not just on the companies list — treat it the same as "not found"
    # instead of only checking that the row exists
    if not company or not company.user or not company.user.is_active:
        return jsonify({"message": "Company not found"}), 404

    # need the student's own profile to work out which jobs they're eligible for
    user_id = get_jwt_identity()
    student_profile = StudentProfile.query.filter_by(user_id=user_id).first()

    # show approved jobs of this company (open and closed, so students can see history)
    jobs = Job.query.filter_by(company_id=company_id, is_approved=True).all()

    job_list = []

    for job in jobs:
        job_list.append({
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "skills": job.skills,
            "experience": job.experience,
            "salary": job.salary,
            "location": job.location,
            "job_type": job.job_type,
            "application_deadline": job.application_deadline,
            "min_cgpa": job.min_cgpa,
            "eligible_branches": job.eligible_branches,
            "eligible_years": job.eligible_years,
            "is_closed": job.is_closed,
            "is_blacklisted": job.is_blacklisted,
            "posted_at": job.posted_at,
            "is_eligible": student_is_eligible_for_job(student_profile, job) if student_profile else True
        })

    return jsonify({
        "company": {
            "id": company.id,
            "company_name": company.company_name,
            "industry": company.industry,
            "website": company.website,
            "location": company.location,
            "company_size": company.company_size,
            "hr_contact": company.hr_contact
        },
        "jobs": job_list
    })


@app.route("/student/upload_resume", methods=["POST"])
@jwt_required()
def upload_resume():
    user_id = get_jwt_identity()
    profile = StudentProfile.query.filter_by(user_id=user_id).first()

    if not profile:
        return jsonify({"message": "Profile not found"}), 404

    file = request.files.get("resume")

    if not file:
        return jsonify({"message": "Resume file is required"}), 400

    if not is_allowed_document(file.filename):
        return jsonify({"message": "Resume must be a PDF, DOC or DOCX file"}), 400

    resumes_folder = os.path.join(app.config["UPLOAD_FOLDER"], "resumes")
    os.makedirs(resumes_folder, exist_ok=True)

    filename = secure_filename(file.filename)
    file_path = os.path.join("uploads/resumes", f"student_{user_id}_{filename}")
    file.save(os.path.join(resumes_folder, f"student_{user_id}_{filename}"))

    profile.resume = file_path
    db.session.commit()

    return jsonify({
        "message": "Resume uploaded successfully",
        "resume_url": url_for("uploaded_file", filename=file_path.replace("uploads/", ""), _external=True),
    })


@app.route("/student/export_applications", methods=["POST"])
@jwt_required()
def export_student_applications():
    user_id = get_jwt_identity()
    profile = StudentProfile.query.filter_by(user_id=user_id).first()

    if not profile:
        return jsonify({"message": "Student profile not found"}), 404

    task = export_student_applications_csv.delay(profile.id)
    return jsonify({
        "message": "Export started",
        "task_id": task.id,
    }), 202


@app.route("/student/export_applications/status/<task_id>", methods=["GET"])
@jwt_required()
def export_student_applications_status(task_id):
    result = AsyncResult(task_id, app=celery_app)

    if result.state == "PENDING":
        return jsonify({"state": result.state, "message": "Export is in queue"})

    if result.state == "FAILURE":
        return jsonify({
            "state": result.state,
            "message": "Export failed",
        }), 500

    return jsonify({
        "state": result.state,
        "result": result.result,
    })


