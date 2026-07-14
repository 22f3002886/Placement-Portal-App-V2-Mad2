# Everything the admin can do: approve/reject companies and drives, search
# and block students/companies/drives, view stats and all applications, and
# trigger the two scheduled report jobs by hand.
#
# "app" and "db" come from app.py, not created here — see public_routes.py
# for why. The two report Celery tasks also live in app.py, so they're
# imported from there the same way.
import json

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from celery.result import AsyncResult

from app import (
    app,
    db,
    celery_app,
    redis_client,
    clear_dashboard_caches,
    send_daily_placement_reminders,
    generate_monthly_placement_report,
)
from models import User, CompanyProfile, Job, Application


@app.route("/admin/all_students", methods=["GET"])
@jwt_required()
def get_all_students():
    admin_user = User.query.get(get_jwt_identity())
    if not admin_user or admin_user.role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    students = User.query.filter_by(role="student").all()

    all_students = []

    for user in students:
        profile = user.student_profile  # always exists — created at registration

        student_data = {
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "profile_complete": profile.is_profile_complete,

            # student profile data
            "department": profile.department,
            "year": profile.year,
            "cgpa": profile.cgpa,
            "skills": profile.skills,
            "placement_status": profile.placement_status,
            "applications": len(profile.applications),
        }

        all_students.append(student_data)

    return jsonify(all_students)


@app.route("/admin/student_details/<int:user_id>", methods=["GET"])
@jwt_required()
def get_student_details(user_id):
    claims = get_jwt()

    if claims.get("role") != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    user = User.query.filter_by(id=user_id, role="student").first()

    if not user:
        return jsonify({"message": "Student not found"}), 404

    profile = user.student_profile

    applications_list = []
    applications_count = 0

    if profile:
        applications_count = len(profile.applications)

        for application in profile.applications:
            applications_list.append({
                "job": application.job.title,
                "company": application.job.company.company_name,
                "status": application.status,
                "applied_at": application.applied_at
            })

    # everything below is just the user row and the student profile row
    # merged into one response, so the frontend doesn't need two requests
    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,

        "department": profile.department if profile else None,
        "year": profile.year if profile else None,
        "cgpa": profile.cgpa if profile else None,
        "skills": profile.skills if profile else None,
        "placement_status": profile.placement_status if profile else None,

        "applications_count": applications_count,
        "applications": applications_list
    })


@app.route("/admin/company_details/<int:company_id>", methods=["GET"])
@jwt_required()
def admin_company_details(company_id):
    claims = get_jwt()

    if claims.get("role") != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    # company_id here is actually the user id — companies are identified
    # the same way everywhere in this app, just like students are
    company = CompanyProfile.query.filter_by(user_id=company_id).first()
    if not company:
        return jsonify({"message": "Company not found"}), 404

    user = User.query.get(company.user_id)

    company_data = {
        "id": company.id,
        "user_id": company.user_id,
        "company_name": company.company_name,
        "email": user.email if user else None,
        "industry": company.industry,
        "website": company.website,
        "location": company.location,
        "company_size": company.company_size,
        "hr_contact": company.hr_contact,
        "is_blocked": not user.is_active if user else False,
        "created_at": user.created_at.strftime("%Y-%m-%d") if user else None
    }

    jobs = Job.query.filter_by(company_id=company.id).all()

    jobs_data = []
    for job in jobs:
        jobs_data.append({
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "salary": job.salary,
            "application_deadline": job.application_deadline,
            "applications_count": len(job.applications),
            "is_blacklisted": job.is_blacklisted,
            "is_closed": job.is_closed,
            "is_approved": job.is_approved
        })

    return jsonify({
        "company": company_data,
        "jobs": jobs_data
    }), 200


