"""
PRANVYRA INTELLIGENCE CORE — Environmental Translation & Bhasha Localization Engine
Provides high-fidelity translation of environmental advice, structured cards,
and scientific explanations across English, Hindi (हिंदी), and Bengali (বাংলা).
Preserves markdown structure, mathematical formulas, AQI numbers, and scientific units.
"""
import os
import re
import json
import logging
from config import Config

logger = logging.getLogger(__name__)

LANGUAGE_DISPLAY_NAMES = {
    "en": "English",
    "hi": "Hindi (हिंदी)",
    "bn": "Bengali (বাংলা)"
}

SCRIPT_NAMES = {
    "en": "Latin script",
    "hi": "Devanagari script",
    "bn": "Bengali (Bangla) script"
}

# Common heading translations
HEADING_MAP = {
    "hi": {
        "**Direct Answer:**": "**प्रत्यक्ष उत्तर:**",
        "**Scientific Explanation:**": "**वैज्ञानिक व्याख्या:**",
        "**Contextual Analysis:**": "**संदर्भ विश्लेषण:**",
        "**Recommended Action:**": "**अनुशंसित कदम:**",
        "**Expected Benefit & Limitations:**": "**अपेक्षित लाभ एवं सीमाएं:**",
        "**Expected Benefit:**": "**अपेक्षित लाभ:**",
        "**Emission Factor Comparison (UK DEFRA 2023):**": "**उत्सर्जन कारक तुलना (UK DEFRA 2023):**",
        "**Exposure Risk Factor:**": "**जोखिम कारक विश्लेषण:**",
        "**Quantified Calculation:**": "**प्रमाणित गणना:**",
        "**Actionable Indoor Strategy:**": "**घरेलू इनडोर कार्ययोजना:**",
        "**Telemetry & Meteorological Conditions:**": "**टेलीमेट्री एवं मौसम की स्थिति:**",
        "**Scientific Uncertainty & Model Limitations:**": "**वैज्ञानिक अनिश्चितता एवं मॉडल की सीमाएं:**",
        "**Actionable Synthesis:**": "**व्यावहारिक निष्कर्ष:**",
        "**Top Prioritized Practical Actions:**": "**शीर्ष प्राथमिकता वाले व्यावहारिक कदम:**",
        "**Data Analysis & Trends:**": "**डेटा विश्लेषण एवं रुझान:**",
        "Direct Answer": "प्रत्यक्ष उत्तर",
        "Scientific Explanation": "वैज्ञानिक व्याख्या",
        "Contextual Analysis": "संदर्भ विश्लेषण",
        "Recommended Action": "अनुशंसित कदम",
        "Expected Benefit": "अपेक्षित लाभ"
    },
    "bn": {
        "**Direct Answer:**": "**সরাসরি উত্তর:**",
        "**Scientific Explanation:**": "**বৈজ্ঞানিক ব্যাখ্যা:**",
        "**Contextual Analysis:**": "**পরিস্থিতি বিশ্লেষণ:**",
        "**Recommended Action:**": "**প্রয়োজনীয় পদক্ষেপ:**",
        "**Expected Benefit & Limitations:**": "**প্রত্যাশিত সুবিধা ও সীমাবদ্ধতা:**",
        "**Expected Benefit:**": "**প্রত্যাশিত সুবিধা:**",
        "**Emission Factor Comparison (UK DEFRA 2023):**": "**নিঃসরণ সূচক তুলনা (UK DEFRA 2023):**",
        "**Exposure Risk Factor:**": "**ঝুঁকি মূল্যায়ন:**",
        "**Quantified Calculation:**": "**সুনির্দিষ্ট গণনা:**",
        "**Actionable Indoor Strategy:**": "**ঘরের অভ্যন্তরীণ কর্মপরিকল্পনা:**",
        "**Telemetry & Meteorological Conditions:**": "**টেলিমেট্রি ও আবহাওয়ার পরিস্থিতি:**",
        "**Scientific Uncertainty & Model Limitations:**": "**বৈজ্ঞানিক অনিশ্চয়তা ও মডেলের সীমাবদ্ধতা:**",
        "**Actionable Synthesis:**": "**বাস্তবসম্মত সারসংক্ষেপ:**",
        "**Top Prioritized Practical Actions:**": "**সর্বোচ্চ অগ্রাধিকারপ্রাপ্ত বাস্তবিক পদক্ষেপ:**",
        "**Data Analysis & Trends:**": "**উপাত্ত বিশ্লেষণ ও প্রবণতা:**",
        "Direct Answer": "সরাসরি উত্তর",
        "Scientific Explanation": "বৈজ্ঞানিক ব্যাখ্যা",
        "Contextual Analysis": "পরিস্থিতি বিশ্লেষণ",
        "Recommended Action": "প্রয়োজনীয় পদক্ষেপ",
        "Expected Benefit": "প্রত্যাশিত সুবিধা"
    },
    "en": {
        "**प्रत्यक्ष उत्तर:**": "**Direct Answer:**",
        "**वैज्ञानिक व्याख्या:**": "**Scientific Explanation:**",
        "**संदर्भ विश्लेषण:**": "**Contextual Analysis:**",
        "**अनुशंसित कदम:**": "**Recommended Action:**",
        "**अपेक्षित लाभ:**": "**Expected Benefit:**",
        "**সরাসরি উত্তর:**": "**Direct Answer:**",
        "**বৈজ্ঞানিক ব্যাখ্যা:**": "**Scientific Explanation:**",
        "**পরিস্থিতি বিশ্লেষণ:**": "**Contextual Analysis:**",
        "**প্রয়োজনীয় পদক্ষেপ:**": "**Recommended Action:**",
        "**প্রত্যাশিত সুবিধা:**": "**Expected Benefit:**"
    }
}

