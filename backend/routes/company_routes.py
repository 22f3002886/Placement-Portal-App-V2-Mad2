# Everything a logged-in company can do: company profile, posting/opening/
# closing drives, viewing applicants for a drive, and updating an
# applicant's status (shortlist / reject / select).
#
# "app" and "db" come from app.py, not created here — see public_routes.py
# for why.
import os
from datetime import datetime

from flask import request, jsonify, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from app import app, db, clear_dashboard_caches, is_allowed_document
from models import CompanyProfile, Job, Application


@app.route('/company/create_profile', methods=['POST'])
@jwt_required()
def create_company_profile():
    try:
        data = request.get_json()
        user_id = get_jwt_identity()

        if not data.get('company_name'):
            return jsonify({"message": "company name is required"}), 400

        # the profile row already exists (created empty at registration) —
        # just fill it in instead of creating a new one
        company = CompanyProfile.query.filter_by(user_id=user_id).first()

        if company.is_profile_complete:
            return jsonify({"message": "Profile already exists"}), 400

        company.company_name = data.get('company_name')
        company.industry = data.get('industry')
        company.website = data.get('website')
        company.location = data.get('location')
        company.company_size = data.get('company_size')
        company.hr_contact = data.get('hr_contact')
        company.is_profile_complete = True

        db.session.commit()
        clear_dashboard_caches()

        return jsonify({"message": "company profile created"}), 201

    except Exception as e:
        return jsonify({"message": "something went wrong"}), 500


@app.route('/edit_company_profile',methods=['POST'])
@jwt_required()
def edit_company_profile():
    user_id = get_jwt_identity()
    data = request.get_json()
    company_profile_tr = CompanyProfile.query.filter_by(user_id= user_id).first()

    company_profile_tr.company_name = data.get('company_name', company_profile_tr.company_name)
    company_profile_tr.industry = data.get('industry', company_profile_tr.industry)
    company_profile_tr.website = data.get('website', company_profile_tr.website)
    company_profile_tr.location = data.get('location', company_profile_tr.location)
    company_profile_tr.company_size = data.get('company_size', company_profile_tr.company_size)
    company_profile_tr.hr_contact = data.get('hr_contact', company_profile_tr.hr_contact)

    db.session.commit()
    clear_dashboard_caches()
    return jsonify({"message": "Company profile updated successfully"})


@app.route('/get_company_profie')
@jwt_required()
def get_company_profie():
    user_id = get_jwt_identity()
    company_profile = CompanyProfile.query.filter_by(user_id = user_id).first()

    if not company_profile or not company_profile.is_profile_complete:
        return jsonify({"message": "Profile not found"}), 404

    return jsonify({
        "company_name": company_profile.company_name,
        "industry": company_profile.industry,
        "website": company_profile.website,
        "location": company_profile.location,
        "company_size": company_profile.company_size,
        "hr_contact": company_profile.hr_contact
    }), 200


@app.route("/company/post_job", methods=["POST"])
@jwt_required()
def post_job():
    user_id = get_jwt_identity()

    company = CompanyProfile.query.filter_by(user_id=user_id).first()

    if not company:
        return jsonify({"message": "Company profile not found"}), 404

    data = request.get_json()

    # title, description and skills are required fields on the Job model —
    # checking here first gives a clean message instead of a database error
    if not data.get("title") or not data.get("description") or not data.get("skills"):
        return jsonify({"message": "Title, description and skills are required"}), 400

    # eligibility criteria must be set on every job so the eligibility
    # filtering feature (CGPA/branch/year) always has something to filter on
    if data.get("min_cgpa") in (None, "") or not data.get("eligible_branches") or not data.get("eligible_years"):
        return jsonify({"message": "Minimum CGPA, eligible branches and eligible years are required"}), 400

    # don't let a company post the exact same job (same title + location) twice by accident
    existing_job = Job.query.filter_by(
        company_id=company.id,
        title=data.get("title"),
        location=data.get("location")
    ).first()

    if existing_job:
        return jsonify({"message": "Duplicate job already posted"}), 400

    try:
        deadline = datetime.strptime(data.get("application_deadline"), "%Y-%m-%d") if data.get("application_deadline") else None
        min_cgpa = float(data.get("min_cgpa"))
    except ValueError:
        return jsonify({"message": "Invalid application deadline or minimum CGPA"}), 400

    new_job = Job(
        company_id=company.id,
        title=data.get("title"),
        description=data.get("description"),
        skills=data.get("skills"),
        experience=data.get("experience"),
        salary=data.get("salary"),
        benefits=data.get("benefits"),
        location=data.get("location"),
        job_type=data.get("job_type"),
        application_deadline=deadline,
        min_cgpa=min_cgpa,
        eligible_branches=data.get("eligible_branches"),
        eligible_years=data.get("eligible_years"),
    )

    db.session.add(new_job)
    db.session.commit()
    clear_dashboard_caches()

    return jsonify({"message": "Job posted successfully"})


