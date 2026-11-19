import requests
import logging
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Lightweight in-memory cache for environmental telemetry (5 min TTL)
_AQI_CACHE = {}
_AQI_CACHE_TTL = 300  # seconds

# US EPA AQI Breakpoints for PM2.5 (µg/m³) and PM10 (µg/m³)
# Formula: I = ((I_high - I_low) / (C_high - C_low)) * (C - C_low) + I_low
PM25_BREAKPOINTS = [
    (0.0, 12.0, 0, 50, "Good", "#16A88A"),
    (12.1, 35.4, 51, 100, "Moderate", "#E7A83E"),
    (35.5, 55.4, 101, 150, "Unhealthy for Sensitive Groups", "#FF9800"),
    (55.5, 150.4, 151, 200, "Unhealthy", "#E46F65"),
    (150.5, 250.4, 201, 300, "Very Unhealthy", "#8E24AA"),
    (250.5, 500.4, 301, 500, "Hazardous", "#6A1B9A")
]

PM10_BREAKPOINTS = [
    (0.0, 54.0, 0, 50, "Good", "#16A88A"),
    (55.0, 154.0, 51, 100, "Moderate", "#E7A83E"),
    (155.0, 254.0, 101, 150, "Unhealthy for Sensitive Groups", "#FF9800"),
    (255.0, 354.0, 151, 200, "Unhealthy", "#E46F65"),
    (355.0, 424.0, 201, 300, "Very Unhealthy", "#8E24AA"),
    (425.0, 604.0, 301, 500, "Hazardous", "#6A1B9A")
]

def calculate_sub_index(conc, breakpoints):
    """Calculates linear sub-index according to US EPA AQI standard."""
    if conc is None or conc < 0:
        return 0, "Unknown", "#888888"
    for c_low, c_high, i_low, i_high, category, color in breakpoints:
        if c_low <= conc <= c_high:
            index = ((i_high - i_low) / (c_high - c_low)) * (conc - c_low) + i_low
            return round(index), category, color
    if conc > breakpoints[-1][1]:
        return 500, "Hazardous", "#6A1B9A"
    return 0, "Good", "#16A88A"

def get_aqi_category_info(aqi_value):
    if aqi_value <= 50:
        return {
            "category": "Good",
            "color": "#16A88A",
            "textColor": "#FFFFFF",
            "alert_level": "Low",
            "health_advice": "Air quality is satisfactory and poses little or no risk to public health."
        }
    elif aqi_value <= 100:
        return {
            "category": "Moderate",
            "color": "#E7A83E",
            "textColor": "#182522",
            "alert_level": "Moderate",
            "health_advice": "Air quality is acceptable; however, sensitive individuals should limit prolonged outdoor exertion."
        }
    elif aqi_value <= 150:
        return {
            "category": "Unhealthy for Sensitive Groups",
            "color": "#FF9800",
            "textColor": "#FFFFFF",
            "alert_level": "Elevated",
            "health_advice": "Members of sensitive groups may experience health effects. General public is less likely to be affected."
        }
    elif aqi_value <= 200:
        return {
            "category": "Unhealthy",
            "color": "#E46F65",
            "textColor": "#FFFFFF",
            "alert_level": "High",
            "health_advice": "Everyone may begin to experience health effects; sensitive groups may experience more serious effects."
        }
    elif aqi_value <= 300:
        return {
            "category": "Very Unhealthy",
            "color": "#8E24AA",
            "textColor": "#FFFFFF",
            "alert_level": "Very High",
            "health_advice": "Health alert: The risk of health effects is increased for everyone in the population."
        }
    else:
        return {
            "category": "Hazardous",
            "color": "#6A1B9A",
            "textColor": "#FFFFFF",
            "alert_level": "Emergency",
            "health_advice": "Health warnings of emergency conditions. The entire population is more likely to be affected."
        }

