"""
PRANVYRA INTELLIGENCE CORE — Environmental Context Service
Gathers structured atmospheric, meteorological, behavioral, and conversational
context for multi-role AI reasoning.
"""
from database.db import get_db_connection, get_or_create_visitor
from services.air_quality import get_live_air_quality
from services.weather import get_live_weather

def build_environmental_context(visitor_id, lat=None, lon=None, max_history=10):
    """
    Builds a clean, structured context dictionary containing:
    1. Visitor profile & mobility habits
    2. Real-time atmospheric & pollutant data
    3. Live meteorological conditions
    4. Active conversation history (up to max_history turns)
    """
    profile = get_or_create_visitor(visitor_id)
    
    target_lat = lat if lat is not None else profile.get("latitude")
    target_lon = lon if lon is not None else profile.get("longitude")
    
    aqi_data = get_live_air_quality(target_lat, target_lon)
    weather_data = get_live_weather(target_lat, target_lon)
    
    # Fetch recent conversation history for multi-turn conversational context
    conn = get_db_connection()
    history_rows = conn.execute(
        """SELECT role, message, language, created_at 
           FROM chat_history 
           WHERE visitor_id = ? 
           ORDER BY id DESC 
           LIMIT ?""",
        (profile["visitor_id"], max_history)
    ).fetchall()
    conn.close()
    
    # Chronological order
    conversation_history = [
        {
            "role": r["role"],
            "message": r["message"],
            "language": r["language"] or "en",
            "created_at": r["created_at"]
        }
        for r in reversed(history_rows)
    ]
    
    # Extract pollutant values if available
    pollutants_summary = {}
    if aqi_data.get("pollutants"):
        for pol_key, pol_info in aqi_data["pollutants"].items():
            if pol_info and pol_info.get("value") is not None:
                pollutants_summary[pol_key.upper()] = {
                    "value": pol_info["value"],
                    "unit": pol_info.get("unit", "µg/m³"),
                    "who_guideline": pol_info.get("who_limit")
                }
                
    return {
        "visitor_profile": {
            "city": profile.get("city") or "Location Not Specified",
            "latitude": target_lat,
            "longitude": target_lon,
            "commute_distance_km": float(profile.get("commute_distance_km", 10.0)),
            "primary_transport": profile.get("primary_transport", "public_transit"),
            "outdoor_hours": profile.get("outdoor_hours", "1-2 hours"),
            "work_schedule": profile.get("work_schedule", "Hybrid / Office"),
            "ventilation_type": profile.get("ventilation_type", "natural"),
            "cooking_fuel": profile.get("cooking_fuel", "lpg"),
            "green_points": profile.get("green_points", 0),
            "language_pref": profile.get("language_pref", "en")
        },
        "atmospheric": {
            "is_available": aqi_data.get("is_available", False),
            "aqi": aqi_data.get("aqi", 100),
            "category": aqi_data.get("category", "Moderate"),
            "alert_level": aqi_data.get("alert_level", "Moderate"),
            "health_advice": aqi_data.get("health_advice", "Air quality is acceptable for most individuals."),
            "data_source": aqi_data.get("data_source", "Open-Meteo CAMS Global Environmental Model"),
            "calculation_standard": aqi_data.get("calculation_standard", "US EPA AQI Standard (40 CFR Part 58)"),
            "timestamp": aqi_data.get("timestamp"),
            "pollutants": pollutants_summary
        },
        "meteorological": {
            "success": weather_data.get("success", False),
            "temperature_c": weather_data.get("temperature", 24.0),
            "humidity_pct": weather_data.get("humidity", 50),
            "wind_speed_kmh": weather_data.get("wind_speed", 5.0),
            "wind_direction_deg": weather_data.get("wind_direction", 0),
            "weather_desc": weather_data.get("weather_desc", "Clear skies")
        },
        "conversation_history": conversation_history
    }