@app.route("/company/edit_job/<int:job_id>", methods=["POST"])
@jwt_required()
def edit_job(job_id):
    user_id = get_jwt_identity()

    company = CompanyProfile.query.filter_by(user_id=user_id).first()

    if not company:
        return jsonify({"message": "Company profile not found"}), 404

    job = Job.query.filter_by(id=job_id, company_id=company.id).first()

    if not job:
        return jsonify({"message": "Job not found"}), 404

    data = request.get_json()

    if not data.get("title") or not data.get("description") or not data.get("skills"):
        return jsonify({"message": "Title, description and skills are required"}), 400

    if data.get("min_cgpa") in (None, "") or not data.get("eligible_branches") or not data.get("eligible_years"):
        return jsonify({"message": "Minimum CGPA, eligible branches and eligible years are required"}), 400

    try:
        deadline = datetime.strptime(data.get("application_deadline"), "%Y-%m-%d") if data.get("application_deadline") else None
        min_cgpa = float(data.get("min_cgpa"))
    except ValueError:
        return jsonify({"message": "Invalid application deadline or minimum CGPA"}), 400

    # editing doesn't touch is_approved/is_closed/is_blacklisted - it just
    # updates the job's own details, keeping whatever status it already had
    job.title = data.get("title")
    job.description = data.get("description")
    job.skills = data.get("skills")
    job.experience = data.get("experience")
    job.salary = data.get("salary")
    job.benefits = data.get("benefits")
    job.location = data.get("location")
    job.job_type = data.get("job_type")
    job.application_deadline = deadline
    job.min_cgpa = min_cgpa
    job.eligible_branches = data.get("eligible_branches")
    job.eligible_years = data.get("eligible_years")

    db.session.commit()
    clear_dashboard_caches()

    return jsonify({"message": "Job updated successfully"})


@app.route("/company/my_jobs", methods=["GET"])
@jwt_required()
def get_my_jobs():
    user_id = get_jwt_identity()
    company = CompanyProfile.query.filter_by(user_id=user_id).first()

    if not company:
        return jsonify({"message": "Company not found"}), 404

    jobs = Job.query.filter_by(company_id=company.id).all()

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
            "posted_at": job.posted_at,
            "is_approved": job.is_approved,
            "is_closed": job.is_closed,
            "is_blacklisted": job.is_blacklisted,
            "applications_count": len(job.applications)
        })

    return jsonify(job_list)


@app.route("/company/open_job/<int:job_id>", methods=["POST"])
@jwt_required()
def open_job(job_id):
    current_user = get_jwt_identity()

    company = CompanyProfile.query.filter_by(user_id=current_user).first()

    if not company:
        return jsonify({"message": "Company not found"}), 404

    job = Job.query.filter_by(id=job_id, company_id=company.id).first()

    if not job:
        return jsonify({"message": "Job not found"}), 404

    if not job.is_closed:
        return jsonify({"message": "Job already open"}), 400

    # a job that auto-closed because its deadline passed can't just be
    # reopened — it would immediately auto-close again on the next request
    if job.application_deadline and job.application_deadline < datetime.utcnow():
        return jsonify({"message": "This job closed because its application deadline passed and can't be reopened."}), 400

    job.is_closed = False
    db.session.commit()

    return jsonify({"message": "Job reopened successfully"})


