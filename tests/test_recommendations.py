import unittest
from services.recommendation_engine import (
    generate_airwise_action,
    calculate_breath_budget,
    generate_smart_daily_planner,
    assess_indoor_air,
    get_sustainable_alternatives_catalog
)

class TestRecommendations(unittest.TestCase):

    def test_generate_airwise_action_high_aqi(self):
        aqi_data = {"aqi": 180, "category": "Unhealthy"}
        weather = {"temperature": 24, "wind_speed": 6.5}
        user = {"primary_transport": "motorcycle", "outdoor_hours": "08:00 - 09:30"}
        
        action = generate_airwise_action(aqi_data, weather, user)
        self.assertEqual(action["urgency"], "High")
        self.assertIn("reschedule", action["title"].lower())
        self.assertTrue("EPA" in action["source"] or "WHO" in action["source"])

    def test_calculate_breath_budget(self):
        res = calculate_breath_budget(aqi=160, outdoor_hours_str="3.0", transport="motorcycle", ventilation="natural")
        self.assertGreater(res["budget_used_pct"], 30.0)
        self.assertIn("disclaimer", res)
        self.assertIn("NOT a clinical measurement", res["disclaimer"])

    def test_generate_smart_daily_planner(self):
        tasks = generate_smart_daily_planner(160, {"temperature": 24}, {"primary_transport": "motorcycle"})
        self.assertGreaterEqual(len(tasks), 4)
        slots = [t["time_slot"] for t in tasks]
        self.assertIn("morning", slots)
        self.assertIn("afternoon", slots)
        self.assertIn("evening", slots)

    def test_assess_indoor_air_scoring(self):
        clean_quiz = {
            "room_size": "medium",
            "occupants": 2,
            "ventilation": "mechanical",
            "cooking_fuel": "electric",
            "has_pets": 0,
            "dust_level": "low",
            "smoking_exposure": 0,
            "has_air_purifier": 1
        }
        res_clean = assess_indoor_air(clean_quiz)
        self.assertGreaterEqual(res_clean["score"], 80)
        
        hazardous_quiz = {
            "room_size": "small",
            "occupants": 4,
            "ventilation": "poor",
            "cooking_fuel": "biomass",
            "has_pets": 1,
            "dust_level": "high",
            "smoking_exposure": 1,
            "has_air_purifier": 0
        }
        res_haz = assess_indoor_air(hazardous_quiz)
        self.assertLess(res_haz["score"], 50)
        self.assertIn("disclaimer", res_haz["scientific_disclaimer"].lower())

    def test_alternatives_catalog(self):
        alts = get_sustainable_alternatives_catalog()
        self.assertGreaterEqual(len(alts), 5)
        self.assertIn("suggested_alternative", alts[0])

if __name__ == "__main__":
    unittest.main()
