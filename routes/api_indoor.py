import json
from flask import Blueprint, request, jsonify, session
from database.db import get_db_connection, get_user_by_id
from services.recommendation_engine import assess_indoor_air
from services.auth import get_current_user_id

indoor_bp = Blueprint("indoor", __name__)

@indoor_bp.route("/check", methods=["POST"])
def submit_indoor_check():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "authenticated": False, "error": "Authentication required."}), 401

    v_id = f"user_{user_id}"
    data = request.get_json() or {}
    result = assess_indoor_air(data)
    
    conn = get_db_connection()
    conn.execute(
        """INSERT INTO indoor_air_checks 
           (user_id, visitor_id, room_size, occupants, ventilation, cooking_fuel, has_pets, 
            dust_level, smoking_exposure, has_air_purifier, overall_score, risk_level, recommendations_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            v_id,
            data.get("room_size", "medium"),
            int(data.get("occupants", 2)),
            data.get("ventilation", "natural"),
            data.get("cooking_fuel", "lpg"),
            int(data.get("has_pets", 0)),
            data.get("dust_level", "moderate"),
            int(data.get("smoking_exposure", 0)),
            int(data.get("has_air_purifier", 0)),
            result["score"],
            result["risk_level"],
            json.dumps(result["actions"])
        )
    )
    # Award green points for running an audit to the authenticated user
    conn.execute("UPDATE users SET green_points = green_points + 20 WHERE id = ?", (user_id,))
    conn.execute(
        """INSERT INTO impact_logs 
           (user_id, visitor_id, action_type, title, description, points_earned)
           VALUES (?, ?, 'indoor_audit', 'Conducted Indoor Air Check', 'Analyzed residential exposure vectors', 20)""",
        (user_id, v_id)
    )
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "assessment": result
    })

@indoor_bp.route("/latest", methods=["GET"])
def get_latest_indoor_check():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "authenticated": False, "error": "Authentication required."}), 401

    v_id = f"user_{user_id}"
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM indoor_air_checks WHERE (user_id = ? OR visitor_id = ?) ORDER BY id DESC LIMIT 1",
        (user_id, v_id)
    ).fetchone()
    conn.close()
    
    if not row:
        default_data = {
            "room_size": "medium",
            "occupants": 2,
            "ventilation": "natural",
            "cooking_fuel": "lpg",
            "has_pets": 0,
            "dust_level": "moderate",
            "smoking_exposure": 0,
            "has_air_purifier": 0
        }
        assessment = assess_indoor_air(default_data)
        return jsonify({"success": True, "has_check": False, "assessment": assessment})
        
    actions = []
    if row["recommendations_json"]:
        try:
            actions = json.loads(row["recommendations_json"])
        except Exception:
            pass
            
    return jsonify({
        "success": True,
        "has_check": True,
        "assessment": {
            "score": row["overall_score"],
            "risk_level": row["risk_level"],
            "room_size": row["room_size"],
            "ventilation": row["ventilation"],
            "cooking_fuel": row["cooking_fuel"],
            "has_pets": bool(row["has_pets"]),
            "dust_level": row["dust_level"],
            "smoking_exposure": bool(row["smoking_exposure"]),
            "has_air_purifier": bool(row["has_air_purifier"]),
            "actions": actions,
            "created_at": row["created_at"],
            "scientific_disclaimer": "This indoor check is an educational heuristic model based on documented environmental building health science. It does NOT claim to measure air quality directly through your browser or device without a certified hardware sensor."
        }
    })

