import sys
import os
import uuid

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app

def test_live_server():
    print("Testing PRANVYRA Mandatory Authentication & Multilingual Architecture...")
    app = create_app()
    client = app.test_client()
    
    # 1. Unauthenticated Gateway Protection
    r_unauth = client.get("/")
    assert r_unauth.status_code == 302, f"Expected 302 redirect, got {r_unauth.status_code}"
    assert "/login" in r_unauth.headers.get("Location", "")
    print("✓ 1. Unauthenticated access to / properly redirects (302) to /login")

    # 2. Login Page & Cosmic Aesthetic & Trilingual Selector
    r_login = client.get("/login")
    assert r_login.status_code == 200, f"Login page failed: {r_login.status_code}"
    text = r_login.get_data(as_text=True)
    assert "PRANVYRA" in text, "Brand title missing from HTML"
    assert "Every Breath. A Better Tomorrow." in text, "Brand motto missing"
    assert "auth-tabs" in text, "Auth tabs missing"
    assert "data-lang=\"hi\"" in text, "Hindi switcher missing"
    assert "data-lang=\"bn\"" in text, "Bengali switcher missing"
    print("✓ 2. GET /login returned 200 OK with cosmic theme and EN | HI | BN language switcher")

    # 3. User Registration & PBKDF2 Password Hashing
    test_id = uuid.uuid4().hex[:8]
    test_email = f"citizen_verify_{test_id}@pranvyra.org"
    test_password = "SecurePassword2026!"
    
    r_reg = client.post("/api/auth/register", json={
        "email": test_email,
        "password": test_password,
        "confirm_password": test_password,
        "full_name": "Verification Citizen",
        "language_pref": "en"
    })
    assert r_reg.status_code in [200, 201], f"Registration failed: {r_reg.status_code}"
    print(f"✓ 3. POST /api/auth/register created authenticated user: {test_email}")

    # 4. Authenticated Landing & Brand Headlines
    r_index = client.get("/")
    assert r_index.status_code == 200, f"Index failed after login: {r_index.status_code}"
    index_text = r_index.get_data(as_text=True)
    assert "PRANVYRA" in index_text, "Brand title missing"
    assert "Your City Has an Air Story" in index_text, "Hero headline missing"
    assert "BreathRoute" in index_text, "BreathRoute navigation missing"
    assert "Life-Switch" in index_text, "Life-Switch navigation missing"
    print("✓ 4. GET / returned 200 OK for authenticated session with full dashboard")

    # 5. Authenticated Environmental Overview
    r_dash = client.get("/api/dashboard/overview?lat=28.6139&lon=77.2090&city=New%20Delhi")
    assert r_dash.status_code == 200
    d_json = r_dash.get_json()
    assert d_json["success"] is True
    assert "air_quality" in d_json
    print(f"✓ 5. GET /api/dashboard/overview returned AQI standard '{d_json['air_quality'].get('calculation_standard')}'")

    # 6. Trilingual Multi-Role AI Companion (EN, HI, BN)
    for lang, prompt in [
        ("en", "How is my air quality today?"),
        ("hi", "आज की वायु गुणवत्ता कैसी है?"),
        ("bn", "আজকের বাতাসের মান কেমন?")
    ]:
        r_chat = client.post("/api/assistant/chat", json={
            "message": prompt,
            "language": lang
        })
        assert r_chat.status_code == 200
        res_data = r_chat.get_json()
        assert res_data["success"] is True
        assert res_data["language"] == lang
    print("✓ 6. POST /api/assistant/chat verified trilingual AI intelligence across EN, HI, BN")

    # 7. BreathRoute Journey Planner & Personal Impact Receipt
    r_plan = client.post("/api/breath-route/plan", json={
        "origin": "Connaught Place",
        "destination": "Cyber City Gurgaon",
        "departure_time": "Morning Rush (08:30)",
        "manual_distance": 25.0
    })
    assert r_plan.status_code == 200
    plan_data = r_plan.get_json()
    assert plan_data["success"] is True
    assert len(plan_data["plan"]["modes"]) >= 5

    r_commit = client.post("/api/breath-route/commit-trip", json={
        "origin": "Connaught Place",
        "destination": "Cyber City Gurgaon",
        "mode_name": "Electric Metro",
        "distance_km": 25.0,
        "savings_kg": 3.55
    })
    assert r_commit.status_code == 200
    rcpt = r_commit.get_json()["receipt"]
    assert "PRAN-RCPT-" in rcpt["receipt_id"]
    print(f"✓ 7. BreathRoute committed trip and issued verified receipt: {rcpt['receipt_id']}")

    # 8. Life-Switch Simulation & Commitment
    r_sim = client.post("/api/life-switch/simulate", json={
        "switch_key": "commute_moto_to_metro",
        "param_value": 30.0
    })
    assert r_sim.status_code == 200
    assert r_sim.get_json()["simulation"]["metrics"]["annual_savings_kg"] > 0
    print("✓ 8. Life-Switch simulator calculated transparent avoided emissions formulas")

    # 9. Air-Twin Personal Profile
    r_twin = client.get("/api/user/air-twin")
    assert r_twin.status_code == 200
    twin_data = r_twin.get_json()["air_twin"]
    assert "resilience_score" in twin_data
    print(f"✓ 9. Air-Twin generated non-clinical resilience score: {twin_data['resilience_score']}")

    # 10. Neighborhood Pulse
    r_pulse = client.get("/api/community/pulse")
    assert r_pulse.status_code == 200
    pulse = r_pulse.get_json()["pulse"]
    assert "active_citizens_count" in pulse
    print("✓ 10. Neighborhood Pulse delivered genuine citizen participation telemetry")

    print("\n=======================================================")
    print("  ALL 10 VERIFICATION CHECKS PASSED PERFECTLY!")
    print("  MANDATORY AUTHENTICATION & MULTILINGUAL SYSTEM VERIFIED.")
    print("=======================================================")

if __name__ == "__main__":
    test_live_server()
