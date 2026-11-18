"""
PRANVYRA INTELLIGENCE CORE — Multi-Role AI Orchestration Service
Coordinates specialized environmental expert roles, context injection,
multi-turn conversational memory, and native trilingual reasoning.
"""
import os
import json
import logging
from datetime import datetime
from config import Config
from database.db import get_db_connection
from services.expert_router import detect_expert_roles, get_expert_details, EXPERT_ROLES
from services.environmental_context import build_environmental_context

logger = logging.getLogger(__name__)

# Base foundation prompt from product specifications
FOUNDATION_PROMPT = """
You are PRANVYRA Intelligence Core, a specialized environmental intelligence assistant.
You are not a generic chatbot.

You possess the reasoning perspective of five environmental specialists:
1. Atmospheric Scientist (AQI, particulates PM2.5/PM10, gases NO2/O3/CO/SO2, atmospheric boundary layer dispersion, meteorology).
2. Urban Mobility & Emission Expert (sustainable commuting, DEFRA greenhouse gas conversion factors, modal shift, travel exposure).
3. Indoor Air Quality Specialist (indoor ventilation, cooking exhaust, dust management, HEPA filtration, building infiltration).
4. Sustainability Strategist (realistic lifestyle shifts, energy conservation, waste reduction, carbon footprint estimation).
5. Environmental Research Analyst (datasets, pollution trends, historical comparisons, statistical correlation vs causation, uncertainty).

Your responsibility is to help ordinary citizens understand environmental conditions and make better everyday decisions.

REASONING PRINCIPLES:
1. Understand the user's actual objective before answering.
2. Adopt the specialized expert role(s) designated for this inquiry.
3. Integrate the provided real-time atmospheric data, meteorological context, and user profile.
4. Identify missing or uncertain information clearly.
5. Evaluate relevant alternatives with practical trade-offs.
6. Explain your reasoning in clear, accessible, respectful language.
7. Provide practical, personalized recommendations.
8. Explain potential benefits and limitations.
9. Clearly disclose uncertainty; distinguish modeled estimations from physical sensor observations.
10. NEVER invent scientific evidence, monitoring stations, or measurements.

INTELLIGENCE REQUIREMENTS:
- Avoid generic responses when specific user or atmospheric context is provided.
- Strictly avoid generic conversational filler such as: 'Great question!', 'Here are five tips!', 'As an AI language model!'.
- Answer naturally, intelligently, and directly.
- Challenge incorrect assumptions when scientifically warranted (e.g. clarify that houseplants do NOT replace mechanical ventilation or active HEPA filtration for particulate removal).
- When discussing travel or emissions, provide transparent calculations based on UK DEFRA 2023 modal factors.
- Connect follow-up questions to earlier conversation turns.

DATA INTEGRITY:
- Never invent live AQI readings.
- Never invent monitoring stations.
- Never invent environmental statistics.
- Never present an educational estimate as a clinical physical measurement.
- If environmental data is unavailable for the selected location, state so transparently.

SCIENTIFIC RESPONSIBILITY:
- Do not diagnose medical conditions.
- Do not promise an activity is medically safe based solely on AQI.
- Explain uncertainty and meteorological limitations.

RESPONSE STRUCTURE:
For complex environmental questions, organize your response with:
1. Direct Answer
2. Scientific Explanation
3. Relevant Contextual Analysis
4. Recommended Action
5. Expected Benefit & Limitations

Followed by an optional structured JSON card block (enclosed in ```json ... ```) with these keys:
{
  "recommended_action": "Clear single high-priority action",
  "problem_identified": "Specific atmospheric or indoor issue",
  "reason": "Scientific explanation of why this occurs",
  "expected_benefit": "Quantified health or emission benefit",
  "estimated_impact": "Numerical estimate (e.g. ~1.8 kg CO2e saved)",
  "confidence_level": "High (90%) / Moderate (75%)",
  "source": "US EPA / UK DEFRA / Open-Meteo"
}
For simple conversational questions, answer conversationally and concisely without forcing a rigid structure.
"""

ROLE_SPECIFIC_INSTRUCTIONS = {
    "atmospheric_scientist": """
PRIMARY ROLE ACTIVATED: ATMOSPHERIC SCIENTIST
- Provide deep scientific analysis of particulate matter (PM2.5, PM10) aerodynamic diameters and gaseous pollutants (NO2, O3, CO, SO2).
- Explain the physical and meteorological mechanisms at play (boundary layer inversions, diurnal solar heating, photochemical smog formation, wind shear dispersion).
- Explain why surface wind velocity alone may or may not clear pollution (e.g. regional advection vs thermal inversion).
- Suggest practical outdoor precautions (e.g. N95/FFP2 particulate respirators, avoiding strenuous aerobic exercise during inversion peaks).
""",
    "urban_mobility_expert": """
PRIMARY ROLE ACTIVATED: URBAN MOBILITY AND EMISSION EXPERT
- Provide rigorous multi-modal transportation analysis comparing solo car, motorcycle, transit bus, electric metro, cycling, and walking.
- Utilize official UK DEFRA 2023 greenhouse gas conversion factors:
  * Solo Petrol Car: ~170.5 g CO2e/km
  * Motorcycle / Scooter: ~103.2 g CO2e/km
  * Public Transit Bus: ~96.5 g CO2e/pkm
  * Shared Carpooling (3 pax): ~56.8 g CO2e/pkm
  * Grade-separated Electric Metro: ~28.5 g CO2e/pkm
  * Walking / Bicycle: 0.0 g direct tailpipe CO2e
- Balance tailpipe emissions against in-transit air pollutant exposure (unshielded two-wheelers vs sealed, filtered rapid transit).
- Provide practical calculations for daily and annual commute savings.
""",
    "indoor_air_specialist": """
PRIMARY ROLE ACTIVATED: INDOOR AIR QUALITY SPECIALIST
- Analyze indoor particulate generation, kitchen cooking fuel (LPG, biomass, induction), and aeration dynamics.
- Differentiate source control (range hood exhaust discipline, avoiding unvented combustion) from dilution ventilation and mechanical filtration.
- Clearly emphasize true building physics: mechanical HEPA filtration (H13/H14) and high CADR ratings are required for PM2.5 removal; houseplants do not purify particulate air.
- Recommend optimal aeration windows based on outdoor diurnal dispersion curves.
""",
    "sustainability_strategist": """
PRIMARY ROLE ACTIVATED: SUSTAINABILITY STRATEGIST
- Evaluate daily habits and propose high-leverage, practical lifestyle transitions.
- Focus on affordable, accessible actions (AC setpoint adjustment from 20°C to 24°C, reusable stainless steel bottles avoiding PET manufacturing footprints, transit shifts).
- Avoid unrealistic or punitive lifestyle prescriptions. Highlight the tangible co-benefits (reduced electricity utility bills, personal wellness).
""",
    "environmental_analyst": """
PRIMARY ROLE ACTIVATED: ENVIRONMENTAL RESEARCH ANALYST
- Examine environmental datasets, diurnal cycles, and seasonal baselines.
- Emphasize statistical distinction between correlation and causation.
- Disclose confidence levels, model limitations (Copernicus CAMS grid resolution vs roadside micro-environments), and data provenance.
"""
}

