from flask import Blueprint, request, jsonify, session
from database.db import get_db_connection, get_user_by_id
from services.impact_calculator import get_cumulative_impact_metrics
from services.recommendation_engine import get_sustainable_alternatives_catalog
from services.impact_receipt import get_visitor_receipts
from services.auth import get_current_user_id

impact_bp = Blueprint("impact", __name__)

@impact_bp.route("/summary", methods=["GET"])
def get_impact_summary():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "authenticated": False, "error": "Authentication required."}), 401

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "error": "User record not found."}), 404

    v_id = f"user_{user_id}"
    conn = get_db_connection()
    row = conn.execute(
        """SELECT 
            COALESCE(SUM(co2_saved_kg), 0.0) as total_co2,
            COALESCE(SUM(energy_saved_kwh), 0.0) as total_energy,
            COALESCE(SUM(waste_reduced_kg), 0.0) as total_waste,
            COUNT(*) as total_actions
           FROM impact_logs WHERE (user_id = ? OR visitor_id = ?)""",
        (user_id, v_id)
    ).fetchone()
    
    co2 = float(row["total_co2"])
    energy = float(row["total_energy"])
    waste = float(row["total_waste"])
    actions = int(row["total_actions"])
    
    metrics = get_cumulative_impact_metrics(co2, energy, waste)
    metrics["green_points"] = user.get("green_points", 0)
    metrics["total_actions"] = actions
    
    # Receipts count for this user
    receipts_count = conn.execute(
        "SELECT COUNT(*) FROM impact_receipts WHERE (user_id = ? OR visitor_id = ?)",
        (user_id, v_id)
    ).fetchone()[0]
    metrics["receipts_issued"] = receipts_count
    
    conn.close()
    
    return jsonify({
        "success": True,
        "metrics": metrics
    })

@impact_bp.route("/receipts", methods=["GET"])
def list_receipts():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "authenticated": False, "error": "Authentication required."}), 401

    receipts = get_visitor_receipts(user_id=user_id)
    return jsonify({"success": True, "receipts": receipts})

@impact_bp.route("/history", methods=["GET"])
def get_impact_history():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "authenticated": False, "error": "Authentication required."}), 401

    v_id = f"user_{user_id}"
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM impact_logs WHERE (user_id = ? OR visitor_id = ?) ORDER BY id DESC LIMIT 20",
        (user_id, v_id)
    ).fetchall()
    conn.close()
    return jsonify({"success": True, "history": [dict(r) for r in rows]})

@impact_bp.route("/alternatives", methods=["GET"])
def get_alternatives():
    catalog = get_sustainable_alternatives_catalog()
    return jsonify({"success": True, "alternatives": catalog})

@impact_bp.route("/log", methods=["POST"])
def log_impact_action():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "authenticated": False, "error": "Authentication required."}), 401

    v_id = f"user_{user_id}"
    data = request.get_json() or {}
    action_type = data.get("action_type", "energy_save")
    title = data.get("title", "Sustainable Action")
    desc = data.get("description", "")
    co2_saved = float(data.get("co2_saved_kg", 0.5))
    energy_saved = float(data.get("energy_saved_kwh", 0.0))
    waste_reduced = float(data.get("waste_reduced_kg", 0.0))
    points = int(data.get("points", 20))
    
    conn = get_db_connection()
    conn.execute(
        """INSERT INTO impact_logs 
           (user_id, visitor_id, action_type, title, description, co2_saved_kg, energy_saved_kwh, waste_reduced_kg, points_earned)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, v_id, action_type, title, desc, co2_saved, energy_saved, waste_reduced, points)
    )
    conn.execute("UPDATE users SET green_points = green_points + ? WHERE id = ?", (points, user_id))
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "points_earned": points,
        "message": f"Action '{title}' recorded! +{points} green points added to your personal profile."
    })