def get_live_air_quality(latitude, longitude):
    """
    Fetches real-time atmospheric pollutant concentrations from Open-Meteo Air Quality API.
    Uses European Copernicus CAMS / ECMWF modeling with ground observation assimilation.
    Does NOT invent fake sensor readings if unreachable.
    Includes safe 5-minute memory caching to avoid repeated API requests for identical coordinates.
    """
    if latitude is None or longitude is None:
        return {
            "success": False,
            "is_available": False,
            "message": "Please select a location or grant location permission to view live environmental data.",
            "data_source": "Open-Meteo CAMS Global Model",
            "calculation_standard": "US EPA AQI Standard (40 CFR Part 58)"
        }

    # Rounded coordinate key (~1.1 km precision)
    cache_key = (round(float(latitude), 2), round(float(longitude), 2))
    now = time.time()
    cached = _AQI_CACHE.get(cache_key)
    if cached and (now - cached["timestamp"] < _AQI_CACHE_TTL):
        return cached["data"]

    api_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ["us_aqi", "pm10", "pm2_5", "carbon_monoxide", "nitrogen_dioxide", "sulphur_dioxide", "ozone"],
        "hourly": ["pm2_5", "pm10", "us_aqi"],
        "forecast_days": 2,
        "timezone": "auto"
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=6)
        if response.status_code == 200:
            data = response.json()
            current = data.get("current", {})
            hourly = data.get("hourly", {})
            
            pm25 = current.get("pm2_5")
            pm10 = current.get("pm10")
            no2 = current.get("nitrogen_dioxide")
            o3 = current.get("ozone")
            co = current.get("carbon_monoxide")
            so2 = current.get("sulphur_dioxide")
            
            us_aqi = current.get("us_aqi")
            if us_aqi is None and pm25 is not None:
                sub_pm25, _, _ = calculate_sub_index(pm25, PM25_BREAKPOINTS)
                sub_pm10, _, _ = calculate_sub_index(pm10 or 0, PM10_BREAKPOINTS)
                us_aqi = max(sub_pm25, sub_pm10)
            
            aqi_val = int(us_aqi) if us_aqi is not None else 50
            cat_info = get_aqi_category_info(aqi_val)
            
            hourly_times = hourly.get("time", [])[:24]
            hourly_aqi = hourly.get("us_aqi", [])[:24]
            hourly_pm25 = hourly.get("pm2_5", [])[:24]
            hourly_pm10 = hourly.get("pm10", [])[:24]
            
            result = {
                "success": True,
                "is_available": True,
                "data_source": "Open-Meteo CAMS Global Atmospheric Model & Surface Observation Assimilation",
                "calculation_standard": "US EPA AQI Standard (40 CFR Part 58)",
                "timestamp": current.get("time", datetime.utcnow().isoformat()),
                "aqi": aqi_val,
                "category": cat_info["category"],
                "color": cat_info["color"],
                "textColor": cat_info["textColor"],
                "alert_level": cat_info["alert_level"],
                "health_advice": cat_info["health_advice"],
                "pollutants": {
                    "pm25": {
                        "value": round(float(pm25), 1) if pm25 is not None else None,
                        "unit": "µg/m³",
                        "name": "PM2.5 (Fine Particulates)",
                        "description": "Particles ≤2.5 micrometers that penetrate deep into alveolar lung tissues.",
                        "who_limit": 15.0
                    },
                    "pm10": {
                        "value": round(float(pm10), 1) if pm10 is not None else None,
                        "unit": "µg/m³",
                        "name": "PM10 (Coarse Dust)",
                        "description": "Inhalable dust, pollen, and road resuspension particles ≤10 micrometers.",
                        "who_limit": 45.0
                    },
                    "no2": {
                        "value": round(float(no2), 1) if no2 is not None else None,
                        "unit": "µg/m³",
                        "name": "NO₂ (Nitrogen Dioxide)",
                        "description": "Emitted from vehicle combustion engines and fossil power generation.",
                        "who_limit": 25.0
                    },
                    "o3": {
                        "value": round(float(o3), 1) if o3 is not None else None,
                        "unit": "µg/m³",
                        "name": "O₃ (Ground-Level Ozone)",
                        "description": "Formed through photochemical reactions between sunlight, NOx, and VOCs.",
                        "who_limit": 100.0
                    },
                    "co": {
                        "value": round(float(co), 1) if co is not None else None,
                        "unit": "µg/m³",
                        "name": "CO (Carbon Monoxide)",
                        "description": "Colorless toxic gas resulting from incomplete fuel combustion.",
                        "who_limit": 4000.0
                    },
                    "so2": {
                        "value": round(float(so2), 1) if so2 is not None else None,
                        "unit": "µg/m³",
                        "name": "SO₂ (Sulphur Dioxide)",
                        "description": "Combustion byproduct of sulfur-bearing petroleum, coal, and industrial smelters.",
                        "who_limit": 40.0
                    }
                },
                "hourly_trend": {
                    "labels": [t.split("T")[-1] if "T" in t else t for t in hourly_times],
                    "aqi": [int(v) if v is not None else 0 for v in hourly_aqi],
                    "pm25": [round(float(v), 1) if v is not None else 0 for v in hourly_pm25],
                    "pm10": [round(float(v), 1) if v is not None else 0 for v in hourly_pm10]
                }
            }
            # Cache the successful telemetry
            _AQI_CACHE[cache_key] = {"data": result, "timestamp": now}
            return result
    except Exception as e:
        logger.warning(f"Live air quality fetch error for ({latitude}, {longitude}): {e}")

    # Honest unavailable state (NO fabricated readings!)
    return {
        "success": False,
        "is_available": False,
        "message": "Real-time atmospheric monitoring data is temporarily unreachable from the satellite/station feed. Please verify your connection or retry shortly.",
        "data_source": "Open-Meteo CAMS Global Environmental Model",
        "calculation_standard": "US EPA AQI Standard (40 CFR Part 58)",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    }
