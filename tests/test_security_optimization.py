"""
Unit Tests for PRANVYRA Security, Authentication Integrity & Telemetry Caching
"""
import unittest
from app import create_app
from database.db import get_user_by_id, create_user
from services.air_quality import get_live_air_quality, _AQI_CACHE
from services.weather import get_live_weather, _WEATHER_CACHE

class TestSecurityAndOptimization(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_unauthenticated_api_access_blocked(self):
        """Protected API endpoints must reject unauthenticated requests with 401."""
        endpoints = [
            "/api/dashboard/overview",
            "/api/assistant/chat",
            "/api/planner/today",
            "/api/indoor/check",
            "/api/impact/summary",
            "/api/user/profile",
            "/api/breath-route/plan",
            "/api/life-switch/calculate"
        ]
        for ep in endpoints:
            res = self.client.get(ep) if ep != "/api/assistant/chat" else self.client.post(ep, json={"message": "test"})
            self.assertEqual(res.status_code, 401, f"Expected 401 for unauthenticated {ep}")
            data = res.get_json()
            self.assertFalse(data.get("authenticated", True))

    def test_x_user_id_header_bypass_blocked(self):
        """Header spoofing using X-User-Id must NOT grant access."""
        res = self.client.get("/api/dashboard/overview", headers={"X-User-Id": "1"})
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertFalse(data.get("authenticated", True))

    def test_telemetry_cache_reusability(self):
        """Environmental telemetry caching prevents duplicate external requests."""
        _AQI_CACHE.clear()
        mock_data = {"success": True, "aqi": 85, "is_available": True}
        cache_key = (28.61, 77.20)
        _AQI_CACHE[cache_key] = {"data": mock_data, "timestamp": 9999999999}
        
        # Retrieval should pull directly from cache without network
        res = get_live_air_quality(28.61, 77.20)
        self.assertEqual(res, mock_data)

    def test_weather_cache_reusability(self):
        """Weather caching prevents duplicate external requests."""
        _WEATHER_CACHE.clear()
        mock_data = {"success": True, "temperature": 26.5, "is_fallback": False}
        cache_key = (28.61, 77.20)
        _WEATHER_CACHE[cache_key] = {"data": mock_data, "timestamp": 9999999999}
        
        # Retrieval should pull directly from cache without network
        res = get_live_weather(28.61, 77.20)
        self.assertEqual(res, mock_data)

if __name__ == '__main__':
    unittest.main()