@app.route("/admin/approve_job/<int:job_id>", methods=["PUT"])
@jwt_required()
def approve_job(job_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or user.role != "admin":
            return jsonify({"msg": "not allowed"}), 403

        job = Job.query.get(job_id)

        if not job:
            return jsonify({"msg": "job not found"}), 404

        job.is_approved = True

        db.session.commit()

        return jsonify({
            "msg": "job approved",
            "job_id": job.id
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/admin/reject_job/<int:job_id>", methods=["PUT"])
@jwt_required()
def reject_job(job_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or user.role != "admin":
            return jsonify({"msg": "not allowed"}), 403

        job = Job.query.get(job_id)

        if not job:
            return jsonify({"msg": "job not found"}), 404

        # rejecting removes the drive entirely — same as rejecting a
        # company — so it disappears everywhere and the company has to
        # post it again from scratch for a fresh approval
        db.session.delete(job)
        db.session.commit()
        clear_dashboard_caches()

        return jsonify({
            "msg": "job rejected",
            "job_id": job_id
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/admin/stats", methods=["GET"])
@jwt_required()
def admin_stats():
    cached_stats = redis_client.get("admin_stats")

    if cached_stats:
        return jsonify(json.loads(cached_stats))

    stats = {
        "companies": User.query.filter_by(role="company", is_approved=True, is_active=True).count(),
        "students": User.query.filter_by(role="student").count(),
        "jobs": Job.query.count(),
        "applications": Application.query.count()
    }
    redis_client.setex("admin_stats", 60, json.dumps(stats))
    return jsonify(stats)


@app.route("/admin/all_applications", methods=["GET"])
@jwt_required()
def admin_all_applications():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or user.role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    applications = Application.query.order_by(Application.applied_at.desc()).all()
    result = []

    for application in applications:
        student = application.student
        student_user = student.user if student else None
        job = application.job
        company = job.company if job else None

        result.append({
            "id": application.id,
            "student_name": student_user.name if student_user else "",
            "student_email": student_user.email if student_user else "",
            "company_name": company.company_name if company else "",
            "job_title": job.title if job else "",
            "status": application.status,
            "applied_at": application.applied_at,
            "updated_at": application.updated_at,
        })

    return jsonify(result)


@app.route("/admin/pending_companies", methods=["GET"])
@jwt_required()
def get_pending_companies():
    admin_user = User.query.get(get_jwt_identity())
    if not admin_user or admin_user.role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    users = User.query.filter_by(
        role="company",
        is_approved=False
    ).all()

    return jsonify([
        {
            "id": u.id,
            "name": u.name,
            "email": u.email
        }
        for u in users
    ])


@app.route("/admin/reject_company/<int:id>", methods=["POST"])
@jwt_required()
def reject_company(id):
    admin_user = User.query.get(get_jwt_identity())

    if not admin_user or admin_user.role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    company_user = User.query.get(id)

    if not company_user or company_user.role != "company":
        return jsonify({"msg": "not found"}), 404

    db.session.delete(company_user)
    db.session.commit()
    clear_dashboard_caches()

    return jsonify({"msg": "rejected"})


@app.route("/admin/approve_company/<int:id>", methods=["POST"])
@jwt_required()
def approve_company(id):
    admin_user = User.query.get(get_jwt_identity())
    if not admin_user or admin_user.role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    user = User.query.get(id)

    if not user:
        return jsonify({"msg": "not found"}), 404

    user.is_approved = True
    db.session.commit()
    clear_dashboard_caches()

    return jsonify({"msg": "approved"})


@app.route("/admin/all_companies", methods=["GET"])
@jwt_required()
def all_companies():
    admin_user = User.query.get(get_jwt_identity())
    if not admin_user or admin_user.role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    # check the cache first so we don't hit the database every time
    cached = redis_client.get("admin_all_companies")
    if cached:
        return jsonify(json.loads(cached))

    # every approved company user always has a profile row (created empty
    # at registration), so this can just read it directly
    company_users = User.query.filter_by(role="company", is_approved=True).all()

    data = []
    for user in company_users:
        profile = user.company_profile

        data.append({
            "user_id": user.id,
            "company_name": profile.company_name or user.name,
            "location": profile.location,
            "jobs_count": len(profile.jobs),
            "profile_complete": profile.is_profile_complete,
            "is_blocked": not user.is_active
        })

    # cache for 60 seconds so it expires and stays fresh
    redis_client.setex("admin_all_companies", 60, json.dumps(data))

    return jsonify(data)


@app.route("/admin/toggle_company_block/<int:id>", methods=["POST"])
@jwt_required()
def toggle_company_block(id):
    admin_user = User.query.get(get_jwt_identity())
    if not admin_user or admin_user.role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    # id here is the company's user id
    user = User.query.filter_by(id=id, role="company").first()

    if not user:
        return jsonify({"msg": "not found"}), 404

    # this only blocks the company account itself. Whether an individual
    # job is blocked is a separate decision the admin makes per-job (see
    # toggle_job_block below) — it doesn't flip automatically just because
    # the company got blocked
    user.is_active = not user.is_active

    db.session.commit()
    clear_dashboard_caches()

    return jsonify({
        "msg": "updated",
        "user_active": user.is_active
    })


@app.route("/admin/pending_jobs", methods=["GET"])
@jwt_required()
def get_pending_jobs():
    admin_user = User.query.get(get_jwt_identity())
    if not admin_user or admin_user.role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    # jobs that are still awaiting a decision (rejected ones are deleted
    # outright, so this only ever sees genuinely pending jobs)
    jobs = Job.query.filter_by(is_approved=False).all()

    data = []
    for j in jobs:
        data.append({
            "id": j.id,
            "title": j.title,
            "company": j.company.company_name if j.company else "N/A",
            "application_deadline": j.application_deadline
        })

    return jsonify(data)


@app.route("/admin/all_jobs", methods=["GET"])
@jwt_required()
def get_all_jobs():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or user.role != "admin":
            return jsonify({"msg": "not allowed"}), 403

        # "All Drives" is for approved drives only — unapproved ones stay
        # in the Pending Drives list until the admin approves them
        jobs = Job.query.filter_by(is_approved=True).all()

        data = []
        for j in jobs:
            data.append({
                "id": j.id,
                "title": j.title,
                "company": j.company.company_name,
                "location": j.location,
                "salary": j.salary,
                "application_deadline": j.application_deadline,
                "is_approved": j.is_approved,
                "is_closed": j.is_closed,
                "is_blacklisted": j.is_blacklisted,
                "posted_at": j.posted_at,
                "applications_count": len(j.applications)
            })

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/admin/search_jobs", methods=["GET"])
@jwt_required()
def search_jobs():
    current_user_id = get_jwt_identity()
    admin = User.query.get(current_user_id)

    if not admin or admin.role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    query = request.args.get("q", "").strip()

    # "All Drives" search only searches approved drives — same rule as the
    # unfiltered list, unapproved ones stay in Pending Drives only
    jobs_query = Job.query.filter_by(is_approved=True)

    if query:
        jobs_query = jobs_query.join(CompanyProfile).filter(
            (
                Job.title.ilike(f"%{query}%") |
                Job.skills.ilike(f"%{query}%") |
                Job.location.ilike(f"%{query}%") |
                CompanyProfile.company_name.ilike(f"%{query}%")
            )
        )

    jobs = jobs_query.all()

    result = []
    for job in jobs:
        result.append({
            "id": job.id,
            "title": job.title,
            "company": job.company.company_name if job.company else "N/A",
            "location": job.location,
            "application_deadline": job.application_deadline,
            "is_approved": job.is_approved,
            "is_closed": job.is_closed,
            "is_blacklisted": job.is_blacklisted,
            "applications_count": len(job.applications)
        })

    return jsonify(result)


@app.route("/admin/toggle_job_block/<int:job_id>", methods=["POST"])
@jwt_required()
def toggle_job_block(job_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or user.role != "admin":
            return jsonify({"msg": "not allowed"}), 403

        job = Job.query.get(job_id)

        if not job:
            return jsonify({"msg": "job not found"}), 404

        job.is_blacklisted = not job.is_blacklisted

        db.session.commit()

        return jsonify({
            "msg": "job block toggled",
            "job_id": job.id,
            "is_blacklisted": job.is_blacklisted
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/admin/toggle_student_block/<int:user_id>", methods=["POST"])
@jwt_required()
def toggle_student_block(user_id):
    current_user_id = get_jwt_identity()
    admin = User.query.get(current_user_id)

    if not admin or admin.role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    user = User.query.get(user_id)

    if not user or user.role != "student":
        return jsonify({"message": "Student not found"}), 404

    user.is_active = not user.is_active
    db.session.commit()
    clear_dashboard_caches()

    return jsonify({
        "message": "Student status updated",
        "is_active": user.is_active
    })


@app.route("/admin/run_daily_reminders", methods=["POST"])
@jwt_required()
def run_daily_reminders_now():
    admin_user = User.query.get(get_jwt_identity())

    if not admin_user or admin_user.role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    task = send_daily_placement_reminders.delay()
    return jsonify({"message": "Daily reminder job started", "task_id": task.id}), 202


@app.route("/admin/generate_monthly_report", methods=["POST"])
@jwt_required()
def generate_monthly_report_now():
    admin_user = User.query.get(get_jwt_identity())

    if not admin_user or admin_user.role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    task = generate_monthly_placement_report.delay()
    return jsonify({"message": "Monthly report job started", "task_id": task.id}), 202


@app.route("/admin/task_status/<task_id>", methods=["GET"])
@jwt_required()
def admin_task_status(task_id):
    admin_user = User.query.get(get_jwt_identity())

    if not admin_user or admin_user.role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    result = AsyncResult(task_id, app=celery_app)

    if result.state == "PENDING":
        return jsonify({"state": result.state, "message": "Job is in queue"})

    if result.state == "FAILURE":
        return jsonify({
            "state": result.state,
            "message": "Job failed",
        }), 500

    return jsonify({
        "state": result.state,
        "result": result.result,
    })


@app.route("/admin/job/<int:job_id>", methods=["GET"])
@jwt_required()
def admin_job_detail(job_id):

    current_user_id = get_jwt_identity()
    admin = User.query.get(current_user_id)

    if not admin or admin.role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    job = Job.query.get(job_id)

    if not job:
        return jsonify({"message": "Job not found"}), 404

    company = job.company
    user = company.user

    return jsonify({
        "job": {
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "skills": job.skills,
            "experience": job.experience,
            "salary": job.salary,
            "benefits": job.benefits,
            "location": job.location,
            "job_type": job.job_type,
            "application_deadline": job.application_deadline,
            "is_approved": job.is_approved,
            "is_closed": job.is_closed,
            "is_blacklisted": job.is_blacklisted,
            "posted_at": job.posted_at
        },
        "company": {
            "company_name": company.company_name,
            "industry": company.industry,
            "website": company.website,
            "location": company.location,
            "company_size": company.company_size,
            "email": user.email,
            "hr_contact": company.hr_contact,
            "is_active": user.is_active
        }
    })


@app.route("/admin/search_students")
@jwt_required()
def search_students():

    current_user_id = get_jwt_identity()
    admin = User.query.get(current_user_id)

    if not admin or admin.role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    query = request.args.get("q", "").strip().lower()

    # every student user always has a profile row — filtering in Python
    # keeps this simple and readable
    students = User.query.filter_by(role="student").all()

    result = []
    for user in students:
        profile = user.student_profile

        matches = (
            query in (user.name or "").lower()
            or query in (user.email or "").lower()
            or query in (user.phone or "").lower()
            or query == str(user.id)
        )

        if not matches:
            continue

        result.append({
            "user_id": user.id,
            "name": user.name,
            "phone": user.phone,
            "profile_complete": profile.is_profile_complete,
            "applications": len(profile.applications),
            "is_active": user.is_active
        })

    return jsonify(result)


@app.route("/admin/search_companies")
@jwt_required()
def search_companies():

    current_user_id = get_jwt_identity()
    admin = User.query.get(current_user_id)

    if not admin or admin.role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    query = request.args.get("q", "").strip().lower()

    # every approved company user always has a profile row — filtering in
    # Python keeps this simple
    companies = User.query.filter_by(role="company", is_approved=True).all()

    result = []
    for user in companies:
        profile = user.company_profile

        matches = (
            query in (user.name or "").lower()
            or query in (profile.company_name or "").lower()
            or query in (profile.industry or "").lower()
        )

        if not matches:
            continue

        result.append({
            "user_id": user.id,
            "company_name": profile.company_name or user.name,
            "industry": profile.industry,
            "profile_complete": profile.is_profile_complete,
            "jobs_count": len(profile.jobs),
            "is_blocked": not user.is_active
        })

    return jsonify(result)


