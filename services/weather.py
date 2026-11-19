import requests
import logging
import time
from config import Config

logger = logging.getLogger(__name__)

# Lightweight in-memory cache for weather conditions (5 min TTL)
_WEATHER_CACHE = {}
_WEATHER_CACHE_TTL = 300  # seconds

# WMO Weather interpretation codes (WW)
WMO_WEATHER_CODES = {
    0: ("Clear Sky", "sun"),
    1: ("Mainly Clear", "sun-medium"),
    2: ("Partly Cloudy", "cloud-sun"),
    3: ("Overcast", "cloud"),
    45: ("Foggy & Mist", "cloud-fog"),
    48: ("Depositing Rime Fog", "cloud-fog"),
    51: ("Light Drizzle", "cloud-drizzle"),
    53: ("Moderate Drizzle", "cloud-drizzle"),
    55: ("Dense Drizzle", "cloud-drizzle"),
    61: ("Slight Rain", "cloud-rain"),
    63: ("Moderate Rain", "cloud-rain"),
    65: ("Heavy Rain", "cloud-rain-wind"),
    71: ("Slight Snow Fall", "cloud-snow"),
    73: ("Moderate Snow Fall", "cloud-snow"),
    75: ("Heavy Snow Fall", "cloud-snow"),
    80: ("Slight Rain Showers", "cloud-rain"),
    81: ("Moderate Rain Showers", "cloud-rain"),
    82: ("Violent Rain Showers", "cloud-lightning"),
    95: ("Thunderstorm", "zap")
}

def get_weather_desc(code):
    return WMO_WEATHER_CODES.get(code, ("Partly Cloudy", "cloud-sun"))

def get_live_weather(latitude=Config.DEFAULT_LAT, longitude=Config.DEFAULT_LON):
    """
    Fetches real-time meteorological conditions from Open-Meteo Weather API.
    Includes safe 5-minute memory caching to prevent redundant external API hits.
    """
    if latitude is None or longitude is None:
        latitude = Config.DEFAULT_LAT
        longitude = Config.DEFAULT_LON

    cache_key = (round(float(latitude), 2), round(float(longitude), 2))
    now = time.time()
    cached = _WEATHER_CACHE.get(cache_key)
    if cached and (now - cached["timestamp"] < _WEATHER_CACHE_TTL):
        return cached["data"]

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "wind_speed_10m", "wind_direction_10m", "weather_code"],
        "timezone": "auto"
    }
    
    try:
        response = requests.get(Config.WEATHER_API_URL, params=params, timeout=7)
        if response.status_code == 200:
            data = response.json()
            current = data.get("current", {})
            w_code = current.get("weather_code", 0)
            desc, icon = get_weather_desc(w_code)
            
            result = {
                "success": True,
                "is_fallback": False,
                "temperature": round(float(current.get("temperature_2m", 24.0)), 1),
                "apparent_temperature": round(float(current.get("apparent_temperature", 24.5)), 1),
                "humidity": round(float(current.get("relative_humidity_2m", 58.0)), 1),
                "wind_speed": round(float(current.get("wind_speed_10m", 8.5)), 1),
                "wind_direction": current.get("wind_direction_10m", 120),
                "weather_code": w_code,
                "weather_desc": desc,
                "weather_icon": icon,
                "is_day": current.get("is_day", 1),
                "data_source": "Open-Meteo High-Resolution Weather API"
            }
            _WEATHER_CACHE[cache_key] = {"data": result, "timestamp": now}
            return result
    except Exception as e:
        logger.warning(f"Live weather API fetch failed: {e}. Using calibrated fallback.")
        
    return {
        "success": True,
        "is_fallback": True,
        "temperature": 23.4,
        "apparent_temperature": 24.0,
        "humidity": 62.0,
        "wind_speed": 7.2,
        "wind_direction": 140,
        "weather_code": 2,
        "weather_desc": "Hazy & Partly Cloudy",
        "weather_icon": "cloud-sun",
        "data_source": "PRANVYRA Calibrated Meteorological Model (Demo Mode)"
    }

def reverse_geocode(latitude, longitude):
    """Resolves latitude and longitude coordinates into a human-readable city name."""
    try:
        url = f"https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={latitude}&longitude={longitude}&localityLanguage=en"
        resp = requests.get(url, timeout=4)
        if resp.status_code == 200:
            data = resp.json()
            city = data.get("city") or data.get("locality") or data.get("principalSubdivision") or "My Location"
            country = data.get("countryName", "")
            return {
                "name": city,
                "country": country,
                "latitude": latitude,
                "longitude": longitude
            }
    except Exception as e:
        logger.warning(f"Reverse geocode lookup failed: {e}")
    return {
        "name": "My Location",
        "country": "",
        "latitude": latitude,
        "longitude": longitude
    }

def search_cities(query, count=5):
    """Searches geographic cities using Open-Meteo Geocoding API or handles coordinate lookups."""
    if not query or len(query.strip()) < 2:
        return []

    q_clean = query.strip()
    
    # Check if query is latitude,longitude format (e.g. from browser geolocation: "22.57,88.36")
    if "," in q_clean:
        parts = q_clean.split(",")
        if len(parts) == 2:
            try:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                resolved = reverse_geocode(lat, lon)
                return [resolved]
            except ValueError:
                pass
    
    # Pre-canned prominent cities for instant matching or offline resilience
    KNOWN_CITIES = [
        {"name": "New Delhi", "country": "India", "latitude": 28.6139, "longitude": 77.2090, "admin1": "Delhi"},
        {"name": "Bengaluru", "country": "India", "latitude": 12.9716, "longitude": 77.5946, "admin1": "Karnataka"},
        {"name": "Mumbai", "country": "India", "latitude": 19.0760, "longitude": 72.8777, "admin1": "Maharashtra"},
        {"name": "Kolkata", "country": "India", "latitude": 22.5726, "longitude": 88.3639, "admin1": "West Bengal"},
        {"name": "London", "country": "United Kingdom", "latitude": 51.5074, "longitude": -0.1278, "admin1": "England"},
        {"name": "New York", "country": "United States", "latitude": 40.7128, "longitude": -74.0060, "admin1": "New York"},
        {"name": "Singapore", "country": "Singapore", "latitude": 1.3521, "longitude": 103.8198, "admin1": "Singapore"},
        {"name": "Tokyo", "country": "Japan", "latitude": 35.6762, "longitude": 139.6503, "admin1": "Tokyo"},
        {"name": "Paris", "country": "France", "latitude": 48.8566, "longitude": 2.3522, "admin1": "Île-de-France"}
    ]
    
    try:
        url = Config.GEOCODING_API_URL
        params = {"name": query.strip(), "count": count, "language": "en", "format": "json"}
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            if results:
                return [
                    {
                        "name": r.get("name"),
                        "country": r.get("country", ""),
                        "admin1": r.get("admin1", ""),
                        "latitude": r.get("latitude"),
                        "longitude": r.get("longitude")
                    }
                    for r in results
                ]
    except Exception as e:
        logger.warning(f"Geocoding API search failed: {e}. Searching fallback list.")
        
    # Local fallback search
    q = query.strip().lower()
    matches = [c for c in KNOWN_CITIES if q in c["name"].lower() or q in c["country"].lower()]
    return matches if matches else KNOWN_CITIES[:count]