LANGUAGE_PROMPT_MAP = {
    "en": "Respond fluently and naturally in English.",
    "hi": "Respond entirely and naturally in Hindi (हिंदी script). Use appropriate scientific and everyday environmental vocabulary in Devanagari.",
    "bn": "Respond entirely and naturally in Bengali (বাংলা script). Use culturally authentic, clear environmental terms in Bengali script."
}

def process_chat_query(user_message, visitor_id="anonymous", requested_role="auto", language="en", lat=None, lon=None):
    """
    Main entry point for PRANVYRA Intelligence Core processing.
    """
    lang = language if language in ["en", "hi", "bn"] else "en"
    
    # 1. Build environmental and user context
    context = build_environmental_context(visitor_id, lat=lat, lon=lon, max_history=8)
    
    # 2. Intelligent expert routing
    routing_result = detect_expert_roles(user_message, requested_role=requested_role, context=context)
    primary_role = routing_result["primary_role"]
    multi_roles = routing_result["multi_expert_roles"]
    
    expert_meta = get_expert_details(primary_role)
    expert_title_key = f"title_{lang}" if f"title_{lang}" in expert_meta else "title"
    expert_title = expert_meta.get(expert_title_key, expert_meta["title"])
    
    # 3. Attempt Gemini API with Multi-Role System Prompt
    api_key = Config.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
    ai_response = None
    is_gemini_success = False
    
    if api_key and api_key.strip() and api_key != "your_gemini_api_key_here":
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            # Assemble comprehensive system instruction
            role_instructions = "\n".join([ROLE_SPECIFIC_INSTRUCTIONS.get(r, "") for r in multi_roles])
            full_system_instruction = f"""
{FOUNDATION_PROMPT}

{role_instructions}

{LANGUAGE_PROMPT_MAP.get(lang, LANGUAGE_PROMPT_MAP['en'])}
"""
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=full_system_instruction
            )
            
            # Format prompt with context & history
            formatted_input = build_gemini_prompt(user_message, context, multi_roles, lang)
            response = model.generate_content(formatted_input)
            
            if response and response.text:
                ai_response = parse_gemini_response(response.text, lang, primary_role)
                is_gemini_success = True
        except Exception as e:
            logger.warning(f"Gemini API execution failed: {e}. Falling back to Intelligence Core reasoning engine.")

    # 4. Fallback to specialized Intelligence Core reasoning engine if Gemini unavailable
    if not is_gemini_success:
        ai_response = execute_expert_reasoning(user_message, context, primary_role, multi_roles, lang)

    # 5. Persist conversation turn in database with user isolation
    conn = get_db_connection()
    structured_json_str = json.dumps(ai_response.get("structured_card")) if ai_response.get("structured_card") else None
    user_id = None
    if visitor_id and str(visitor_id).startswith("user_"):
        try:
            user_id = int(str(visitor_id).replace("user_", ""))
        except Exception:
            pass
    
    conn.execute(
        "INSERT INTO chat_history (visitor_id, user_id, role, message, language, structured_card_json) VALUES (?, ?, 'user', ?, ?, NULL)",
        (visitor_id, user_id, user_message, lang)
    )
    conn.execute(
        "INSERT INTO chat_history (visitor_id, user_id, role, message, language, structured_card_json) VALUES (?, ?, 'assistant', ?, ?, ?)",
        (visitor_id, user_id, ai_response.get("text", ""), lang, structured_json_str)
    )
    conn.commit()
    conn.close()

    # 6. Generate dynamic contextual follow-up suggestions
    follow_ups = generate_follow_up_suggestions(user_message, primary_role, lang)

    return {
        "success": True,
        "reply": ai_response.get("text"),
        "structured_card": ai_response.get("structured_card"),
        "primary_role": primary_role,
        "multi_expert_roles": multi_roles,
        "expert_title": expert_title,
        "expert": {
            "id": primary_role,
            "title": expert_title
        },
        "routing_reason": routing_result["routing_reason"],
        "is_auto_routed": routing_result["is_auto_routed"],
        "language": lang,
        "is_ai_generated": is_gemini_success,
        "follow_ups": follow_ups,
        "follow_up_suggestions": follow_ups
    }

