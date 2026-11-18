"""
PRANVYRA AIR-TWIN — Personal Environmental Intelligence Engine
Synthesizes user's voluntarily provided routine, transport, indoor conditions,
and current ambient atmospheric data into an adaptive personal profile.
"""

def generate_air_twin_profile(visitor_profile, aqi_data, weather_data):
    """
    Feature A: AIR-TWIN
    Adaptive environmental intelligence profile.
    Distinguishes estimated exposure indicators from clinical measurements and medical assessments.
    """
    city = visitor_profile.get("city", "Your City")
    transport = visitor_profile.get("primary_transport", "public_transit")
    distance_km = float(visitor_profile.get("commute_distance_km", 10.0))
    outdoor_hours = visitor_profile.get("outdoor_hours", "1-2 hours")
    ventilation = visitor_profile.get("ventilation_type", "natural")
    cooking_fuel = visitor_profile.get("cooking_fuel", "lpg")
    
    current_aqi = aqi_data.get("aqi", 100) if aqi_data.get("is_available") else 100
    temp = weather_data.get("temperature", 24.0) if weather_data.get("success") else 24.0
    wind = weather_data.get("wind_speed", 5.0) if weather_data.get("success") else 5.0

    # 1. Transport Exposure Vulnerability
    transport_vulnerabilities = {
        "motorcycle": {
            "tier": "High Vulnerability",
            "score": 30,
            "description": "Direct, unshielded breathing-zone exposure to vehicular tailpipes, tyre friction, and road-level NOx plumes."
        },
        "cycling": {
            "tier": "High Physiological Intake",
            "score": 35,
            "description": "Cardio-respiratory ventilation increases minute volume of air inhaled by 2.5x to 3x."
        },
        "walking": {
            "tier": "Moderate-High Exposure",
            "score": 45,
            "description": "Surface-level exposure along transit corridors; mitigated by off-street walkways and park trails."
        },
        "carpool": {
            "tier": "Moderate Protection",
            "score": 70,
            "description": "Enclosed vehicle cabin shields from heavy particulates; requires cabin filter inspection and internal air recirculation."
        },
        "petrol_car": {
            "tier": "Moderate Protection",
            "score": 70,
            "description": "Cabin isolation protects passengers, but high personal carbon footprint."
        },
        "bus": {
            "tier": "Moderate Protection",
            "score": 65,
            "description": "Transit bus cabin provides basic barrier; door opening intervals allow minor roadside infiltration."
        },
        "public_transit": {
            "tier": "Low Vulnerability / Optimal Shielding",
            "score": 85,
            "description": "Grade-separated electric rail provides filtered indoor transit and eliminates direct street exhaust exposure."
        },
        "metro": {
            "tier": "Low Vulnerability / Optimal Shielding",
            "score": 85,
            "description": "Grade-separated electric rail provides filtered indoor transit and eliminates direct street exhaust exposure."
        }
    }
    t_info = transport_vulnerabilities.get(transport, transport_vulnerabilities["public_transit"])

    # 2. Indoor Environment Vulnerability
    indoor_score = 75
    if ventilation == "poor":
        indoor_score -= 25
    if cooking_fuel in ["biomass", "kerosene"]:
        indoor_score -= 30
    elif cooking_fuel in ["lpg", "piped_gas"]:
        indoor_score -= 8

    # 3. Overall Adaptive Exposure Index (0 to 100, where 100 = lowest personal risk)
    aqi_penalty = min(50, int((current_aqi / 300.0) * 50))
    overall_resilience_score = max(10, min(100, (t_info["score"] * 0.4 + indoor_score * 0.4 + (50 - aqi_penalty) * 0.4)))
    overall_resilience_score = round(overall_resilience_score)

    # 4. Adaptive Next Best Action specifically for this Twin
    if current_aqi > 150:
        if transport in ["motorcycle", "cycling"]:
            next_best_action = {
                "title": f"Shift Today's {distance_km} km Commute to Electric Rail & Wear N95",
                "urgency": "High Priority",
                "problem": f"Elevated ambient AQI ({current_aqi}) creates dangerous inhalation levels on open two-wheelers.",
                "action": "Switch to metro or closed transit for your journey; use an N95 respirator during outdoor walking transitions.",
                "reason": "Electric rail bypasses ground-level vehicle exhaust plumes trapped by light winds.",
                "benefit": "Reduces inhaled fine particulate deposition by ~85%."
            }
        else:
            next_best_action = {
                "title": "Seal Indoor Air & Time Aeration for Midday Solar Mixing",
                "urgency": "Medium Priority",
                "problem": f"Outdoor AQI of {current_aqi} promotes steady infiltration through window micro-crevices.",
                "action": "Keep windows closed during morning rush hours; ventilate between 12:00 PM and 3:00 PM.",
                "reason": "Midday solar heating elevates the atmospheric boundary layer, dispersing surface pollution.",
                "benefit": "Flushes indoor carbon dioxide without drawing in heavy traffic particulates."
            }
    else:
        next_best_action = {
            "title": f"Clean Air Mobility Opportunity for {city}",
            "urgency": "Favorable Conditions",
            "problem": f"AQI is acceptable ({current_aqi}). Urban baseline emissions remain steady.",
            "action": f"Take public transit or active travel for local errands under 3 km.",
            "reason": "Atmospheric dispersion is optimal; outdoor physical activity confers high cardiovascular health benefits.",
            "benefit": f"Avoids ~{round(distance_km * 0.17, 2)} kg CO₂ per trip."
        }

    disclaimer = "The Air-Twin exposure indicator is an adaptive mathematical model based on environmental building physics and commute factors. It is NOT a clinical medical diagnosis, personal dose measurement, or medical device."

    return {
        "city": city,
        "commute_distance_km": distance_km,
        "primary_transport": transport,
        "transport_vulnerability": t_info,
        "commute_vulnerability": {
            "vulnerability_tier": t_info["tier"],
            "assessment": t_info["description"]
        },
        "indoor_resilience_score": indoor_score,
        "overall_resilience_score": overall_resilience_score,
        "resilience_score": overall_resilience_score,
        "next_best_action": next_best_action,
        "safe_ventilation_window": "11:30 AM - 3:00 PM",
        "optimal_exercise_window": "12:00 PM - 4:00 PM (Winter) / 06:00 AM - 07:30 AM (Summer)",
        "adaptive_windows": {
            "safest_ventilation_window": "11:30 AM - 3:00 PM",
            "safest_outdoor_exercise_window": "12:00 PM - 4:00 PM (Winter) / 06:00 AM - 07:30 AM (Summer)",
            "highest_exposure_rush_hours": "08:00 AM - 10:30 AM & 06:00 PM - 08:30 PM"
        },
        "scientific_disclaimer": disclaimer,
        "non_clinical_disclaimer": disclaimer
    }
