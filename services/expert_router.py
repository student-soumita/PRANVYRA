"""
PRANVYRA INTELLIGENCE CORE — Expert Router & Intent Classifier
Intelligently classifies user queries into specialized expert roles
or multi-expert syntheses across English, Hindi, and Bengali.
"""
import re
import logging

logger = logging.getLogger(__name__)

EXPERT_ROLES = {
    "atmospheric_scientist": {
        "id": "atmospheric_scientist",
        "title": "Atmospheric Scientist",
        "title_hi": "वायुमंडलीय वैज्ञानिक",
        "title_bn": "বায়ুমণ্ডলীয় বিজ্ঞানী",
        "icon": "cloud-rain",
        "focus": "AQI, Particulates (PM2.5/PM10), Gaseous Pollutants, Meteorology & Inversion Dynamics",
        "keywords": [
            # English
            "aqi", "pm2.5", "pm10", "pm 2.5", "pm 10", "ozone", "o3", "no2", "nitrogen dioxide",
            "so2", "sulfur dioxide", "co", "carbon monoxide", "smog", "haze", "inversion", "dispersion",
            "wind", "temperature", "humidity", "fog", "particulate", "pollution level", "air quality index",
            "ppm", "ug/m3", "boundary layer", "stagnation", "photochemical", "why is pollution", "air today",
            "toxic air", "smoke outside", "dust storm", "satellite", "cams", "monitoring station",
            "precaution", "precautions", "unhealthy", "mask", "masks", "protection", "safe outdoor", "health effect",
            # Hindi
            "हवा", "वायु", "प्रदूषण", "एक्यूआई", "धुंध", "तापमान", "नमी", "हवा की गति", "धुआं",
            "सल्फर", "नाइट्रोजन", "कण", "पार्टिकुलेट", "मौसम", "बढ़ रहा है", "खराब हवा",
            "सावधानी", "सावधानियां", "बचाव", "सुरक्षा", "मास्क", "खराब", "स्वास्थ्य",
            # Bengali
            "বাতাস", "বায়ু", "দূষণ", "কুয়াশা", "তাপমাত্রা", "আর্দ্রতা", "বায়ুর মান", "বাতাসের মান",
            "ধোঁয়াশা", "কণা", "নাইট্রোজেন", "ওজোন", "খারাপ বাতাস",
            "সতর্কতা", "সাবধানতা", "সুরক্ষা", "মাস্ক", "খারাপ", "অস্বাস্থ্যকর", "স্বাস্থ্য"
        ]
    },
    "urban_mobility_expert": {
        "id": "urban_mobility_expert",
        "title": "Urban Mobility & Emission Expert",
        "title_hi": "शहरी गतिशीलता एवं उत्सर्जन विशेषज्ञ",
        "title_bn": "নগর গতিশীলতা ও নিঃসরণ বিশেষজ্ঞ",
        "icon": "bus",
        "focus": "Commuting, DEFRA Emission Factors, Transit Mode Comparison & Travel Exposure",
        "keywords": [
            # English
            "commute", "travel", "transport", "metro", "subway", "train", "bus", "car", "motorcycle",
            "bike", "scooter", "cycling", "walking", "carpool", "tailpipe", "emission", "vehicle",
            "traffic", "transit", "distance", "km", "drive", "route", "defra", "petrol", "diesel",
            "cng", "electric vehicle", "ev", "highway", "rush hour", "roadside exposure", "journey",
            # Hindi
            "सफ़र", "यात्रा", "गाड़ी", "मेट्रो", "बस", "कार", "मोटरसाइकिल", "स्कूटर", "साइकिल",
            "उत्सर्जन", "पेट्रोल", "डीजल", "दूरी", "ट्रैफिक", "सड़क", "रूट", "रास्ता",
            # Bengali
            "যাতায়াত", "ভ্রমণ", "গাড়ি", "মেট্রো", "বাস", "মোটরসাইকেল", "সাইকেল", "হাঁটা",
            "নিঃসরণ", "পেট্রোল", "ডিজেল", "দূরত্ব", "রাস্তা", "ট্র্যাফিক"
        ]
    },
    "indoor_air_specialist": {
        "id": "indoor_air_specialist",
        "title": "Indoor Air Quality Specialist",
        "title_hi": "घर की वायु गुणवत्ता विशेषज्ञ",
        "title_bn": "ঘরের অভ্যন্তরীণ বায়ু মান বিশেষজ্ঞ",
        "icon": "home",
        "focus": "Indoor Ventilation, Cooking Exhaust, HEPA Filtration, Dust & Infiltration Mitigation",
        "keywords": [
            # English
            "indoor", "room", "house", "home", "bedroom", "kitchen", "cooking", "smoke", "smell",
            "odor", "ventilation", "ventilate", "window", "purifier", "hepa", "filter", "filtration",
            "houseplant", "plants", "exhaust", "chimney", "lpg", "gas stove", "dust", "mold",
            "humidity", "damp", "sealing", "air conditioner", "ac", "hvac", "cleaning", "frying",
            # Hindi
            "घर", "कमरा", "रसोई", "किचन", "खाना बनाना", "धुआं", "खिड़की", "हवादार", "प्यूरीफायर",
            "फिल्टर", "एसी", "धूल", "पौधे", "वेंटिलेशन", "सिलेंडर", "गैस चूल्हा",
            # Bengali
            "ঘর", "বাড়ি", "রান্নাঘর", "রান্না", "ধোঁয়া", "জানালা", "বায়ু চলাচল", "ফিল্টার",
            "পিউরিফায়ার", "এসি", "ধুলো", "গাছপালা", "ভেন্টিলেশন", "চুলা"
        ]
    },
    "sustainability_strategist": {
        "id": "sustainability_strategist",
        "title": "Sustainability Strategist",
        "title_hi": "स्थिरता एवं जीवनशैली रणनीतिकार",
        "title_bn": "স্থায়িত্ব ও জীবনযাত্রা কৌশলবিদ",
        "icon": "leaf",
        "focus": "Realistic Lifestyle Shifts, Energy Conservation, Plastic & Carbon Footprint Reduction",
        "keywords": [
            # English
            "sustainable", "sustainability", "carbon footprint", "lifestyle", "habit", "plastic",
            "bottle", "waste", "recycle", "energy", "electricity", "conservation", "green points",
            "eco", "co2 reduction", "climate impact", "what-if", "switch", "alternative", "save power",
            "kwh", "thermostat", "sustainable choices", "reusable", "zero waste", "solar",
            # Hindi
            "स्थिरता", "जीवनशैली", "कार्बन फुटप्रिंट", "पर्यावरण", "प्लास्टिक", "कचरा", "बिजली",
            "ऊर्जा", "बचत", "विकल्प", "आदत", "ग्रीन प्वाइंट्स",
            # Bengali
            "স্থায়িত্ব", "জীবনযাত্রা", "কার্বন ফুটপ্রিন্ট", "প্লাস্টিক", "বর্জ্য", "বিদ্যুৎ",
            "শক্তি সাশ্রয়", "বিকল্প", "অভ্যাস", "সবুজ পয়েন্ট"
        ]
    },
    "environmental_analyst": {
        "id": "environmental_analyst",
        "title": "Environmental Research Analyst",
        "title_hi": "पर्यावरण अनुसंधान विश्लेषक",
        "title_bn": "পরিবেশ গবেষণা বিশ্লেষক",
        "icon": "line-chart",
        "focus": "Datasets, Trends, Historical Comparisons, Scientific Uncertainty & Evidence Evaluation",
        "keywords": [
            # English
            "trend", "compare", "historical", "data", "dataset", "statistics", "correlation",
            "causation", "research", "study", "scientific evidence", "sensor vs model", "satellite data",
            "cams model", "who guideline", "epa standard", "uncertainty", "confidence level",
            "yesterday vs today", "seasonal", "winter vs summer", "analysis", "evaluation", "graph",
            # Hindi
            "रुझান", "ट्रेंड", "तुलना", "डेटा", "आंकड़े", "इतिहास", "शोध", "अध्ययन", "सबूत", "वैज्ञानिक",
            # Bengali
            "প্রবণতা", "তুলনা", "উপাত্ত", "তথ্য", "পরিসংখ্যান", "গবেষণা", "প্রমাণ", "ঐতিহাসিক"
        ]
    }
}