def build_gemini_prompt(user_message, context, multi_roles, lang):
    """Prepares structured prompt with recent conversation history and environmental data."""
    atm = context["atmospheric"]
    met = context["meteorological"]
    prof = context["visitor_profile"]
    hist = context["conversation_history"]
    
    history_str = ""
    if hist:
        history_lines = []
        for h in hist[-6:]:  # Last 6 turns
            sender = "User" if h["role"] == "user" else "Assistant"
            history_lines.append(f"{sender}: {h['message']}")
        history_str = "\nRECENT CONVERSATION HISTORY:\n" + "\n".join(history_lines) + "\n"

    pollutants_str = ", ".join([f"{k}: {v['value']} {v['unit']}" for k, v in atm.get("pollutants", {}).items()]) or "No individual pollutant sensor feeds reported."

    prompt = f"""
LIVE ENVIRONMENTAL CONTEXT:
- Target Location: {prof['city']} (Lat: {prof['latitude']}, Lon: {prof['longitude']})
- Ambient Air Quality: AQI {atm['aqi']} ({atm['category']}, Alert Level: {atm['alert_level']})
- Reported Pollutant Concentrations: {pollutants_str}
- Data Provenance: {atm['data_source']} | Standard: {atm['calculation_standard']}
- Meteorology: Temperature {met['temperature_c']}°C, Humidity {met['humidity_pct']}%, Wind {met['wind_speed_kmh']} km/h ({met['wind_direction_deg']}°), Conditions: {met['weather_desc']}

VISITOR HABITS (Voluntarily Stated):
- Primary Commute: {prof['commute_distance_km']} km via {prof['primary_transport']}
- Daily Outdoor Hours: {prof['outdoor_hours']} | Work Schedule: {prof['work_schedule']}
- Indoor Setup: Ventilation '{prof['ventilation_type']}', Cooking Fuel '{prof['cooking_fuel']}'
{history_str}
USER INQUIRY:
{user_message}

Answer with the depth of the active expert role(s): {', '.join(multi_roles)}. Respond in language code '{lang}'.
"""
    return prompt

def parse_gemini_response(raw_text, lang, primary_role):
    """Parses Gemini output and extracts optional structured card."""
    text_content = raw_text
    card = None
    
    if "```json" in raw_text:
        try:
            parts = raw_text.split("```json")
            text_part = parts[0].strip()
            json_part = parts[1].split("```")[0].strip()
            card = json.loads(json_part)
            
            # Append any trailing commentary
            after_part = parts[1].split("```")[1].strip() if len(parts[1].split("```")) > 1 else ""
            if after_part:
                text_content = f"{text_part}\n\n{after_part}".strip()
            else:
                text_content = text_part
        except Exception as e:
            logger.warning(f"Could not parse JSON block from Gemini output: {e}")
            card = None

    return {
        "text": text_content,
        "structured_card": card
    }

