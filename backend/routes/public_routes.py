# Routes anyone can hit without being logged in: registering an account,
# logging in, and downloading an uploaded file (resume / offer letter).
#
# "app" and "db" are imported from app.py instead of created here — app.py
# creates them once, and every routes file (this one included) reuses that
# same app/db so there's only ever one Flask app and one database connection.
from flask import request, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token

from app import app, db
from models import User, StudentProfile, CompanyProfile


@app.route("/register", methods=["POST"])
def register():
    data = request.json
    name = data["name"]
    email = data["email"]
    password = data["password"]
    role = data["role"]  # student or company — admin can't self-register
    phone = data.get("phone")

    # only students and companies can sign up here — the one admin account
    # is created programmatically in init_db(), never through this route
    if role not in ["student", "company"]:
        return jsonify({"message": "Invalid role. Only student or company can self-register."}), 400

    # check if email already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"message": "User already registered"}), 400
    user = User(
        name=name,
        email=email,
        password=generate_password_hash(password),
        role=role,
        phone=phone,
        is_active=True,
        is_approved=False if role == "company" else True
    )
    db.session.add(user)
    db.session.flush()  # so user.id is ready to use below, before the final commit

    # create an empty profile row right away too, so this student/company
    # shows up in admin lists immediately, even before they fill it in
    if role == "student":
        db.session.add(StudentProfile(user_id=user.id))
    elif role == "company":
        db.session.add(CompanyProfile(user_id=user.id))

    db.session.commit()
    return jsonify({
        "message": "User registered successfully",
        "user_id": user.id,
        "role": user.role
    })


@app.route("/login", methods=["POST"])
def login_user():

    data = request.get_json()

    if not data:
        return jsonify({"msg": "No data provided"}), 400

    user = User.query.filter_by(email=data["email"]).first()

    if not user:
        return jsonify({"msg": "User not found"}), 404

    # passwords are stored hashed, so we can't just compare strings directly
    if not check_password_hash(user.password, data["password"]):
        return jsonify({"msg": "Password is wrong"}), 401

    if not user.is_active:
        return jsonify({"msg": "Your account has been blocked by admin.", "reason": "blocked"}), 401

    if user.role == "company" and not user.is_approved:
        return jsonify({"msg": "Your company is not yet approved. Please wait for admin approval.", "reason": "pending_approval"}), 401

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "role": user.role,
            "email": user.email
        }
    )

    return jsonify({
        "msg": "Login successful",
        "token": access_token,
        "role": user.role,
        "name": user.name
    }), 200


# ---------------- FILE DOWNLOADS ----------------

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