@app.route("/company/close_job/<int:job_id>", methods=["POST"])
@jwt_required()
def close_job(job_id):
    current_user = get_jwt_identity()

    company = CompanyProfile.query.filter_by(user_id=current_user).first()

    if not company:
        return jsonify({"message": "Company not found"}), 404

    job = Job.query.filter_by(id=job_id, company_id=company.id).first()

    if not job:
        return jsonify({"message": "Job not found"}), 404

    if job.is_closed:
        return jsonify({"message": "Job already closed"}), 400

    job.is_closed = True
    db.session.commit()

    return jsonify({"message": "Job closed successfully"})


@app.route("/company/job/<int:job_id>/applicants", methods=["GET"])
@jwt_required()
def get_applicants(job_id):
    current_user = get_jwt_identity()

    company = CompanyProfile.query.filter_by(user_id=current_user).first()
    if not company:
        return jsonify({"message": "Company not found"}), 404

    job = Job.query.filter_by(id=job_id, company_id=company.id).first()
    if not job:
        return jsonify({"message": "Job not found"}), 404

    applicants = []

    # named "application" rather than "app" so it doesn't shadow the Flask
    # app object used everywhere else in this file
    for application in job.applications:
        student = application.student
        user = student.user

        # resume/offer letter are stored as relative paths, so turn them
        # into full URLs the frontend can actually open in a new tab
        resume_url = None
        if student.resume:
            resume_url = request.host_url + student.resume

        offer_letter_url = None
        if application.offer_letter:
            offer_letter_url = url_for('uploaded_file', filename=application.offer_letter.replace("uploads/", ""), _external=True)

        applicants.append({
            "application_id": application.id,
            "status": application.status,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "skills": student.skills,
            "cgpa": student.cgpa,
            "resume": resume_url,
            "interview_datetime": application.interview_datetime,
            "interview_link": application.interview_link,
            "offer_letter": offer_letter_url
        })

    return jsonify(applicants), 200


@app.route("/company/application/<int:app_id>/status", methods=["PUT"])
@jwt_required()
def update_application_status(app_id):
    current_user = get_jwt_identity()

    company = CompanyProfile.query.filter_by(user_id=current_user).first()
    if not company:
        return jsonify({"message": "Company not found"}), 404

    application = Application.query.get_or_404(app_id)

    # the application has to belong to a job posted by THIS company —
    # otherwise any logged-in company could update any other company's
    # applicants just by guessing an application id
    if not application.job or application.job.company_id != company.id:
        return jsonify({"message": "Application not found"}), 404

    status = request.form.get("status")

    if status not in ["Applied", "Shortlisted", "Rejected", "Selected"]:
        return jsonify({"message": "Invalid status"}), 400

    if application.status == "Selected":
        return jsonify({"message": "Status cannot be changed after selection"}), 400

    # an offer letter is required before locking a candidate in as Selected,
    # since the status can never be changed again after this
    if status == "Selected":
        offer_letter_file = request.files.get("offer_letter")
        if not offer_letter_file:
            return jsonify({"message": "Please upload an offer letter before marking as Selected"}), 400
        if not is_allowed_document(offer_letter_file.filename):
            return jsonify({"message": "Offer letter must be a PDF, DOC or DOCX file"}), 400

    application.status = status
    application.updated_at = datetime.utcnow()

    # clear out fields from any previous status — otherwise, e.g., a
    # rejection feedback message would keep showing even after the
    # student gets shortlisted or selected later on
    application.interview_datetime = None
    application.interview_link = None
    application.feedback = None
    application.offer_letter = None

    if status == "Shortlisted":
        interview_str = request.form.get("interview_datetime")

        if interview_str:
            application.interview_datetime = datetime.strptime(
                interview_str, "%Y-%m-%dT%H:%M"
            )

        application.interview_link = request.form.get("interview_link")

    if status == "Rejected":
        application.feedback = request.form.get("feedback")

    if status == "Selected":
        offer_letter_file = request.files.get("offer_letter")
        filename = secure_filename(offer_letter_file.filename)
        offers_folder = os.path.join(app.config["UPLOAD_FOLDER"], "offers")
        os.makedirs(offers_folder, exist_ok=True)
        offer_letter_file.save(os.path.join(offers_folder, filename))
        application.offer_letter = os.path.join("uploads/offers", filename)

        # mark student placed
        application.student.placement_status = "Placed"

    db.session.commit()

    return jsonify({"message": "Updated successfully"})