def detect_expert_roles(message, requested_role="auto", context=None):
    """
    Determines the primary and secondary expert roles for a user's inquiry.
    
    Returns:
        {
            "primary_role": str (role_id),
            "multi_expert_roles": list of str (role_ids),
            "routing_reason": str,
            "is_auto_routed": bool
        }
    """
    cleaned_msg = message.lower().strip()
    
    # 1. If user explicitly picked a manual expert role, honor it
    if requested_role and requested_role != "auto" and requested_role in EXPERT_ROLES:
        return {
            "primary_role": requested_role,
            "multi_expert_roles": [requested_role],
            "routing_reason": f"Manually selected expert: {EXPERT_ROLES[requested_role]['title']}.",
            "is_auto_routed": False
        }
    
    # 2. Score matches across all roles
    scores = {}
    for role_id, role_info in EXPERT_ROLES.items():
        score = 0
        for kw in role_info["keywords"]:
            # Word boundary matching where appropriate or substring for Indian languages
            if len(kw) <= 3 and kw.isalpha():
                if re.search(r'\b' + re.escape(kw) + r'\b', cleaned_msg):
                    score += 3
            else:
                if kw in cleaned_msg:
                    score += 2
        scores[role_id] = score

    # Contextual boosts
    if context:
        # If user has a commute question in context
        if "commute" in cleaned_msg or "travel" in cleaned_msg or "km" in cleaned_msg:
            scores["urban_mobility_expert"] += 2
        # If discussing indoor room or kitchen
        if "room" in cleaned_msg or "indoor" in cleaned_msg or "kitchen" in cleaned_msg or "cook" in cleaned_msg:
            scores["indoor_air_specialist"] += 2
        # If asking why or trend
        if "why" in cleaned_msg or "compare" in cleaned_msg or "difference" in cleaned_msg:
            scores["environmental_analyst"] += 1
            scores["atmospheric_scientist"] += 1

    sorted_roles = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_role, top_score = sorted_roles[0]

    # Default fallback to Atmospheric Scientist if no strong match
    if top_score < 2:
        top_role = "atmospheric_scientist"
        top_score = 1
        multi_roles = ["atmospheric_scientist"]
        reason = "Routed to Atmospheric Scientist as general environmental baseline."
    else:
        # Check for multi-expert synergy (e.g. top 2 are both significant)
        second_role, second_score = sorted_roles[1]
        if second_score >= 2 and (second_score / top_score) >= 0.6:
            multi_roles = [top_role, second_role]
            reason = f"Multi-domain inquiry detected: Synthesizing {EXPERT_ROLES[top_role]['title']} and {EXPERT_ROLES[second_role]['title']}."
        else:
            multi_roles = [top_role]
            reason = f"Primary intent matched: {EXPERT_ROLES[top_role]['title']}."

    logger.info(f"Expert routing for '{message[:40]}...': {top_role} (multi: {multi_roles})")

    return {
        "primary_role": top_role,
        "multi_expert_roles": multi_roles,
        "routing_reason": reason,
        "is_auto_routed": True
    }

def get_expert_details(role_id):
    """Returns metadata for a given role ID or the default."""
    return EXPERT_ROLES.get(role_id, EXPERT_ROLES["atmospheric_scientist"])

def list_all_experts():
    """Returns list of all supported expert roles for frontend UI."""
    return [
        {
            "id": r["id"],
            "title": r["title"],
            "title_hi": r["title_hi"],
            "title_bn": r["title_bn"],
            "icon": r["icon"],
            "focus": r["focus"]
        }
        for r in EXPERT_ROLES.values()
    ]

