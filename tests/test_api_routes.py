import unittest
import json
import uuid
from app import create_app
from database.db import get_db_connection

class TestMandatoryAuthAndApiRoutes(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_01_unauthenticated_access_is_strictly_blocked(self):
        """Verifies mandatory authentication redirects web visitors and returns 401 for APIs."""
        # Root route redirects to /login
        resp_root = self.client.get("/")
        self.assertEqual(resp_root.status_code, 302)
        self.assertIn("/login", resp_root.headers.get("Location", ""))

        # Direct navigation to protected pages redirects to /login
        resp_dash = self.client.get("/dashboard")
        self.assertEqual(resp_dash.status_code, 302)
        self.assertIn("/login", resp_dash.headers.get("Location", ""))

        # Protected API endpoints return 401
        for endpoint in [
            "/api/dashboard/overview",
            "/api/assistant/chat",
            "/api/breath-route/plan",
            "/api/life-switch/catalog",
            "/api/user/air-twin",
            "/api/impact/summary",
            "/api/planner/routine"
        ]:
            resp = self.client.get(endpoint)
            self.assertEqual(resp.status_code, 401, f"Endpoint {endpoint} was not blocked!")
            data = resp.get_json()
            self.assertIn("error", data)

    def test_02_login_page_renders_cosmic_auth_interface(self):
        """Verifies the login page renders properly with brand elements and trilingual support."""
        resp = self.client.get("/login")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"PRANVYRA", resp.data)
        self.assertIn(b"Every Breath. A Better Tomorrow.", resp.data)
        self.assertIn(b"auth_security_badge", resp.data)
        self.assertIn(b"data-lang=\"hi\"", resp.data)
        self.assertIn(b"data-lang=\"bn\"", resp.data)

    def test_03_registration_and_login_workflow(self):
        """Verifies user registration, password hashing, and login/logout."""
        unique_id = uuid.uuid4().hex[:8]
        test_email = f"citizen_auth_{unique_id}@pranvyra.org"
        test_password = "SecurePassword2026!"
        test_name = "Auth Test Citizen"

        # 1. Register new user
        reg_payload = {
            "email": test_email,
            "password": test_password,
            "full_name": test_name
        }
        reg_resp = self.client.post("/api/auth/register", json=reg_payload)
        self.assertIn(reg_resp.status_code, [200, 201])
        reg_data = reg_resp.get_json()
        self.assertTrue(reg_data["success"])
        self.assertEqual(reg_data["user"]["email"], test_email)

        # Verify password in DB is hashed with pbkdf2:sha256 and NOT plaintext
        conn = get_db_connection()
        try:
            row = conn.execute("SELECT password_hash FROM users WHERE email = ?", (test_email,)).fetchone()
            self.assertIsNotNone(row)
            pw_hash = row["password_hash"]
            self.assertTrue(pw_hash.startswith("pbkdf2:sha256:"), f"Invalid hash: {pw_hash}")
            self.assertNotIn(test_password, pw_hash)
        finally:
            conn.close()

        # 2. Duplicate registration rejected
        dup_resp = self.client.post("/api/auth/register", json=reg_payload)
        self.assertIn(dup_resp.status_code, [400, 409])

        # 3. Test /api/auth/me returns authenticated user
        me_resp = self.client.get("/api/auth/me")
        self.assertEqual(me_resp.status_code, 200)
        self.assertEqual(me_resp.get_json()["user"]["email"], test_email)

        # 4. Logout clears session
        logout_resp = self.client.post("/api/auth/logout")
        self.assertEqual(logout_resp.status_code, 200)

        # Me returns 401 after logout
        me_after = self.client.get("/api/auth/me")
        self.assertEqual(me_after.status_code, 401)

        # 5. Invalid login fails
        bad_login = self.client.post("/api/auth/login", json={"identifier": test_email, "password": "WrongPassword!"})
        self.assertEqual(bad_login.status_code, 401)

        # 6. Valid login succeeds
        good_login = self.client.post("/api/auth/login", json={"identifier": test_email, "password": test_password})
        self.assertEqual(good_login.status_code, 200)
        self.assertTrue(good_login.get_json()["success"])

    def test_04_authenticated_features_and_multilingual_chat(self):
        """Verifies full platform functionality for authenticated users across EN, HI, BN."""
        unique_id = uuid.uuid4().hex[:8]
        user_email = f"multilingual_{unique_id}@pranvyra.org"
        reg_resp = self.client.post("/api/auth/register", json={
            "email": user_email,
            "password": "Password123!",
            "full_name": "Multilingual Tester"
        })
        self.assertIn(reg_resp.status_code, [200, 201])

        # 1. Dashboard overview
        resp = self.client.get("/api/dashboard/overview?lat=28.6139&lon=77.2090&city=New%20Delhi")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertIn("air_quality", data)
        self.assertIn("weather", data)

        # 2. Multilingual AI Companion (English)
        en_resp = self.client.post("/api/assistant/chat", json={
            "message": "Analyze my air quality.",
            "language": "en"
        })
        self.assertEqual(en_resp.status_code, 200)
        en_data = en_resp.get_json()
        self.assertTrue(en_data["success"])
        self.assertEqual(en_data["language"], "en")

        # 3. Multilingual AI Companion (Hindi)
        hi_resp = self.client.post("/api/assistant/chat", json={
            "message": "आज की वायु गुणवत्ता की व्याख्या करें।",
            "language": "hi"
        })
        self.assertEqual(hi_resp.status_code, 200)
        hi_data = hi_resp.get_json()
        self.assertTrue(hi_data["success"])
        self.assertEqual(hi_data["language"], "hi")

        # 4. Multilingual AI Companion (Bengali)
        bn_resp = self.client.post("/api/assistant/chat", json={
            "message": "আজকের বাতাসের মান কেমন?",
            "language": "bn"
        })
        self.assertEqual(bn_resp.status_code, 200)
        bn_data = bn_resp.get_json()
        self.assertTrue(bn_data["success"])
        self.assertEqual(bn_data["language"], "bn")

        # 5. BreathRoute planning & commitment
        plan_resp = self.client.post("/api/breath-route/plan", json={
            "origin": "Connaught Place",
            "destination": "Cyber City Gurgaon",
            "departure_time": "Morning Rush (08:30)",
            "manual_distance": 25.0
        })
        self.assertEqual(plan_resp.status_code, 200)

        commit_resp = self.client.post("/api/breath-route/commit-trip", json={
            "origin": "Connaught Place",
            "destination": "Cyber City Gurgaon",
            "mode_name": "Electric Metro",
            "distance_km": 25.0,
            "savings_kg": 3.55
        })
        self.assertEqual(commit_resp.status_code, 200)
        commit_data = commit_resp.get_json()
        self.assertTrue(commit_data["success"])
        self.assertIn("PRAN-RCPT-", commit_data["receipt"]["receipt_id"])

    def test_05_strict_user_data_isolation(self):
        """Verifies User A's data (receipts, routines, profile) is strictly isolated from User B."""
        unique_a = uuid.uuid4().hex[:8]
        unique_b = uuid.uuid4().hex[:8]

        # Create client for User A
        client_a = self.app.test_client()
        reg_a = client_a.post("/api/auth/register", json={
            "email": f"user_alpha_{unique_a}@pranvyra.org",
            "password": "PasswordAlpha123!",
            "full_name": "User Alpha"
        })
        self.assertIn(reg_a.status_code, [200, 201])

        # User A updates profile and commits an impact receipt
        client_a.post("/api/user/profile", json={"city": "Kolkata", "commute_distance_km": 18.0})
        rcpt_resp = client_a.post("/api/breath-route/commit-trip", json={
            "origin": "Salt Lake",
            "destination": "Park Street",
            "mode_name": "Electric Metro",
            "distance_km": 14.0,
            "savings_kg": 2.1
        })
        self.assertEqual(rcpt_resp.status_code, 200)
        receipt_a_id = rcpt_resp.get_json()["receipt"]["receipt_id"]

        # User A loads/generates their daily routine
        tasks_a_resp = client_a.get("/api/planner/today")
        self.assertEqual(tasks_a_resp.status_code, 200)
        tasks_a = tasks_a_resp.get_json().get("tasks", [])
        self.assertGreater(len(tasks_a), 0)
        task_a_id = tasks_a[0]["id"]

        # Create client for User B
        client_b = self.app.test_client()
        reg_b = client_b.post("/api/auth/register", json={
            "email": f"user_beta_{unique_b}@pranvyra.org",
            "password": "PasswordBeta123!",
            "full_name": "User Beta"
        })
        self.assertIn(reg_b.status_code, [200, 201])

        # 1. User B checks receipts — MUST NOT see User A's receipt
        receipts_b = client_b.get("/api/impact/receipts").get_json()["receipts"]
        receipt_ids_b = [r["receipt_id"] for r in receipts_b]
        self.assertNotIn(receipt_a_id, receipt_ids_b, "CRITICAL: User B saw User A's impact receipt!")

        # 2. User B tries to toggle User A's task — MUST be rejected (404)
        toggle_resp = client_b.post("/api/planner/toggle", json={"task_id": task_a_id})
        self.assertEqual(toggle_resp.status_code, 404, "CRITICAL: User B was able to toggle User A's task!")

        # 3. User B checks impact summary — User B has 0 savings despite User A having 2.1 kg
        metrics_b = client_b.get("/api/impact/summary").get_json()["metrics"]
        self.assertEqual(metrics_b["co2_saved_kg"], 0.0)

if __name__ == "__main__":
    unittest.main()

if __name__ == "__main__":
    unittest.main()
