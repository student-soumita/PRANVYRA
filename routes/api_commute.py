from flask import Blueprint, request, jsonify, session
from database.db import get_db_connection
from services.impact_calculator import compare_all_modes, simulate_commute_switch
from services.auth import get_current_user_id

commute_bp = Blueprint("commute", __name__)

@commute_bp.route("/compare", methods=["POST"])
def compare_transport():
    data = request.get_json() or {}
    distance_km = float(data.get("distance_km", 14.5))
    current_mode = data.get("current_mode", "motorcycle")
    passengers = int(data.get("passengers", 1))
    
    result = compare_all_modes(distance_km, current_mode, passengers)
    return jsonify({"success": True, "result": result})

@commute_bp.route("/simulate", methods=["POST"])
def run_simulation():
    data = request.get_json() or {}
    distance_km = float(data.get("distance_km", 14.5))
    from_mode = data.get("from_mode", "motorcycle")
    to_mode = data.get("to_mode", "metro")
    daily_trips = int(data.get("daily_trips", 2))
    
    sim = simulate_commute_switch(distance_km, from_mode, to_mode, daily_trips)
    return jsonify({"success": True, "simulation": sim})

@commute_bp.route("/log", methods=["POST"])
def log_green_commute():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "authenticated": False, "error": "Authentication required."}), 401

    data = request.get_json() or {}
    distance_km = float(data.get("distance_km", 14.5))
    from_mode = data.get("from_mode", "motorcycle")
    to_mode = data.get("to_mode", "metro")
    
    sim = simulate_commute_switch(distance_km, from_mode, to_mode, daily_trips=1)
    saved_kg = sim["trip_savings_kg"]
    points = max(15, int(saved_kg * 25))
    
    conn = get_db_connection()
    v_id = f"user_{user_id}"
    conn.execute(
        """INSERT INTO impact_logs 
           (user_id, visitor_id, action_type, title, description, co2_saved_kg, points_earned)
           VALUES (?, ?, 'commute_switch', ?, ?, ?, ?)""",
        (
            user_id,
            v_id,
            f"Switched from {sim['from_mode']} to {sim['to_mode']}",
            f"Completed {distance_km} km journey avoiding {saved_kg} kg tailpipe CO₂",
            saved_kg,
            points
        )
    )
    conn.execute("UPDATE users SET green_points = green_points + ? WHERE id = ?", (points, user_id))
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "saved_kg": saved_kg,
        "points_earned": points,
        "message": f"Recorded green commute! You avoided {saved_kg} kg CO₂ and earned {points} green points."
    })
