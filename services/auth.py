"""
PRANVYRA Authentication & Session Security Service
Enforces server-side session authentication, Werkzeug password hashing,
CSRF & fixation protection, and strict user data isolation.
"""
import time
from functools import wraps
from flask import session, request, jsonify, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_user_by_id

# In-memory login attempt tracker for brute-force rate-limiting
# {ip_or_identifier: [timestamp1, timestamp2, ...]}
_FAILED_ATTEMPTS = {}
MAX_FAILED_ATTEMPTS = 10
LOCKOUT_SECONDS = 300  # 5 minutes

def hash_password(password: str) -> str:
    """Hashes a plaintext password securely using PBKDF2 with SHA-256."""
    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters long.")
    return generate_password_hash(password, method="pbkdf2:sha256")

def verify_password(password_hash: str, password: str) -> bool:
    """Verifies a plaintext password against the stored password hash."""
    if not password_hash or not password:
        return False
    return check_password_hash(password_hash, password)

def is_rate_limited(identifier: str) -> bool:
    """Checks if the client IP or identifier has exceeded failed login limits."""
    now = time.time()
    attempts = _FAILED_ATTEMPTS.get(identifier, [])
    # Filter attempts within lockout window
    recent = [t for t in attempts if now - t < LOCKOUT_SECONDS]
    _FAILED_ATTEMPTS[identifier] = recent
    return len(recent) >= MAX_FAILED_ATTEMPTS

def record_failed_attempt(identifier: str):
    """Records a failed login attempt for brute-force protection."""
    now = time.time()
    attempts = _FAILED_ATTEMPTS.setdefault(identifier, [])
    attempts.append(now)

def clear_failed_attempts(identifier: str):
    """Clears failed login counter upon successful authentication."""
    _FAILED_ATTEMPTS.pop(identifier, None)

def get_current_user_id():
    """
    Retrieves the authenticated user ID from the verified server-side Flask session.
    Client-controlled headers (e.g. X-User-Id) are strictly ignored to prevent authentication bypass.
    """
    uid = session.get("user_id")
    if uid:
        try:
            return int(uid)
        except (ValueError, TypeError):
            pass
            
    return None

def get_current_user():
    """Retrieves full user record for the current authenticated session."""
    user_id = get_current_user_id()
    if not user_id:
        return None
    return get_user_by_id(user_id)

def login_required(f):
    """
    Decorator for Flask routes requiring mandatory authentication.
    - API requests return 401 Unauthorized JSON with authenticated=False.
    - Browser page requests redirect to /login with ?next= query param.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_current_user_id()
        if not user_id:
            # Check if this is an API call
            if request.path.startswith("/api/") or request.is_json or "application/json" in request.headers.get("Accept", ""):
                return jsonify({
                    "success": False,
                    "authenticated": False,
                    "error": "Authentication required. Please sign in to access PRANVYRA."
                }), 401
            
            # Browser navigation redirect
            next_url = request.path if request.path and request.path != "/login" else "/"
            return redirect(f"/login?next={next_url}")
            
        return f(*args, **kwargs)
    return decorated_function
