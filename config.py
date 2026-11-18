import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "pranvyra_hyperlocal_air_secret_key_2026")
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, "database", "pranvyra.db")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # Open-Meteo Endpoints (Free, no key required)
    AIR_QUALITY_API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
    WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
    GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
    
    # Default Coordinates (New Delhi, a global benchmark for urban air monitoring)
    DEFAULT_LAT = 28.6139
    DEFAULT_LON = 77.2090
    DEFAULT_CITY = "New Delhi"

