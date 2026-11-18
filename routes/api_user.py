import json
from flask import Blueprint, request, jsonify, session
from database.db import get_user_by_id, update_user_profile, get_db_connection
from services.air_twin import generate_air_twin_profile
from services.air_quality import get_live_air_quality
from services.weather import get_live_weather
from services.auth import get_current_user_id

user_bp = Blueprint("user", __name__)

@user_bp.route("/air-twin", methods=["GET"])
def get_air_twin():
    """
    Feature A: AIR-TWIN — Adaptive Personal Environmental Intelligence.
    Generates personalized resilience and vulnerability metrics for the authenticated user.
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "authenticated": False, "error": "Authentication required."}), 401

    profile = get_user_by_id(user_id)
    if not profile:
        return jsonify({"success": False, "error": "User not found."}), 404

    profile["visitor_id"] = f"user_{user_id}"
    lat = profile.get("latitude")
    lon = profile.get("longitude")
    aqi_data = {"is_available": False, "aqi": 100}
    weather_data = {"success": False, "temperature": 24.0, "wind_speed": 5.0}

    if lat is not None and lon is not None:
        aqi_data = get_live_air_quality(lat, lon)
        weather_data = get_live_weather(lat, lon)

    twin = generate_air_twin_profile(profile, aqi_data, weather_data)

    return jsonify({
        "success": True,
        "profile": profile,
        "air_twin": twin
    })

@user_bp.route("/profile", methods=["GET"])
def get_profile():
    """Retrieves private environmental and lifestyle profile of the authenticated user."""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "authenticated": False, "error": "Authentication required."}), 401

    profile = get_user_by_id(user_id)
    if not profile:
        return jsonify({"success": False, "error": "User not found."}), 404

    profile["visitor_id"] = f"user_{user_id}"
    return jsonify({"success": True, "profile": profile})

@user_bp.route("/profile", methods=["PUT"])
def update_profile():
    """Updates private environmental and lifestyle settings of the authenticated user."""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "authenticated": False, "error": "Authentication required."}), 401

    data = request.get_json() or {}
    updated_profile = update_user_profile(user_id, **data)
    if not updated_profile:
        return jsonify({"success": False, "error": "Failed to update profile."}), 400

    # Also sync language preference to active session
    if "language_pref" in data:
        session["language_pref"] = data["language_pref"]

    updated_profile["visitor_id"] = f"user_{user_id}"
    return jsonify({
        "success": True,
        "profile": updated_profile,
        "message": "Air-Twin profile updated."
    })
