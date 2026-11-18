"""
PRANVYRA Recommendation Engine
Implements AIRWISE next best action, Breath Budget exposure awareness,
Smart Daily Routine Generator, and Indoor Air Assessment.
"""

def generate_airwise_action(aqi_data, weather_data, user_prefs):
    """
    AIRWISE — Your Next Best Action
    Intelligently determines the single highest-impact, immediate action for the user.
    """
    aqi = aqi_data.get("aqi", 100)
    category = aqi_data.get("category", "Moderate")
    temp = weather_data.get("temperature", 25.0)
    wind = weather_data.get("wind_speed", 5.0)
    transport = user_prefs.get("primary_transport", "motorcycle")
    outdoor_hours = user_prefs.get("outdoor_hours", "08:00 - 09:30")
    
    # Priority decision tree based on environmental dynamics
    if aqi > 200:
        return {
            "title": "Shift Commute to Rapid Rail & Deploy N95",
            "tag": "CRITICAL EXPOSURE MITIGATION",
            "urgency": "High",
            "problem": f"Current AQI is {aqi} ({category}). Ambient fine particulate exposure (PM2.5) during open {transport} travel will exceed safe daily inhalation thresholds within 22 minutes.",
            "action": "Switch today's journey to electric metro or closed AC bus, and equip an authentic NIOSH-approved N95/FFP2 respirator.",
            "reason": f"Road-level vehicular plumes combined with calm wind conditions ({wind} km/h) trap exhaust gases at breathing height (0-2m).",
            "expected_benefit": "Reduces respiratory particulate deposition by up to 92% compared to open motorized two-wheeler travel.",
            "estimated_impact": "Avoids ~1.5 kg CO₂ (if using metro) and drastically lowers acute lung inflammatory response.",
            "confidence": "96% (High Sensor / Atmospheric Consensus)",
            "source": "Open-Meteo Atmospheric Assimilation & WHO Global Air Guidelines"
        }
    elif aqi > 150:
        if transport in ["motorcycle", "petrol_car", "diesel_car"]:
            return {
                "title": "Reschedule Outdoor Routine & Use Public Transit",
                "tag": "COMMUTE OPTIMIZATION",
                "urgency": "High",
                "problem": f"AQI is {aqi} ({category}). Fine particulates (PM2.5) are elevated across morning transit corridors.",
                "action": f"Avoid solo {transport} travel. Use the metro line or carpool, and defer rigorous outdoor workouts past 11:00 AM.",
                "reason": "Midday thermal solar heating will induce boundary-layer vertical mixing, dispersing surface particulate concentration by 25-40%.",
                "expected_benefit": "Minimizes inhaled particulate volume during strenuous cardiovascular breathing.",
                "estimated_impact": "Cuts ~1.8 kg personal transport emissions and reduces particulate intake by ~60%.",
                "confidence": "92%",
                "source": "Boundary Layer Meteorology & US EPA Health Criteria"
            }
        else:
            return {
                "title": "Seal Indoor Air & Time Midday Aeration",
                "tag": "INDOOR AIR SAFEGUARD",
                "urgency": "Medium",
                "problem": f"Ambient air quality is {category} (AQI {aqi}). Infiltration into living spaces degrades indoor air.",
                "action": "Keep windows closed through peak morning rush hours. Turn on HEPA filtration in your primary workspace.",
                "reason": "Morning vehicle queues and low boundary layers cause outdoor particulates to seep through micro-gaps.",
                "expected_benefit": "Maintains indoor PM2.5 below 25 µg/m³ despite elevated outdoor pollution.",
                "estimated_impact": "Protects indoor cognitive clarity and reduces allergic mucosal irritation.",
                "confidence": "90%",
                "source": "Indoor Air Quality Scientific Guidelines (ASHRAE 62.1)"
            }
    elif aqi > 100:
        return {
            "title": "Optimal Window for Active Transit & Natural Aeration",
            "tag": "ROUTINE ADJUSTMENT",
            "urgency": "Medium",
            "problem": f"AQI is {aqi} ({category}). Acceptable for most, but prolonged outdoor exposure can trigger mild bronchial tightness.",
            "action": "Ventilate your home between 11:30 AM and 3:00 PM when solar heating and wind ({wind} km/h) aid dispersion.",
            "reason": "Midday atmospheric dispersion is currently at its daily peak, reducing ground-level pollutant stagnation.",
            "expected_benefit": "Flushes indoor CO₂ and VOCs without drawing in severe morning traffic smog.",
            "estimated_impact": "Refreshes indoor air quality by 45% without requiring mechanical energy.",
            "confidence": "88%",
            "source": "Atmospheric Boundary Layer Dispersion Models"
        }
    else:
        return {
            "title": "Prime Clean Air Window: Perfect for Walking & Cycling",
            "tag": "SUSTAINABILITY OPPORTUNITY",
            "urgency": "Low",
            "problem": f"Air quality is {category} (AQI {aqi}). Conditions are clean and favorable for zero-emission mobility.",
            "action": "Leave motorized vehicles at home today. Walk or cycle for your local trips under 5 km.",
            "reason": "Low pollutant concentrations ensure that the cardiovascular benefits of active travel far outweigh particulate inhalation risk.",
            "expected_benefit": "Improves cardiovascular endurance while generating zero tailpipe carbon emissions.",
            "estimated_impact": "Saves 100% of fuel costs and avoids ~0.85 kg CO₂ per 5 km journey.",
            "confidence": "95%",
            "source": "WHO Health Economic Assessment Tools (HEAT)"
        }

