import re
from flask import Blueprint, request, jsonify, session
from database.db import (
    get_user_by_email,
    get_user_by_email_or_username,
    create_user,
    get_user_by_id,
    get_db_connection
)
from services.auth import (
    hash_password,
    verify_password,
    is_rate_limited,
    record_failed_attempt,
    clear_failed_attempts,
    get_current_user_id
)

auth_bp = Blueprint("auth", __name__)

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Mandatory Registration Endpoint.
    Validates input, checks duplicate email, hashes password with Werkzeug PBKDF2,
    creates distinct user record, and authenticates the user into the session.
    """
    data = request.get_json() or {}
    full_name = data.get("full_name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()
    confirm_password = data.get("confirm_password", "").strip()
    language_pref = data.get("language_pref", "en").strip().lower()
    
    if language_pref not in ["en", "hi", "bn"]:
        language_pref = "en"

    # Validation
    if not full_name or len(full_name) < 2:
        return jsonify({"success": False, "error": "Please enter your full name (at least 2 characters)."}), 400

    if not email or not EMAIL_REGEX.match(email):
        return jsonify({"success": False, "error": "Please enter a valid email address."}), 400

    if not password or len(password) < 6:
        return jsonify({"success": False, "error": "Password must be at least 6 characters long."}), 400

    if "confirm_password" in data and password != confirm_password:
        return jsonify({"success": False, "error": "Passwords do not match."}), 400

    # Check duplicate
    existing = get_user_by_email(email)
    if existing:
        return jsonify({"success": False, "error": "An account with this email address already exists. Please sign in."}), 409

    # Create user with hashed password
    try:
        pw_hash = hash_password(password)
        user_id = create_user(
            email=email,
            password_hash=pw_hash,
            display_name=full_name,
            language_pref=language_pref
        )

        # Protect against session fixation and set session
        session.clear()
        session["user_id"] = user_id
        session["language_pref"] = language_pref
        session.permanent = True

        user = get_user_by_id(user_id)
        return jsonify({
            "success": True,
            "message": "Account created successfully. Welcome to PRANVYRA!",
            "user": user,
            "redirect_url": "/"
        }), 201

    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to register account: {str(e)}"}), 500

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Mandatory Login Endpoint.
    Validates credentials, verifies password hash, applies rate limiting,
    establishes secure server-side session, and loads saved language preference.
    """
    client_ip = request.remote_addr or "client"
    if is_rate_limited(client_ip):
        return jsonify({
            "success": False,
            "error": "Too many failed login attempts. Please wait 5 minutes before trying again."
        }), 429

    data = request.get_json() or {}
    identifier = (data.get("email_or_username") or data.get("identifier") or data.get("email") or "").strip()
    password = data.get("password", "").strip()
    remember_me = bool(data.get("remember_me", False))

    if not identifier or not password:
        return jsonify({"success": False, "error": "Please enter your email or username and password."}), 400

    user = get_user_by_email_or_username(identifier)
    if not user or not verify_password(user.get("password_hash"), password):
        record_failed_attempt(client_ip)
        return jsonify({"success": False, "error": "Invalid email/username or password."}), 401

    # Authentication succeeded
    clear_failed_attempts(client_ip)

    # Invalidate old session to prevent session fixation
    session.clear()
    session["user_id"] = user["id"]
    session["language_pref"] = user.get("language_pref", "en") or "en"
    session.permanent = remember_me

    # Update last login timestamp
    try:
        conn = get_db_connection()
        conn.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user["id"],))
        conn.commit()
        conn.close()
    except Exception:
        pass

    user_info = get_user_by_id(user["id"])
    return jsonify({
        "success": True,
        "message": "Sign in successful.",
        "user": user_info,
        "redirect_url": "/"
    })

@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Invalidates the active session on the server and clears authentication state."""
    session.clear()
    return jsonify({
        "success": True,
        "message": "Signed out successfully.",
        "redirect_url": "/login"
    })

@auth_bp.route("/me", methods=["GET"])
def get_current_session_user():
    """Returns the authenticated user details for the active session, or 401 if unauthenticated."""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "authenticated": False, "error": "Not authenticated."}), 401

    user = get_user_by_id(user_id)
    if not user:
        session.clear()
        return jsonify({"success": False, "authenticated": False, "error": "User record not found."}), 401

    return jsonify({
        "success": True,
        "authenticated": True,
        "user": user
    })
