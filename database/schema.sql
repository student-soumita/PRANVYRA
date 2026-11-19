-- PRANVYRA Relational Database Schema
-- Mandatory Authentication & Strict User Data Isolation
-- Every authenticated user owns their private environmental intelligence,
-- chat history, daily routines, receipts, and Air-Twin models.

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    username TEXT,
    password_hash TEXT NOT NULL,
    display_name TEXT NOT NULL,
    language_pref TEXT DEFAULT 'en', -- 'en', 'hi', 'bn'
    city TEXT DEFAULT 'Select Your City',
    latitude REAL,
    longitude REAL,
    commute_distance_km REAL DEFAULT 10.0,
    primary_transport TEXT DEFAULT 'public_transit',
    outdoor_hours TEXT DEFAULT '1-2 hours',
    work_schedule TEXT DEFAULT 'Standard Day',
    ventilation_type TEXT DEFAULT 'natural',
    cooking_fuel TEXT DEFAULT 'lpg',
    green_points INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_routines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    visitor_id TEXT,
    routine_date TEXT NOT NULL,
    time_slot TEXT NOT NULL, -- 'morning', 'afternoon', 'evening'
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    priority TEXT NOT NULL, -- 'high', 'medium', 'low'
    action_type TEXT,       -- 'commute', 'indoor', 'health', 'energy', 'outdoor'
    is_completed INTEGER DEFAULT 0,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS indoor_air_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    visitor_id TEXT,
    room_size TEXT,
    occupants INTEGER,
    ventilation TEXT,
    cooking_fuel TEXT,
    has_pets INTEGER DEFAULT 0,
    dust_level TEXT DEFAULT 'moderate',
    smoking_exposure INTEGER DEFAULT 0,
    has_air_purifier INTEGER DEFAULT 0,
    overall_score INTEGER,
    risk_level TEXT,
    recommendations_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS breath_routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    visitor_id TEXT,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    distance_km REAL NOT NULL,
    travel_time_mins INTEGER,
    recommended_mode TEXT NOT NULL,
    baseline_emissions_kg REAL NOT NULL,
    recommended_emissions_kg REAL NOT NULL,
    emissions_saved_kg REAL NOT NULL,
    air_quality_context TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS life_switches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    visitor_id TEXT,
    switch_key TEXT NOT NULL,
    category TEXT NOT NULL,
    current_habit TEXT NOT NULL,
    alternative_habit TEXT NOT NULL,
    baseline_emissions_kg REAL NOT NULL,
    alternative_emissions_kg REAL NOT NULL,
    savings_kg REAL NOT NULL,
    methodology TEXT NOT NULL,
    assumptions TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS impact_receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    visitor_id TEXT,
    decision_title TEXT NOT NULL,
    before_desc TEXT NOT NULL,
    after_desc TEXT NOT NULL,
    savings_kg REAL NOT NULL,
    why_it_matters TEXT NOT NULL,
    methodology TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS impact_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    visitor_id TEXT,
    action_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    co2_saved_kg REAL DEFAULT 0.0,
    energy_saved_kwh REAL DEFAULT 0.0,
    waste_reduced_kg REAL DEFAULT 0.0,
    points_earned INTEGER DEFAULT 10,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS community_challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL, -- 'transport', 'indoor', 'waste', 'energy'
    points INTEGER NOT NULL,
    duration_days INTEGER DEFAULT 7,
    badge_name TEXT,
    badge_icon TEXT
);

CREATE TABLE IF NOT EXISTS user_challenge_participation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    visitor_id TEXT,
    challenge_id INTEGER NOT NULL,
    status TEXT DEFAULT 'in_progress', -- 'in_progress', 'completed'
    progress_pct INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(challenge_id) REFERENCES community_challenges(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    visitor_id TEXT,
    role TEXT NOT NULL, -- 'user', 'assistant'
    message TEXT NOT NULL,
    language TEXT DEFAULT 'en',
    structured_card_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
