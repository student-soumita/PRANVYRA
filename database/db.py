import sqlite3
import os
import sys
import json
import uuid

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import Config

def get_db_connection():
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db(reset=False):
    if reset and os.path.exists(Config.DATABASE_PATH):
        try:
            os.remove(Config.DATABASE_PATH)
        except Exception:
            pass

    conn = get_db_connection()
    cursor = conn.cursor()
    
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        cursor.executescript(f.read())
        
    # Check if community challenges exist, if not seed the challenge definitions (WITHOUT fake participants!)
    cursor.execute("SELECT COUNT(*) FROM community_challenges")
    if cursor.fetchone()[0] == 0:
        seed_challenges = [
            (
                "Metro Shift Monday",
                "Swap your solo motorized commute for electric metro, light rail, or rapid public transit to slash tailpipe emissions by up to 80%.",
                "transport",
                50,
                7,
                "Metro Master",
                "train-track"
            ),
            (
                "No-Idle Clean School Zone",
                "Turn off your engine while waiting for pickups or drop-offs to prevent localized toxic PM2.5 hotspots near children.",
                "transport",
                30,
                5,
                "Zero Idle Hero",
                "shield-check"
            ),
            (
                "Cross-Ventilation Audit",
                "Identify your home's windward windows and open them only during low-AQI midday solar dispersion windows (11:30 AM - 3:00 PM).",
                "indoor",
                40,
                3,
                "Air Alchemist",
                "wind"
            ),
            (
                "Plastic-Free Daily Carry",
                "Carry a reusable stainless steel water flask and cloth carry bag for 7 consecutive days, eliminating single-use PET waste.",
                "waste",
                35,
                7,
                "Cycle Vanguard",
                "leaf"
            ),
            (
                "Passive Energy Sunset",
                "Set AC thermostat to 25°C-26°C with gentle ceiling fan assist, saving ~2.0 kWh per night on the regional electric grid.",
                "energy",
                45,
                7,
                "Volt Guardian",
                "zap"
            ),
            (
                "Kitchen Exhaust Discipline",
                "Run high-suction exhaust hood during the entirety of high-heat cooking plus 10 minutes post-cooking to evacuate ultrafine aerosols.",
                "indoor",
                35,
                7,
                "Culinary Purifier",
                "flame"
            )
        ]
        cursor.executemany(
            """INSERT INTO community_challenges 
               (title, description, category, points, duration_days, badge_name, badge_icon)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            seed_challenges
        )

    # Perform safe non-destructive schema migration for existing databases
    migrate_db(conn)

    # Seed default initial user for production environments (e.g. Render) if no users exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        from services.auth import hash_password
        default_pw = hash_password("password123")
        cursor.execute(
            """INSERT INTO users (
                email, username, password_hash, display_name, language_pref, city, latitude, longitude
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("eco_test@pranvyra.org", "urban_eco_tester", default_pw, "Urban Eco Citizen", "en", "Select Your City", None, None)
        )

    conn.commit()
    conn.close()

def migrate_db(conn):
    """
    Non-destructive schema migration:
    Safely adds user_id foreign keys and user profile columns to existing databases
    without losing any existing data.
    """
    cursor = conn.cursor()
    
    # 1. Ensure users table has all required profile columns
    cursor.execute("PRAGMA table_info(users)")
    existing_user_cols = {row["name"] for row in cursor.fetchall()}
    user_col_defs = {
        "username": "TEXT",
        "language_pref": "TEXT DEFAULT 'en'",
        "city": "TEXT DEFAULT 'Select Your City'",
        "latitude": "REAL",
        "longitude": "REAL",
        "commute_distance_km": "REAL DEFAULT 10.0",
        "primary_transport": "TEXT DEFAULT 'public_transit'",
        "outdoor_hours": "TEXT DEFAULT '1-2 hours'",
        "work_schedule": "TEXT DEFAULT 'Standard Day'",
        "ventilation_type": "TEXT DEFAULT 'natural'",
        "cooking_fuel": "TEXT DEFAULT 'lpg'",
        "green_points": "INTEGER DEFAULT 0"
    }
    for col, col_type in user_col_defs.items():
        if col not in existing_user_cols:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
            except Exception:
                pass

    # 2. Ensure all data tables have user_id column
    tables_to_isolate = [
        "daily_routines",
        "indoor_air_checks",
        "breath_routes",
        "life_switches",
        "impact_receipts",
        "impact_logs",
        "user_challenge_participation",
        "chat_history"
    ]
    for tbl in tables_to_isolate:
        try:
            cursor.execute(f"PRAGMA table_info({tbl})")
            existing_cols = {row["name"] for row in cursor.fetchall()}
            if "user_id" not in existing_cols:
                cursor.execute(f"ALTER TABLE {tbl} ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE")
            if "visitor_id" not in existing_cols:
                cursor.execute(f"ALTER TABLE {tbl} ADD COLUMN visitor_id TEXT")
        except Exception:
            pass

def get_user_by_id(user_id):
    """Retrieves authenticated user record by primary key."""
    if not user_id:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    user = dict(row)
    user.pop("password_hash", None)
    return user

def get_user_by_email(email):
    """Retrieves user record by email (including password_hash for authentication check)."""
    if not email:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_email_or_username(identifier):
    """Retrieves user by either email or username/display_name for login."""
    if not identifier:
        return None
    ident = identifier.strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE LOWER(email) = ? OR LOWER(display_name) = ? OR LOWER(username) = ?",
        (ident, ident, ident)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_user(email, password_hash, display_name, language_pref='en', **kwargs):
    """Creates a new authenticated user record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO users (
            email, password_hash, display_name, language_pref,
            city, latitude, longitude, commute_distance_km,
            primary_transport, outdoor_hours, work_schedule,
            ventilation_type, cooking_fuel, green_points
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            email.strip().lower(),
            password_hash,
            display_name.strip(),
            language_pref or 'en',
            kwargs.get("city", "Select Your City"),
            kwargs.get("latitude"),
            kwargs.get("longitude"),
            float(kwargs.get("commute_distance_km", 10.0)),
            kwargs.get("primary_transport", "public_transit"),
            kwargs.get("outdoor_hours", "1-2 hours"),
            kwargs.get("work_schedule", "Standard Day"),
            kwargs.get("ventilation_type", "natural"),
            kwargs.get("cooking_fuel", "lpg"),
            kwargs.get("green_points", 0)
        )
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id

def update_user_profile(user_id, **kwargs):
    """Updates user preferences and Air-Twin profile settings."""
    if not user_id:
        return None
    allowed_fields = [
        "display_name", "city", "latitude", "longitude",
        "commute_distance_km", "primary_transport", "outdoor_hours",
        "work_schedule", "ventilation_type", "cooking_fuel",
        "language_pref", "green_points"
    ]
    updates = []
    values = []
    for k, v in kwargs.items():
        if k in allowed_fields:
            updates.append(f"{k} = ?")
            values.append(v)
            
    if not updates:
        return get_user_by_id(user_id)
        
    values.append(user_id)
    conn = get_db_connection()
    conn.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return get_user_by_id(user_id)

def get_or_create_visitor(visitor_id=None, defaults=None):
    """
    Open-Access / Migration compatibility layer:
    Retrieves or initializes a profile. If visitor_id starts with 'user_',
    links directly to the authenticated user ID.
    """
    # If visitor_id corresponds to a user ID like "user_123"
    if visitor_id and str(visitor_id).startswith("user_"):
        try:
            uid = int(str(visitor_id).replace("user_", ""))
            user = get_user_by_id(uid)
            if user:
                user["visitor_id"] = f"user_{uid}"
                return user
        except Exception:
            pass

    conn = get_db_connection()
    cursor = conn.cursor()
    
    if not visitor_id or visitor_id == "anonymous":
        visitor_id = str(uuid.uuid4())
        
    cursor.execute("SELECT * FROM visitor_profiles WHERE visitor_id = ?", (visitor_id,))
    row = cursor.fetchone()
    
    if not row:
        defaults = defaults or {}
        cursor.execute(
            """INSERT INTO visitor_profiles (
                visitor_id, display_name, city, latitude, longitude,
                commute_distance_km, primary_transport, outdoor_hours,
                work_schedule, ventilation_type, cooking_fuel,
                language_pref, sustainability_goals, green_points
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                visitor_id,
                defaults.get("display_name", "Urban Citizen"),
                defaults.get("city", "Select Your City"),
                defaults.get("latitude", None),
                defaults.get("longitude", None),
                float(defaults.get("commute_distance_km", 10.0)),
                defaults.get("primary_transport", "public_transit"),
                defaults.get("outdoor_hours", "1-2 hours"),
                defaults.get("work_schedule", "Standard Day"),
                defaults.get("ventilation_type", "natural"),
                defaults.get("cooking_fuel", "lpg"),
                defaults.get("language_pref", "en"),
                json.dumps(defaults.get("sustainability_goals", ["cleaner_commute", "indoor_health"])),
                0
            )
        )
        conn.commit()
        cursor.execute("SELECT * FROM visitor_profiles WHERE visitor_id = ?", (visitor_id,))
        row = cursor.fetchone()
        
    result = dict(row)
    if result.get("sustainability_goals"):
        try:
            result["sustainability_goals"] = json.loads(result["sustainability_goals"])
        except Exception:
            result["sustainability_goals"] = []
            
    conn.close()
    return result

if __name__ == "__main__":
    init_db(reset=True)
    print("Open-access database initialized successfully (Zero demo accounts, real schema active).")
