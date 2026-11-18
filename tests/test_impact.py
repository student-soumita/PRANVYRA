import unittest
from services.impact_calculator import (
    calculate_journey_emissions,
    compare_all_modes,
    simulate_commute_switch,
    get_cumulative_impact_metrics,
    EMISSION_FACTORS
)

class TestImpactCalculator(unittest.TestCase):
    
    def test_calculate_journey_emissions_petrol(self):
        # 10 km petrol car (170.5 g/km) -> 1.705 kg CO2
        res = calculate_journey_emissions(10.0, "petrol_car", passengers=1)
        self.assertEqual(res["distance_km"], 10.0)
        self.assertAlmostEqual(res["emissions_kg"], 1.705, places=3)
        self.assertEqual(res["factor_g_per_km"], 170.5)

    def test_calculate_journey_emissions_carpool(self):
        # Carpool across 3 passengers divides petrol factor: 170.5 / 3 = 56.83 g/pkm
        res = calculate_journey_emissions(10.0, "carpool", passengers=3)
        self.assertAlmostEqual(res["emissions_kg"], 0.568, places=2)
        
    def test_calculate_journey_emissions_zero_emission(self):
        res_bike = calculate_journey_emissions(15.0, "cycling")
        self.assertEqual(res_bike["emissions_kg"], 0.0)
        res_walk = calculate_journey_emissions(5.0, "walking")
        self.assertEqual(res_walk["emissions_kg"], 0.0)

    def test_compare_all_modes(self):
        res = compare_all_modes(14.5, "motorcycle")
        self.assertEqual(res["distance_km"], 14.5)
        self.assertEqual(len(res["comparison"]), 8)
        # Metro should have lower emissions than motorcycle
        metro_item = next(i for i in res["comparison"] if i["mode_key"] == "metro")
        moto_item = next(i for i in res["comparison"] if i["mode_key"] == "motorcycle")
        self.assertLess(metro_item["emissions_kg"], moto_item["emissions_kg"])
        self.assertGreater(metro_item["savings_kg"], 0)

    def test_simulate_commute_switch(self):
        # 14.5 km from motorcycle to metro
        sim = simulate_commute_switch(14.5, "motorcycle", "metro", daily_trips=2, working_days_per_year=240)
        self.assertGreater(sim["trip_savings_kg"], 0)
        self.assertGreater(sim["annual_savings_kg"], 100.0)
        self.assertGreater(sim["equiv_car_km_annual"], 500.0)
        self.assertGreater(sim["trees_equivalent_annual"], 5.0)

    def test_get_cumulative_impact_metrics(self):
        metrics = get_cumulative_impact_metrics(co2_saved_kg=10.0, energy_saved_kwh=5.0, waste_reduced_kg=2.0)
        self.assertEqual(metrics["co2_saved_kg"], 10.0)
        # 10 kg CO2 / 0.1705 kg/km = ~58.65 km
        self.assertAlmostEqual(metrics["equiv_car_km"], 58.7, places=1)
        self.assertAlmostEqual(metrics["grid_co2_avoided_kg"], 4.1, places=1)

if __name__ == "__main__":
    unittest.main()

