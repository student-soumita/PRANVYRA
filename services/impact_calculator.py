"""
PRANVYRA Environmental Impact & Green Commute Engine
Uses scientifically documented emission factors based on UK DESNZ/DEFRA 2023/2024 
and US EPA GHG Conversion Factors.
"""

# Emission Factors in grams of CO2 equivalent per passenger-kilometer (g CO2e / pkm)
# Reference: UK DESNZ / DEFRA GHG Conversion Factors for Company Reporting & US EPA Emission Factors Hub
EMISSION_FACTORS = {
    "petrol_car": {
        "name": "Private Petrol Car",
        "factor_g_per_km": 170.5, # Average medium petrol car
        "cost_per_km": 8.50,      # Fuel & maintenance estimate (INR / local equivalent)
        "description": "Standard internal combustion engine operating on unleaded gasoline."
    },
    "diesel_car": {
        "name": "Private Diesel Car",
        "factor_g_per_km": 168.0,
        "cost_per_km": 7.80,
        "description": "Compression-ignition diesel engine with higher localized particulate/NOx profile."
    },
    "motorcycle": {
        "name": "Motorcycle / Scooter",
        "factor_g_per_km": 103.2,
        "cost_per_km": 2.70,
        "description": "Typical four-stroke two-wheeler with single passenger occupancy."
    },
    "carpool": {
        "name": "Carpool (3 Passengers)",
        "factor_g_per_km": 56.8,  # 170.5 g / 3 passengers
        "cost_per_km": 2.85,
        "description": "Ride-sharing in a private car across 3 commuters, distributing tailpipe emissions."
    },
    "bus": {
        "name": "Public Transit Bus",
        "factor_g_per_km": 96.5,  # Average urban transit bus per passenger
        "cost_per_km": 1.50,
        "description": "City transit fleet operating at standard average passenger load capacity."
    },
    "metro": {
        "name": "Electric Metro / Subway",
        "factor_g_per_km": 28.5,  # High-efficiency electrified urban rail traction
        "cost_per_km": 2.20,
        "description": "Grade-separated electric rapid rail with zero direct roadside tailpipe emissions."
    },
    "cycling": {
        "name": "Bicycle",
        "factor_g_per_km": 0.0,   # Zero direct tailpipe emissions
        "cost_per_km": 0.0,
        "description": "Active human-powered mobility with zero combustion emissions."
    },
    "walking": {
        "name": "Walking",
        "factor_g_per_km": 0.0,
        "cost_per_km": 0.0,
        "description": "Zero direct tailpipe emissions and optimal cardio-respiratory health."
    }
}

# Grid emission factor: ~0.82 kg CO2 / kWh (Standard mixed regional urban electricity grid)
GRID_EMISSION_FACTOR_KG_PER_KWH = 0.82

# Equivalent car distance factor: 1 kg CO2 avoided ≈ 5.865 km of avoided petrol car driving (1 / 0.1705)
EQUIV_KM_PER_KG_CO2 = 5.865

# Plastic life-cycle footprint: 1 standard 500ml PET bottle ≈ 0.0828 kg CO2e
PET_BOTTLE_KG_CO2 = 0.0828

def calculate_journey_emissions(distance_km, mode, passengers=1):
    """
    Calculates estimated direct CO2 emissions for a journey.
    """
    mode_info = EMISSION_FACTORS.get(mode, EMISSION_FACTORS["petrol_car"])
    base_factor = mode_info["factor_g_per_km"]
    
    # Adjust for carpooling passenger count if applicable
    if mode in ["petrol_car", "diesel_car"] and passengers > 1:
        effective_factor = base_factor / passengers
    elif mode == "carpool":
        effective_factor = base_factor / max(1, (passengers / 3.0))
    else:
        effective_factor = base_factor
        
    total_emissions_g = effective_factor * distance_km
    total_emissions_kg = total_emissions_g / 1000.0
    estimated_cost = mode_info["cost_per_km"] * distance_km / max(1, passengers if "car" in mode else 1)
    
    return {
        "mode": mode,
        "mode_name": mode_info["name"],
        "distance_km": distance_km,
        "emissions_kg": round(total_emissions_kg, 3),
        "emissions_g": round(total_emissions_g, 1),
        "cost_estimate": round(estimated_cost, 1),
        "factor_g_per_km": round(effective_factor, 1),
        "description": mode_info["description"]
    }