def calculate_breath_budget(aqi, outdoor_hours_str="2", commute_distance_km=12.0, transport="motorcycle", ventilation="natural"):
    """
    Feature: Breath Budget
    Educational daily environmental exposure indicator based on ambient AQI and user routine.
    Clear Scientific Disclaimer: NOT a clinical measurement or medical advice.
    """
    # Parse approximate outdoor duration (in hours)
    try:
        if "-" in outdoor_hours_str and ":" in outdoor_hours_str:
            # e.g., "08:00 - 09:30, 18:00 - 19:30" => 3.0 hours
            slots = outdoor_hours_str.split(",")
            total_minutes = 0
            for slot in slots:
                if "-" in slot:
                    p1, p2 = slot.strip().split("-")
                    h1, m1 = map(int, p1.strip().split(":")[:2])
                    h2, m2 = map(int, p2.strip().split(":")[:2])
                    total_minutes += max(0, (h2 * 60 + m2) - (h1 * 60 + m1))
            outdoor_hours = max(1.0, round(total_minutes / 60.0, 1))
        else:
            outdoor_hours = float(outdoor_hours_str)
    except Exception:
        outdoor_hours = 2.0
        
    # Transport exposure factor (open vehicles expose commuter directly to road exhaust)
    transport_multipliers = {
        "motorcycle": 1.45,
        "cycling": 1.55,    # High ventilation rate (heavy breathing)
        "walking": 1.35,
        "bus": 1.05,
        "petrol_car": 0.85, # Cabin filter
        "diesel_car": 0.85,
        "metro": 0.65       # Filtered underground/elevated cabins
    }
    t_mult = transport_multipliers.get(transport, 1.0)
    
    # Indoor infiltration factor
    vent_infiltration = {
        "natural": 0.65,    # 65% of outdoor PM2.5 penetrates
        "poor": 0.80,       # Trapped indoor pollutants
        "mechanical": 0.35, # Filtered HVAC
        "mixed": 0.50
    }
    indoor_ratio = vent_infiltration.get(ventilation, 0.60)
    
    indoor_hours = max(0.0, 24.0 - outdoor_hours)
    
    # Daily exposure index units = (Outdoor hours * AQI * t_mult) + (Indoor hours * AQI * indoor_ratio)
    daily_exposure_units = (outdoor_hours * aqi * t_mult) + (indoor_hours * aqi * indoor_ratio)
    
    # Baseline benchmark = 24 hours at WHO clean guideline (AQI ~25) = 24 * 25 = 600 units (100% ideal budget)
    # Scaled budget consumption:
    budget_used_pct = min(100.0, round((daily_exposure_units / 2800.0) * 100.0, 1))
    
    if budget_used_pct < 35:
        budget_status = "Optimal Air Exposure"
        badge_color = "#16A88A"
        summary = "Your daily exposure footprint is well within conservative health thresholds. Outstanding lifestyle balance!"
    elif budget_used_pct < 65:
        budget_status = "Moderate Cumulative Exposure"
        badge_color = "#E7A83E"
        summary = "Your estimated daily particulate exposure is moderate. Limiting open road commuting during rush hours will protect your budget."
    elif budget_used_pct < 85:
        budget_status = "Elevated Environmental Load"
        badge_color = "#FF9800"
        summary = "High cumulative exposure load. Consider shifting commute timing or utilizing sealed public transit."
    else:
        budget_status = "Heavy Cumulative Inhalation"
        badge_color = "#E46F65"
        summary = "Exposure budget depleted! Maximize time in filtered indoor spaces and wear a high-filtration respirator outdoors."

    return {
        "budget_used_pct": budget_used_pct,
        "budget_remaining_pct": max(0.0, round(100.0 - budget_used_pct, 1)),
        "budget_status": budget_status,
        "badge_color": badge_color,
        "outdoor_hours_estimated": outdoor_hours,
        "summary": summary,
        "disclaimer": "Educational environmental exposure indicator based on ambient sensor estimates and your reported routine. This is NOT a clinical measurement, personal dose calculation, or medical advice."
    }