def execute_expert_reasoning(user_message, context, primary_role, multi_roles, lang):
    """
    High-fidelity offline/fallback reasoning engine.
    Applies exact scientific principles across all 5 expert roles in EN, HI, and BN.
    """
    atm = context["atmospheric"]
    met = context["meteorological"]
    prof = context["visitor_profile"]
    aqi = atm.get("aqi", 100)
    city = prof.get("city") or "Your City"
    transport = prof.get("primary_transport", "public_transit")
    dist = prof.get("commute_distance_km", 10.0)
    
    q_lower = user_message.lower()

    # 1. Atmospheric Scientist Domain
    if primary_role == "atmospheric_scientist":
        if "wind" in q_lower or "बढ़" in q_lower or "বাতাস" in q_lower:
            if lang == "hi":
                text = f"**प्रत्यक्ष उत्तर:** तेज़ या मध्यम हवा के बावजूद एक्यूआई बढ़ने का मुख्य कारण वायुमंडलीय सीमा परत (Boundary Layer) का नीचे गिरना या क्षेत्रीय प्रदूषण (Regional Advection) का स्थानांतरण होना है।\n\n**वैज्ञानिक व्याख्या:** जब ज़मीन के पास का तापमान ऊपरी हवा की तुलना में ठंडा होता है (Thermal Inversion), तो हवा का ऊर्ध्वाधर फैलाव (Vertical Dispersion) रुक जाता है। तेज़ हवा अक्सर खुले इलाकों से धूल और महीन कणों (PM10 और PM2.5) को उठाकर शहरी गलियारों में फंसा देती है।\n\n**संदर्भ विश्लेषण:** {city} में वर्तमान एक्यूआई {aqi} दर्ज है। हवा की गति {met['wind_speed_kmh']} किमी/घंटा और आर्द्रता {met['humidity_pct']}% है। उच्च आर्द्रता प्रदूषकों को भारी बनाकर सांस लेने की ऊंचाई पर रखती है।\n\n**अनुशंसित कदम:** सुबह और शाम के समय जब ज़मीनी स्तर पर प्रदूषण सबसे घना होता है, खुले में तीव्र व्यायाम न करें। बाहर जाते समय N95 रेस्पिरेटर पहनें।"
                action = "सुबह की व्यस्तता के दौरान बाहरी व्यायाम सीमित करें और N95 मास्क का उपयोग करें।"
            elif lang == "bn":
                text = f"**সরাসরি উত্তর:** বাতাস থাকা সত্ত্বেও বায়ু মান (AQI) খারাপ হওয়ার প্রধান কারণ হলো বায়ুমণ্ডলীয় বিপরীতমুখী তাপমাত্রা (Thermal Inversion) অথবা পার্শ্ববর্তী অঞ্চল থেকে দূষণ ভেসে আসা (Regional Advection)।\n\n**বৈজ্ঞানিক ব্যাখ্যা:** যখন মাটির কাছাকাছি বাতাস ঠান্ডা থাকে, তখন ধোঁয়া ও ভাসমান কণা উপরে উঠতে পারে না। দমকা বাতাস উল্টো দূরবর্তী নির্মাণকাজ বা মাটির ধূলিকণা (PM10) শহরের রাস্তায় উড়িয়ে আনে।\n\n**পরিস্থিতি বিশ্লেষণ:** {city}-তে বর্তমান AQI {aqi}। বাতাসের গতি {met['wind_speed_kmh']} কিমি/ঘণ্টা এবং আর্দ্রতা {met['humidity_pct']}%।\n\n**প্রয়োজনীয় পদক্ষেপ:** সকাল এবং সন্ধ্যার পিক ট্র্যাফিকের সময় ভারী ব্যায়াম এড়িয়ে চলুন এবং ঘরের বাইরের হাঁটার সময় N95 মাস্ক ব্যবহার করুন।"
                action = "সকালের রাশ আওয়ারে জানালা বন্ধ রাখুন এবং বাইরে বেরোলে N95 মাস্ক ব্যবহার করুন।"
            else:
                text = f"**Direct Answer:** AQI can rise despite windy conditions due to shallow atmospheric boundary layer inversions, regional pollution transport (advection), or high surface dust resuspension.\n\n**Scientific Explanation:** Wind is a two-dimensional vector that disperses pollution horizontally, but if a thermal boundary layer inversion suppresses vertical mixing, surface emissions remain trapped near human breathing height. Furthermore, gusty winds often re-suspend coarse dust particles (PM10) from dry verges and construction corridors.\n\n**Contextual Analysis:** For {city}, the current AQI is {aqi} ({atm['category']}). Meteorological telemetry indicates wind velocity at {met['wind_speed_kmh']} km/h with {met['humidity_pct']}% relative humidity. High humidity facilitates hygroscopic growth of fine particulates, increasing optical scattering and perceived haziness.\n\n**Recommended Action:** Avoid high-aerobic outdoor workouts during the morning rush. When commuting along high-traffic corridors, use an N95/FFP2 respirator to filter inhalable sub-micron particulates."
                action = "Avoid peak-hour cardio near traffic corridors; utilize certified N95 respirators."
            
            card = {
                "recommended_action": action,
                "problem_identified": f"Elevated particulate concentration (AQI {aqi}) despite ambient wind advection.",
                "reason": "Thermal boundary layer suppression traps ground-level tailpipe and dust plumes.",
                "expected_benefit": "Reduces deep-lung alveolar deposition of PM2.5 by up to 90%.",
                "estimated_impact": "Avoids ~150-250 µg of inhaled particulate matter per 45-min exposure window.",
                "confidence_level": "High (92%)",
                "source": "US EPA & Copernicus Atmospheric Monitoring Service"
            }
            return {"text": text, "structured_card": card}

    # 2. Urban Mobility Domain
    if primary_role == "urban_mobility_expert" or "commute" in q_lower or "metro" in q_lower or "motorcycle" in q_lower:
        moto_emiss = round(dist * 0.1032 * 2, 2)
        metro_emiss = round(dist * 0.0285 * 2, 2)
        daily_saving = round(moto_emiss - metro_emiss, 2)
        annual_saving = round(daily_saving * 240, 1)

        if lang == "hi":
            text = f"**प्रत्यक्ष उत्तर:** हाँ, आपके {dist} किमी के दैनिक सफर के लिए इलेक्ट्रिक मेट्रो मोटरसाइकिल की तुलना में स्वास्थ्य और पर्यावरण दोनों दृष्टियों से बहुत बेहतर है।\n\n**वैज्ञानिक एवं उत्सर्जन विश्लेषण:** \n- सोलो मोटरसाइकिल: ~103.2 ग्राम CO₂e प्रति किमी\n- इलेक्ट्रिक मेट्रो: ~28.5 ग्राम CO₂e प्रति यात्री-किमी\n\nआपके {dist} किमी राउंड-ट्रिप में:\n- मोटरसाइकिल से उत्सर्जन: ~{moto_emiss} किग्रा CO₂e/दिन\n- मेट्रो से उत्सर्जन: ~{metro_emiss} किग्रा CO₂e/दिन\n- **दैनिक शुद्ध बचत:** {daily_saving} किग्रा CO₂e (वार्षिक बचत: ~{annual_saving} किग्रा CO₂e)।\n\n**स्वास्थ्य सुरक्षा लाभ:** मोटरसाइकिल पर आप सड़क स्तर पर वाहनों के जहरीले साइलेंसर एग्जॉस्ट (NOx और PM2.5) के सीधे संपर्क में रहते हैं। मेट्रो में एयर-फिल्टर्ड केबिन आपको इस जहरीले धुएं से 85% तक सुरक्षित रखता है।"
            action = f"दैनिक {dist} किमी सफर को इलेक्ट्रिक मेट्रो पर शिफ्ट करें।"
        elif lang == "bn":
            text = f"**সরাসরি উত্তর:** হ্যাঁ, আপনার {dist} কিমি দৈনন্দিন যাতায়াতের জন্য মোটরসাইকেলের চেয়ে ইলেকট্রিক মেট্রো অনেক বেশি স্বাস্থ্যকর এবং পরিবেশবান্ধব।\n\n**নিঃসরণ ও বৈজ্ঞানিক তুলনা:**\n- মোটরসাইকেল: ~১০৩.২ গ্রাম CO₂e প্রতি কিমি\n- ইলেকট্রিক মেট্রো: ~২৮.৫ গ্রাম CO₂e প্রতি যাত্রী-কিমি\n\nপ্রতিদিনের যাতায়াতে:\n- মোটরসাইকেলে মোট নিঃসরণ: ~{moto_emiss} কেজি CO₂e\n- মেট্রোতে নিঃসরণ: ~{metro_emiss} কেজি CO₂e\n- **দৈনিক নিঃসরণ সাশ্রয়:** {daily_saving} কেজি CO₂e (বছরে প্রায় {annual_saving} কেজি CO₂e)।\n\n**স্বাস্থ্যগত সুবিধা:** মোটরসাইকেলে আপনি সরাসরি গাড়ির নির্গত বিষাক্ত গ্যাস ও ধোঁয়ার সংস্পর্শে আসেন। মেট্রোর ফিল্টার করা বগিতে যাতায়াত ফুসফুসে দূষণ প্রবেশ বহুলাংশে কমিয়ে দেয়।"
            action = f"দৈনন্দিন {dist} কিমি যাতায়াত মেট্রো রেলে স্থানান্তর করুন।"
        else:
            text = f"**Direct Answer:** Yes. For your daily {dist} km round-trip commute, transitioning from a solo motorcycle to electric rapid rail (Metro) is significantly superior for both personal respiratory health and verified emissions reduction.\n\n**Emission Factor Comparison (UK DEFRA 2023):**\n- Solo Motorcycle/Scooter: ~103.2 g CO₂e/km\n- Grade-Separated Electric Metro: ~28.5 g CO₂e/passenger-km\n\n**Quantified Calculation:**\n- Baseline Commute via Motorcycle: ~{moto_emiss} kg CO₂e per day\n- Shifted Commute via Metro: ~{metro_emiss} kg CO₂e per day\n- **Direct Avoided Emissions:** **{daily_saving} kg CO₂e/day** (~**{annual_saving} kg CO₂e/year** across a 240-day work year).\n\n**Exposure Risk Factor:** Riding an unshielded two-wheeler subjects you to the ground-level breathing zone where heavy vehicle tailpipes and tyre-wear friction plumes are densest. Enclosed rapid rail provides physical shielding and filtered carriage air."
            action = f"Transition your {dist} km daily trip to electric rapid rail (Metro)."

        card = {
            "recommended_action": action,
            "problem_identified": f"Tailpipe emissions (~{moto_emiss} kg/day) and direct road-level exhaust inhalation during solo motorcycle transit.",
            "reason": "Internal combustion two-wheelers lack exhaust aftertreatment efficiency comparable to centralized electric grid rail.",
            "expected_benefit": f"Eliminates {daily_saving} kg CO₂e daily and minimizes road-level toxic exhaust inhalation.",
            "estimated_impact": f"{annual_saving} kg CO₂e avoided per year.",
            "confidence_level": "High (95%)",
            "source": "UK DEFRA 2023 Greenhouse Gas Conversion Factors"
        }
        return {"text": text, "structured_card": card}

    # 3. Indoor Air Quality Domain
    if primary_role == "indoor_air_specialist" or "smell" in q_lower or "cook" in q_lower or "indoor" in q_lower or "ventil" in q_lower:
        if lang == "hi":
            text = f"**प्रत्यक्ष उत्तर:** खाना बनाते समय धुआं या गंध आना यह दर्शाता है कि रसोई का एग्जॉस्ट अपर्याप्त है और तेल के एरोसोल तथा गैस दहन के उप-उत्पाद (NO₂ और PM2.5) कमरे में जमा हो रहे हैं।\n\n**वैज्ञानिक व्याख्या:** एलपीजी और तेल का उच्च तापमान पर जलना अल्ट्राफाइन पार्टिकल्स (UFPs) और नाइट्रोजन डाइऑक्साइड पैदा करता है। केवल पंखा चलाने से धुआं पूरे घर में फैल जाता है, बाहर नहीं निकलता। इसके अलावा, मनी प्लांट या पौधे इस तरह के पार्टिकुलेट धुएं को साफ नहीं कर सकते।\n\n**अनुशंसित समाधान:**\n1. खाना शुरू करने से 1 मिनट पहले ही किचन का एग्जॉस्ट हुड या चिमनी चालू करें ताकि नकारात्मक दबाव (Negative Pressure) बन सके।\n2. खाना बनाते समय किचन का दरवाजा बाकी कमरों की तरफ बंद रखें और बाहरी खिड़की खुली रखें।\n3. यदि बाहरी हवा (एक्यूआई {aqi}) खराब है, तो दोपहर 12 बजे से 3 बजे के बीच घर में क्रॉस-वेंटिलेशन करें जब धूप से प्रदूषण का बिखराव अधिक होता है।"
            action = "किचन में फोर्सड एग्जॉस्ट चालू रखें और बाकी कमरों से अलग वेंटिलेशन बनाए रखें।"
        elif lang == "bn":
            text = f"**সরাসরি উত্তর:** রান্নার সময় ঘরে ধোঁয়া বা গন্ধ জমে থাকার অর্থ হলো পর্যাপ্ত নিষ্কাশন (Exhaust) ব্যবস্থার অভাব, যার ফলে বিষাক্ত গ্যাস (NO₂) ও অতিসূক্ষ্ম তেলকণা (PM2.5) ঘরের বাতাসে আটকা পড়ছে।\n\n**বৈজ্ঞানিক ব্যাখ্যা:** রান্নাঘরের ধোঁয়ায় প্রচুর পরিমাণে কার্বন কণা ও উদ্বায়ী যৌগ থাকে। ঘরের সিলিং ফ্যান চালালে ধোঁয়া ঘরের সব কোণে ছড়িয়ে পড়ে। ঘরের গাছপালা বা সাধারণ এয়ার ফ্রেশনার এই ক্ষতিকারক কণা দূর করতে পারে না।\n\n**বাস্তবসম্মত পদক্ষেপ:**\n১. রান্না শুরু করার আগেই এক্সহস্ট ফ্যান বা কিচেন চিমনি চালু করুন।\n২. রান্নার সময় রান্নাঘরের দরজা বাকি ঘরের দিক থেকে বন্ধ রাখুন এবং বাইরের দিকের জানালা খোলা রাখুন।\n৩. বাইরের AQI বেশি থাকলে দুপুর ১২টা থেকে ৩টার মধ্যে জানালা খুলে ঘরের অভ্যন্তরীণ বাতাস পরিবর্তন করুন।"
            action = "রান্নাঘরে ফোর্সড এক্সহস্ট নিশ্চিত করুন এবং দুপুরের রোদ চলাকালীন বাতাস চলাচল করান।"
        else:
            text = f"**Direct Answer:** Persistent cooking odors and smoke indicate insufficient localized capture velocity at the stovetop, leading to rapid accumulation of ultrafine particles (UFPs), acrolein, and combustion byproducts (NO₂ and PM2.5) throughout indoor living areas.\n\n**Scientific Explanation:** High-temperature oil frying and fuel combustion generate dense concentrations of inhalable aerosolized droplets. Merely running a ceiling fan does not remove pollutants; it recirculates them into living and sleeping quarters. Furthermore, building science research confirms that indoor houseplants cannot remove particulate matter or replace mechanical ventilation.\n\n**Actionable Indoor Strategy:**\n1. **Establish Negative Pressure:** Activate your dedicated kitchen range hood or exhaust fan 1 minute *before* igniting burners, establishing an extraction airflow draft.\n2. **Isolate Kitchen Boundary:** Keep interior kitchen doors closed to prevent plume migration to bedrooms while leaving an exterior window cracked for makeup air.\n3. **Solar Ventilation Timing:** When outdoor AQI is elevated ({aqi}), ventilate between 11:30 AM and 3:00 PM when solar thermal mixing maximizes boundary layer depth and lowers ambient baseline pollution."
            action = "Enforce continuous kitchen exhaust extraction during cooking and isolate living areas."

        card = {
            "recommended_action": action,
            "problem_identified": "Stovetop emission capture failure resulting in indoor PM2.5 and NO₂ buildup.",
            "reason": "Thermal cooking plumes diffuse rapidly through open doorways without dedicated negative-pressure extraction.",
            "expected_benefit": "Reduces indoor peak PM2.5 spikes by 70–85% within living quarters.",
            "estimated_impact": "Prevents indoor AQI from exceeding 250 µg/m³ during cooking periods.",
            "confidence_level": "High (90%)",
            "source": "ASHRAE Standard 62.2 & Environmental Health Perspectives"
        }
        return {"text": text, "structured_card": card}

    # 4. Sustainability Strategist Domain
    if primary_role == "sustainability_strategist" or "footprint" in q_lower or "plastic" in q_lower or "save" in q_lower:
        if lang == "hi":
            text = f"**प्रत्यक्ष उत्तर:** घरेलू कार्बन फुटप्रिंट घटाने के लिए सबसे व्यावहारिक और किफायती शुरुआत ऊर्जा दक्षता और आवागमन के साधनों से होती है, न कि अत्यधिक महंगे बदलावों से।\n\n**उच्च प्रभाव वाले व्यावहारिक कदम:**\n1. **एसी थर्मोस्टेट 24°C पर सेट करें:** 20°C की बजाय 24°C पर एसी चलाने से बिजली की खपत में 24% की कमी आती है, जिससे प्रति मौसम ~177 किग्रा CO₂e की बचत होती है।\n2. **दोपहिया से सार्वजनिक परिवहन शिफ्ट:** हर 10 किमी की मेट्रो यात्रा कार की तुलना में ~2.8 किग्रा CO₂e बचाती है।\n3. **रीयूजेबल पानी की बोतल का उपयोग:** प्रतिवर्ष 150 से अधिक प्लास्टिक पीईटी बोतलों को रोककर ~78 किग्रा जीवनचक्र उत्सर्जन टाला जा सकता है।"
            action = "एसी को 24°C पर सेट करें और दैनिक आवागमन में सार्वजनिक परिवहन को प्राथमिकता दें।"
        elif lang == "bn":
            text = f"**সরাসরি উত্তর:** ঘরের কার্বন ফুটপ্রিন্ট কমানোর সবচেয়ে সাশ্রয়ী ও কার্যকর উপায় হলো বিদ্যুৎ সাশ্রয় এবং সচেতন যাতায়াত ব্যবস্থা বেছে নেওয়া।\n\n**উচ্চ প্রভাবসম্পন্ন বাস্তবসম্মত পদক্ষেপ:**\n১. **এয়ার কন্ডিশনার ২৪°C তাপমাত্রায় সেট করুন:** ২০ ডিগ্রির বদলে ২৪ ডিগ্রিতে এসি চালালে প্রায় ২৪% বিদ্যুৎ বাঁচে এবং মৌসুমে ~১৭৭ কেজি CO₂e নির্গমন হ্রাস পায়।\n২. **প্লাস্টিক বর্জন ও পুনর্ব্যবহারযোগ্য ফ্লাস্ক:** একবার ব্যবহারযোগ্য পিইটি বোতল বাদ দিয়ে স্টেইনলেস স্টিল বোতল ব্যবহারে বছরে প্রায় ৭৮ কেজি জীবনচক্র কার্বন সাশ্রয় হয়।\n৩. **স্থানীয় যাতায়াতে গণপরিবহন:** স্বল্প দূরত্বের জন্য সাইকেল বা মেট্রো বেছে নেওয়া।"
            action = "ঘরের বিদ্যুৎ সাশ্রয় ও একবার ব্যবহারযোগ্য প্লাস্টিক বর্জন দিয়ে শুরু করুন।"
        else:
            text = f"**Direct Answer:** Reducing your household environmental footprint is most effectively accomplished through high-leverage thermal and mobility optimizations that save financial cost while eliminating verified greenhouse gas emissions.\n\n**Top Prioritized Practical Actions:**\n1. **Air Conditioner Setpoint Calibration (24°C):** Raising your cooling thermostat from 20°C to 24°C reduces continuous compressor electrical load by ~24%, saving ~216 kWh (~177 kg CO₂e) per cooling season while cutting electricity utility bills.\n2. **Reusable Hydration Discipline:** Replacing disposable single-use PET bottles with a durable stainless steel flask avoids the high-heat petroleum cracking emissions of PET manufacturing (~78 kg CO₂e/year avoided for a 2-bottle/day habit).\n3. **Modal Transit Substitution:** Prioritize grade-separated rail (Metro) over solo motor vehicles, saving ~142 g CO₂e per passenger-kilometer traveled."
            action = "Calibrate cooling setpoints to 24°C and replace single-use packaging with durable alternatives."

        card = {
            "recommended_action": action,
            "problem_identified": "Avoidable household energy draw and single-use packaging consumption.",
            "reason": "Cooling compressor duty cycles and petrochemical manufacturing generate high baseline indirect emissions.",
            "expected_benefit": "Avoids ~250–400 kg CO₂e annually per household with immediate electricity cost reduction.",
            "estimated_impact": "Direct reduction of 200+ kWh electricity and dozens of kilograms of lifecycle plastic.",
            "confidence_level": "High (94%)",
            "source": "US EPA Greenhouse Gas Equivalencies & Bureau of Energy Efficiency"
        }
        return {"text": text, "structured_card": card}

    # 5. Environmental Research Analyst Domain (General / Trends)
    if lang == "hi":
        text = f"**पर्यावरण अनुसंधान विश्लेषण:** {city} के लिए वर्तमान परिवेशीय वायु गुणवत्ता सूचकांक (AQI) **{aqi}** ({atm['category']}) है, जो US EPA 40 CFR Part 58 मानक पर आधारित है।\n\n**डेटा विश्लेषण एवं रुझान:**\n- तापमान: {met['temperature_c']}°C, आर्द्रता: {met['humidity_pct']}%\n- हवा की गति: {met['wind_speed_kmh']} किमी/घंटा ({met['weather_desc']})\n\n**वैज्ञानिक अनिश्चितता:** यह रीडिंग ओपन-मेटियो CAMS वैश्विक वायुमंडलीय मॉडल और क्षेत्रीय अवशोषण पर आधारित है। सड़क स्तर के सूक्ष्म वातावरण (Micro-environments) में ट्रैफ़िक के कारण प्रदूषण स्थानीय रूप से 20-30% अधिक हो सकता है।\n\n**कार्य योजना:** यदि आप बाहर जा रहे हैं, तो दोपहर के समय जाएं जब वायुमंडलीय फैलाव उच्चतम होता है।"
        action = f"{city} में आज की वायु परिस्थितियों के अनुरूप दैनिक गतिविधियों की योजना बनाएं।"
    elif lang == "bn":
        text = f"**পরিবেশ গবেষণা বিশ্লেষণ:** {city}-এর জন্য বর্তমান বায়ু মান সূচক (AQI) **{aqi}** ({atm['category']}), যা আন্তর্জাতিক US EPA মান অনুযায়ী গণনাকৃত।\n\n**উপাত্ত ও আবহাওয়া পরিস্থিতি:**\n- তাপমাত্রা: {met['temperature_c']}°C, আর্দ্রতা: {met['humidity_pct']}%\n- বাতাসের গতি: {met['wind_speed_kmh']} কিমি/ঘণ্টা ({met['weather_desc']})\n\n**বৈজ্ঞানিক সীমাবদ্ধতা:** এটি উপগ্রহ এবং ভূপৃষ্ঠের মডেলের সমন্বয়ে তৈরি। সরাসরি ট্র্যাফিক করিডোরে বা ভবনের কোণে বায়ুর মান এর চেয়ে কিছুটা ভিন্ন হতে পারে।\n\n**পরামর্শ:** দুপুরের সময় বাইরে কাজ সম্পন্ন করুন যখন সূর্যের তাপে বাতাসের ঘনত্ব কমে এবং দূষণ দ্রুত ছড়িয়ে পড়ে।"
        action = f"বর্তমান AQI {aqi} বিবেচনায় নিয়ে আজকের বাইরের সূচি নির্ধারণ করুন।"
    else:
        text = f"**Environmental Research Analysis:** The verified ambient Air Quality Index for {city} stands at **{aqi}** ({atm['category']}), evaluated according to US EPA AQI Standard (40 CFR Part 58) criteria.\n\n**Telemetry & Meteorological Conditions:**\n- Ambient Temperature: {met['temperature_c']}°C | Relative Humidity: {met['humidity_pct']}%\n- Surface Wind Vector: {met['wind_speed_kmh']} km/h ({met['wind_direction_deg']}°) | Conditions: {met['weather_desc']}\n- Data Provenance: {atm['data_source']}\n\n**Scientific Uncertainty & Model Limitations:** Regional assimilation models provide broad grid estimates (~11 km resolution); street-level micro-climates near arterial roads may exhibit up to 30% higher localized particulate spikes due to vehicular wake turbulence.\n\n**Actionable Synthesis:** Schedule outdoor ventilation during the midday convective mixing window (11:30 AM to 3:00 PM) when solar heating maximizes atmospheric boundary layer height."
        action = f"Plan outdoor activities according to today's {atm['category']} air conditions."

    card = {
        "recommended_action": action,
        "problem_identified": f"Ambient air quality categorized as {atm['category']} (AQI {aqi}).",
        "reason": "Copernicus CAMS atmospheric model reports steady ground-level particulate loading.",
        "expected_benefit": "Informs daily travel and indoor aeration timing to prevent unnecessary peak exposure.",
        "estimated_impact": "Reduces respiratory exposure through informed scheduling.",
        "confidence_level": "Moderate-High (85%)",
        "source": atm['data_source']
    }
    return {"text": text, "structured_card": card}

