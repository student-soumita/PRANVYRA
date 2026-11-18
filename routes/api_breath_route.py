from flask import Blueprint, request, jsonify, session
from database.db import get_db_connection, get_user_by_id
from services.breath_route import plan_breath_route
from services.weather import search_cities
from services.air_quality import get_live_air_quality
from services.impact_receipt import generate_impact_receipt
from services.auth import get_current_user_id

breath_route_bp = Blueprint("breath_route", __name__)

@breath_route_bp.route("/plan", methods=["POST"])
def plan_route():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "authenticated": False, "error": "Authentication required."}), 401

    v_id = f"user_{user_id}"
    data = request.get_json() or {}
    origin_text = data.get("origin", "").strip()
    dest_text = data.get("destination", "").strip()
    dep_time = data.get("departure_time", "Now")
    preferred_mode = data.get("preferred_mode", "public_transit")
    
    if not origin_text or not dest_text:
        return jsonify({"success": False, "error": "Both origin and destination are required."}), 400
        
    # Resolve coordinates if names provided
    origin_results = search_cities(origin_text, count=1)
    dest_results = search_cities(dest_text, count=1)
    
    origin_data = {
        "name": origin_text,
        "lat": origin_results[0]["latitude"] if origin_results else None,
        "lon": origin_results[0]["longitude"] if origin_results else None,
        "manual_distance": float(data.get("manual_distance", 12.0))
    }
    dest_data = {
        "name": dest_text,
        "lat": dest_results[0]["latitude"] if dest_results else None,
        "lon": dest_results[0]["longitude"] if dest_results else None
    }
    
    # Get current air quality for origin if coordinates exist
    current_aqi = 100
    if origin_data["lat"] and origin_data["lon"]:
        aqi_res = get_live_air_quality(origin_data["lat"], origin_data["lon"])
        if aqi_res.get("is_available"):
            current_aqi = aqi_res.get("aqi", 100)
            
    plan = plan_breath_route(origin_data, dest_data, dep_time, current_aqi, preferred_mode)
    
    # Persist search in breath_routes table with user_id
    conn = get_db_connection()
    conn.execute(
        """INSERT INTO breath_routes 
           (user_id, visitor_id, origin, destination, distance_km, travel_time_mins, recommended_mode, 
            baseline_emissions_kg, recommended_emissions_kg, emissions_saved_kg, air_quality_context)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            v_id,
            origin_text,
            dest_text,
            plan["distance_km"],
            plan["recommended_mode"]["est_minutes"],
            plan["recommended_mode"]["mode_name"],
            plan["modes"][4]["emissions_kg"] if len(plan["modes"]) > 4 else 1.5,
            plan["recommended_mode"]["emissions_kg"],
            plan["savings_vs_car_kg"],
            f"AQI {current_aqi} ({origin_text})"
        )
    )
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "plan": plan
    })

@breath_route_bp.route("/commit-trip", methods=["POST"])
def commit_route_trip():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "authenticated": False, "error": "Authentication required."}), 401

    v_id = f"user_{user_id}"
    data = request.get_json() or {}
    origin = data.get("origin", "Origin")
    destination = data.get("destination", "Destination")
    mode_name = data.get("mode_name", "Electric Metro")
    distance_km = float(data.get("distance_km", 10.0))
    savings_kg = float(data.get("savings_kg", 1.2))
    
    # Generate official Personal Impact Receipt
    receipt = generate_impact_receipt(
        visitor_id=v_id,
        user_id=user_id,
        decision_title=f"Completed Clean Journey: {origin} to {destination} via {mode_name}",
        before_desc=f"Solo passenger car travel ({round(distance_km * 0.1705, 2)} kg CO₂e)",
        after_desc=f"Chosen {mode_name} travel ({round(distance_km * 0.0285, 2)} kg CO₂e)",
        savings_kg=savings_kg,
        why_it_matters=f"Opting for {mode_name} eliminated {savings_kg} kg of tailpipe emissions and avoided peak street exhaust exposure.",
        methodology="Great-circle distance with 1.25x urban detour coefficient and UK DEFRA 2023 modal emission conversion factors."
    )
    
    # Update points & impact log
    points = max(15, int(savings_kg * 25))
    conn = get_db_connection()
    conn.execute(
        """INSERT INTO impact_logs 
           (user_id, visitor_id, action_type, title, description, co2_saved_kg, points_earned)
           VALUES (?, ?, 'breath_route_trip', ?, ?, ?, ?)""",
        (user_id, v_id, f"BreathRoute: {origin} → {destination}", f"Travelled via {mode_name}", savings_kg, points)
    )
    conn.execute("UPDATE users SET green_points = green_points + ? WHERE id = ?", (points, user_id))
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "points_earned": points,
        "receipt": receipt,
        "message": f"Journey recorded! You avoided {savings_kg} kg CO₂e and earned {points} green points."
    })