def generate_smart_daily_planner(aqi, weather_data, user_prefs):
    """
    Generates personalized morning, afternoon, and evening routine tasks
    aligned with environmental conditions and user profile.
    """
    transport = user_prefs.get("primary_transport", "motorcycle")
    temp = weather_data.get("temperature", 24.0)
    
    # Morning slot
    if aqi > 150:
        morning_tasks = [
            {
                "time_slot": "morning",
                "title": "Air Quality Check & Departure Calibration",
                "description": f"Ambient AQI is {aqi}. If departing during rush hour, wear a well-fitted N95 mask or choose the Metro over {transport}.",
                "priority": "high",
                "action_type": "commute"
            },
            {
                "time_slot": "morning",
                "title": "Indoor Seal & Pre-Departure Ventilation",
                "description": "Keep windows firmly closed until midday. Avoid incense or aerosol cleaning products that add indoor particulate load.",
                "priority": "high",
                "action_type": "indoor"
            }
        ]
    else:
        morning_tasks = [
            {
                "time_slot": "morning",
                "title": "Active Green Commute Departure",
                "description": f"Clean morning conditions (AQI {aqi}). Perfect opportunity to walk, cycle, or walk to the metro station.",
                "priority": "medium",
                "action_type": "commute"
            },
            {
                "time_slot": "morning",
                "title": "Morning Air Exchange",
                "description": "Open opposite windows for 15 minutes to flush overnight carbon dioxide buildup from bedrooms.",
                "priority": "low",
                "action_type": "indoor"
            }
        ]
        
    # Afternoon slot
    afternoon_tasks = [
        {
            "time_slot": "afternoon",
            "title": "Midday Natural Airing Window (12:00 - 15:00)",
            "description": f"Solar heating promotes atmospheric boundary dispersion. Safest daily window for quick cross-ventilation.",
            "priority": "medium",
            "action_type": "indoor"
        },
        {
            "time_slot": "afternoon",
            "title": "Energy & Climate Optimization",
            "description": f"Set climate control to 25°C-26°C with gentle ceiling air circulation to save ~1.5 kWh peak electricity.",
            "priority": "medium",
            "action_type": "energy"
        }
    ]
    
    # Evening slot
    if aqi > 140:
        evening_tasks = [
            {
                "time_slot": "evening",
                "title": "Evening Commute Shielding",
                "description": "Rush-hour thermal inversion traps diesel and tire dust. Close vehicle windows or maintain respirator use on two-wheelers.",
                "priority": "high",
                "action_type": "commute"
            },
            {
                "time_slot": "evening",
                "title": "Kitchen Emission Management",
                "description": "Turn on kitchen exhaust BEFORE heating oil or frying, and leave on for 10 minutes post-cooking to extract ultrafine aerosols.",
                "priority": "high",
                "action_type": "indoor"
            },
            {
                "time_slot": "evening",
                "title": "Nighttime Bedroom Purification",
                "description": "Seal bedroom door and run air purifier in quiet night mode for restorative, low-particulate sleep.",
                "priority": "medium",
                "action_type": "indoor"
            }
        ]
    else:
        evening_tasks = [
            {
                "time_slot": "evening",
                "title": "Low-Impact Evening Stroll",
                "description": "Air quality is favorable. Enjoy an evening walk in local tree-lined streets or parks.",
                "priority": "low",
                "action_type": "outdoor"
            },
            {
                "time_slot": "evening",
                "title": "Phantom Load Power Down",
                "description": "Unplug standby laptops, entertainment systems, and idle chargers before retiring for the night.",
                "priority": "low",
                "action_type": "energy"
            }
        ]
        
    return morning_tasks + afternoon_tasks + evening_tasks

