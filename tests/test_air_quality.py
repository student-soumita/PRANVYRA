import unittest
from services.air_quality import (
    calculate_sub_index,
    get_aqi_category_info,
    get_live_air_quality,
    PM25_BREAKPOINTS,
    PM10_BREAKPOINTS
)

class TestAirQuality(unittest.TestCase):

    def test_calculate_sub_index_pm25_good(self):
        # 0 - 12.0 µg/m³ -> 0 - 50 Good
        idx, cat, color = calculate_sub_index(6.0, PM25_BREAKPOINTS)
        self.assertEqual(idx, 25)
        self.assertEqual(cat, "Good")

    def test_calculate_sub_index_pm25_moderate(self):
        # 12.1 - 35.4 µg/m³ -> 51 - 100 Moderate
        idx, cat, color = calculate_sub_index(23.75, PM25_BREAKPOINTS)
        self.assertTrue(51 <= idx <= 100)
        self.assertEqual(cat, "Moderate")

    def test_calculate_sub_index_pm25_unhealthy(self):
        # 55.5 - 150.4 µg/m³ -> 151 - 200 Unhealthy
        idx, cat, color = calculate_sub_index(88.5, PM25_BREAKPOINTS)
        self.assertTrue(151 <= idx <= 200)
        self.assertEqual(cat, "Unhealthy")

    def test_get_aqi_category_info(self):
        good = get_aqi_category_info(40)
        self.assertEqual(good["category"], "Good")
        self.assertEqual(good["alert_level"], "Low")

        haz = get_aqi_category_info(350)
        self.assertEqual(haz["category"], "Hazardous")
        self.assertEqual(haz["alert_level"], "Emergency")

    def test_live_air_quality_offline_state(self):
        # When network is unreachable or dummy coords, returns clean unavailable state (NO fake numbers)
        data = get_live_air_quality(None, None)
        self.assertFalse(data.get("is_available", True))
        self.assertIn("location", data.get("message", "").lower())
        self.assertEqual(data.get("calculation_standard"), "US EPA AQI Standard (40 CFR Part 58)")

if __name__ == "__main__":
    unittest.main()
