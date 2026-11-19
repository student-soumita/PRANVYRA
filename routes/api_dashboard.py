from flask import Blueprint, request, jsonify, session
from services.air_quality import get_live_air_quality
from services.weather import get_live_weather, search_cities
from services.recommendation_engine import generate_airwise_action, calculate_breath_budget
from database.db import get_user_by_id, update_user_profile
from services.auth import get_current_user_id

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/overview", methods=["GET"])
def get_dashboard_overview():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "authenticated": False, "error": "Authentication required."}), 401

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "error": "User record not found."}), 404

    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    city_param = request.args.get("city")
    
    # If client passed new coordinates or city, persist to user's profile
    if (lat is not None and lon is not None) or city_param:
        updates = {}
        if lat is not None and lon is not None:
            updates["latitude"] = lat
            updates["longitude"] = lon
        if city_param:
            updates["city"] = city_param
        user = update_user_profile(user_id, **updates)

    user["visitor_id"] = f"user_{user_id}"
    current_lat = user.get("latitude")
    current_lon = user.get("longitude")
    
    # If no coordinates are set, use calibrated benchmark coordinates for weather/AQI calculations,
    # but DO NOT overwrite user's saved city in the returned profile unless explicitly saved
    is_benchmark_location = False
    profile_response = dict(user)
    if current_lat is None or current_lon is None:
        from config import Config
        current_lat = Config.DEFAULT_LAT
        current_lon = Config.DEFAULT_LON
        is_benchmark_location = True
        
    # Fetch real live environmental data
    aqi_data = get_live_air_quality(current_lat, current_lon)
    weather_data = get_live_weather(current_lat, current_lon)
    airwise_action = generate_airwise_action(aqi_data, weather_data, user)
    breath_budget = calculate_breath_budget(
        aqi=aqi_data.get("aqi", 100) if aqi_data.get("is_available") else 100,
        outdoor_hours_str=user.get("outdoor_hours", "1-2 hours"),
        commute_distance_km=user.get("commute_distance_km", 10.0),
        transport=user.get("primary_transport", "public_transit"),
        ventilation=user.get("ventilation_type", "natural")
    )
    
    return jsonify({
        "success": True,
        "requires_location": False,
        "is_benchmark_location": is_benchmark_location,
        "profile": profile_response,
        "air_quality": aqi_data,
        "weather": weather_data,
        "airwise_action": airwise_action,
        "breath_budget": breath_budget
    })

@dashboard_bp.route("/cities/search", methods=["GET"])
def search_city_locations():
    q = request.args.get("q", "")
    cities = search_cities(q)
    return jsonify({"success": True, "results": cities})