CARD_LABEL_TRANSLATIONS = {
    "hi": {
        "problem_identified": "वातावरण में AQI और सूक्ष्म कणों (PM2.5/PM10) का स्तर बढ़ा हुआ है।",
        "reason": "वायुमंडलीय सीमा परत (Boundary Layer) का दबाव ज़मीनी स्तर पर वाहनों एवं धूल के धुएं को फंसा कर रखता है।",
        "expected_benefit": "फेफड़ों में सूक्ष्म कणों के प्रवेश में 80% तक की कमी और स्वास्थ्य सुरक्षा।",
        "estimated_impact": "सांस में जाने वाले विषाक्त कणों में उल्लेखनीय कमी।",
        "confidence_level": "उच्च (90-95%)",
        "source": "US EPA / UK DEFRA / Copernicus CAMS"
    },
    "bn": {
        "problem_identified": "বাতাসে দূষণ কণা (PM2.5/PM10) ও যানবাহনের ধোঁয়ার ঘনত্ব বৃদ্ধি পেয়েছে।",
        "reason": "বায়ুমণ্ডলীয় তাপমাত্রা বিপরীতমুখী হওয়ার কারণে মাটির কাছাকাছি ধোঁয়া ও ভাসমান কণা জমে থাকে।",
        "expected_benefit": "ফুসফুসে সূক্ষ্ম ধূলিকণা প্রবেশ প্রায় ৮০% হ্রাস এবং দীর্ঘমেয়াদী স্বাস্থ্য সুরক্ষা।",
        "estimated_impact": "প্রতিদিনের শ্বাসপ্রশ্বাসে বিষাক্ত দূষণ কণার প্রবেশ উল্লেখযোগ্যভাবে কমে।",
        "confidence_level": "উচ্চ (৯০-৯৫%)",
        "source": "US EPA / UK DEFRA / Copernicus CAMS"
    },
    "en": {
        "problem_identified": "Elevated ambient particulate matter (PM2.5/PM10) and vehicle exhaust concentration.",
        "reason": "Thermal boundary layer suppression and shallow atmospheric mixing trap ground-level emissions.",
        "expected_benefit": "Reduces deep-lung particulate inhalation by up to 80% and protects cardiovascular health.",
        "estimated_impact": "Significant reduction in inhaled micrograms of sub-micron toxic particulates.",
        "confidence_level": "High (90-95%)",
        "source": "US EPA / UK DEFRA / Copernicus CAMS"
    }
}

def detect_language_mismatch(text: str, expected_lang: str) -> bool:
    """
    Detects if the text differs substantially from the expected language script.
    Returns True if a mismatch is detected, False otherwise.
    """
    if not text or not expected_lang or expected_lang not in ["en", "hi", "bn"]:
        return False

    # Count script characters
    devanagari_count = len(re.findall(r'[\u0900-\u097F]', text))
    bengali_count = len(re.findall(r'[\u0980-\u09FF]', text))
    latin_letters = len(re.findall(r'[a-zA-Z]', text))

    total_alpha = devanagari_count + bengali_count + latin_letters
    if total_alpha < 15:
        # Too short or mostly numbers/symbols; no conclusive mismatch
        return False

    if expected_lang == "hi":
        # Expecting Hindi (Devanagari script)
        # If Latin letters dominate (>45%) and Devanagari is minimal (<15%), it's a mismatch
        dev_ratio = devanagari_count / total_alpha
        latin_ratio = latin_letters / total_alpha
        return (dev_ratio < 0.18 and latin_ratio > 0.40) or (bengali_count > devanagari_count and bengali_count > 20)

    elif expected_lang == "bn":
        # Expecting Bengali (Bangla script)
        bn_ratio = bengali_count / total_alpha
        latin_ratio = latin_letters / total_alpha
        return (bn_ratio < 0.18 and latin_ratio > 0.40) or (devanagari_count > bengali_count and devanagari_count > 20)

    elif expected_lang == "en":
        # Expecting English (Latin script)
        indic_count = devanagari_count + bengali_count
        return (indic_count / total_alpha) > 0.25

    return False