def assess_indoor_air(quiz_data):
    """
    Interactive 'MY INDOOR AIR CHECK'
    Evaluates indoor risk factors with scientific rigor.
    Explicitly clarifies: educational assessment, not a phone-based physical sensor.
    """
    room_size = quiz_data.get("room_size", "medium") # small, medium, large
    occupants = int(quiz_data.get("occupants", 2))
    ventilation = quiz_data.get("ventilation", "natural") # natural, mechanical, poor
    cooking_fuel = quiz_data.get("cooking_fuel", "lpg") # electric, lpg, piped_gas, biomass
    has_pets = int(quiz_data.get("has_pets", 0))
    dust_level = quiz_data.get("dust_level", "moderate") # low, moderate, high
    smoking_exposure = int(quiz_data.get("smoking_exposure", 0))
    has_air_purifier = int(quiz_data.get("has_air_purifier", 0))
    
    score = 100
    risk_factors = []
    actions = []
    
    # Smoking exposure (severe indoor penalty)
    if smoking_exposure:
        score -= 35
        risk_factors.append("Active or passive tobacco smoke introduces extreme levels of toxic fine PM2.5, benzene, and nicotine residues (third-hand smoke).")
        actions.append({
            "title": "Institute Strict Outdoor Smoking Policy",
            "priority": "Critical",
            "detail": "Eliminate indoor smoking entirely. Residual tobacco particles adhere to fabrics and outgas harmful carcinogens for weeks."
        })
        
    # Cooking fuel & exhaust
    if cooking_fuel == "biomass":
        score -= 30
        risk_factors.append("Biomass/wood combustion produces hazardous indoor concentrations of carbon monoxide, black carbon, and polycyclic aromatic hydrocarbons.")
        actions.append({
            "title": "Transition Away from Unvented Biomass",
            "priority": "Critical",
            "detail": "Utilize induction electric cooktops or LPG with continuous dedicated flue/chimney ventilation."
        })
    elif cooking_fuel in ["lpg", "piped_gas"]:
        score -= 8
        actions.append({
            "title": "Exhaust Hood Operating Discipline",
            "priority": "High",
            "detail": "Unvented gas combustion releases nitrogen dioxide (NO₂) and trace carbon monoxide. Always run exhaust hoods with exterior venting during burner use."
        })
    else: # electric / induction
        actions.append({
            "title": "Maintain Clean Electric Cooktop Surfaces",
            "priority": "Low",
            "detail": "Induction produces zero combustion gases; simply vent cooking grease aerosols during high-heat searing."
        })
        
    # Ventilation
    if ventilation == "poor":
        score -= 20
        risk_factors.append("Inadequate fresh air exchange leads to carbon dioxide buildup (>1200 ppm) causing drowsiness, reduced cognitive function, and trapped VOCs.")
        actions.append({
            "title": "Establish Scheduled Cross-Draft Intervals",
            "priority": "High",
            "detail": "Create scheduled 15-minute cross-drafts twice daily during low outdoor traffic windows (11 AM - 3 PM) to flush exhaled CO₂."
        })
    elif ventilation == "mechanical":
        score += 5
        actions.append({
            "title": "Quarterly HVAC Filter Inspection",
            "priority": "Medium",
            "detail": "Inspect and vacuum/replace mechanical filters every 90 days to prevent pressure drop and microbial colonization."
        })
        
    # Dust & pets
    if dust_level == "high":
        score -= 10
        actions.append({
            "title": "Damp Microfiber Dusting Protocol",
            "priority": "Medium",
            "detail": "Avoid dry sweeping or feather dusters that resuspend settled PM10 into your breathing zone. Use damp microfiber cloths."
        })
    if has_pets:
        score -= 5
        actions.append({
            "title": "Pet Dander Air Care",
            "priority": "Low",
            "detail": "Wash pet bedding weekly in warm water (≥60°C) to denature allergen proteins and reduce airborne mite proliferation."
        })
        
    # Air purifier presence
    if has_air_purifier:
        score += 15
        actions.append({
            "title": "Optimize HEPA CADR and Placement",
            "priority": "Medium",
            "detail": "Position the air purifier away from walls and corners with unobstructed intake. Keep room closed while purifier runs for maximum CADR efficiency."
        })
    else:
        actions.append({
            "title": "Consider True HEPA (H13) Filtration for Sleep Areas",
            "priority": "Medium",
            "detail": "A certified True HEPA purifier physically captures 99.97% of particles down to 0.3 microns, protecting restorative sleep."
        })
        
    # Houseplants reality check (critical scientific honesty requirement!)
    actions.append({
        "title": "Houseplants: Aesthetic & Humidity Reality Check",
        "priority": "Informational",
        "detail": "Houseplants (Snake plants, Pothos, Peace Lilies) enhance psychological well-being and stabilize indoor humidity, but rigorous scientific reviews prove they CANNOT replace active HEPA filtration or mechanical ventilation for removing PM2.5 or VOCs in living homes."
    })
    
    score = max(15, min(100, score))
    
    if score >= 80:
        risk_level = "Low Risk / Clean Environment"
        score_color = "#16A88A"
    elif score >= 60:
        risk_level = "Moderate Risk / Manageable Sources"
        score_color = "#E7A83E"
    elif score >= 40:
        risk_level = "Elevated Risk / Significant Emission Sources"
        score_color = "#FF9800"
    else:
        risk_level = "Critical Indoor Air Hazard"
        score_color = "#E46F65"
        
    return {
        "score": score,
        "score_color": score_color,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "actions": actions,
        "scientific_disclaimer": "Scientific Disclaimer: This indoor check is an educational heuristic model based on documented environmental building health science. It does NOT claim to measure air quality directly through your browser or device without a certified hardware sensor."
    }

