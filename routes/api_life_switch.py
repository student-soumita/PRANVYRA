from flask import Blueprint, request, jsonify, session
from database.db import get_db_connection, get_user_by_id
from services.life_switch import get_all_switches, simulate_life_switch
from services.impact_receipt import generate_impact_receipt
from services.auth import get_current_user_id

life_switch_bp = Blueprint("life_switch", __name__)

@life_switch_bp.route("/catalog", methods=["GET"])
def get_catalog():
    switches = get_all_switches()
    return jsonify({"success": True, "switches": switches})

@life_switch_bp.route("/simulate", methods=["POST"])
def simulate():
    data = request.get_json() or {}
    switch_key = data.get("switch_key", "commute_moto_to_metro")
    param_val = data.get("param_value")
    
    result = simulate_life_switch(switch_key, param_val)
    return jsonify({"success": True, "simulation": result})

@life_switch_bp.route("/commit", methods=["POST"])
def commit_switch():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "authenticated": False, "error": "Authentication required."}), 401

    v_id = f"user_{user_id}"
    data = request.get_json() or {}
    switch_key = data.get("switch_key", "commute_moto_to_metro")
    param_val = data.get("param_value")
    
    sim = simulate_life_switch(switch_key, param_val)
    m = sim["metrics"]
    savings_kg = m.get("monthly_savings_kg") or m.get("annual_savings_kg", 5.0)
    
    # Generate official Personal Impact Receipt for authenticated user
    receipt = generate_impact_receipt(
        visitor_id=v_id,
        user_id=user_id,
        decision_title=f"Adopted Life-Switch: {sim['title']}",
        before_desc=f"{sim['current_habit']} (~{m.get('current_annual_kg', 'N/A')} kg/yr)",
        after_desc=f"{sim['alternative_habit']} (~{m.get('alternative_annual_kg', 'N/A')} kg/yr)",
        savings_kg=savings_kg,
        why_it_matters=sim["why_it_matters"],
        methodology=m["methodology"]
    )
    
    # Persist in life_switches table
    conn = get_db_connection()
    conn.execute(
        """INSERT INTO life_switches 
           (user_id, visitor_id, switch_key, category, current_habit, alternative_habit, baseline_emissions_kg, alternative_emissions_kg, savings_kg, methodology, assumptions)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            v_id,
            switch_key,
            sim["category"],
            sim["current_habit"],
            sim["alternative_habit"],
            float(m.get("current_annual_kg", 0)),
            float(m.get("alternative_annual_kg", 0)),
            float(savings_kg),
            m["methodology"],
            m["assumptions"]
        )
    )
    
    points = 40
    conn.execute(
        """INSERT INTO impact_logs 
           (user_id, visitor_id, action_type, title, description, co2_saved_kg, points_earned)
           VALUES (?, ?, 'life_switch_adopted', ?, ?, ?, ?)""",
        (user_id, v_id, f"Adopted: {sim['title']}", f"Estimated monthly savings: {savings_kg} kg CO₂e", float(savings_kg), points)
    )
    conn.execute("UPDATE users SET green_points = green_points + ? WHERE id = ?", (points, user_id))
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "receipt": receipt,
        "points_earned": points,
        "message": f"Committed switch '{sim['title']}'! Impact Receipt #{receipt['receipt_id']} generated."
    })