def generate_follow_up_suggestions(user_message, primary_role, lang):
    """Generates 3 contextual follow-up questions tailored to the expert domain and language."""
    suggestions_map = {
        "atmospheric_scientist": {
            "en": [
                "What is the difference between PM2.5 and PM10?",
                "When is the safest time for outdoor exercise today?",
                "How does temperature inversion trap winter smog?"
            ],
            "hi": [
                "PM2.5 और PM10 में क्या अंतर है?",
                "आज बाहर व्यायाम करने का सबसे सुरक्षित समय क्या है?",
                "तापमान उलटाव (Inversion) प्रदूषण को कैसे फंसाता है?"
            ],
            "bn": [
                "PM2.5 এবং PM10 কণার মধ্যে পার্থক্য কী?",
                "আজ বাইরে ব্যায়াম করার সবচেয়ে নিরাপদ সময় কখন?",
                "শীতকালে তাপমাত্রা উল্টে গিয়ে কীভাবে ধোঁয়াশা তৈরি হয়?"
            ]
        },
        "urban_mobility_expert": {
            "en": [
                "How much carbon do I save by taking the metro?",
                "Is cycling in high AQI worse for my lungs than driving?",
                "Compare carpooling vs private car emissions."
            ],
            "hi": [
                "मेट्रो से यात्रा करने पर कितना कार्बन बचता है?",
                "क्या प्रदूषण में साइकिल चलाना कार से ज्यादा हानिकारक है?",
                "कारपूलिंग और निजी कार के उत्सर्जन की तुलना करें।"
            ],
            "bn": [
                "মেট্রোতে যাতায়াত করলে কতটা কার্বন সাশ্রয় হয়?",
                "বেশি দূষণের সময় সাইকেল চালানো কি স্বাস্থ্যের ক্ষতি করে?",
                "কারপুলিং এবং ব্যক্তিগত গাড়ির নিঃসরণের তুলনা করুন।"
            ]
        },
        "indoor_air_specialist": {
            "en": [
                "Do indoor houseplants really clean PM2.5 air?",
                "When should I open my windows today for ventilation?",
                "How effective are HEPA H13 filters against cooking smoke?"
            ],
            "hi": [
                "क्या घर के पौधे वास्तव में PM2.5 हवा साफ करते हैं?",
                "आज ताजी हवा के लिए खिड़कियां कब खोलनी चाहिए?",
                "रसोई के धुएं के लिए HEPA H13 फिल्टर कितने प्रभावी हैं?"
            ],
            "bn": [
                "ঘরের গাছপালা কি আসলেই PM2.5 বাতাস পরিষ্কার করে?",
                "আজ ঘরে বাতাস প্রবেশের জন্য কখন জানালা খোলা উচিত?",
                "রান্নার ধোঁয়া দূর করতে HEPA ফিল্টার কতটা কার্যকর?"
            ]
        },
        "sustainability_strategist": {
            "en": [
                "How much electricity does setting AC to 24°C save?",
                "What are the best affordable sustainable habits to start?",
                "Calculate my annual savings by avoiding plastic bottles."
            ],
            "hi": [
                "एसी को 24°C पर रखने से कितनी बिजली बचती है?",
                "शुरू करने के लिए सबसे किफायती पर्यावरण-अनुकूल आदतें क्या हैं?",
                "प्लास्टिक बोतलें न खरीदने पर वार्षिक बचत का हिसाब लगाएं।"
            ],
            "bn": [
                "এসি ২৪°C তাপমাত্রায় চালালে কতটা বিদ্যুৎ সাশ্রয় হয়?",
                "শুরু করার জন্য সবচেয়ে সহজ পরিবেশবান্ধব অভ্যাসগুলো কী?",
                "প্লাস্টিকের বোতল বর্জন করলে বছরে কতটা দূষণ এড়ানো যায়?"
            ]
        },
        "environmental_analyst": {
            "en": [
                "How is Open-Meteo CAMS data calibrated against ground stations?",
                "Compare today's AQI trend with yesterday's diurnal curve.",
                "What are the main uncertainties in urban air quality models?"
            ],
            "hi": [
                "ओपन-मेटियो CAMS डेटा को ज़मीनी स्टेशनों के साथ कैसे जांचा जाता है?",
                "कल और आज के प्रदूषण के रुझान की तुलना करें।",
                "शहरी वायु गुणवत्ता मॉडल में मुख्य अनिश्चितताएं क्या हैं?"
            ],
            "bn": [
                "CAMS মডেল কীভাবে ভূপৃষ্ঠের পরিমাপক যন্ত্রের সাথে মেলানো হয়?",
                "গতকালের সাথে আজকের বায়ু মানের প্রবণতা তুলনা করুন।",
                "বায়ু মান পূর্বাভাসের প্রধান অনিশ্চয়তাগুলো কী কী?"
            ]
        }
    }
    
    role_suggestions = suggestions_map.get(primary_role, suggestions_map["atmospheric_scientist"])
    return role_suggestions.get(lang, role_suggestions["en"])