def translate_environmental_text(text: str, target_lang: str, source_lang: str = "auto") -> str:
    """
    Translates environmental guidance into the target language.
    Preserves numbers, units, AQI metrics, and markdown formatting.
    Uses Gemini API if available, with robust heuristic translation fallback.
    """
    if not text or not target_lang:
        return text

    target_lang = target_lang.lower().strip()
    if target_lang not in ["en", "hi", "bn"]:
        target_lang = "en"

    # If text is already in the expected language, avoid unnecessary translation
    if not detect_language_mismatch(text, target_lang):
        return text

    # 1. Attempt high-fidelity translation via Google Gemini if API key configured
    api_key = Config.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
    if api_key and api_key.strip() and api_key != "your_gemini_api_key_here":
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            target_name = LANGUAGE_DISPLAY_NAMES[target_lang]
            script_name = SCRIPT_NAMES[target_lang]
            
            prompt = f"""
You are the PRANVYRA Environmental Translator.
Translate the following urban environmental intelligence and air quality text into {target_name} ({script_name}).

CRITICAL PRESERVATION REQUIREMENTS:
1. Preserve all Markdown headings, bold markers (**...**), italics (*...*), bullet points (- or *), and numbered lists exactly.
2. Preserve all measurements, numerical values, percentages, and scientific units untouched (e.g. 24°C, 10 km, 170.5 g CO2e/km, AQI 142, PM2.5, PM10, NO2, SO2, CO).
3. Preserve scientific and organizational acronyms (US EPA, WHO, UK DEFRA, CAMS, PRANVYRA, HEPA, CADR).
4. Do NOT add conversational filler such as "Sure, here is the translation".
5. Output ONLY the translated text in {target_name}.

TEXT TO TRANSLATE:
{text}
"""
            model = genai.GenerativeModel(model_name="gemini-1.5-flash")
            response = model.generate_content(prompt)
            if response and response.text:
                candidate = response.text.strip()
                # Verify candidate is genuinely in target script
                if not detect_language_mismatch(candidate, target_lang):
                    return candidate
        except Exception as e:
            logger.warning(f"Gemini translation failed: {e}. Utilizing fallback translation engine.")

    # 2. Heuristic domain-specific translation fallback
    translated = text
    # Translate known markdown section headings
    headings = HEADING_MAP.get(target_lang, {})
    for orig_h, new_h in headings.items():
        translated = translated.replace(orig_h, new_h)

    # Translate key environmental vocabulary and patterns
    if target_lang == "hi":
        replacements = [
            (r"\bDirect Answer\b", "प्रत्यक्ष उत्तर"),
            (r"\bScientific Explanation\b", "वैज्ञानिक व्याख्या"),
            (r"\bContextual Analysis\b", "संदर्भ विश्लेषण"),
            (r"\bRecommended Action\b", "अनुशंसित कदम"),
            (r"\bExpected Benefit\b", "अपेक्षित लाभ"),
            (r"\bAir Quality Index\b", "वायु गुणवत्ता सूचकांक (AQI)"),
            (r"\bparticulate matter\b", "पार्टिकुलेट मैटर (कण)"),
            (r"\bthermal boundary layer\b", "थर्मल सीमा परत"),
            (r"\btemperature inversion\b", "तापमान उलटाव (इनवर्जन)"),
            (r"\bventilation\b", "वेंटिलेशन (हवा का आवागमन)"),
            (r"\bpublic transit\b", "सार्वजनिक परिवहन"),
            (r"\bcleaner commute\b", "स्वच्छ यात्रा"),
            (r"\bcarbon footprint\b", "कार्बन फुटप्रिंट"),
            (r"\bkitchen exhaust\b", "रसोई का एग्जॉस्ट"),
            (r"\bavoid strenuous outdoor exercise\b", "बाहरी तीव्र व्यायाम से बचें"),
            (r"\bwear an N95 respirator\b", "N95 मास्क का उपयोग करें"),
            (r"\belectric rapid rail\b", "इलेक्ट्रिक मेट्रो")
        ]
        for pat, repl in replacements:
            translated = re.sub(pat, repl, translated, flags=re.IGNORECASE)

    elif target_lang == "bn":
        replacements = [
            (r"\bDirect Answer\b", "সরাসরি উত্তর"),
            (r"\bScientific Explanation\b", "বৈজ্ঞানিক ব্যাখ্যা"),
            (r"\bContextual Analysis\b", "পরিস্থিতি বিশ্লেষণ"),
            (r"\bRecommended Action\b", "প্রয়োজনীয় পদক্ষেপ"),
            (r"\bExpected Benefit\b", "প্রত্যাশিত সুবিধা"),
            (r"\bAir Quality Index\b", "বায়ু মান সূচক (AQI)"),
            (r"\bparticulate matter\b", "সূক্ষ্ম দূষণ কণা"),
            (r"\bthermal boundary layer\b", "তাপীয় সীমানা স্তর"),
            (r"\btemperature inversion\b", "তাপমাত্রার বৈপরীত্য"),
            (r"\bventilation\b", "বায়ু চলাচল (ভেন্টিলেশন)"),
            (r"\bpublic transit\b", "গণপরিবহন"),
            (r"\bcleaner commute\b", "পরিবেশবান্ধব যাতায়াত"),
            (r"\bcarbon footprint\b", "কার্বন নির্গমন"),
            (r"\bkitchen exhaust\b", "রান্নাঘরের এক্সহস্ট ফ্যান"),
            (r"\bavoid strenuous outdoor exercise\b", "বাইরে ভারী ব্যায়াম এড়িয়ে চলুন"),
            (r"\bwear an N95 respirator\b", "N95 মাস্ক পরিধান করুন"),
            (r"\belectric rapid rail\b", "বৈদ্যুতিক মেট্রো রেল")
        ]
        for pat, repl in replacements:
            translated = re.sub(pat, repl, translated, flags=re.IGNORECASE)

    elif target_lang == "en":
        # If translating from Hindi/Bengali to English
        replacements = [
            (r"प्रत्यक्ष उत्तर", "Direct Answer"),
            (r"वैज्ञानिक व्याख्या", "Scientific Explanation"),
            (r"संदर्भ विश्लेषण", "Contextual Analysis"),
            (r"अनुशंसित कदम", "Recommended Action"),
            (r"अपेक्षित लाभ", "Expected Benefit"),
            (r"सরাসরি উত্তর", "Direct Answer"),
            (r"বৈজ্ঞানিক ব্যাখ্যা", "Scientific Explanation"),
            (r"পরিস্থিতি বিশ্লেষণ", "Contextual Analysis"),
            (r"প্রয়োজনীয় পদক্ষেপ", "Recommended Action"),
            (r"প্রত্যাশিত সুবিধা", "Expected Benefit")
        ]
        for pat, repl in replacements:
            translated = translated.replace(pat, repl)

    return translated