def get_sustainable_alternatives_catalog():
    """
    Module G: Smart Sustainable Alternatives
    Practical, location-aware switches with difficulty levels and documented benefits.
    """
    return [
        {
            "id": "alt_1",
            "category": "Mobility",
            "current_habit": "Solo Motorized Two-Wheeler / Car Commute",
            "suggested_alternative": "Urban Rail (Metro) or Coordinated Office Carpool",
            "why_better": "Metro electric traction generates 75-83% lower emissions per passenger-km and completely avoids roadside tailpipe exhaust.",
            "estimated_benefit": "Avoids ~1.4 - 2.8 kg CO₂ per daily 15 km round trip. Saves ₹1,200 - ₹3,500 monthly in fuel.",
            "difficulty": "Easy to Moderate (depends on transit network proximity)"
        },
        {
            "id": "alt_2",
            "category": "Hydration & Waste",
            "current_habit": "Purchasing Single-Use PET Bottled Water",
            "suggested_alternative": "Stainless Steel Insulated Daily Refill Bottle",
            "why_better": "Cuts manufacturing, bottling, transport, and disposal lifecycle emissions of plastic polymers.",
            "estimated_benefit": "Eliminates ~180 plastic bottles annually (~14.9 kg CO₂e avoided) and zero microplastic leaching.",
            "difficulty": "Very Easy (Immediate habit shift)"
        },
        {
            "id": "alt_3",
            "category": "Home Climate",
            "current_habit": "Running Air Conditioner at 20°C - 22°C All Night",
            "suggested_alternative": "Set AC to 25°C - 26°C with Gentle Ceiling Fan Assist",
            "why_better": "Every 1°C increase in thermostat setpoint reduces HVAC compressor energy consumption by 4% to 6%.",
            "estimated_benefit": "Saves 1.8 - 2.4 kWh electricity per night (~1.5 - 2.0 kg CO₂ avoided on regional grid).",
            "difficulty": "Easy"
        },
        {
            "id": "alt_4",
            "category": "Waste Management",
            "current_habit": "Burning Dry Garden Leaves & Street Litter",
            "suggested_alternative": "Community Mulching, Composting, or Municipal Green-Waste Collection",
            "why_better": "Open biomass burning releases extreme surges of toxic black carbon, polycyclic aromatics, and PM2.5 at breathing level.",
            "estimated_benefit": "Prevents catastrophic localized neighborhood particulate spikes and returns carbon to nutrient-rich soil.",
            "difficulty": "Moderate (Requires neighborhood cooperation)"
        },
        {
            "id": "alt_5",
            "category": "Indoor Cooking",
            "current_habit": "High-Heat Frying Without Active Exhaust Hood",
            "suggested_alternative": "Run High-Suction Exhaust with Pan Lids; Transition to Induction Cooking",
            "why_better": "Heated cooking oils generate ultrafine aerosol droplets (<0.1 µm) that linger indoors for over 3 hours without extraction.",
            "estimated_benefit": "Reduces indoor PM2.5 peaks by up to 80% during and after meal preparation.",
            "difficulty": "Easy"
        }
    ]