def compare_all_modes(distance_km, current_mode="petrol_car", passengers=1):
    """
    Compares all transportation modes against the user's current commute.
    """
    current = calculate_journey_emissions(distance_km, current_mode, passengers)
    comparison_table = []
    
    for mode_key in EMISSION_FACTORS.keys():
        calc = calculate_journey_emissions(distance_km, mode_key, passengers=3 if mode_key == "carpool" else 1)
        savings_kg = round(current["emissions_kg"] - calc["emissions_kg"], 3)
        pct_diff = 0.0
        if current["emissions_kg"] > 0:
            pct_diff = round(((current["emissions_kg"] - calc["emissions_kg"]) / current["emissions_kg"]) * 100.0, 1)
            
        comparison_table.append({
            "mode_key": mode_key,
            "mode_name": calc["mode_name"],
            "emissions_kg": calc["emissions_kg"],
            "savings_kg": savings_kg,
            "pct_reduction": pct_diff,
            "is_current": (mode_key == current_mode),
            "cost_estimate": calc["cost_estimate"],
            "factor_g_per_km": calc["factor_g_per_km"],
            "description": calc["description"]
        })
        
    # Sort from lowest emitting to highest
    comparison_table.sort(key=lambda x: x["emissions_kg"])
    
    return {
        "current_mode": current,
        "distance_km": distance_km,
        "comparison": comparison_table,
        "methodology": "UK DESNZ/DEFRA 2023 & US EPA GHG Emission Factors for Urban Passenger Transport",
        "assumptions": "Direct tailpipe/traction emissions per passenger-km. Excludes upstream vehicle manufacturing lifecycle."
    }

def simulate_commute_switch(distance_km, from_mode, to_mode, daily_trips=2, working_days_per_year=240):
    """
    Simulates the environmental and economic impact of shifting commuting modes.
    """
    current_trip = calculate_journey_emissions(distance_km, from_mode)
    new_trip = calculate_journey_emissions(distance_km, to_mode)
    
    trip_savings_kg = max(0.0, current_trip["emissions_kg"] - new_trip["emissions_kg"])
    monthly_savings_kg = round(trip_savings_kg * daily_trips * 20, 2)
    annual_savings_kg = round(trip_savings_kg * daily_trips * working_days_per_year, 2)
    
    trip_cost_diff = current_trip["cost_estimate"] - new_trip["cost_estimate"]
    monthly_cost_diff = round(trip_cost_diff * daily_trips * 20, 1)
    
    # Equivalent metrics
    equiv_car_km_annual = round(annual_savings_kg * EQUIV_KM_PER_KG_CO2, 1)
    trees_equivalent = round(annual_savings_kg / 21.77, 1) # ~21.77 kg CO2 absorbed per mature urban tree per year
    
    return {
        "distance_km": distance_km,
        "from_mode": current_trip["mode_name"],
        "to_mode": new_trip["mode_name"],
        "trip_savings_kg": round(trip_savings_kg, 3),
        "monthly_savings_kg": monthly_savings_kg,
        "annual_savings_kg": annual_savings_kg,
        "monthly_cost_diff": monthly_cost_diff,
        "equiv_car_km_annual": equiv_car_km_annual,
        "trees_equivalent_annual": trees_equivalent,
        "explanation": f"Switching from {current_trip['mode_name']} to {new_trip['mode_name']} eliminates {round(trip_savings_kg, 2)} kg CO₂ per journey, saving an estimated {annual_savings_kg} kg CO₂ annually (equivalent to avoiding {equiv_car_km_annual} km of solo car driving)."
    }

def get_cumulative_impact_metrics(co2_saved_kg, energy_saved_kwh=0.0, waste_reduced_kg=0.0):
    """
    Generates transparent, multi-dimensional environmental metrics from logged actions.
    """
    equiv_car_km = round(co2_saved_kg * EQUIV_KM_PER_KG_CO2, 1)
    grid_co2_from_energy = round(energy_saved_kwh * GRID_EMISSION_FACTOR_KG_PER_KWH, 2)
    pet_bottles_equiv = round(waste_reduced_kg / 0.04, 0) # ~40g per standard beverage packaging
    
    return {
        "co2_saved_kg": round(co2_saved_kg, 2),
        "equiv_car_km": equiv_car_km,
        "energy_saved_kwh": round(energy_saved_kwh, 1),
        "grid_co2_avoided_kg": grid_co2_from_energy,
        "waste_reduced_kg": round(waste_reduced_kg, 2),
        "pet_bottles_equiv": int(pet_bottles_equiv),
        "formulas": {
            "equiv_car_km": "co2_saved_kg / 0.1705 kg/km (US EPA Average Passenger Vehicle)",
            "energy_co2": "energy_saved_kwh * 0.82 kg CO2/kWh (Standard regional mixed grid factor)",
            "waste_conversion": "Direct self-reported mass avoided in kg"
        }
    }