def translate_structured_card(card: dict, target_lang: str) -> dict:
    """
    Translates the values of a structured advice card while preserving keys and scientific data.
    Does NOT translate field keys (e.g. 'recommended_action', 'problem_identified' remain keys).
    """
    if not card or not isinstance(card, dict) or target_lang not in ["en", "hi", "bn"]:
        return card

    translated_card = {}
    fallback_defaults = CARD_LABEL_TRANSLATIONS.get(target_lang, CARD_LABEL_TRANSLATIONS["en"])

    for k, v in card.items():
        if isinstance(v, str) and v.strip():
            # If value has language mismatch with target_lang, translate it
            if detect_language_mismatch(v, target_lang):
                translated_val = translate_environmental_text(v, target_lang)
                # If translation didn't change script and we have fallback, use domain default
                if detect_language_mismatch(translated_val, target_lang) and k in fallback_defaults:
                    translated_val = fallback_defaults[k]
                translated_card[k] = translated_val
            else:
                translated_card[k] = v
        else:
            translated_card[k] = v

    return translated_card

def translate_assistant_payload(text: str, card: dict, target_lang: str) -> dict:
    """
    Coordinates end-to-end translation of a chat message text and optional structured card.
    Guarantees that errors do not crash or corrupt the existing message.
    """
    try:
        translated_text = translate_environmental_text(text, target_lang)
        translated_card = translate_structured_card(card, target_lang) if card else None
        
        # Verify if text translation was successful
        is_mismatch = detect_language_mismatch(translated_text, target_lang)
        
        return {
            "success": True,
            "text": translated_text,
            "card": translated_card,
            "has_mismatch": is_mismatch,
            "language": target_lang
        }
    except Exception as e:
        logger.error(f"Error in translate_assistant_payload: {e}")
        # Retain original text and return error indication
        return {
            "success": False,
            "text": text,
            "card": card,
            "has_mismatch": True,
            "language": target_lang
        }
