import math
from services.impact_calculator import EMISSION_FACTORS

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates great-circle distance between two coordinate pairs in kilometers."""
    R = 6371.0 # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    direct_dist = R * c
    # Urban route winding factor: urban street grids typically average 1.25x geodesic distance
    return round(direct_dist * 1.25, 1)

# Average urban transit speeds in km/h
MODE_SPEEDS_KMH = {
    "walking": 4.5,
    "cycling": 14.0,
    "metro": 32.0,      # Grade-separated rapid transit
    "bus": 16.0,        # Surface traffic with stops
    "motorcycle": 25.0, # Urban maneuvering
    "carpool": 22.0,
    "petrol_car": 22.0,
    "diesel_car": 22.0
}

def plan_breath_route(origin_data, dest_data, departure_time="Now", current_aqi=100, preferred_mode="public_transit"):
    """
    Feature B: BREATHROUTE — Environmentally Aware Journey Planner
    Compares transportation choices with real distance, duration, emissions, and air health exposure.
    Does not invent fake route sensor readings; uses transparent urban physics and documented DEFRA factors.
    """
    lat1 = origin_data.get("lat")
    lon1 = origin_data.get("lon")
    lat2 = dest_data.get("lat")
    lon2 = dest_data.get("lon")
    origin_name = origin_data.get("name", "Origin")
    dest_name = dest_data.get("name", "Destination")
    
    if lat1 is not None and lon1 is not None and lat2 is not None and lon2 is not None:
        distance_km = haversine_distance(lat1, lon1, lat2, lon2)
        if distance_km < 0.5:
            distance_km = 1.0
    else:
        distance_km = float(origin_data.get("manual_distance", 10.0))

    modes_evaluated = []
    
    # Modes to compare
    target_modes = ["metro", "bus", "carpool", "motorcycle", "petrol_car", "cycling", "walking"]
    
    for m in target_modes:
        speed = MODE_SPEEDS_KMH.get(m, 20.0)
        est_minutes = round((distance_km / speed) * 60)
        factor = EMISSION_FACTORS.get(m, {}).get("factor_g_per_km", 170.5)
        emissions_kg = round((distance_km * factor) / 1000.0, 3)
        cost_est = round(distance_km * EMISSION_FACTORS.get(m, {}).get("cost_per_km", 3.0), 1)
        
        # Exposure and health trade-off note
        if m in ["motorcycle"]:
            exposure_desc = "High direct roadside exposure to tailpipe exhaust and resuspended road dust at breathing height (0-2m)."
            health_precaution = "Wear an authentic N95/FFP2 respirator if AQI > 120."
        elif m in ["cycling", "walking"]:
            if distance_km > 6.0 and m == "walking":
                exposure_desc = "Excessive walking distance for a single commute leg."
                health_precaution = "Combine with rapid rail transit."
            elif current_aqi > 150:
                exposure_desc = "Heavy cardiovascular respiration multiplies inhaled particulate volume by 2.5x to 3.5x."
                health_precaution = "Avoid rigorous outdoor active travel when AQI > 150."
            else:
                exposure_desc = "Optimal zero-emission active mobility during clean air windows."
                health_precaution = "Excellent cardio benefit with zero carbon footprint."
        elif m in ["metro"]:
            exposure_desc = "Protected indoor cabins; grade-separated electric transit eliminates direct exposure to street exhaust plumes."
            health_precaution = "Lowest respiratory exposure and optimal carbon avoidance."
        else: # cars, bus
            exposure_desc = "Moderate exposure depending on vehicle cabin filter condition."
            health_precaution = "Keep vehicle air ventilation on internal recirculation mode during traffic jams."

        modes_evaluated.append({
            "mode_key": m,
            "mode_name": EMISSION_FACTORS.get(m, {}).get("name", m.title()),
            "distance_km": distance_km,
            "est_minutes": est_minutes,
            "emissions_kg": emissions_kg,
            "cost_estimate": cost_est,
            "exposure_desc": exposure_desc,
            "health_precaution": health_precaution
        })
        
    # Sort: recommend the optimal blend of low emissions and safety
    baseline_car = next((m for m in modes_evaluated if m["mode_key"] == "petrol_car"), modes_evaluated[0])
    
    # Recommendation logic
    if distance_km <= 3.0 and current_aqi <= 100:
        recommended = next(m for m in modes_evaluated if m["mode_key"] == "cycling" or m["mode_key"] == "walking")
        rec_reason = f"Short trip ({distance_km} km) during acceptable air conditions (AQI {current_aqi}). Active travel is fastest and produces zero emissions."
    elif any(m["mode_key"] == "metro" for m in modes_evaluated):
        recommended = next(m for m in modes_evaluated if m["mode_key"] == "metro")
        rec_reason = f"Electric Metro cuts tailpipe emissions by ~83% compared to private car, while insulating you from street-level NOx and PM2.5."
    else:
        recommended = next(m for m in modes_evaluated if m["mode_key"] == "bus")
        rec_reason = "Public bus shares passenger emissions efficiently and lowers your individual carbon footprint."
        
    saved_kg = max(0.0, round(baseline_car["emissions_kg"] - recommended["emissions_kg"], 3))

    return {
        "origin": origin_name,
        "destination": dest_name,
        "distance_km": distance_km,
        "departure_time": departure_time,
        "current_aqi": current_aqi,
        "recommended_mode": recommended,
        "recommendation_reason": rec_reason,
        "savings_vs_car_kg": saved_kg,
        "modes": modes_evaluated,
        "methodology": "Great-circle distance with urban routing coefficient (1.25x) and UK DEFRA 2023 greenhouse gas emission factors.",
        "scientific_disclaimer": "Route emissions and travel times are educational estimates based on standard urban fleet averages and modal factors. Route air quality reflects regional atmospheric monitoring."
    }

